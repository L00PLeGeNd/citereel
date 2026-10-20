from __future__ import annotations

from citereel.generate.openai_gen import OpenAIGenerator, citations_from_answer
from citereel.models import Chunk, Run


class FakeChatClient:
    """Stand-in for OpenAI: returns a fixed completion string."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.content


def _chunks() -> list[Chunk]:
    return [
        Chunk(id="handbook.md#0", source="handbook.md", text="Refunds within 14 days."),
        Chunk(id="faq.md#0", source="faq.md", text="Support hours are 9–5."),
    ]


def test_citations_subset_of_retrieved_and_resolve() -> None:
    client = FakeChatClient("You may request a refund within 14 days [1]. Hours are in the FAQ [2].")
    gen = OpenAIGenerator(client=client, model="fake")
    answer, citations, step = gen.generate("What is the refund window?", _chunks())

    assert "[1]" in answer
    assert step.detail["mode"] == "openai"
    assert step.detail["model"] == "fake"

    retrieved = _chunks()
    ids = {c.id for c in retrieved}
    for cite in citations:
        assert cite.chunk_id in ids

    run = Run(
        query="q",
        retrieved=retrieved,
        answer=answer,
        citations=citations,
        steps=[step],
        meta={"generator": "openai"},
    )
    for cite in citations:
        assert run.resolve_citation(cite.n).id == cite.chunk_id


def test_out_of_range_citation_marks_are_stripped() -> None:
    client = FakeChatClient("Bad claim [9] but good [1].")
    gen = OpenAIGenerator(client=client)
    answer, citations, _ = gen.generate("q", _chunks())
    assert "[9]" not in answer
    assert "[1]" in answer
    assert all(c.n == 1 for c in citations)
    assert citations[0].chunk_id == "handbook.md#0"


def test_citations_from_answer_helper() -> None:
    chunks = _chunks()
    cites = citations_from_answer("See [2] and [1] and [2].", chunks)
    assert [c.n for c in cites] == [2, 1]
    assert cites[0].chunk_id == "faq.md#0"
