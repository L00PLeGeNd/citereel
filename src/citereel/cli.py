from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, TypeVar

import typer

from citereel import __version__
from citereel.diff import diff_runs, format_diff
from citereel.generate.providers import format_providers_help
from citereel.html import render_html
from citereel.models import Run
from citereel.paths import (
    DEMO_DOCS,
    DEMO_EVAL_SUITE,
    resolve_run_path,
    sample_html_path,
    sample_run_path,
)
from citereel.pipeline import ask
from citereel.replay import replay as replay_run
from citereel.term import get_console, open_hint, safe_str
from citereel.validate import validate_run
from citereel.view import html_written, render_citation, render_home, render_next_steps, render_run

# gui / eval imported lazily to keep core CLI light.

F = TypeVar("F", bound=Callable[..., object])

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "Verifiable RAG run records: cite, check evidence, eval configs, compare. "
        "Short cmds (PowerShell/cmd/bash/zsh): "
        "a ask | e eval | c check | df diff | g gui | d demo | r replay"
    ),
)
console = get_console()


def _cmds(*names: str) -> Callable[[F], F]:
    """Register one handler under several command names (no shell aliases needed)."""

    def deco(fn: F) -> F:
        for name in names:
            app.command(name)(fn)
        return fn

    return deco


@app.callback()
def main(ctx: typer.Context) -> None:
    """Cited RAG: record > cite > jump to the supporting chunk."""
    if ctx.invoked_subcommand is None:
        render_home(version=__version__)


@_cmds("version")
def version_command() -> None:
    """Print package version."""
    console.print(f"citereel {__version__}")


@_cmds("providers", "prov", "p")
def providers_command() -> None:
    """List OpenAI-compatible provider presets."""
    console.print(format_providers_help())


@_cmds("ask", "a")
def ask_command(
    query: str = typer.Argument(..., help="User question"),
    docs: Path = typer.Option(DEMO_DOCS, "--docs", "-d", help="Folder of .md/.txt/.pdf docs"),
    out: Path = typer.Option(Path("run.json"), "--out", "-o", help="Where to write the run file"),
    k: int = typer.Option(3, "--k", help="Top-k chunks"),
    retriever: str = typer.Option(
        "embedding",
        "--retriever",
        "-R",
        help="Retriever: embedding|keyword",
    ),
    generator: str = typer.Option(
        "auto",
        "--generator",
        "-g",
        help="Generator: auto|offline|openai",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-P",
        help="LLM preset (see: citereel p)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Chat model id (or OPENAI_MODEL)",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        "-b",
        help="OpenAI-compatible API base URL",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        "-S",
        help="Fail if citation validation errors are found",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show step details"),
) -> None:
    """Run cited RAG over local docs and save a run.json."""
    console.print("[dim]working...[/dim]")
    try:
        run = ask(
            query,
            docs,
            k=k,
            retriever=retriever,
            generator=generator,
            model=model,
            provider=provider,
            base_url=base_url,
            strict=strict,
        )
    except (RuntimeError, ValueError) as exc:
        console.print(f"[red]error[/red]  {safe_str(exc)}")
        raise typer.Exit(code=1) from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    run.save(str(out))
    render_run(run, saved_to=out.resolve(), verbose=verbose)
    out_disp = safe_str(out)
    render_next_steps(
        f"citereel s 1 {out_disp}",
        f"citereel h {out_disp}",
        f"citereel r {out_disp}",
    )


@_cmds("view", "vw")
def view_command(
    path: Optional[Path] = typer.Argument(None, help="run.json (default: sample)"),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show step details"),
) -> None:
    """Pretty-print a recorded run and citation map."""
    run_path = _load_path(path)
    render_run(Run.load(str(run_path)), verbose=verbose)


@_cmds("show", "s")
def show_command(
    n: int = typer.Argument(..., help="Citation number, e.g. 1 for [1]"),
    path: Optional[Path] = typer.Argument(None, help="run.json (default: sample)"),
) -> None:
    """Show the chunk behind citation N."""
    run_path = _load_path(path)
    render_citation(Run.load(str(run_path)), n)


@_cmds("html", "h")
def html_command(
    path: Optional[Path] = typer.Argument(None, help="run.json (default: sample)"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="HTML output path"),
) -> None:
    """Write a single-file HTML page with clickable citations."""
    run_path = _load_path(path)
    sample = sample_run_path()
    destination = out or (
        sample_html_path() if run_path.resolve() == sample.resolve() else Path("run.html")
    )
    run = Run.load(str(run_path))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_html(run), encoding="utf-8", newline="\n")
    html_written(destination.resolve())


@_cmds("replay", "r")
def replay_command(
    path: Optional[Path] = typer.Argument(None, help="run.json (default: sample)"),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show step details"),
) -> None:
    """Replay a run offline (no LLM)."""
    run_path = _load_path(path)
    replay_run(Run.load(str(run_path)), verbose=verbose)


@_cmds("diff", "df")
def diff_command(
    a: Path = typer.Argument(..., help="First run.json"),
    b: Path = typer.Argument(..., help="Second run.json"),
) -> None:
    """Compare two recorded runs."""
    left_path = _load_path(a)
    right_path = _load_path(b)
    left = Run.load(str(left_path))
    right = Run.load(str(right_path))
    report = format_diff(diff_runs(left, right), label_a=left_path.name, label_b=right_path.name)
    console.print(safe_str(report))


