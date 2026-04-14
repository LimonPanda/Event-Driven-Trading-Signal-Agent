"""Schema + policy validator: confidence gate, ticker universe check, guardrails."""

from __future__ import annotations

from src.models import (
    EventType,
    ImpactDirection,
    LLMClassificationResult,
    LLMImpactResult,
    SuppressionReason,
)


def validate_classification(
    result: LLMClassificationResult,
    *,
    min_confidence: float = 0.4,
) -> SuppressionReason | None:
    """Return a SuppressionReason if the classification should be suppressed."""
    if result.event_type == EventType.NONE:
        return SuppressionReason.NO_EVENT
    if result.confidence < min_confidence:
        return SuppressionReason.LOW_CONFIDENCE
    return None


def validate_impact(
    result: LLMImpactResult,
    *,
    min_confidence: float = 0.3,
) -> SuppressionReason | None:
    if result.confidence < min_confidence:
        return SuppressionReason.LOW_CONFIDENCE
    return None


def validate_ticker(ticker: str | None, universe: set[str]) -> SuppressionReason | None:
    if not ticker:
        return SuppressionReason.NO_TICKER
    if ticker.upper() not in universe:
        return SuppressionReason.TICKER_AMBIGUOUS
    return None


def full_validation(
    ticker: str | None,
    universe: set[str],
    classification: LLMClassificationResult,
    impact: LLMImpactResult,
    *,
    classify_min_conf: float = 0.4,
    impact_min_conf: float = 0.3,
) -> SuppressionReason | None:
    """Run all policy gates. Return first failing reason, or None if all pass."""
    reason = validate_ticker(ticker, universe)
    if reason:
        return reason
    reason = validate_classification(classification, min_confidence=classify_min_conf)
    if reason:
        return reason
    reason = validate_impact(impact, min_confidence=impact_min_conf)
    if reason:
        return reason
    return None
