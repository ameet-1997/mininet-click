#!/usr/bin/python
"""
Create a topology with some nodes and a switch.
"""
import argparse
import collections
import os
import os.path
from pprint import pprint
from signal import SIGINT
from string import Template
import sys
import time

os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))

from mininet.node import Controller, OVSSwitch
from mininet.net import Mininet
from mininet.log import setLogLevel, debug, info
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.util import pmonitor
import click
from click import ClickUserSwitch, ClickKernelSwitch
import numpy as np
import random


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true")

    # Define a topology
    parser.add_argument("--no_click", action="store_true")
    parser.add_argument("--kernel", action="store_true")
    parser.add_argument("--topology", default="chain")
    parser.add_argument("--num_routers", type=int, default=3)
    parser.add_argument("--nodes_per_router", type=int, default=3)
    parser.add_argument("--sparsity", type=float, default=None)

    # Run an experiment
    parser.add_argument("--run_experiment", action="store_true")
    parser.add_argument("--output", default="output/results.txt")
    parser.add_argument("--ttl", help="ttl in seconds", type=int, default=3)
    parser.add_argument("--rate", help="k/sec", type=int, default=20)
    parser.add_argument("--size", help="bytes per packet", type=int, default=64)

    # Run the net in the CLI.
    parser.add_argument("--cli", action="store_true")

    parser.add_argument("--log_level", default="info")

    args = parser.parse_args()
    if args.rate == 0:
        args.rate = 1
    return args


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


def create_single_switch_topology(num_routers):
    return np.ones((1, 1))


def create_star_topology(num_routers):
    """Every router is connect by a single central router"""
    adjacency_matrix = np.zeros((num_routers + 1, num_routers + 1))
    center = num_routers
    for i in xrange(num_routers):
        adjacency_matrix[i][center] = 1
    print(adjacency_matrix)
    return adjacency_matrix


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


def initialize_topology(args, adjacency_matrix):
    """
    Initialize topology of routers defined by an adjancency matrix
    Add args.nodes_per_router nodes to each router.
    """
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    if args.topology == "single_switch":
        num_routers = 1
        nodes_per_router = args.num_routers * args.nodes_per_router
    else:
        num_routers, nodes_per_router = args.num_routers, args.nodes_per_router

    if args.no_click:
        switch = OVSSwitch
    elif args.kernel:
        switch = ClickKernelSwitch
    else:
        switch = ClickUserSwitch

    net = Mininet(switch=switch, link=TCLink)

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts and switches\n")
    switches = []
    hosts = []
    for j in xrange(adjacency_matrix.shape[0]):
        switches.append(net.addSwitch("s" + str(j)))
        # Star topology has one router that isn't connected to any hosts.
        if j < num_routers:
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

    if args.no_click:
        return net

    # Initialize the routing table for each switch.
    for s in switches:
        s.init_neighbors()

    # Update the tables until convergence. (The number of iterations should be
    # equal to the length of the longest path between routers.)
    while any(s.update() for s in switches):
        continue

    return net


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def get_net(args):
    if type(args) == dict:
        args = dotdict(args)
    if args.topology == "single_switch":
        topo = create_single_switch_topology(1)
    elif args.topology == "star":
        topo = create_star_topology(args.num_routers)
    elif args.topology == "chain":
        topo = create_chain_topology(args.num_routers)
    elif args.topology == "random":
        topo = create_random_topology(args.num_routers, args.sparsity)
    else:
        raise NotImplementedError(args.topology)
    return initialize_topology(args, topo)


def cleanup():
    links = os.popen("ip link list").read()
    for line in links.split("\n"):
        if "@" in line:
            s = line.split("@")[0]
            s = s.split(": ")[-1]
            cmd = "ip link del " + s
            print(cmd)
            os.system(cmd)


def print_rows(rows):
    if type(rows) != list:
        rows = [rows]
    keys = list(rows[0].keys())
    out = ["\t".join(keys)]
    for row in rows:
        out.append("\t".join([str(row[k]) for k in keys]))
    s = "\n".join(out)
    print(s)
    return s


