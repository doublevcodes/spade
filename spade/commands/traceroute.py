from typing import Generator, Final
import socket
import struct
import sys

TRACEROUTE_PORT: Final[int] = 33434


def traceroute_lookup(target: str, hops: int = 99) -> Generator[str, None, None]:
    """
    Args:
        target: The hostname/IP address to trace the route of packets to
        hops: The maximum number of hops the packet is allowed to take

    Returns:

    """
    dest_addr: str = socket.gethostbyname(target)
    port = TRACEROUTE_PORT
    ttl = 1
    while True:
        rec_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)

        timeout = struct.pack("ll", 5, 0)
        rec_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)

        rec_socket.bind(("", port))
        sys.stdout.write(" %d   " % ttl)
        send_socket.sendto(bytes("", "utf-8"), (target, port))

        curr_addr = None
        curr_name = None
        finished = False
        tries = 3
        while not finished and tries > 0:
            try:
                _, curr_addr = rec_socket.recvfrom(512)
                finished = True
                curr_addr = curr_addr[0]
                try:
                    curr_name = socket.gethostbyaddr(curr_addr)[0]
                except socket.error:
                    curr_name = curr_addr
            except socket.error as err:
                tries -= 1
                sys.stdout.write("* ")

        send_socket.close()
        rec_socket.close()

        if not finished:
            pass

        if curr_addr is not None:
            curr_host = "%s (%s)" % (curr_name, curr_addr)
        else:
            curr_host = ""
        print("%s\n" % (curr_host))

        ttl += 1
        if curr_addr == dest_addr or ttl > hops:
            break

if __name__ == "__main__":
    traceroute_lookup("bad.horse")