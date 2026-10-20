from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    """OpenAI-compatible chat endpoint defaults."""

    name: str
    base_url: str | None
    model: str
    api_key_envs: tuple[str, ...] = ("OPENAI_API_KEY",)
    notes: str = ""


# Keep this list short and practical; any other host works via --base-url + --model.
PROVIDERS: dict[str, ProviderPreset] = {
    "openai": ProviderPreset(
        name="openai",
        base_url=None,
        model="gpt-4o-mini",
        api_key_envs=("OPENAI_API_KEY",),
        notes="Official OpenAI API",
    ),
    "deepseek": ProviderPreset(
        name="deepseek",
        base_url="https://api.deepseek.com",
        model="deepseek-flash",
        api_key_envs=("DEEPSEEK_API_KEY", "OPENAI_API_KEY"),
        notes="Also accepts deepseek-v4-pro depending on account",
    ),
    "moonshot": ProviderPreset(
        name="moonshot",
        base_url="https://api.moonshot.cn/v1",
        model="moonshot-v1-8k",
        api_key_envs=("MOONSHOT_API_KEY", "OPENAI_API_KEY"),
        notes="Kimi / Moonshot",
    ),
    "siliconflow": ProviderPreset(
        name="siliconflow",
        base_url="https://api.siliconflow.cn/v1",
        model="deepseek-ai/DeepSeek-V3",
        api_key_envs=("SILICONFLOW_API_KEY", "OPENAI_API_KEY"),
    ),
    "openrouter": ProviderPreset(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        model="openai/gpt-4o-mini",
        api_key_envs=("OPENROUTER_API_KEY", "OPENAI_API_KEY"),
    ),
    "groq": ProviderPreset(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        api_key_envs=("GROQ_API_KEY", "OPENAI_API_KEY"),
    ),
    "together": ProviderPreset(
        name="together",
        base_url="https://api.together.xyz/v1",
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        api_key_envs=("TOGETHER_API_KEY", "OPENAI_API_KEY"),
    ),
    "ollama": ProviderPreset(
        name="ollama",
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.2",
        api_key_envs=("OPENAI_API_KEY",),
        notes="Local; API key optional (dummy ok)",
    ),
}

_HOST_HINTS: tuple[tuple[str, str], ...] = (
    ("deepseek.com", "deepseek"),
    ("moonshot.cn", "moonshot"),
    ("siliconflow", "siliconflow"),
    ("openrouter.ai", "openrouter"),
    ("groq.com", "groq"),
    ("together.xyz", "together"),
    ("11434", "ollama"),
    ("localhost", "ollama"),
    ("127.0.0.1", "ollama"),
)


@dataclass(frozen=True)
class LlmConfig:
    provider: str
    model: str
    base_url: str | None
    api_key: str | None


def list_providers() -> list[ProviderPreset]:
    return [PROVIDERS[name] for name in sorted(PROVIDERS)]


def detect_provider(base_url: str | None) -> str | None:
    if not base_url:
        return None
    lowered = base_url.lower()
    for needle, name in _HOST_HINTS:
        if needle in lowered:
            return name
    return None


def resolve_llm_config(
    *,
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> LlmConfig:
    """Resolve OpenAI-compatible settings from flags, env, and presets.

    Precedence for each field:
      explicit flag > env > provider preset > openai defaults
    """
    env_provider = (os.environ.get("CITEREEL_PROVIDER") or os.environ.get("OPENAI_PROVIDER") or "").strip()
    env_base = (os.environ.get("OPENAI_BASE_URL") or "").strip() or None
    env_model = (os.environ.get("OPENAI_MODEL") or "").strip() or None

    resolved_base = (base_url or env_base or None)
    if resolved_base == "":
        resolved_base = None

    explicit_provider = bool(provider or env_provider)
    name = (provider or env_provider or detect_provider(resolved_base) or "openai").lower().strip()
    if name not in PROVIDERS:
        known = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"unknown provider {name!r}; try: {known}")

    preset = PROVIDERS[name]
    if resolved_base is None and preset.base_url:
        resolved_base = preset.base_url

    # If only a base URL was set (or openai + foreign host), prefer host preset.
    if not explicit_provider or name == "openai":
        hinted = detect_provider(resolved_base)
        if hinted and hinted in PROVIDERS:
            name = hinted
            preset = PROVIDERS[name]
            if base_url is None and env_base is None and preset.base_url:
                resolved_base = preset.base_url

    resolved_model = model or env_model or preset.model
    resolved_key = api_key
    if not resolved_key:
        for env_name in preset.api_key_envs:
            value = os.environ.get(env_name)
            if value:
                resolved_key = value
                break
    if not resolved_key and name == "ollama":
        resolved_key = "ollama"

    return LlmConfig(
        provider=name,
        model=resolved_model,
        base_url=resolved_base,
        api_key=resolved_key,
    )


def format_providers_help() -> str:
    lines = ["OpenAI-compatible providers (use --provider NAME):", ""]
    for preset in list_providers():
        base = preset.base_url or "(OpenAI default)"
        note = f"  # {preset.notes}" if preset.notes else ""
        lines.append(f"  {preset.name:12} model={preset.model}")
        lines.append(f"               base={base}{note}")
    lines.append("")
    lines.append("Env: OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL / CITEREEL_PROVIDER")
    lines.append("Or provider keys: DEEPSEEK_API_KEY, MOONSHOT_API_KEY, GROQ_API_KEY, ...")
    lines.append("Any other host: --base-url URL --model NAME")
    return "\n".join(lines)
