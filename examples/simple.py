#!/usr/bin/python
"""
Create a topology with some nodes and a switch.

$ sudo python examples/simple.py
or
$ sudo python examples/simple.py no_click
"""
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


def simpleNoClick(n=3):
    net = Mininet()

    info("*** Adding controller\n")
    net.addController( "c0" )

    info("*** Adding hosts\n")
    hosts = [net.addHost("h" + str(i)) for i in xrange(n)]
    s1 = net.addSwitch("s1")

    info("*** Adding links\n")
    links = [net.addLink(h, s1) for h in hosts]

    return net


def simpleClick(n=3):
    net = Mininet(switch=ClickUserSwitch)

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts\n")
    hosts = [net.addHost("h" + str(i)) for i in xrange(n)]
    s0 = net.addSwitch("s0")

    info("*** Adding links\n")
    # Connect every host to the switch.
    links = [net.addLink(h, s0) for h in hosts]

    return net


if __name__ == "__main__":
    setLogLevel("info")
    net = (simpleNoClick() if len(sys.argv) > 1 and sys.argv[1] == "no_click"
           else simpleClick())

    info("*** Starting network\n")
    net.start()

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network")
    net.stop()
