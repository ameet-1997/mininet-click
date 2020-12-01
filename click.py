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
        cur_ip = max([ipParse(l.intf1.IP()) for l in links]) + 1
        for link in links:
            link.intf2.ifconfig(ipStr(cur_ip) + "/8")
            cur_ip += 1

        # Routing table--map ip address to an index.
        rt = "rt :: StaticIPLookup(\n  "
        rt += ",\n  ".join(["{}/32 {}".format(l.intf1.IP(), i)
                           for i, l in enumerate(links)])
        rt += ");"

        from_device_t = Template("\n  ".join([
            "FromDevice('$src') ",
            "-> Print(got) ",
            "-> Strip(14) ",
            #"-> Print(stripped) ",
            "-> CheckIPHeader ",
            "-> Print(checked) ",
            #"-> StripIPHeader ",
            "-> GetIPAddress(16) ",
            "-> Print(hhhh, 100) ",
            "-> [0]rt;",
        ]))
        from_device = "\n".join(
            [from_device_t.substitute(src=l.intf2.name) for l in links])

        to_device_t = Template("\n  ".join([
            "rt[$i] ",
            "-> Print(hhh) ",
            "-> Queue(8) ",
            "-> ToDevice('$dst');",
        ]))
        to_device = "\n".join(
            [to_device_t.substitute(i=i, dst=l.intf2.name)
             for i, l in enumerate(links)])
        return "\n".join([rt, from_device, to_device])

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
        print("config:\n" + 78*"-" + "\n" + config)
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
