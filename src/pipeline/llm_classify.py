"""LLM event classification step with Draft-Verify-Fix (DVF) cycle."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from src.models import Article, EventType, LLMClassificationResult, ToolError

logger = logging.getLogger(__name__)

EVENT_TYPES_CSV = ", ".join(e.value for e in EventType)

SYSTEM_PROMPT = f"""\
You are a financial news event classifier for Russian MOEX-listed equities.

Given a news article, return a JSON object with exactly two fields:
  "event_type": one of [{EVENT_TYPES_CSV}]
  "confidence": float 0.0-1.0

Rules:
- If the article does not describe any corporate/market event, use "no_event".
- Do NOT add any extra fields or commentary.
- Output ONLY valid JSON.
"""


def _build_user_message(article: Article) -> str:
    parts = [f"Title: {article.title}"]
    if article.summary:
        parts.append(f"Body excerpt: {article.summary[:2000]}")
    if article.source_feed:
        parts.append(f"Source: {article.source_feed}")
    if article.published:
        parts.append(f"Published: {article.published}")
    if article.ticker:
        parts.append(f"Ticker hint: {article.ticker}")
    return "\n".join(parts)


def _parse_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(text)


def classify_event(
    client: OpenAI,
    article: Article,
    *,
    model: str = "deepseek-chat",
    timeout: float = 30.0,
) -> LLMClassificationResult | ToolError:
    """
    DVF cycle:
      Draft  -> call LLM
      Verify -> parse JSON, check event_type in taxonomy, confidence in range
      Fix    -> one strict re-prompt; if still bad, return ToolError
    """
    user_msg = _build_user_message(article)

    for attempt in range(2):
        strict_suffix = (
            "\nIMPORTANT: Return ONLY a raw JSON object, no markdown."
            if attempt == 1
            else ""
        )
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + strict_suffix},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                timeout=timeout,
            )
        except Exception as exc:
            logger.warning("LLM call failed (attempt %d): %s", attempt, exc)
            if attempt == 0:
                continue
            return ToolError(
                code="llm_timeout",
                message=f"LLM request failed after retries: {exc}",
                suggestion="Suppress article and retry in next cycle.",
            )

        raw_text = (resp.choices[0].message.content or "").strip()

        try:
            parsed = _parse_response(raw_text)
        except (json.JSONDecodeError, IndexError) as exc:
            logger.warning("JSON parse failed (attempt %d): %s", attempt, exc)
            if attempt == 0:
                continue
            return ToolError(
                code="schema_invalid",
                message=f"LLM returned unparseable JSON after strict re-prompt: {raw_text[:200]}",
                suggestion="Suppress this article with reason schema_invalid.",
            )

        et_raw = parsed.get("event_type", "")
        conf_raw = parsed.get("confidence", 0)

        try:
            event_type = EventType(et_raw)
        except ValueError:
            if attempt == 0:
                continue
            return ToolError(
                code="schema_invalid",
                message=f"event_type '{et_raw}' not in taxonomy.",
                suggestion="Suppress with schema_invalid.",
            )

        try:
            confidence = float(conf_raw)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("out of range")
        except (ValueError, TypeError):
            if attempt == 0:
                continue
            return ToolError(
                code="schema_invalid",
                message=f"confidence '{conf_raw}' not a valid float 0-1.",
                suggestion="Suppress with schema_invalid.",
            )

        return LLMClassificationResult(
            event_type=event_type,
            confidence=confidence,
            raw_json=parsed,
        )

    return ToolError(
        code="schema_invalid",
        message="Exhausted DVF attempts.",
        suggestion="Suppress article.",
    )
