"""Deterministic pipeline orchestrator: ingest -> dedup -> link -> classify -> impact -> validate -> store -> notify."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from src.models import (
    Article,
    ArticleStatus,
    LLMClassificationResult,
    LLMImpactResult,
    Signal,
    SuppressionReason,
    ToolError,
)
from src.pipeline.dedup import deduplicate
from src.pipeline.entity_linker import TickerDictionary
from src.pipeline.llm_classify import classify_event
from src.pipeline.llm_impact import estimate_impact
from src.pipeline.sanitizer import sanitize_text
from src.pipeline.signal_store import SignalStore
from src.pipeline.telegram_notifier import send_signal
from src.pipeline.validator import full_validation

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    model: str = "deepseek-chat"
    classify_min_confidence: float = 0.4
    impact_min_confidence: float = 0.3
    llm_timeout: float = 30.0
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    notify_enabled: bool = True
    db_path: str = "data/signals.db"


@dataclass
class RunStats:
    total_ingested: int = 0
    duplicates: int = 0
    no_ticker: int = 0
    llm_errors: int = 0
    suppressed: int = 0
    emitted: int = 0
    notify_failures: int = 0
    articles_detail: list[dict[str, Any]] = field(default_factory=list)


def run_pipeline(
    articles: list[Article],
    *,
    llm_client: OpenAI,
    ticker_dict: TickerDictionary,
    config: PipelineConfig,
) -> RunStats:
    """Execute the full deterministic pipeline on a batch of articles."""
    stats = RunStats(total_ingested=len(articles))
    store = SignalStore(db_path=config.db_path)

    try:
        canonical = deduplicate(articles)
        stats.duplicates = stats.total_ingested - len(canonical)

        for art in canonical:
            detail: dict[str, Any] = {"article_id": art.article_id, "title": art.title}
            art.status = ArticleStatus.PROCESSING

            # --- Sanitize ---
            cleaned_title, title_modified = sanitize_text(art.title)
            cleaned_summary, summary_modified = sanitize_text(art.summary)
            if title_modified or summary_modified:
                logger.info("Sanitized injection patterns from article %s", art.article_id)
            art.title = cleaned_title
            art.summary = cleaned_summary

            # --- Entity linking ---
            combined_text = f"{art.title} {art.summary[:500]}"
            art.ticker = ticker_dict.resolve(combined_text)
            if not art.ticker:
                art.status = ArticleStatus.SUPPRESSED
                art.suppression_reason = SuppressionReason.NO_TICKER
                store.save_suppression(art, SuppressionReason.NO_TICKER)
                stats.no_ticker += 1
                detail["outcome"] = "suppressed:no_ticker"
                stats.articles_detail.append(detail)
                continue
            detail["ticker"] = art.ticker

            # --- LLM event classification (DVF) ---
            cls_result = classify_event(
                llm_client, art, model=config.model, timeout=config.llm_timeout
            )
            if isinstance(cls_result, ToolError):
                art.status = ArticleStatus.FAILED
                art.suppression_reason = SuppressionReason(cls_result.code)
                store.save_suppression(art, art.suppression_reason, cls_result.message)
                stats.llm_errors += 1
                detail["outcome"] = f"failed:{cls_result.code}"
                stats.articles_detail.append(detail)
                continue
            detail["event_type"] = cls_result.event_type.value
            detail["classify_confidence"] = cls_result.confidence

            # --- LLM impact estimation (DVF) ---
            imp_result = estimate_impact(
                llm_client, art, cls_result.event_type,
                model=config.model, timeout=config.llm_timeout,
            )
            if isinstance(imp_result, ToolError):
                art.status = ArticleStatus.FAILED
                art.suppression_reason = SuppressionReason(imp_result.code)
                store.save_suppression(art, art.suppression_reason, imp_result.message)
                stats.llm_errors += 1
                detail["outcome"] = f"failed:{imp_result.code}"
                stats.articles_detail.append(detail)
                continue
            detail["impact"] = imp_result.impact.value
            detail["impact_confidence"] = imp_result.confidence

            # --- Validation gate ---
            reason = full_validation(
                art.ticker,
                ticker_dict.universe,
                cls_result,
                imp_result,
                classify_min_conf=config.classify_min_confidence,
                impact_min_conf=config.impact_min_confidence,
            )
            if reason is not None:
                art.status = ArticleStatus.SUPPRESSED
                art.suppression_reason = reason
                store.save_suppression(art, reason)
                stats.suppressed += 1
                detail["outcome"] = f"suppressed:{reason.value}"
                stats.articles_detail.append(detail)
                continue

            # --- Build and persist signal ---
            combined_confidence = min(cls_result.confidence, imp_result.confidence)
            signal = Signal(
                article_id=art.article_id,
                ticker=art.ticker,
                event_type=cls_result.event_type,
                impact=imp_result.impact,
                confidence=combined_confidence,
                source_url=art.link,
                source_name=art.source_feed,
                published=art.published,
                model_name=config.model,
            )
            store.save_signal(signal)
            art.status = ArticleStatus.EMITTED
            stats.emitted += 1
            detail["signal_id"] = signal.signal_id
            detail["outcome"] = "emitted"

            # --- Telegram notification ---
            if (
                config.notify_enabled
                and config.telegram_bot_token
                and config.telegram_chat_id
            ):
                tg_result = send_signal(
                    signal,
                    bot_token=config.telegram_bot_token,
                    chat_id=config.telegram_chat_id,
                )
                if isinstance(tg_result, ToolError):
                    stats.notify_failures += 1
                    detail["notify"] = "failed"
                    logger.warning(
                        "Telegram notify failed for signal %s: %s",
                        signal.signal_id, tg_result.message,
                    )
                else:
                    detail["notify"] = "sent"

            stats.articles_detail.append(detail)
    finally:
        store.close()

    return stats
