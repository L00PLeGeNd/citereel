from pathlib import Path

import pytest

from citereel.paths import DEMO_DOCS, resolve_run_path, sample_run_path


def test_bundled_demo_docs_exist() -> None:
    assert DEMO_DOCS.is_dir()
    assert (DEMO_DOCS / "handbook.md").is_file()


def test_resolve_default_sample_run() -> None:
    path = resolve_run_path(None)
    assert path == sample_run_path().resolve() or path.name == "sample_run.json"
    assert path.is_file()


def test_resolve_falls_back_to_repo_examples(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = resolve_run_path(Path("sample_run.json"))
    assert path == sample_run_path().resolve()


def test_resolve_missing_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="not found"):
        resolve_run_path(Path("nope.json"))
