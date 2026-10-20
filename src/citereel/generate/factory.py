from __future__ import annotations

from citereel.generate.base import Generator
from citereel.generate.offline import OfflineGenerator
from citereel.generate.openai_gen import OpenAIGenerator
from citereel.generate.providers import LlmConfig, resolve_llm_config


def default_chat_model(*, model: str | None = None, base_url: str | None = None) -> str:
    """Back-compat helper: resolve model only."""
    return resolve_llm_config(model=model, base_url=base_url).model


def build_generator(
    name: str | None = None,
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    provider: str | None = None,
) -> Generator:
    """Resolve generator backend. `auto` uses an OpenAI-compatible API when a key is set."""
    key = (name or "auto").lower().strip()
    if key == "offline":
        return OfflineGenerator()

    cfg = resolve_llm_config(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
    if key in {"openai", "llm"}:
        return _openai_from_config(cfg)
    if key == "auto":
        if cfg.api_key:
            return _openai_from_config(cfg)
        return OfflineGenerator()
    raise ValueError(f"unknown generator {name!r}; use offline, openai, or auto")


def _openai_from_config(cfg: LlmConfig) -> OpenAIGenerator:
    return OpenAIGenerator(
        model=cfg.model,
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        provider=cfg.provider,
    )
