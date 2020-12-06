"""Listen for UDP packets. https://wiki.python.org/moin/UdpCommunication"""
import argparse
import collections
import fpformat
import json
from multiprocessing import Process, Value
from pprint import pprint
import socket
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--ttl", help="ttl in seconds", type=int, default=5)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--log", default="/dev/null")
    return parser.parse_args()


def listen(args, count):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.ip, args.port))
    while True:
        msg, _ = sock.recvfrom(args.size)
        count.value += 1


def receive(args):
    count = Value("i", 0)
    p = Process(target=listen, args=(args, count))
    p.start()
    p.join(args.ttl)
    print("%d" % count.value)
    with open(args.log, "w") as f:
        f.write("%d\n" % count.value)


if __name__ == "__main__":
    args = parse_args()
    receive(args)
