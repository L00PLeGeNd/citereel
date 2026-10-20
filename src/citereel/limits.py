from __future__ import annotations

import os


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def max_files() -> int:
    return env_int("CITEREEL_MAX_FILES", 500)


def max_chunk_chars() -> int:
    return env_int("CITEREEL_MAX_CHUNK_CHARS", 8000)


def max_total_chars() -> int:
    return env_int("CITEREEL_MAX_TOTAL_CHARS", 2_000_000)


def llm_timeout_s() -> float:
    return env_float("CITEREEL_LLM_TIMEOUT", 60.0)


def llm_retries() -> int:
    return max(0, env_int("CITEREEL_LLM_RETRIES", 2))
