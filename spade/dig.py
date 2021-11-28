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
    resolver.nameservers = [str(nameserver)]
    resolver.port = nameserver_port

    hostname: name.Name = name.from_text(target)

    try:
        record_type_enum: int = getattr(RecordType, record_type)
    except AttributeError:
        raise ValueError(f"Invalid record type: {record_type}")

    try:
        current_time = time.time()
        result = resolver.resolve(
            qname=hostname,
            rdtype=record_type_enum,
            tcp=tcp,
        )
        time_taken = time.time() - current_time
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
    nameserver_port: int = typer.Option(53, help="The port to send the request to"),
    tcp: bool = typer.Option(False, help="Use TCP instead of UDP"),
    zone_file: bool = typer.Option(False, help="Output the result in zone file format"),
) -> None:
    lookup, time_taken = dns_lookup(
        target=name,
        record_type=record_type,
        nameserver=nameserver,
        nameserver_port=nameserver_port,
        tcp=tcp,
    )
    output = f"\nDNS Lookup for {typer.style(lookup.rdtype._name_, fg=typer.colors.BLUE)!s} records for {typer.style(b'.'.join(lookup.qname.labels).decode('utf-8'), fg=typer.colors.GREEN)} through {typer.style(f'{lookup.nameserver}:{lookup.port}', fg=typer.colors.RED)!s}:\n"

    if not zone_file:
        records: list[str] = lookup.rrset.to_text().split("\n")
        styled_records: list[str] = []
        for record in records:
            name, ttl, rclass, rtype, *rdata = record.split(" ")
            styled_records.append(
                f"- {typer.style(name, fg=typer.colors.GREEN)!s} {typer.style(ttl, fg=typer.colors.RESET)!s} {typer.style(rclass, fg=typer.colors.RESET)!s} {typer.style(rtype, fg=typer.colors.BLUE)!s} {typer.style(' ' .join(rdata), fg=typer.colors.MAGENTA)!s}"
            )
        output += "\n".join(styled_records)
        time_taken = f"{time_taken * 1000:.3f}ms"
        output += (
            f"\n\n{typer.style('Query Metadata:', fg=typer.colors.CYAN, underline=True)}\n"
            f"Time taken: {typer.style(time_taken, fg=typer.colors.YELLOW)}\n"
        )

        typer.secho(output)

    if zone_file:
        temp_rrset = lookup.rrset.to_text().split("\n")
        rrset = []
        for ix, rr in enumerate(temp_rrset):
            if ix == 0:
                rrset.append(rr)
                continue
            rrset.append(textwrap.indent(rr, " " * 12))
        rrset = "\n".join(rrset)
        output = textwrap.dedent(
            f"""
            ; <<>> Spade {__version__} <<>> {b'.'.join(lookup.qname.labels).decode('utf-8')} 
            ;; Got answer:
            ;; ->>HEADER<<- opcode: {opcode.to_text(lookup.response.opcode())}, status: NOERROR, id: {lookup.response.id}
            ;; flags: {flags.to_text(lookup.response.flags)};

            ;; ANSWER SECTION:
            {rrset}

            ;; Query time: {time_taken * 1000:.3f} msec
            ;; SERVER: {lookup.nameserver}:{lookup.port}
            ;; WHEN: {time.strftime("%H:%M:%S %a %d %b %Y %Z")}
            """
        )
        typer.echo(output)
