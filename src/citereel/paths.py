from __future__ import annotations

from pathlib import Path

_PKG = Path(__file__).resolve().parent
_BUNDLED = _PKG / "bundled"

# Always shipped inside the package (works after pip install).
DEMO_DOCS = _BUNDLED / "demo_docs"
DEMO_EVAL_SUITE = _BUNDLED / "eval" / "demo_suite.json"


def package_root() -> Path | None:
    """Repo root for an editable/source checkout; None when installed from a wheel."""
    maybe_src = _PKG.parent
    maybe_root = maybe_src.parent
    if maybe_src.name == "src" and (maybe_root / "pyproject.toml").is_file():
        return maybe_root
    return None


def sample_run_path() -> Path:
    """Where demo writes / default show+html read the sample run."""
    root = package_root()
    if root is not None:
        return root / "examples" / "sample_run.json"
    return Path.cwd() / "sample_run.json"


def sample_html_path() -> Path:
    root = package_root()
    if root is not None:
        return root / "examples" / "sample_run.html"
    return Path.cwd() / "sample_run.html"


def resolve_run_path(path: Path | None = None) -> Path:
    """Resolve a run.json path.

    Order: explicit path → CWD sample_run.json → repo examples/ → error.
    """
    if path is None:
        candidates = [
            Path.cwd() / "sample_run.json",
            sample_run_path(),
        ]
        root = package_root()
        if root is not None:
            candidates.append(root / "examples" / "sample_run.json")
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        raise FileNotFoundError(
            "No run file given. Run: citereel demo\n"
            "Or pass a path: citereel show 1 path/to/run.json"
        )

    if path.is_file():
        return path.resolve()

    cwd_hit = Path.cwd() / path
    if cwd_hit.is_file():
        return cwd_hit.resolve()

    root = package_root()
    if root is not None:
        under_examples = root / "examples" / path.name
        if under_examples.is_file():
            return under_examples.resolve()
        nested = root / path
        if nested.is_file():
            return nested.resolve()

    raise FileNotFoundError(
        f"Run file not found: {path}\n"
        "Tried the current directory"
        + (" and the repo examples/ folder" if root else "")
        + ". Run: citereel demo"
    )
