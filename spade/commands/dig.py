import textwrap
import time

import dns.rdatatype as RecordType
import typer
from dns import flags, name, opcode
from dns.resolver import NXDOMAIN, YXDOMAIN, Answer, NoAnswer, NoNameservers, Resolver
from spade import __app_name__, __version__


def dns_lookup(
    target: str,
    record_type: str = "A",
    nameserver: str = "1.1.1.1",
    nameserver_port: int = 53,
    tcp: bool = False,
) -> tuple[Answer, float]:
    """
    Lookup a DNS record.
    """

    resolver: Resolver = Resolver()

    # The resolver can have multiple nameservers to query but we only give the user
    # an option for one and so it is cast to a list.
    resolver.nameservers = [str(nameserver)]

    # Some public DNS servers expose ports other than the conventional 53 for DNS queries.
    # Some examples are 208.67.222.222, 208.67.220.220, 208.67.222.123, 208.67.220.123, which
    # all expose ports 443 and 5353 for DNS queries.
    resolver.port = nameserver_port

    hostname: name.Name = name.from_text(target)

    try:
        record_type_enum: int = getattr(RecordType, record_type)
    except AttributeError:
        # Reaching this part of the code means that the user entered an invalid DNS record type.
        raise ValueError(f"Invalid record type: {record_type}")

    try:
        current_time = time.perf_counter()

        result = resolver.resolve(
            qname=hostname,
            rdtype=record_type_enum,
            tcp=tcp,
        )

        # By calculating the difference between the current time and the time before the DNS query,
        # we can calculate the time taken to perform the DNS query.
        time_taken = time.perf_counter() - current_time

    # Multiple exceptions can be raised by the resolver, where each exception explains what went wrong.
    except NXDOMAIN:
        raise Exception(f"{hostname} does not exist")
    except YXDOMAIN:
        raise Exception(f"{hostname} exists but is not authoritative")
    except NoAnswer:
        raise Exception(f"{hostname} has no {record_type} record")
    except NoNameservers:
        raise Exception(f"No nameservers available")
    return result, time_taken


def dig(
    name: str = typer.Argument(..., help="The name to perform a DNS lookup on"),
    record_type: str = typer.Argument("A", help="The record type to request"),
    nameserver: str = typer.Argument(
        "1.1.1.1", help="The nameserver to send the request to"
    ),
    nameserver_port: int = typer.Option(
        53, "-p", "--port", help="The port to send the request to"
    ),
    tcp: bool = typer.Option(False, "--tcp", help="Use TCP instead of UDP"),
    zone_file: bool = typer.Option(
        False, "-z", "--zone-file", help="Output the result in zone file format"
    ),
) -> None:
    """
    Run a DNS lookup.
    """

    # Perform a DNS query and get the result and the time taken to perform the query.
    lookup, time_taken = dns_lookup(
        target=name,
        record_type=record_type,
        nameserver=nameserver,
        nameserver_port=nameserver_port,
        tcp=tcp,
    )

    # If the user requested zone file output, we will output the result in the zone file format.
    if zone_file:
        rrset: list[str] = lookup.rrset.to_text()
        hostname_repr: str = b".".join(lookup.qname.labels).decode("utf-8")
        opcode_repr: str = opcode.to_text(lookup.response.opcode())
        id_: str = str(lookup.response.id)
        flags_repr: str = flags.to_text(lookup.response.flags)

        output = textwrap.dedent(
            f"""
; <<>> Spade {__version__} <<>> {hostname_repr} 
;; Got answer:
;; ->>HEADER<<- opcode: {opcode_repr}, status: NOERROR, id: {id_}
;; flags: {flags_repr};

;; ANSWER SECTION:
{rrset}

;; Query time: {time_taken * 1000:.3f} msec
;; SERVER: {lookup.nameserver}:{lookup.port}
;; WHEN: {time.strftime("%H:%M:%S %a %d %b %Y %Z")}
"""
        )
        typer.echo(output)

    if not zone_file:
        styled_record_type: str = typer.style(
            lookup.rdtype._name_, fg=typer.colors.BLUE
        )
        styled_hostname: str = typer.style(
            b".".join(lookup.qname.labels).decode("utf-8"), fg=typer.colors.GREEN
        )
        styled_nameserver: str = typer.style(
            f"{lookup.nameserver}:{lookup.port}", fg=typer.colors.RED
        )

        output = f"\nDNS Lookup for {styled_record_type} records for {styled_hostname} through {styled_nameserver}:\n"

        records: list[str] = lookup.rrset.to_text().split("\n")
        styled_records: list[str] = []

        for record in records:
            name, ttl, rclass, rtype, *rdata = record.split(" ")
            styled_hostname: str = typer.style(name, fg=typer.colors.GREEN)
            styled_ttl: str = typer.style(ttl, fg=typer.colors.RESET)
            styled_rclass: str = typer.style(rclass, fg=typer.colors.RESET)
            styled_rtype: str = typer.style(rtype, fg=typer.colors.BLUE)
            styled_rdata: str = typer.style(" ".join(rdata), fg=typer.colors.MAGENTA)
            styled_records.append(
                f" → {styled_hostname} {styled_ttl} {styled_rclass} {styled_rtype} {styled_rdata}"
            )

        output += "\n".join(styled_records)

        time_taken = f"{time_taken * 1000:.3f}ms"
        output += f"\n\nQuery time: {time_taken}\n"

        typer.echo(output)
