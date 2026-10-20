from typer.testing import CliRunner

from citereel.cli import app

runner = CliRunner()


def test_short_commands_are_registered() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    out = result.stdout
    for name in ("a", "s", "h", "d", "c", "r", "p", "df", "e", "ask", "show", "demo", "eval"):
        assert name in out


def test_show_alias_works() -> None:
    result = runner.invoke(app, ["s", "1"])
    assert result.exit_code == 0
    assert "14 days" in result.stdout or "handbook" in result.stdout.lower()


def test_check_alias_works() -> None:
    result = runner.invoke(app, ["c"])
    assert result.exit_code == 0
    assert "ok" in result.stdout.lower()
