from __future__ import annotations

import os
import re
import time
from typing import Any, Protocol

from citereel.limits import llm_retries, llm_timeout_s
from citereel.models import Chunk, Citation, Step

_CITE = re.compile(r"\[(\d+)\]")


class ChatClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


class OpenAIHttpClient:
    """Thin wrapper around any OpenAI-compatible chat.completions API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        provider: str = "openai",
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised when extra missing
            raise ImportError(
                "OpenAIGenerator needs the openai package. Install with: pip install 'citereel[llm]'"
            ) from exc
        key = api_key or os.environ.get("OPENAI_API_KEY")
        timeout = llm_timeout_s()
        kwargs: dict[str, Any] = {"api_key": key or "unused", "timeout": timeout}
        if base_url or os.environ.get("OPENAI_BASE_URL"):
            kwargs["base_url"] = base_url or os.environ.get("OPENAI_BASE_URL")
        self._client = OpenAI(**kwargs)
        self.model = model
        self.provider = provider
        self.base_url = kwargs.get("base_url")
        self.timeout = timeout

    def complete(self, messages: list[dict[str, str]]) -> str:
        attempts = llm_retries() + 1
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0,
                    max_tokens=400,
                )
                content = resp.choices[0].message.content
                return content or ""
            except Exception as exc:
                last_exc = exc
                if attempt >= attempts or not _retryable(exc):
                    break
                time.sleep(min(2 ** (attempt - 1), 8))
        assert last_exc is not None
        raise _friendly_llm_error(
            last_exc, model=self.model, provider=self.provider, base_url=self.base_url
        ) from last_exc


class OpenAIGenerator:
    """LLM answers that must cite retrieved chunks with [n] marks."""

    def __init__(
        self,
        *,
        client: ChatClient | None = None,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        provider: str = "openai",
    ) -> None:
        self.model = model
        self.provider = provider
        self._client = client or OpenAIHttpClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            provider=provider,
        )
        self.base_url = base_url or getattr(self._client, "base_url", None)

    def generate(
        self,
        query: str,
        retrieved: list[Chunk],
    ) -> tuple[str, list[Citation], Step]:
        t0 = time.perf_counter()
        if not retrieved:
            answer = "I could not find supporting documents for that question."
            citations: list[Citation] = []
        else:
            raw = self._client.complete(_prompt_messages(query, retrieved))
            answer = sanitize_answer(raw, len(retrieved))
            citations = citations_from_answer(answer, retrieved)
        ms = (time.perf_counter() - t0) * 1000
        detail: dict[str, Any] = {
            "mode": "openai",
            "provider": self.provider,
            "model": self.model,
            "query": query,
            "citation_count": len(citations),
        }
        if self.base_url:
            detail["base_url"] = self.base_url
        step = Step(
            type="generate",
            ms=round(ms, 2),
            detail=detail,
        )
        return answer, citations, step


def citations_from_answer(answer: str, retrieved: list[Chunk]) -> list[Citation]:
    """Map unique [n] marks in answer order to retrieved chunk ids (1-based)."""
    seen: set[int] = set()
    out: list[Citation] = []
    for match in _CITE.finditer(answer):
        n = int(match.group(1))
        if n in seen or n < 1 or n > len(retrieved):
            continue
        seen.add(n)
        out.append(Citation(n=n, chunk_id=retrieved[n - 1].id))
    return out


def sanitize_answer(answer: str, n_chunks: int) -> str:
    """Drop [n] marks that do not point at a retrieved chunk."""

    def repl(match: re.Match[str]) -> str:
        n = int(match.group(1))
        if 1 <= n <= n_chunks:
            return match.group(0)
        return ""

    cleaned = _CITE.sub(repl, answer)
    return re.sub(r"  +", " ", cleaned).strip()


def _prompt_messages(query: str, retrieved: list[Chunk]) -> list[dict[str, str]]:
    lines = []
    for i, chunk in enumerate(retrieved, start=1):
        lines.append(f"[{i}] source={chunk.source} id={chunk.id}\n{chunk.text}")
    context = "\n\n".join(lines)
    system = (
        "Answer ONLY from the numbered passages. "
        "Be concise (1-3 sentences). State facts precisely; do not speculate. "
        "Cite each used passage with [n] (1-based). "
        "Never invent citation numbers. Never cite a number not listed. "
        "A citation mark means the passage must actually support that claim; "
        "do not attach [n] to unsupported conclusions. "
        "If the passages do not support an answer, say so without citations."
    )
    user = f"Passages:\n\n{context}\n\nQuestion: {query}\n\nAnswer with citations:"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _retryable(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "timeout" in name or "timeout" in text or "timed out" in text:
        return True
    if "rate" in text or "429" in text or "503" in text or "502" in text:
        return True
    if "connection" in name or "connection" in text:
        return True
    return False


def _friendly_llm_error(
    exc: Exception,
    *,
    model: str,
    provider: str,
    base_url: str | None,
) -> RuntimeError:
    text = str(exc)
    hint = (
        f"LLM call failed (provider={provider}, model={model}, base_url={base_url or 'default'}).\n"
        f"  Fix with: --provider {provider} --model <name>\n"
        "  Or set OPENAI_MODEL / OPENAI_BASE_URL\n"
        "  Timeouts: CITEREEL_LLM_TIMEOUT / CITEREEL_LLM_RETRIES\n"
        "  List presets: citereel providers\n"
        f"  Upstream: {text}"
    )
    return RuntimeError(hint)
