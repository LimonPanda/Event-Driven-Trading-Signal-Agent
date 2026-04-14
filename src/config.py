"""Centralized config loader: reads .env and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader — no third-party dependency."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = val


@dataclass
class AppConfig:
    deepseek_api_key: str
    deepseek_base_url: str
    telegram_bot_token: str
    telegram_chat_id: str
    llm_model: str
    classify_min_confidence: float
    impact_min_confidence: float
    llm_timeout: float
    feeds_config: str
    tickers_config: str
    db_path: str

    @classmethod
    def from_env(cls, dotenv_path: str = ".env") -> AppConfig:
        _load_dotenv(dotenv_path)
        return cls(
            deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            deepseek_base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            llm_model=os.environ.get("LLM_MODEL", "deepseek-chat"),
            classify_min_confidence=float(os.environ.get("CLASSIFY_MIN_CONFIDENCE", "0.4")),
            impact_min_confidence=float(os.environ.get("IMPACT_MIN_CONFIDENCE", "0.3")),
            llm_timeout=float(os.environ.get("LLM_TIMEOUT", "30.0")),
            feeds_config=os.environ.get("FEEDS_CONFIG", "config/feeds.yaml"),
            tickers_config=os.environ.get("TICKERS_CONFIG", "config/tickers.yaml"),
            db_path=os.environ.get("DB_PATH", "data/signals.db"),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is not set")
        if not Path(self.feeds_config).exists():
            errors.append(f"Feeds config not found: {self.feeds_config}")
        if not Path(self.tickers_config).exists():
            errors.append(f"Tickers config not found: {self.tickers_config}")
        return errors
