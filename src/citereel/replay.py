from __future__ import annotations

from citereel.models import Run
from citereel.term import get_console, safe_str
from citereel.view import render_run

console = get_console()


def format_replay_banner(run: Run) -> str:
    """One-line repro summary for offline replay (no retrieve / no LLM)."""
    meta = run.meta or {}
    cfg = meta.get("config") if isinstance(meta.get("config"), dict) else {}
    docs_fp = str(meta.get("docs_fingerprint") or "-")
    parts = [
        f"schema={run.schema_version}",
        f"docs_fp={docs_fp[:12]}",
        f"mode={meta.get('replay_mode', 'offline')}",
        f"retriever={cfg.get('retriever') or meta.get('retriever') or '-'}",
        f"generator={cfg.get('generator') or meta.get('generator') or '-'}",
    ]
    if cfg.get("embedder") or meta.get("embedder"):
        parts.append(f"embedder={cfg.get('embedder') or meta.get('embedder')}")
    if cfg.get("model") or meta.get("model"):
        parts.append(f"model={cfg.get('model') or meta.get('model')}")
    if cfg.get("provider") or meta.get("provider"):
        parts.append(f"provider={cfg.get('provider') or meta.get('provider')}")
    if cfg.get("base_url") or meta.get("base_url"):
        parts.append(f"base_url={cfg.get('base_url') or meta.get('base_url')}")
    if cfg.get("chunk_strategy"):
        parts.append(f"chunk={cfg['chunk_strategy']}")
    if cfg.get("max_chunk_chars") is not None:
        parts.append(f"max_chunk={cfg['max_chunk_chars']}")
    if cfg.get("k") is not None:
        parts.append(f"k={cfg['k']}")
    version = cfg.get("citereel_version") or meta.get("citereel_version")
    if version:
        parts.append(f"citereel={version}")
    return "  ".join(str(p) for p in parts)


def replay(run: Run, *, verbose: bool = False) -> None:
    """Offline replay only: re-display a saved run. Does not re-retrieve or call an LLM.

    To re-execute an experiment with live retrieval/generation, run `citereel ask` again
    and compare with `citereel diff`.
    """
    console.print()
    console.print("[bold]replay[/bold]  [dim]offline · no retrieve · no LLM[/dim]")
    console.print(f"[dim]{safe_str(format_replay_banner(run))}[/dim]")
    if verbose and run.meta:
        console.print(f"[dim]{safe_str(run.meta)}[/dim]")
    render_run(run, verbose=verbose)
