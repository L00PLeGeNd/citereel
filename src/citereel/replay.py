from __future__ import annotations

from citereel.models import Run
from citereel.term import get_console, safe_str
from citereel.view import render_run

console = get_console()


def replay(run: Run, *, verbose: bool = False) -> None:
    """Offline replay only: re-display a saved run. Does not re-retrieve or call an LLM.

    To re-execute an experiment with live retrieval/generation, run `citereel ask` again
    and compare with `citereel diff`.
    """
    console.print()
    console.print("[bold]replay[/bold]  [dim]offline · no retrieve · no LLM[/dim]")
    console.print(
        f"[dim]schema={run.schema_version}  "
        f"docs_fp={(run.meta or {}).get('docs_fingerprint', '-')[:12]}  "
        f"mode={(run.meta or {}).get('replay_mode', 'offline')}[/dim]"
    )
    if verbose and run.meta:
        console.print(f"[dim]{safe_str(run.meta)}[/dim]")
    render_run(run, verbose=verbose)
