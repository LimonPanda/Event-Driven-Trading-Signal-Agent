"""LLM impact estimation step with Draft-Verify-Fix (DVF) cycle."""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from src.models import Article, EventType, ImpactDirection, LLMImpactResult, ToolError

logger = logging.getLogger(__name__)

IMPACTS_CSV = ", ".join(d.value for d in ImpactDirection)

SYSTEM_PROMPT = f"""\
You are a financial market impact analyst for Russian MOEX-listed equities.

Given a news article and its detected event type, estimate the short-term
directional impact on the company's stock price.

Return a JSON object with exactly two fields:
  "impact": one of [{IMPACTS_CSV}]
  "confidence": float 0.0-1.0

Rules:
- "positive" = likely price increase.
- "negative" = likely price decrease.
- "neutral" = minimal or no expected impact.
- "uncertain" = insufficient information to judge.
- Do NOT add any extra fields or commentary.
- Output ONLY valid JSON.
"""


def _build_user_message(article: Article, event_type: EventType) -> str:
    parts = [
        f"Title: {article.title}",
        f"Event type: {event_type.value}",
    ]
    if article.summary:
        parts.append(f"Body excerpt: {article.summary[:2000]}")
    if article.ticker:
        parts.append(f"Ticker: {article.ticker}")
    if article.published:
        parts.append(f"Published: {article.published}")
    return "\n".join(parts)


def _parse_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(text)


def estimate_impact(
    client: OpenAI,
    article: Article,
    event_type: EventType,
    *,
    model: str = "deepseek-chat",
    timeout: float = 30.0,
) -> LLMImpactResult | ToolError:
    """
    DVF cycle:
      Draft  -> call LLM with article + event type
      Verify -> parse JSON, check impact in enum, confidence in range
      Fix    -> one strict re-prompt; if still bad, return ToolError
    """
    user_msg = _build_user_message(article, event_type)

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
            logger.warning("LLM impact call failed (attempt %d): %s", attempt, exc)
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
        except (json.JSONDecodeError, IndexError):
            if attempt == 0:
                continue
            return ToolError(
                code="schema_invalid",
                message=f"Unparseable JSON from impact LLM: {raw_text[:200]}",
                suggestion="Suppress with schema_invalid.",
            )

        impact_raw = parsed.get("impact", "")
        conf_raw = parsed.get("confidence", 0)

        try:
            impact = ImpactDirection(impact_raw)
        except ValueError:
            if attempt == 0:
                continue
            return ToolError(
                code="schema_invalid",
                message=f"impact '{impact_raw}' not in taxonomy.",
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

        return LLMImpactResult(
            impact=impact,
            confidence=confidence,
            raw_json=parsed,
        )

    return ToolError(
        code="schema_invalid",
        message="Exhausted DVF attempts for impact estimation.",
        suggestion="Suppress article.",
    )
