import pytest

from citereel.generate.factory import default_chat_model
from citereel.generate.providers import resolve_llm_config


def test_default_model_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("CITEREEL_PROVIDER", raising=False)
    assert default_chat_model(base_url=None) == "gpt-4o-mini"


def test_deepseek_from_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("CITEREEL_PROVIDER", raising=False)
    cfg = resolve_llm_config(base_url="https://api.deepseek.com")
    assert cfg.provider == "deepseek"
    assert cfg.model == "deepseek-flash"
    assert cfg.base_url == "https://api.deepseek.com"


def test_provider_preset_sets_base_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    cfg = resolve_llm_config(provider="deepseek", api_key="sk-test")
    assert cfg.provider == "deepseek"
    assert cfg.model == "deepseek-flash"
    assert cfg.base_url == "https://api.deepseek.com"
    assert cfg.api_key == "sk-test"


def test_explicit_model_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "deepseek-v4-pro")
    assert default_chat_model(model="deepseek-flash") == "deepseek-flash"
    assert default_chat_model(base_url="https://api.deepseek.com") == "deepseek-v4-pro"


def test_provider_specific_api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")
    cfg = resolve_llm_config(provider="deepseek")
    assert cfg.api_key == "sk-deepseek"


def test_ollama_allows_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = resolve_llm_config(provider="ollama")
    assert cfg.base_url and "11434" in cfg.base_url
    assert cfg.api_key == "ollama"


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        resolve_llm_config(provider="nope")