def run_experiment(args, net):
    # Partition hosts into senders and receivers.
    hosts = net.hosts
    assert len(hosts) % 2 == 0
    senders, receivers = hosts[: len(hosts) / 2], hosts[len(hosts) / 2 :]
    rcmd_t = Template(
        "python -u traffic/receive.py --ip $ip --ttl $ttl --size $size "
        "--log '/home/mininet/mininet-click/log/$h-r.log'"
    )
    scmd_t = Template(
        "python -u traffic/send.py --ip $ip --ttl $ttl --size $size "
        "--rate $rate --log '/home/mininet/mininet-click/log/$h-s.log'"
    )
    print("ttl: %d, rate: %dk, size: %d" % (args.ttl, args.rate, args.size))
    print("starting %d flows" % len(senders))
    popens = {}
    for s, r in zip(senders, receivers):
        debug("sender: %s, receiver: %s (%s)\n" % (s.name, r.name, r.IP()))
        rcmd = rcmd_t.substitute(
            ip=r.IP(),
            ttl=args.ttl,
            size=args.size,
            rate=args.rate / len(senders),
            h=r.name,
        ).split(" ")
        scmd = scmd_t.substitute(
            ip=r.IP(),
            ttl=args.ttl,
            size=args.size,
            rate=args.rate / len(senders),
            h=s.name,
        ).split(" ")
        popens[r] = r.popen(rcmd)
        popens[s] = s.popen(scmd)
    print("monitoring for %d seconds" % (args.ttl + 3))
    end_at = time.time() + args.ttl + 3
    results = {h: 0 for h in hosts}
    cur = None
    for h, line in pmonitor(popens, timeoutms=500):
        debug("%s: '%s'\n" % (str(h), line.strip()))
        if h and line.strip():
            results[h] = int(line.strip())
        if time.time() > end_at:
            break
    for p in popens.values():
        p.send_signal(SIGINT)
    rows = []
    for s, r in zip(senders, receivers):
        assert s in results and r in results
        sent = results[s]
        received = results[r]
        d = collections.OrderedDict(
            [
                ("src", s.name),
                ("dst", r.name),
                ("s", sent),
                ("s/s", sent / args.ttl),
                ("r", received),
                ("r/s", received / args.ttl),
                ("drop%", int(100 * (1 - (float(received) / sent)))),
            ]
        )
        rows.append(d)
    print_rows(rows)
    summary = collections.OrderedDict()
    summary["rate"] = str(args.rate) + "k"
    keys = list(rows[0].keys())
    for k in keys:
        if type(rows[0][k]) != str:
            summary[k] = sum(row[k] for row in rows)
            if "%" in k:
                summary[k] /= float(len(rows))
    print("-" * 80)
    print_rows([summary])
    return summary


def run(args, net):
    summary = run_experiment(args, net)
    if args.topology == "single_switch":
        args.nodes_per_router = args.nodes_per_router * args.num_routers
        args.num_routers = 1
    report = collections.OrderedDict(
        [
            ("topology", args.topology),
            ("sparsity", args.sparsity),
            ("num_routers", args.num_routers),
            ("nodes_per_router", args.nodes_per_router),
        ]
    )
    report.update(summary)
    s = print_rows(report)
    empty = os.stat(args.output).st_size == 0
    with open(args.output, "a") as f:
        if empty:
            f.write("\t".join(list(report.keys())) + "\n")
        f.write("\t".join([str(v) for v in report.values()]) + "\n")


if __name__ == "__main__":
    args = parse_args()
    if args.cleanup:
        cleanup()
        exit()
    print("Params: {}".format(vars(args)))
    setLogLevel(args.log_level)
    click.debug = args.log_level == "debug"

    net = get_net(args)

    info("*** Starting network\n")
    net.start()

    if args.run_experiment:
        try:
            run(args, net)
        except Exception:
            net.stop()
            raise

    if args.cli:
        info("*** Running CLI\n")
        CLI(net)

    info("*** Stopping network")
    net.stop()
