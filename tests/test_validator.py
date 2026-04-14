"""Tests for schema + policy validator."""

from src.models import (
    EventType,
    ImpactDirection,
    LLMClassificationResult,
    LLMImpactResult,
    SuppressionReason,
)
from src.pipeline.validator import full_validation, validate_classification, validate_ticker


def test_valid_classification_passes():
    r = LLMClassificationResult(event_type=EventType.EARNINGS, confidence=0.8)
    assert validate_classification(r) is None


def test_no_event_suppressed():
    r = LLMClassificationResult(event_type=EventType.NONE, confidence=0.9)
    assert validate_classification(r) == SuppressionReason.NO_EVENT


def test_low_confidence_suppressed():
    r = LLMClassificationResult(event_type=EventType.EARNINGS, confidence=0.2)
    assert validate_classification(r) == SuppressionReason.LOW_CONFIDENCE


def test_ticker_in_universe():
    assert validate_ticker("SBER", {"SBER", "GAZP"}) is None


def test_ticker_missing():
    assert validate_ticker(None, {"SBER"}) == SuppressionReason.NO_TICKER


def test_ticker_not_in_universe():
    assert validate_ticker("AAPL", {"SBER", "GAZP"}) == SuppressionReason.TICKER_AMBIGUOUS


def test_full_validation_pass():
    cls = LLMClassificationResult(event_type=EventType.EARNINGS, confidence=0.8)
    imp = LLMImpactResult(impact=ImpactDirection.POSITIVE, confidence=0.7)
    assert full_validation("SBER", {"SBER"}, cls, imp) is None


def test_full_validation_fails_on_ticker():
    cls = LLMClassificationResult(event_type=EventType.EARNINGS, confidence=0.8)
    imp = LLMImpactResult(impact=ImpactDirection.POSITIVE, confidence=0.7)
    assert full_validation(None, {"SBER"}, cls, imp) == SuppressionReason.NO_TICKER
