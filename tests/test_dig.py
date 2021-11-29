import pytest
from spade import cli
from typer.testing import CliRunner


def test_dns_lookup():
    result = CliRunner().invoke(cli.spade, ["dig", "example.com"])
    assert result.exit_code == 0
    assert "example.com." in result.stdout
    assert "A" in result.stdout
    assert "93.184.216.34" in result.stdout
    assert "IN" in result.stdout
    assert "1.1.1.1:53" in result.stdout


def test_dns_lookup_invalid_record_type():
    with pytest.raises(AttributeError):
        CliRunner().invoke(cli.spade, ["dig", "example.com", "BAD"])
