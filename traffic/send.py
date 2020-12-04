"""Send UDP packets. https://wiki.python.org/moin/UdpCommunication"""
import argparse
import fpformat
import socket
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--ttl", help="ttl in seconds", type=int, default=30)
    parser.add_argument("--rate", help="kpackets/sec", type=int, default=0)
    parser.add_argument("--log", default="/dev/null")
    return parser.parse_args()


def send(args):
    count = 0
    end_at = time.time() + args.ttl
    # Timestamps are seconds since epoch to six decimal places, so calculate
    # how much we need to pad to get 64 byte packets.
    pad = " " * (args.size - sys.getsizeof(fpformat.fix(time.time(), 6)))
    tick = (1.0 / (args.rate * 1000)) if args.rate >= 0 else 0.0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        msg = fpformat.fix(time.time(), 6) + pad
        sock.sendto(msg, (args.ip, args.port))
        count += 1
        if time.time() > end_at:
            break
        next_tick = time.time() + tick
        while time.time() < next_tick:
            continue
    with open(args.log, "w") as f:
        print("%d" % count)
        f.write("%d\n" % count)


if __name__ == "__main__":
    args = parse_args()
    send(args)
