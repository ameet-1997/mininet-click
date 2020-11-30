"""
Provides a Click based switch class.
Forked from https://github.com/frawi/click-mininet
"""

from mininet.node import Switch

class ClickSwitch(Switch):
    """Use ClickUserSwitch or ClickKernelSwitch"""
    @property
    def install_cmd(self):
        raise NotImplementedError

    @property
    def uninstall_cmd(self):
        raise NotImplementedError

    def __init__(self, name, log_file=None, **params):
        Switch.__init__( self, name, **params )
        self.log_file = log_file if log_file else "{}.log".format(self.name)

    def make_config(self, ip_to_intf):
        intfs = sorted(list(ip_to_intf.items()), key=lambda i: i[1])
        ip_classifier = (
            "ip :: IPClassifier(" +
            ", ".join(["ip dst {}".format(ip) for ip, _ in intfs]) +
            ", -)"
        )
        return "\n".join(
            ["FromDevice('{}', SNIFFER false) -> Queue(8) -> ToDevice('{}');".format(
                intfs[i][1], intfs[(i + 1) % len(intfs)][1])
             for i in xrange(len(intfs))])
    
        # from_device = "\n".join(
        #     ["FromDevice('{}') -> [0]ip;".format(intf) for _, intf in intfs])
        # to_device = "\n".join(
        #     ["ip[{}] -> Queue(8) -> ToDevice('{}');".format(i, intf)
        #      for i, (_, intf) in enumerate(intfs)])
        # discard = "ip[{}] -> Discard;".format(len(intfs))
        # return "\n".join([ip_classifier, from_device, to_device, discard]) + "\n"

    def start(self, controllers):
        print("click startup")
        ip_to_intf = {}
        # Each interface has already been configured by net.addLink.
        for intf in self.intfs.values():
            if intf.name == "lo":
                continue
            ip_to_intf[intf.link.intf1.IP()] = intf.name
            intf.link.intf2.ifconfig("mtu", "50000")
        config = self.make_config(ip_to_intf)
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
