from time import sleep
from socket import gethostbyaddr
from icmplib.utils import resolve, unique_identifier
from icmplib.sockets import ICMPv4Socket, ICMPv6Socket
from icmplib.models import ICMPRequest, TimeExceeded, Hop
from icmplib.exceptions import ICMPLibError, SocketPermissionError as SPE
from rich.text import Text
from rich.table import Table
from rich.live import Live
from ipwhois.net import Net
from ipwhois.asn import IPASN
from re import match
import typer

from spade.error.traceroute import SocketPermissionError

def traceroute_mine(address, count=1, interval=0.0, timeout=25, first_hop=1,
        max_hops=30, id=None, source=None, family=None,
        **kwargs):
    if match(r'(?i)^([a-z0-9-]+|([a-z0-9_-]+[.])+[a-z]+)$', address) is not None:
        address = resolve(address, family)[0]

    if ":" in address:
        _Socket = ICMPv6Socket
    else:
        _Socket = ICMPv4Socket

    id = id or unique_identifier()
    ttl = first_hop
    host_reached = False

    try:
        _ = _Socket(source)
    except SPE:
        SocketPermissionError().raise_cli()
    with _Socket(source) as sock:
        while not host_reached and ttl <= max_hops:
            reply = None
            packets_sent = 0
            rtts = []

            for sequence in range(count):
                request = ICMPRequest(
                    destination=address,
                    id=id,
                    sequence=sequence,
                    ttl=ttl,
                    **kwargs)

                try:
                    sock.send(request)
                    packets_sent += 1

                    reply = sock.receive(request, timeout)
                    rtt = (reply.time - request.time) * 1000
                    rtts.append(rtt)

                    reply.raise_for_status()
                    host_reached = True

                except TimeExceeded:
                    sleep(interval)

                except ICMPLibError:
                    break
            if reply:
                hop = Hop(
                    address=reply.source,
                    packets_sent=packets_sent,
                    rtts=rtts,
                    distance=ttl)
                yield hop
            else:
                yield None
            ttl += 1


def trace(host):
    hops = traceroute_mine(host)

    table = Table(title=f"Traceroute to {host}")
    table.add_column("Hop", justify="left")
    table.add_column("Hostname", justify="left")
    table.add_column("Address", justify="left")
    table.add_column("Packets sent", justify="left")
    table.add_column("Packets lost (%)", justify="left")
    table.add_column("Average RTT (ms)", justify="left")
    table.add_column("Minimum RTT (ms)", justify="left")
    table.add_column("Maximum RTT (ms)", justify="left")
    table.add_column("ASN", justify="left")
    table.add_column("ASN Info", justify="left")
    with Live(table):
        for hop in hops:
            if hop is None:
                table.add_row(
                    Text("(no response)", style="red"),
                    Text("*", style="red"),
                    Text("*", style="red"),
                    Text("*", style="red"),
                    Text("*", style="red"),
                    Text("*", style="red"),
                    Text("*", style="red"),
                    Text("*", style="red"),
                )
                continue
            try:
                hostname = gethostbyaddr(hop.address)[0]
            except Exception:
                hostname = hop.address

            try:
                net_ip = Net(hop.address)
                asn_obj = IPASN(net_ip)
                asn = asn_obj.lookup().get('asn', "Error")
            except Exception:
                asn = "err"

            table.add_row(
                Text(str(hop.distance), style="green"),
                Text(str(hostname), style="blue"),
                str(hop.address),
                str(hop.packets_sent),
                str(hop.packet_loss * 100),
                str(hop.avg_rtt),
                str(hop.max_rtt),
                str(hop.min_rtt),
                asn,
                f"https://bgp.tools/as/{asn}"
            )

def traceroute(host):
    """
    Perform a traceroute to a host.
    """
    trace(host)