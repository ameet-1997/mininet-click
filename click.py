"""
Provides a Click based switch class.
Forked from https://github.com/frawi/click-mininet
"""
import collections
import itertools
from string import Template

from mininet.node import Switch
from mininet.util import ipParse, ipStr

Entry = collections.namedtuple("Entry", ["node", "intf_to_node"])


class ClickSwitch(Switch):
    """Use ClickUserSwitch or ClickKernelSwitch"""

    @property
    def install_cmd(self):
        raise NotImplementedError

    @property
    def uninstall_cmd(self):
        raise NotImplementedError

    def __init__(self, name, switch_type="router", log_file=None, **params):
        Switch.__init__(self, name, **params)
        self.log_file = log_file if log_file else "{}.log".format(self.name)
        if switch_type == "simple_switch":
            self.make_config = self.simple_switch
        elif switch_type == "router":
            self.make_config = self.router
        else:
            raise NotImplementedError(switch_type)

    def links(self):
        return [intf.link for intf in self.intfs.values() if intf.name != "lo"]

    def intf_from_name(self, name):
        return [intf for intf in self.intfs.values() if intf.name == name][0]

    def init_neighbors(self):
        self.node_table = {}
        self.intf_to_neighbor = {}
        for l in self.links():
            neighbor_intf = l.intf1 if l.intf1.node != self else l.intf2
            self_intf = l.intf1 if l.intf1.node == self else l.intf2
            self.intf_to_neighbor[self_intf.name] = neighbor_intf.node
            self.node_table[neighbor_intf.node.name] = Entry(
                node=neighbor_intf.node,
                intf_to_node=self_intf,
            )

    def update(self):
        neighbors = list(self.intf_to_neighbor.items())
        updated = False
        for intf, n in neighbors:
            if not hasattr(n, "node_table"):
                continue
            for name, entry in n.node_table.items():
                if name not in self.node_table and name != self.name:
                    updated = True
                    self.node_table[name] = Entry(
                        node=entry.node,
                        intf_to_node=self.intf_from_name(intf),
                    )
        return updated

    def router(self):
        # Sort by the name of the host (e.g. h0).
        nodes = sorted(self.node_table.values(), key=lambda n: n.node.name)
        intfs = sorted(
            list(set([n.intf_to_node for n in nodes])), key=lambda i: i.name
        )
        intf_to_idx = {intf.name: idx for idx, intf in enumerate(intfs)}

        out = []

        # Add some comments
        for n in nodes:
            out.append(
                "// {} {} {} <-> {} {}".format(
                    intf_to_idx[n.intf_to_node.name],
                    n.node.name,
                    n.node.IP(),
                    n.intf_to_node.name,
                    n.intf_to_node.MAC(),
                )
            )
        out[-1] += "\n"

        # Three buckets: ARP request, ARP response, IP packets, anything else.
        out.append(
            "c0 :: Classifier(12/0806 20/0001, 12/0806 20/0002, "
            "12/0800, -);\n"
        )

        # FromDevice: 'Paint' packets from each interface so we can identify
        # the source later if needed, then send it to the classifier.
        for idx, intf in enumerate(intfs):
            out.append(
                "\n".join(
                    [
                        "FromDevice('{}')".format(intf.name),
                        "-> Print(got{})".format(idx),
                        "-> Paint({})".format(idx),
                        "-> [0]c0;\n",
                    ]
                )
            )

        # ToDevice variables.
        for idx, intf in enumerate(intfs):
            out.append(
                "\n".join(
                    [
                        "out{} :: Queue(8)".format(idx),
                        "-> Print(out{})".format(idx),
                        "-> ToDevice('{}');\n".format(intf),
                    ]
                )
            )

        # Proxy ARP for every request. I.e. if the topography is:
        #   h1 -- s0-eth1 : s0 : s0-eth2 -- h2
        # and h1 sends an ARP request for h2, respond with "s0-eth1".
        arp_responder_s = "ARPResponder(\n  "
        arp_responder_s += ",\n  ".join(
            [
                "{} $mac".format(n.node.IP())
                for n in nodes
                if n.node.IP()  # switches don't have IP addresses
            ]
        )
        arp_responder_s += ")"
        arp_responder_t = Template(arp_responder_s)

        # `Tee` splits the request to n channels (one per interface). For each
        # interface, respond with the proxy ARP table.
        out.append("c0[0] -> arpt :: Tee({});\n".format(len(intfs)))
        for idx, intf in enumerate(intfs):
            out.append(
                "\n".join(
                    [
                        "arpt[{}]".format(idx),
                        "-> CheckPaint({})".format(idx),
                        "-> Print(arp_req_from{})".format(idx),
                        "-> {}".format(
                            arp_responder_t.substitute(mac=intf.MAC())
                        ),
                        "-> Print(arp_response)",
                        "-> out{};\n".format(idx),
                    ]
                )
            )

        # ARP responses--just toss because we know where everything is.
        out.append("c0[1] -> Discard;\n")

        # non-IP packets are dropped.
        out.append("c0[3] -> Discard;\n")

        # IP request. Static routing table maps IP address to the index of the
        # interface.
        rt = "rt :: StaticIPLookup(\n  "
        rt += ",\n  ".join(
            [
                "{}/32 {}".format(n.node.IP(), intf_to_idx[n.intf_to_node.name])
                for n in nodes
                if n.node.IP()
            ]
        )
        rt += ");\n"
        out.append(rt)

        out.append(
            "\n".join(
                [
                    "c0[2]",
                    "-> Print(ip_req)",
                    "-> Strip(14)",  # Strip ethernet header
                    "-> Print(stripped)",
                    "-> CheckIPHeader",
                    "-> GetIPAddress(16)",
                    "-> Print(ip)",
                    "-> [0]rt;\n",
                ]
            )
        )

        # Route requests to the correct interface.
        for idx, intf in enumerate(intfs):
            src_mac = intf.MAC()
            dst_mac = (
                intf.link.intf1 if intf.link.intf1 != intf else intf.link.intf2
            ).MAC()
            out.append(
                "\n".join(
                    [
                        "rt[{}]".format(idx),
                        "-> Print(out{})".format(idx),
                        "-> EtherEncap(0x0800, {}, {})".format(
                            src_mac, dst_mac
                        ),
                        "-> Print(ether)",
                        "-> out{};\n".format(idx),
                    ]
                )
            )

        return "\n".join(out) + "\n"

    def simple_switch(self):
        links = self.links()
        ip_to_intf = [(l.intf1.IP(), l.intf1.name) for l in links]
        ip_to_intf.sort(key=lambda t: t[1])
        ips, intfs = zip(*ip_to_intf)
        from_device = Template(
            "\n".join(
                [
                    "FromDevice('$src') ",
                    "-> Queue(8) ",
                    "-> ToDevice('$dst');",
                ]
            )
        )
        return "\n".join(
            [
                from_device.substitute(
                    src=intfs[i], dst=intfs[(i + 1) % len(intfs)]
                )
                for i in xrange(len(intfs))
            ]
        )

    def start(self, controllers):
        print("click startup")
        config = self.make_config()
        config_fn = "{}.click".format(self.name)
        print("writing config to {}".format(config_fn))
        with open(config_fn, "w") as f:
            f.write(config)
        cmd = [self.install_cmd, config_fn]
        if self.log_file:
            cmd.append('> "%s" 2>&1' % self.log_file)
        self.cmd(" ".join(cmd) + " &")

    def stop(self):
        print("click shutdown")
        self.cmd(self.uninstall_cmd)
        # self.cmd(OurClickKernelSwitch.uninstall_cmd)


class ClickUserSwitch(ClickSwitch):
    @property
    def install_cmd(self):
        return "click"

    @property
    def uninstall_cmd(self):
        return "kill %click"


class ClickKernelSwitch(ClickSwitch):
    @property
    def install_cmd(self):
        return "click-install"

    @property
    def uninstall_cmd(self):
        return "click-uninstall"
