"""Send UDP packets. https://wiki.python.org/moin/UdpCommunication"""
import argparse
import fpformat
import socket
import struct
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip")
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--ttl", help="ttl in seconds", type=int, default=5)
    parser.add_argument("--rate", help="kpackets/sec", type=int, default=0)
    parser.add_argument("--log", default="/dev/null")
    return parser.parse_args()


def send(args):
    # From Kohler et al: "Each 64-byte UDP packet includes Ethernet,
    # IP, and UDP headers as well as 14 bytes of data and the 4-byte
    # Ethernet CRC." So create a 14-byte message which should get
    # padded into a 64 byte packet.
    msg = struct.pack("c" * 14, *["x" for _ in xrange(14)])
    count = 0
    end_at = time.time() + args.ttl
    tick = (1.0 / (args.rate * 1000)) if args.rate > 0 else 0.0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while time.time() < end_at:
        sock.sendto(msg, (args.ip, args.port))
        count += 1
        next_tick = time.time() + tick
        while time.time() < next_tick:
            continue
    print("%d" % count)
    with open(args.log, "w") as f:
        f.write("%d\n" % count)


if __name__ == "__main__":
    args = parse_args()
    send(args)
