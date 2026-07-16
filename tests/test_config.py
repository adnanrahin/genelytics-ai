from __future__ import annotations

from pathlib import Path

import pytest

from genelytics.config.loader import list_environments, load_settings, settings_from_dict
from genelytics.config.settings import Settings
from genelytics.llm.factory import create_chat_model


def _write_env(env_dir: Path, name: str, body: str) -> None:
    env_dir.mkdir(parents=True, exist_ok=True)
    (env_dir / f"{name}.yaml").write_text(body, encoding="utf-8")


def test_settings_require_yaml_values():
    """Schema has no provider hard-codes — constructing without llm fails."""
    with pytest.raises(Exception):
        Settings(env="local")  # type: ignore[call-arg]


def test_load_local_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_root = tmp_path / "config"
    env_dir = config_root / "environments"
    _write_env(
        env_dir,
        "local",
        "llm:\n  provider: ollama\n  model: testdb\n  base_url: http://127.0.0.1:11434\n"
        "  temperature: 0\n"
        "database:\n  uri: null\n"
        "analytics:\n  max_rows: 42\n  query_timeout_seconds: 30\n  read_only: true\n"
        "few_shot:\n  path: x.json\n  enabled: false\n  max_examples: 1\n",
    )
    monkeypatch.delenv("GENELYTICS_LLM__MODEL", raising=False)
    settings = load_settings(env="local", config_dir=config_root)
    assert settings.llm.model == "testdb"
    assert settings.llm.provider == "ollama"
    assert settings.analytics.max_rows == 42
    assert settings.env == "local"


def test_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    config_root = tmp_path / "config"
    env_dir = config_root / "environments"
    _write_env(
        env_dir,
        "local",
        "llm:\n  provider: ollama\n  model: mistral\n  base_url: http://127.0.0.1:11434\n"
        "  temperature: 0\n"
        "database:\n  uri: null\n"
        "analytics:\n  max_rows: 100\n  query_timeout_seconds: 30\n  read_only: true\n"
        "few_shot:\n  path: x.json\n  enabled: true\n  max_examples: 5\n",
    )
    monkeypatch.setenv("GENELYTICS_LLM__MODEL", "llama3")
    monkeypatch.setenv("GENELYTICS_LLM__PROVIDER", "openai")
    settings = load_settings(env="local", config_dir=config_root)
    assert settings.llm.model == "llama3"
    assert settings.llm.provider == "openai"


def test_missing_env_lists_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_root = tmp_path / "config"
    env_dir = config_root / "environments"
    _write_env(
        env_dir,
        "staging",
        "llm:\n  provider: ollama\n  model: m\n  base_url: http://x\n  temperature: 0\n"
        "database:\n  uri: null\n"
        "analytics:\n  max_rows: 1\n  query_timeout_seconds: 1\n  read_only: true\n"
        "few_shot:\n  path: x.json\n  enabled: false\n  max_examples: 1\n",
    )
    monkeypatch.delenv("GENELYTICS_ENV", raising=False)
    with pytest.raises(ValueError, match="GENELYTICS_ENV"):
        load_settings(config_dir=config_root)
    assert list_environments(config_root) == ["staging"]


def test_unknown_env_file(tmp_path: Path):
    config_root = tmp_path / "config"
    (config_root / "environments").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="Environment config not found"):
        load_settings(env="nope", config_dir=config_root)


def test_factory_rejects_unknown_provider():
    settings = settings_from_dict(
        {
            "env": "t",
            "llm": {
                "provider": "not-a-vendor",
                "model": "x",
                "temperature": 0,
            },
            "database": {"uri": None},
            "analytics": {
                "max_rows": 10,
                "query_timeout_seconds": 5,
                "read_only": True,
            },
            "few_shot": {"path": "x.json", "enabled": False, "max_examples": 1},
        }
    )
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_chat_model(settings.llm)


def test_factory_requires_bedrock_region():
    settings = settings_from_dict(
        {
            "env": "t",
            "llm": {
                "provider": "bedrock",
                "model": "anthropic.claude-3-haiku-20240307-v1:0",
                "temperature": 0,
            },
            "database": {"uri": None},
            "analytics": {
                "max_rows": 10,
                "query_timeout_seconds": 5,
                "read_only": True,
            },
            "few_shot": {"path": "x.json", "enabled": False, "max_examples": 1},
        }
    )
    with pytest.raises(ValueError, match="region"):
        create_chat_model(settings.llm)
