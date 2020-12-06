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
    count = 0
    end_at = time.time() + args.ttl
    while time.time() < end_at:
        msg, _ = sock.recvfrom(args.size)
        count += 1
    print("%d" % count)
    with open(args.log, "w") as f:
        f.write("%d\n" % count)


if __name__ == "__main__":
    args = parse_args()
    receive(args)
