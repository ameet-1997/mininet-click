#!/usr/bin/python
"""
Create a topology with some nodes and a switch.

$ sudo python examples/simple.py (click|no_click) --n 3
"""
import argparse
import sys
import os
import os.path
from pprint import pprint

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
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--no_click", action="store_true")
    parser.add_argument("--topology", default="chain")
    parser.add_argument("--num_routers", type=int, default=3)
    parser.add_argument("--nodes_per_router", type=int, default=3)
    parser.add_argument("--sparsity", type=float, default=0.15)
    parser.add_argument("--log_level", default="info")
    return parser.parse_args()


def adjacency_matrix_to_adjacency_list(adjacency_matrix):
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    assert np.array_equal(adjacency_matrix, adjacency_matrix.T)
    adjacency_list = {}
    for j in xrange(adjacency_matrix.shape[0]):
        adjacency_list[j] = set(np.nonzero(adjacency_matrix[j, :])[0].tolist())
    return adjacency_list


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


def create_star_topology(num_routers):
    assert num_routers == 1
    return np.ones((1, 1))


def create_chain_topology(num_routers):
    adjacency_matrix = np.zeros((num_routers, num_routers))
    for i in xrange(1, num_routers):
        adjacency_matrix[i - 1][i] = 1
    return adjacency_matrix


def create_ring_topology(num_routers):
    pass


def create_bottleneck_topology(num_routers):
    """
    h0            h5
    h1 s0  s2  s3 h6
    h2 s1      s4 h7
    h3            h8
    """
    pass


def initialize_topology(adjacency_matrix, nodes_per_router=3, no_click=False):
    """
    Initialize topology of routers defined by an adjancency matrix
    Add nodes_per_router nodes to each router.
    """
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    num_routers = adjacency_matrix.shape[0]

    net = Mininet(
        switch=OVSSwitch if no_click else ClickUserSwitch, link=TCLink
    )

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts and switches\n")
    switches = []
    hosts = []
    for j in xrange(num_routers):
        switches.append(net.addSwitch("s" + str(j)))
        for i in xrange(nodes_per_router):
            hosts.append(net.addHost("h" + str(len(hosts))))
            net.addLink(hosts[-1], switches[-1])

    info("*** Adding router links\n")
    router_router_links = []
    added = set([])
    # We don't want to add self-links or duplicates.
    for row in xrange(len(adjacency_matrix)):
        for col in xrange(len(adjacency_matrix[row])):
            if row == col or adjacency_matrix[row][col] == 0:
                continue
            i, j = sorted([row, col])
            if (i, j) not in added:
                added.add((i, j))
                net.addLink(switches[i], switches[j])

    if no_click:
        return net

    # Initialize the routing table for each switch.
    for s in switches:
        s.init_neighbors()

    # Update the tables until convergence. (The number of iterations should be
    # equal to the length of the longest path between routers.)
    while any(s.update() for s in switches):
        continue

    return net


def get_net(args):
    if args.topology == "star":
        topo = create_star_topology(args.num_routers)
    elif args.topology == "chain":
        topo = create_chain_topology(args.num_routers)
    elif args.topology == "random":
        topo = create_random_topology(args.num_routers, args.sparsity)
    else:
        raise NotImplementedError(args.topology)
    return initialize_topology(topo, args.nodes_per_router, args.no_click)


def cleanup():
    links = os.popen("ip link list").read()
    for line in links.split("\n"):
        if "@" in line:
            s = line.split("@")[0]
            s = s.split(": ")[-1]
            cmd = "ip link del " + s
            print(cmd)
            os.system(cmd)


if __name__ == "__main__":
    args = parse_args()
    if args.cleanup:
        cleanup()
        exit()
    setLogLevel(args.log_level)
    net = get_net(args)

    info("*** Starting network\n")
    net.start()

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network")
    net.stop()
