"""OpenAI-compatible client pointed at DeepSeek (semantic agents call this)."""

from __future__ import annotations

import os

from openai import OpenAI


def get_deepseek_chat_client() -> OpenAI:
    """
    Build an OpenAI SDK client for DeepSeek.

    Environment:
      DEEPSEEK_API_KEY — required
      DEEPSEEK_BASE_URL — optional, default https://api.deepseek.com
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    return OpenAI(api_key=api_key, base_url=base_url)
