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
import numpy as np
import random


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--switch", default="click")
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--switch_type", default="router")
    parser.add_argument("--topo", default="star")
    parser.add_argument("--r", type=int, default=3)
    parser.add_argument("--log_level", default="info")
    return parser.parse_args()


def adjacency_matrix_to_adjacency_list(adjacency_matrix):
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    assert np.array_equal(adjacency_matrix, adjacency_matrix.T)
    adjacency_list = {}
    for j in xrange(adjacency_matrix.shape[0]):
        adjacency_list[j] = set(np.nonzero(adjacency_matrix[j, :])[0].tolist())
    return adjacency_list


def initialize_topology(
    adjacency_matrix, n=1, switch_type="router", click_switch=True
):
    """
    Initialize topology of routers defined by an adjancency matrix
    Add a node to each router; We need to figure out why we need
    """
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    assert np.array_equal(adjacency_matrix, adjacency_matrix.T)

    num_routers = adjacency_matrix.shape[0]

    net = Mininet(
        switch=ClickUserSwitch if click_switch else Switch, link=TCLink
    )

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts and switches\n")
    switches = []
    hosts = []
    for j in xrange(num_routers):
        if click_switch:
            switches.append(
                net.addSwitch("s" + str(j), switch_type=switch_type)
            )
        else:
            switches.append(net.addSwitch("s" + str(j)))
        for i in xrange(n):
            hosts.append(net.addHost("h" + str(len(hosts))))
            net.addLink(hosts[-1], switches[-1])

    info("*** Adding router links\n")
    router_router_links = []
    added = set([])
    for row in xrange(len(adjacency_matrix)):
        for col in xrange(len(adjacency_matrix[row])):
            if row == col or adjacency_matrix[row][col] == 0:
                continue
            i, j = sorted([row, col])
            print((row, col), (i, j))
            if (i, j) not in added:
                added.add((i, j))
                net.addLink(switches[i], switches[j])

    for s in switches:
        s.init_neighbors()
    while any(s.update() for s in switches):
        continue

    return net


def create_random_topology(num_routers, sparsity=0.15):
    """Initialize a random topology with n routers and one node per
    router; Ensures that the topology is connected by adding random
    edges to a randomly sampled tree

    Returns: Adjancency matrix of size N x N
    """
    frontier = []
    frontier.append(0)
    exterior = list(xrange(1, num_routers))
    adjacency_matrix = np.zeros((num_routers, num_routers))
    while len(exterior):
        # randomly select a router in the frontier and the exterior;
        # create an edge b/w them then update the frontier and
        # exterior
        sampled_exterior_router_id = random.randrange(len(exterior))
        sampled_exterior_router = exterior[sampled_exterior_router_id]

        sampled_frontier_router_id = random.randrange(len(frontier))
        sampled_frontier_router = frontier[sampled_frontier_router_id]

        # add edges; 2 edges for symmetry
        adjacency_matrix[sampled_exterior_router, sampled_frontier_router] = 1
        adjacency_matrix[sampled_frontier_router, sampled_exterior_router] = 1

        # update frontier, exterior
        exterior.pop(sampled_exterior_router_id)
        frontier.append(sampled_exterior_router)

    assert len(frontier) == num_routers
    assert len(set(frontier)) == num_routers

    # sample a random symmetric adjency matrix; append edges to the sampled tree
    x_upper, y_upper = np.triu_indices(num_routers, 1)
    random_adjacency_matrix = np.zeros((num_routers, num_routers))
    edges = np.random.rand(len(x_upper)) < sparsity
    random_adjacency_matrix[x_upper, y_upper] = edges
    random_adjacency_matrix[y_upper, x_upper] = edges
    random_adjacency_matrix[np.arange(num_routers), np.arange(num_routers)] = 1

    print("number of edges in tree", np.sum(adjacency_matrix) // 2)
    print("number of sparse edges", np.sum(random_adjacency_matrix) // 2)
    return (adjacency_matrix + random_adjacency_matrix) >= 1


def create_star_topology():
    return [[1]]


def create_ring_topology(num_routers):
    pass


def create_bottleneck_topology(depth):
    """
    h0            h5
    h1 s0  s2  s3 h6
    h2 s1      s4 h7
    h3            h8
    """
    pass


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


def chainTopology(switch_type, n=3, r=3):
    net = Mininet(switch=ClickUserSwitch, link=TCLink)

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts, switches, and links\n")
    hosts = []
    switches = []
    for i in xrange(r):
        s = net.addSwitch("s" + str(i), switch_type=switch_type)
        hs = [net.addHost("h" + str(len(hosts) + j)) for j in xrange(n)]
        for h in hs:
            net.addLink(h, s)
        hosts += hs
        switches.append(s)

    info("*** Connecting switches\n")
    # Simple chain topology: s0 <-> s1 <-> ... <-> sr
    for i in xrange(1, len(switches)):
        net.addLink(switches[i], switches[i - 1])
    for s in switches:
        s.init_neighbors()
    while True:
        if not any(s.update() for s in switches):
            break

    return net


def get_net(args):
    if args.switch == "no_click":
        return simpleNoClick(args.n)
    if args.topo == "star":
        return simpleClick(switch_type=args.switch_type, n=args.n)
    if args.topo == "chain":
        return chainTopology(switch_type=args.switch_type, n=args.n, r=args.r)
    if args.top == "random":
        topo = create_random_topology(args.r)
        return initialize_topology(topo)
    raise NotImplementedError(args.switch + "." + args.topo)


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
