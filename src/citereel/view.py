from __future__ import annotations

import re
import textwrap
from pathlib import Path

from rich.markup import escape
from rich.rule import Rule
from rich.text import Text

from citereel.models import Run
from citereel.term import get_console, open_hint, safe_str, wrap_width

console = get_console()

_CITE = re.compile(r"\[(\d+)\]")
_EXCERPT = 72


def render_home(*, version: str) -> None:
    console.print()
    console.print(f"[bold cyan]citereel[/bold cyan]  [dim]v{safe_str(version)}[/dim]")
    console.print(
        "[dim]why did RAG answer that? cite · evidence · eval configs · compare[/dim]"
    )
    console.print()
    console.print("[bold]start[/bold]  [dim](same on PowerShell / cmd / bash / zsh)[/dim]")
    console.print("  citereel e          # fixed-suite eval (bundled demo)")
    console.print("  citereel d          # interactive demo")
    console.print("  citereel c run.json -E   # structure + evidence")
    console.print()
    console.print("[bold]shorts[/bold]")
    console.print("  e eval | a ask | c check | df diff | g gui | d demo | r replay | s show")
    console.print("  citereel e -n emb -o ./out && citereel e -n kw -R keyword -A ./out/report__emb.json")
    console.print()
    console.print("[dim]-h/--help everywhere; path args optional after demo[/dim]")
    console.print()


def render_run(run: Run, *, saved_to: Path | None = None, verbose: bool = False) -> None:
    console.print()
    console.print(Rule(f"[bold]run[/bold] {escape(safe_str(run.id))}"))
    meta = _meta_line(run)
    if meta:
        console.print(f"[dim]{escape(meta)}[/dim]")

    console.print()
    console.print("[bold cyan]Q[/bold cyan]  " + escape(safe_str(run.query)))
    console.print()
    console.print("[bold green]A[/bold green]")
    _print_wrapped(run.answer, cite=True)

    console.print()
    console.print("[bold]citations[/bold]  [dim]citereel show N[/dim]")
    by_id = run.chunk_by_id()
    if not run.citations:
        console.print("  [dim](none)[/dim]")
    for cite in run.citations:
        chunk = by_id.get(cite.chunk_id)
        source = chunk.source if chunk else "?"
        preview = _excerpt(chunk.text if chunk else "(missing)")
        console.print(
            f"  [bold yellow]\\[{cite.n}][/bold yellow]  "
            f"{escape(safe_str(source))}  [dim]{escape(safe_str(cite.chunk_id))}[/dim]"
        )
        console.print(f"      {escape(safe_str(preview))}")

    console.print()
    console.print("[bold]steps[/bold]")
    if not run.steps:
        console.print("  [dim](none)[/dim]")
    for index, step in enumerate(run.steps, start=1):
        console.print(f"  {index}. {escape(step.type)}  [dim]{step.ms} ms[/dim]")
        if verbose:
            for key, value in step.detail.items():
                console.print(
                    f"      [dim]{escape(safe_str(key))}={escape(safe_str(value))}[/dim]"
                )

    if saved_to is not None:
        console.print()
        console.print(f"[green]saved[/green]  {escape(safe_str(saved_to))}")


def render_next_steps(*lines: str) -> None:
    console.print()
    console.print("[bold]next[/bold]")
    for line in lines:
        console.print(f"  {safe_str(line)}")
    console.print()


def render_citation(run: Run, n: int) -> None:
    """Full supporting chunk. Avoid Rich Panel -- it clips on some Windows consoles."""
    chunk = run.resolve_citation(n)
    console.print()
    console.print(Rule(f"[bold yellow]\\[{n}][/bold yellow]  {escape(safe_str(chunk.source))}"))
    console.print(f"[dim]{escape(safe_str(chunk.id))}[/dim]")
    console.print()
    _print_wrapped(chunk.text, cite=False)
    console.print()
    console.print("[dim]citation -> supporting chunk[/dim]")
    console.print()


def html_written(path: Path) -> None:
    console.print()
    console.print(f"[green]wrote[/green]  {escape(safe_str(path))}")
    render_next_steps(open_hint(path), "citereel show 1")


def _print_wrapped(text: str, *, cite: bool) -> None:
    width = wrap_width(console)
    body = safe_str(text).strip()
    if not body:
        console.print("[dim](empty)[/dim]")
        return
    for paragraph in body.splitlines() or [body]:
        if not paragraph.strip():
            console.print()
            continue
        wrapped = textwrap.fill(paragraph, width=width)
        if cite:
            console.print(_answer_text(wrapped))
        else:
            console.print(wrapped)


def _meta_line(run: Run) -> str:
    parts = []
    for key in ("retriever", "generator", "provider", "model"):
        if key in run.meta:
            parts.append(f"{key}={run.meta[key]}")
    return "  ".join(parts)


def _excerpt(text: str, width: int = _EXCERPT) -> str:
    one_line = " ".join(text.split())
    return textwrap.shorten(one_line, width=width, placeholder="...")


def _answer_text(answer: str) -> Text:
    text = Text()
    pos = 0
    for match in _CITE.finditer(answer):
        if match.start() > pos:
            text.append(safe_str(answer[pos : match.start()]))
        text.append(f"[{match.group(1)}]", style="bold yellow")
        pos = match.end()
    if pos < len(answer):
        text.append(safe_str(answer[pos:]))
    return text
