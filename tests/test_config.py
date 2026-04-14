"""Tests for config loader."""

import os

from src.config import AppConfig


def test_from_env_with_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=test-key-123\n"
        "TELEGRAM_BOT_TOKEN=bot123\n"
        "TELEGRAM_CHAT_ID=chat456\n"
    )
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    cfg = AppConfig.from_env(str(env_file))
    assert cfg.deepseek_api_key == "test-key-123"
    assert cfg.telegram_bot_token == "bot123"
    assert cfg.telegram_chat_id == "chat456"
    assert cfg.llm_model == "deepseek-chat"


def test_validate_missing_key():
    cfg = AppConfig(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        telegram_bot_token="",
        telegram_chat_id="",
        llm_model="deepseek-chat",
        classify_min_confidence=0.4,
        impact_min_confidence=0.3,
        llm_timeout=30.0,
        feeds_config="nonexistent.yaml",
        tickers_config="nonexistent.yaml",
        db_path="data/signals.db",
    )
    errors = cfg.validate()
    assert any("DEEPSEEK_API_KEY" in e for e in errors)
    assert any("Feeds config" in e for e in errors)