@_cmds("check", "c")
def check_command(
    path: Optional[Path] = typer.Argument(None, help="run.json (default: sample)"),
    evidence: bool = typer.Option(
        False,
        "--evidence",
        "-E",
        help="Also judge whether cited passages support the claims (not just structure)",
    ),
) -> None:
    """Validate citation structure; optionally evaluate semantic evidence support."""
    run_path = _load_path(path)
    run = Run.load(str(run_path))
    result = validate_run(run, evidence=evidence)
    if result.ok:
        console.print(f"[green]ok[/green]  {safe_str(run_path)}")
    else:
        console.print(f"[red]fail[/red]  {safe_str(run_path)}")
        for err in result.errors:
            console.print(f"  - {safe_str(err)}")
        for err in result.evidence_errors:
            console.print(f"  - [evidence] {safe_str(err)}")
    for warn in result.warnings:
        console.print(f"[yellow]warn[/yellow]  {safe_str(warn)}")
    if not result.ok:
        raise typer.Exit(code=1)


@_cmds("eval", "e")
def eval_command(
    suite: Optional[Path] = typer.Argument(
        None,
        help="Eval suite JSON (default: bundled demo-refund)",
    ),
    name: str = typer.Option("default", "--name", "-n", help="Config label in the report"),
    retriever: str = typer.Option("embedding", "--retriever", "-R", help="embedding|keyword"),
    generator: str = typer.Option("offline", "--generator", "-g", help="offline|openai|auto"),
    provider: Optional[str] = typer.Option(None, "--provider", "-P", help="LLM preset"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Chat model"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-b", help="API base URL"),
    k: int = typer.Option(3, "--k", help="Top-k chunks"),
    out_dir: Optional[Path] = typer.Option(
        None,
        "--out-dir",
        "-o",
        help="Write per-case run.json + report JSON here",
    ),
    against: Optional[Path] = typer.Option(
        None,
        "--against",
        "-A",
        help="Previous report__*.json to compare against",
    ),
) -> None:
    """Run a fixed eval suite; optionally compare to a prior report."""
    from citereel.eval.compare import compare_suite_reports, format_comparison, format_suite_report
    from citereel.eval.dataset import load_suite
    from citereel.eval.report import SuiteReport
    from citereel.eval.runner import RagConfig, run_suite

    suite_path = suite or DEMO_EVAL_SUITE
    loaded = load_suite(suite_path)
    config = RagConfig(
        name=name,
        retriever=retriever,
        generator=generator,
        k=k,
        provider=provider,
        model=model,
        base_url=base_url,
    )
    console.print(
        f"[dim]eval[/dim]  suite={safe_str(loaded.id)}  config={safe_str(name)}  "
        f"docs={safe_str(loaded.resolve_docs())}"
    )
    report = run_suite(loaded, config, out_dir=out_dir)
    console.print(safe_str(format_suite_report(report)))
    if against is not None:
        import json

        raw = json.loads(Path(against).read_text(encoding="utf-8"))
        prior = SuiteReport.from_dict(raw)
        console.print()
        console.print(safe_str(format_comparison(compare_suite_reports(prior, report))))
    if report.passed_count < report.total:
        raise typer.Exit(code=1)


@_cmds("gui", "g", "ui")
def gui_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8765, "--port", help="Bind port"),
) -> None:
    """Open the desktop GUI (webview shell; browser fallback)."""
    from citereel.gui import run_gui

    run_gui(host=host, port=port)


@_cmds("demo", "d")
def demo_command(
    retriever: str = typer.Option("embedding", "--retriever", "-R", help="embedding|keyword"),
    generator: str = typer.Option("auto", "--generator", "-g", help="auto|offline|openai"),
    provider: Optional[str] = typer.Option(None, "--provider", "-P", help="LLM preset"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Chat model"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-b", help="API base URL"),
    html: bool = typer.Option(False, "--html", "-H", help="Also write sample_run.html"),
    strict: bool = typer.Option(False, "--strict", "-S", help="Fail on validation errors"),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show step details"),
) -> None:
    """Run the bundled refund-window demo and write the sample run."""
    console.print("[dim]demo: loading docs / retrieving / generating...[/dim]")
    try:
        run = ask(
            "What is the refund window?",
            DEMO_DOCS,
            k=3,
            retriever=retriever,
            generator=generator,
            model=model,
            provider=provider,
            base_url=base_url,
            strict=strict,
        )
    except (RuntimeError, ValueError) as exc:
        console.print(f"[red]error[/red]  {safe_str(exc)}")
        raise typer.Exit(code=1) from exc
    out_run = sample_run_path()
    out_html = sample_html_path()
    out_run.parent.mkdir(parents=True, exist_ok=True)
    run.save(str(out_run))
    render_run(run, saved_to=out_run, verbose=verbose)

    if html:
        out_html.write_text(render_html(run), encoding="utf-8", newline="\n")
        console.print(f"[green]wrote[/green]  {safe_str(out_html)}")
        render_next_steps(open_hint(out_html), "citereel s 1")
    else:
        render_next_steps("citereel s 1", "citereel h", "citereel r")


def _load_path(path: Path | None) -> Path:
    try:
        return resolve_run_path(path)
    except FileNotFoundError as exc:
        console.print(f"[red]error[/red]  {safe_str(exc)}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
