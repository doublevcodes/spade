import importlib
from pathlib import Path
from typing import Optional

import typer

from spade import __app_name__, __version__


class Spade(typer.Typer):
    def __init__(self):
        super().__init__()


spade = Spade()


def _version_callback(value: bool):
    if value:
        print(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@spade.callback()
def version(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the version and exit",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return


for command_file in (Path(__file__).parent / "commands").glob("*.py"):
    command_name = command_file.stem
    command_module = importlib.import_module(f"spade.commands.{command_name}")
    command_function = getattr(command_module, command_name)
    spade.command()(command_function)

if __name__ == "__main__":
    spade(prog_name=__app_name__)
