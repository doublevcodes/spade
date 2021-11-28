from typing import Optional

import typer

from spade import __app_name__, __version__, dig


class Spade(typer.Typer):
    def __init__(self):
        super().__init__()


spade = Spade()


def _version_callback(value: bool):
    if value:
        print(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@spade.callback()
def main(
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


spade.command()(dig.dig)

if __name__ == "__main__":
    spade(prog_name=__app_name__)
