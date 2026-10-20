from __future__ import annotations

import time
import webbrowser

from citereel.gui.server import start_server
from citereel.term import get_console, safe_str

console = get_console()


def run_gui(*, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start local UI; prefer a desktop webview shell, fall back to the system browser."""
    server, url = start_server(host=host, port=port)
    console.print(f"[green]gui[/green]  {safe_str(url)}")
    console.print("[dim]close the window (or Ctrl+C) to stop[/dim]")

    try:
        import webview
    except ImportError:
        console.print(
            "[yellow]tip[/yellow]  desktop shell: pip install 'citereel[gui]' then citereel g"
        )
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            server.shutdown()
        return

    webview.create_window(
        "citereel",
        url,
        width=960,
        height=780,
        min_size=(720, 560),
    )
    try:
        webview.start()
    finally:
        server.shutdown()
