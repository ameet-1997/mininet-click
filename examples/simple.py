#!/usr/bin/python
"""
Create a topology with some nodes and a switch.

$ sudo python examples/simple.py (click|no_click) --n 3
"""
import argparse
import sys
import os
import os.path

os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
sys.path.append("..")

from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from click import ClickUserSwitch, ClickKernelSwitch


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("switch", default="click")
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--switch_type", default="router")
    parser.add_argument("--log_level", default="info")
    return parser.parse_args()


def simpleNoClick(n=3):
    net = Mininet()

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts\n")
    hosts = [net.addHost("h" + str(i)) for i in xrange(n)]
    s1 = net.addSwitch("s1")

    info("*** Adding links\n")
    links = [net.addLink(h, s1) for h in hosts]

    return net


def simpleClick(switch_type, n=3):
    net = Mininet(switch=ClickUserSwitch, link=TCLink)

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts\n")
    hosts = [net.addHost("h" + str(i)) for i in xrange(n)]
    s0 = net.addSwitch("s0", switch_type=switch_type)

    info("*** Adding links\n")
    # Connect every host to the switch.
    links = [net.addLink(h, s0) for h in hosts]
    for link in links:
        link.intf2.ifconfig("mtu", "50000")

    return net

def get_net(args):
    if args.switch == "no_click":
        return simpleNoClick(args.n)
    return simpleClick(switch_type=args.switch_type, n=args.n)

if __name__ == "__main__":
    args = parse_args()
    setLogLevel(args.log_level)
    net = get_net(args)

    info("*** Starting network\n")
    net.start()

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network")
    net.stop()
