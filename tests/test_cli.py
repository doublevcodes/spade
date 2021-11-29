from spade import __app_name__, __version__, cli
from typer.testing import CliRunner

runner = CliRunner()


def test_version():
    result = runner.invoke(cli.spade, ["--version"])
    assert result.exit_code == 0
    assert f"{__app_name__} v{__version__}" in result.stdout


def test_version_callback():
    result = cli.version(True)
    assert result is None
