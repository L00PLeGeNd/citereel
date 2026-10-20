import sys

from citereel.term import open_hint, safe_str


def test_safe_str_ascii() -> None:
    assert safe_str("refund 14 days") == "refund 14 days"


def test_open_hint_matches_platform() -> None:
    hint = open_hint("/tmp/run.html")
    if sys.platform.startswith("win"):
        assert hint.startswith("start ")
    elif sys.platform == "darwin":
        assert hint.startswith("open ")
    else:
        assert hint.startswith("xdg-open ")
    assert "run.html" in hint
