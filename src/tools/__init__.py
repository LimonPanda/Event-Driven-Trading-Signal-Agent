"""Deterministic helpers: RSS ingestion, MOEX ISS, DeepSeek-compatible LLM client."""

from .deepseek_client import get_deepseek_chat_client
from .moex_iss import fetch_share_daily_bars
from .rss_feeds import RssEntry, load_feed_config, parse_rss_bytes

__all__ = [
    "RssEntry",
    "fetch_share_daily_bars",
    "get_deepseek_chat_client",
    "load_feed_config",
    "parse_rss_bytes",
]
