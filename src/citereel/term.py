from __future__ import annotations

import os
import sys
from functools import lru_cache

from rich.console import Console


def _prefer_utf8_stdio() -> bool:
    """Best-effort UTF-8 so Windows GBK consoles do not crash on paths/text."""
    ok = True
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                ok = False
        else:
            ok = False
    return ok


def _want_no_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return True
    if os.environ.get("CITEREEL_NO_COLOR"):
        return True
    if os.environ.get("TERM") == "dumb":
        return True
    return False


@lru_cache(maxsize=1)
def get_console() -> Console:
    utf8_ok = _prefer_utf8_stdio()
    # Legacy Win32 renderer clips Panel text; modern VT mode is safer after UTF-8.
    use_legacy = sys.platform.startswith("win") and not utf8_ok
    return Console(
        soft_wrap=True,
        emoji=False,
        highlight=False,
        legacy_windows=use_legacy,
        no_color=_want_no_color(),
    )


def safe_str(value: object) -> str:
    """Encode-safe string for the active stdout encoding."""
    text = str(value)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except UnicodeEncodeError:
        return text.encode(encoding, errors="replace").decode(encoding)


def open_hint(path: object) -> str:
    """Platform-appropriate 'open this file' hint (display only)."""
    target = safe_str(path)
    if sys.platform.startswith("win"):
        return f'start "" "{target}"'
    if sys.platform == "darwin":
        return f'open "{target}"'
    return f'xdg-open "{target}"'


def wrap_width(console: Console, *, pad: int = 2, cap: int = 88) -> int:
    width = console.width or 80
    return max(40, min(width - pad, cap))
