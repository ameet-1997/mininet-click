"""
Provides a Click based switch class.
Forked from https://github.com/frawi/click-mininet
"""
import itertools
from string import Template

from mininet.node import Switch
from mininet.util import ipParse, ipStr

class ClickSwitch(Switch):
    """Use ClickUserSwitch or ClickKernelSwitch"""
    @property
    def install_cmd(self):
        raise NotImplementedError

    @property
    def uninstall_cmd(self):
        raise NotImplementedError

    def __init__(self, name, switch_type, log_file=None, **params):
        Switch.__init__( self, name, **params )
        self.log_file = log_file if log_file else "{}.log".format(self.name)
        if switch_type == "simple_switch":
            self.make_config = self.simple_switch
        elif switch_type == "router":
            self.make_config = self.router
        else:
            raise NotImplementedError(switch_type)

    def router(self, links):
        # Sort by the name of the host interface (e.g. h0-eth0).
        links = sorted(links, key=lambda l: l.intf1.name)

        out = []

        # Add some comments
        for i, l in enumerate(links):
            out.append("// {} {} {} {} <-> {} {}".format(
                i, l.intf1.name, l.intf1.IP(), l.intf1.MAC(),
                l.intf2.MAC(), l.intf2.name))
        out[-1] += "\n"

        # Three buckets: ARP request, ARP response, IP packets, anything else.
        out.append("c0 :: Classifier(12/0806 20/0001, 12/0806 20/0002, "
                   "12/0800, -);\n")

        # FromDevice: 'Paint' packets from each interface so we can identify
        # the source later if needed, then send it to the classifier.
        for i, l in enumerate(links):
            out.append("\n".join([
                "FromDevice('{}')".format(l.intf2.name),
                "-> Print(got{})".format(i),
                "-> Paint({})".format(i),
                "-> [0]c0;\n"]))

        # ToDevice variables.
        for i, l in enumerate(links):
            out.append("\n".join([
                "out{} :: Queue(8)".format(i),
                "-> Print(out{})".format(i),
                "-> ToDevice('{}');\n".format(l.intf2.name)
            ]))

        # Proxy ARP for every request. I.e. if the topography is:
        #   h1 -- s0-eth1 : s0 : s0-eth2 -- h2
        # and h1 sends an ARP request for h2, respond with "s0-eth1".
        arp_responder_s = "ARPResponder(\n  "
        arp_responder_s += ",\n  ".join(
            ["{} $mac".format(l.intf1.IP()) for l in links])
        arp_responder_s += ")"
        arp_responder_t = Template(arp_responder_s)

        # `Tee` splits the request to n channels (one per interface). For each
        # interface, respond with the proxy ARP table.
        out.append("c0[0] -> arpt :: Tee({});\n".format(len(links)))
        for i, l in enumerate(links):

            out.append("\n".join([
                "arpt[{}]".format(i),
                "-> CheckPaint({})".format(i),
                "-> Print(arp_req_from{})".format(i),
                "-> {}".format(arp_responder_t.substitute(mac=l.intf2.MAC())),
                "-> Print(arp_response)",
                "-> out{};\n".format(i)]))

        # ARP responses--just toss because we know where everything is.
        out.append("c0[1] -> Discard;\n")

        # non-IP packets are dropped.
        out.append("c0[3] -> Discard;\n")


        # IP request. Static routing table maps IP address to the index of the
        # interface.
        rt = "rt :: StaticIPLookup(\n  "
        rt += ",\n  ".join(["{}/32 {}".format(l.intf1.IP(), i)
                           for i, l in enumerate(links)])
        rt += ");\n"
        out.append(rt)

        out.append("\n".join([
            "c0[2]",
            "-> Print(ip_req)",
            "-> Strip(14)",  # Strip ethernet header
            "-> Print(stripped)",
            "-> CheckIPHeader",
            "-> GetIPAddress(16)",
            "-> Print(ip)",
            "-> [0]rt;\n"]))

        # Route requests to the correct interface.
        for i, l in enumerate(links):
            out.append("\n".join([
                "rt[{}]".format(i),
                "-> Print(out{})".format(i),
                "-> EtherEncap(0x0800, {}, {})".format(l.intf2.MAC(),
                                                       l.intf1.MAC()),
                "-> Print(ether)",
                "-> out{};\n".format(i)]))

        return "\n".join(out) + "\n"


    def simple_switch(self, links):
        ip_to_intf = [(l.intf1.IP(), l.intf1.name) for l in links]
        ip_to_intf.sort(key=lambda t: t[1])
        ips, intfs = zip(*ip_to_intf)
        from_device = Template("\n".join([
            "FromDevice('$src') ",
            "-> Queue(8) ",
            "-> ToDevice('$dst');",
        ]))
        return "\n".join(
            [from_device.substitute(src=intfs[i], dst=intfs[(i+1) % len(intfs)])
             for i in xrange(len(intfs))])

    def links(self):
        return [intf.link for intf in self.intfs.values() if intf.name != "lo"]
    
    def start(self, controllers):
        print("click startup")
        links = self.links()
        config = self.make_config(links)
        config_fn = "{}.click".format(self.name)
        print("writing config to {}".format(config_fn))
        with open(config_fn, "w") as f:
            f.write(config)
        # print("config:\n" + 78*"-" + "\n" + config)
        cmd = [self.install_cmd, config_fn]
        if self.log_file:
            cmd.append('> "%s" 2>&1' % self.log_file)
        self.cmd(" ".join(cmd) + " &")

    def stop(self):
        print("click shutdown")
        self.cmd(self.uninstall_cmd)
        #self.cmd(OurClickKernelSwitch.uninstall_cmd)


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
