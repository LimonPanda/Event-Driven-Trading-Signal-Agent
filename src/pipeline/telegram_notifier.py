"""Outbound-only Telegram notifier: send read-only signal alerts to allowlisted chat_id."""

from __future__ import annotations

import logging

import httpx

from src.models import Signal, ToolError

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


def _format_message(signal: Signal) -> str:
    direction_emoji = {
        "positive": "\u2191",   # ↑
        "negative": "\u2193",   # ↓
        "neutral": "\u2194",    # ↔
        "uncertain": "?",
    }
    arrow = direction_emoji.get(signal.impact.value, "?")
    return (
        f"{arrow} {signal.ticker} — {signal.event_type.value.replace('_', ' ').title()}\n"
        f"Impact: {signal.impact.value} (confidence {signal.confidence:.0%})\n"
        f"Source: {signal.source_url or 'N/A'}\n"
        f"Published: {signal.published or 'N/A'}"
    )


def send_signal(
    signal: Signal,
    *,
    bot_token: str,
    chat_id: str,
    timeout: float = 10.0,
) -> bool | ToolError:
    """
    Send a single signal alert via Telegram Bot API.

    Returns True on success, or ToolError on failure.
    """
    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    text = _format_message(signal)

    for attempt in range(2):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                )
            if resp.status_code == 200:
                return True
            logger.warning(
                "Telegram API returned %d (attempt %d): %s",
                resp.status_code, attempt, resp.text[:300],
            )
        except Exception as exc:
            logger.warning("Telegram send failed (attempt %d): %s", attempt, exc)

    return ToolError(
        code="telegram_send_failed",
        message="Failed to deliver Telegram alert after retries.",
        suggestion="Signal is persisted; queue for retry in next cycle.",
    )
