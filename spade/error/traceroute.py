import typer
from rich import box
from rich import print
from rich.panel import Panel


class SocketPermissionError(Exception):
    def repr(self):
        return Panel.fit(
            f"\n[red]This user doesn't have permission to create raw sockets on this system[/red]\n[orange]You can retry this command as an administrator or superuser[/orange]\n",
            title=f"Missing required permissions",
            box=box.SQUARE,
        )

    def raise_cli(self) -> str:
        print()
        print(self.repr())
        print()
        raise typer.Exit(code=1)