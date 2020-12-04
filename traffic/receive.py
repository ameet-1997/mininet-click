"""Listen for UDP packets. https://wiki.python.org/moin/UdpCommunication"""
import argparse
import collections
import fpformat
import json
from pprint import pprint
import socket
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--ttl", help="ttl in seconds", type=int, default=30)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--log", default="/dev/null")
    return parser.parse_args()


def receive(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.ip, args.port))
    counts = collections.Counter()
    latencies = collections.defaultdict(float)
    end_at = time.time() + args.ttl
    while time.time() < end_at:
        msg, (src, _) = sock.recvfrom(args.size)
        sent_at = float(msg)
        received_at = time.time()
        counts[src] += 1
        latencies[src] += received_at - sent_at
    with open(args.log, "w") as f:
        for k in counts:
            f.write("%d, %f\n" % (counts[k], latencies[k] / counts[k]))
            print("%d, %f" % (counts[k], latencies[k] / counts[k]))


if __name__ == "__main__":
    args = parse_args()
    receive(args)
