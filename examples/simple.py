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
    parser.add_argument("switch", default="click")
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--switch_type", default="router")
    parser.add_argument("--log_level", default="info")
    return parser.parse_args()

def adjacency_matrix_to_adjacency_list(adjacency_matrix):
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    assert np.array_equal(adjacency_matrix, adjacency_matrix.T)
    adjacency_list = {}
    for j in xrange(adjacency_matrix.shape[0]):
        adjacency_list[j] = set(np.nonzero(adjacency_matrix[j, :])[0].tolist())
    return adjacency_list

"""
Return dictionary of nodes with distances from input node
"""

def BFS(adjacency_list, node_id):
    visited = []
    queue = []
    visited_nodes = set()

    queue.append(node_id)
    cur_distance = 0
    visited = {}
    visited[node_id] = cur_distance

    while len(queue):
        s = queue.pop(0)
        cur_distance += 1
        for neighbor in adjacency_list[s]:
            if neighbor not in visited:
                visited[neighbor] = cur_distance
                queue.append(neighbor)
    return visited

"""
Generates IP maps for each of the nodes
{router id: { outgoing router id : set of router ids}
Generate the mapping by iteratively going through all the routers
"""

def shortest_path_IP_map(adjacency_matrix):

    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    assert np.array_equal(adjacency_matrix, adjacency_matrix.T)
    num_nodes = adjacency_matrix.shape[0]
    # generate forwarding tables
    adjacency_list = adjacency_matrix_to_adjacency_list(adjacency_matrix)
    shortest_path_IP_map = {}
    bfs_out = []
    for j in xrange(num_nodes):
        bfs_out.append(BFS(adjacency_list, j))
    for j in xrange(num_nodes):
        shortest_path_IP_map[j] = {} 
        # need to figure out which edges lead to the shortest path; compare bfs outputs
        cur_neighbors = list(adjacency_list[j])
        # remove self loops
        cur_neighbors.remove(j)
        distance_matrix = np.zeros((len(cur_neighbors), num_nodes))
        for i, cur_neighbor in enumerate(cur_neighbors):
            for node in bfs_out[cur_neighbor]:
                distance_matrix[i, node] = bfs_out[cur_neighbor][node]
            shortest_path_IP_map[j][cur_neighbor] = []

        shortest_path_indices = np.argmin(distance_matrix, axis=0)

        # get the argmin among all of them
        for n in xrange(num_nodes):
            if n != j:
                shortest_path_IP_map[j][cur_neighbors[shortest_path_indices[n]]].append(n)
    return shortest_path_IP_map

"""
Initialize topology of routers defined by an adjancency matrix
Add a node to each router; We need to figure out why we need 
"""
def initialize_topology(adjacency_matrix, switch_type='router', click_switch=True):
    assert adjacency_matrix.shape[0] == adjacency_matrix.shape[1]
    assert adjacency_matrix == adjacency_matrix.T

    num_routers = adjacency_matrix.shape[0]

    net = Mininet(switch=ClickUserSwitch, link=TCLink) if click_switch else Mininet()

    info("*** Adding controller\n")
    net.addController("c0")

    info("*** Adding hosts\n")
    # 1 host per router
    hosts = [net.addHost("h" + str(i)) for i in xrange(num_routers)]

    # adding n swithches
    switches = []
    for j in xrange(num_routers):
        if click_switch:
            switches.append(net.addSwitch("s" + str(j), switch_type=switch_type))
        else:
            switches.append(net.addSwitch("s" + str(j)))

    info("*** Adding links\n")
    # Connect a host to a switch.
    # Add router links
    
    host_router_links = [net.addLink(hosts[j], switches[j]) for j in xrange(num_routers)]
    router_router_links = []
    for i in xrange(num_routers):
        for k in xrange(num_routers):
            if i != k and adjacency_matrix[i][k]:
                router_router_links.append(net.addLink(switches[i], switches[j]))
    # connect a host to a switch
       
    for link in (host_router_links + router_router_links):
        link.intf2.ifconfig("mtu", "50000")

    return net

"""
Initialize a random topology with n routers and one node per router; Ensures that the topology is connected
by adding random edges to a randomly sampled tree

Returns: Adjancency matrix of size N x N
"""
def create_random_topology(num_routers, sparsity=0.15):

    frontier = []
    frontier.append(0)
    exterior = list(xrange(1, num_routers))
    adjacency_matrix = np.zeros((num_routers, num_routers))
    while len(exterior):
        # randomly select a router in the frontier and the exterior; create an edge b/w them
        # then update the frontier and exterior
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
    pass

def create_ring_topology(num_routers):
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

def get_net(args):
    if args.switch == "no_click":
        return simpleNoClick(args.n)
    return simpleClick(switch_type=args.switch_type, n=args.n)

if __name__ == "__main__":
    topo = create_random_topology(10)
    print(topo)
    adjacency_list = adjacency_matrix_to_adjacency_list(topo)
    print(adjacency_list)
    print(BFS(adjacency_list, 0))

    print(shortest_path_IP_map(topo))
    # args = parse_args()
    # setLogLevel(args.log_level)
    # net = get_net(args)

    # info("*** Starting network\n")
    # net.start()

    # info("*** Running CLI\n")
    # CLI(net)

    # info("*** Stopping network")
    # net.stop()
