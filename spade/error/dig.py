import typer
from rich import box
from rich import print
from rich.panel import Panel


class InvalidRecordType(Exception):
    def __init__(self, rtype: str):
        self.rtype = rtype

    def repr(self):
        return Panel.fit(
            f"\n[red]The record type you provided - [bold]{self.rtype}[/bold] - is not valid[/red]\n[orange]Check out [blue]https://www.cloudflare.com/learning/dns/dns-records/[/blue] to see valid record types[/orange]\n",
            title=f"Invalid record type",
            box=box.SQUARE,
        )

    def raise_cli(self) -> str:
        print()
        print(self.repr())
        print()
        raise typer.Exit(code=1)


class TargetNonExistent(Exception):
    def __init__(self, target: str):
        self.target = target

    def repr(self):
        return Panel.fit(
            f"\n[red]The hostname you provided - [bold]{self.target}[/bold] - does not exist[/red]\n[orange]Make sure that the hostname you've provided exists[/orange]\n",
            title=f"Hostname not found",
            box=box.SQUARE,
        )

    def raise_cli(self) -> str:
        print()
        print(self.repr())
        print()
        raise typer.Exit(code=1)


class YXDOMAINError(Exception):
    def __init__(self, target: str):
        self.target = target

    def repr(self):
        return Panel.fit(
            f"\n[red]The hostname you provided - [bold]{self.target}[/bold] - should not exist, but it does[/red]\n[orange]The YXDOMAIN DNS status code is not very common. Please look into this further[/orange]\n",
            title=f"YXDOMAIN: {self.target}",
            box=box.SQUARE,
        )

    def raise_cli(self) -> str:
        print()
        print(self.repr())
        print()
        raise typer.Exit(code=1)


class RecordNonExistent(Exception):
    def __init__(self, target: str, rtype: str):
        self.rtype = rtype
        self.target = target

    def repr(self):
        return Panel.fit(
            f"\n[red]The hostname you provided - [bold]{self.target}[/bold] - does not have a [bold]{self.rtype}[/bold] record[/red]\n[orange]Make sure that the hostname you've provided contains a {self.rtype} record.\nIt may take time for a DNS record to propogate[/orange]\n",
            title=f"Record not found",
            box=box.SQUARE,
        )

    def raise_cli(self) -> str:
        print()
        print(self.repr())
        print()
        raise typer.Exit(code=1)
