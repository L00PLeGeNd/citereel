import json
from pathlib import Path

import pytest

from citereel.models import Run, RunSchemaError


def test_load_missing_required_field(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"answer": "hi", "retrieved": [], "citations": []}), encoding="utf-8")
    with pytest.raises(RunSchemaError, match="query"):
        Run.load(str(path))


def test_load_wrong_type(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "query": "q",
                "answer": "a",
                "retrieved": "not-a-list",
                "citations": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RunSchemaError, match="retrieved"):
        Run.load(str(path))


def test_load_unknown_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 99,
                "query": "q",
                "answer": "a",
                "retrieved": [],
                "citations": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RunSchemaError, match="schema_version"):
        Run.load(str(path))


def test_load_corrupt_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(RunSchemaError, match="JSON"):
        Run.load(str(path))


def test_load_accepts_v1_and_preserves_chunk_page(tmp_path: Path) -> None:
    path = tmp_path / "ok.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "query": "q",
                "answer": "a [1]",
                "retrieved": [
                    {
                        "id": "g.pdf#p1",
                        "source": "g.pdf",
                        "text": "14 days",
                        "page": 1,
                    }
                ],
                "citations": [{"n": 1, "chunk_id": "g.pdf#p1"}],
                "meta": {},
            }
        ),
        encoding="utf-8",
    )
    run = Run.load(str(path))
    assert run.retrieved[0].page == 1
