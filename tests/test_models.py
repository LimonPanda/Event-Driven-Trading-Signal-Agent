"""Tests for shared data models."""

from src.models import (
    Article,
    ArticleStatus,
    EventType,
    ImpactDirection,
    Signal,
    SuppressionReason,
    ToolError,
)


def test_article_defaults():
    a = Article(title="Test", link="https://example.com")
    assert a.status == ArticleStatus.INGESTED
    assert a.ticker is None
    assert len(a.article_id) == 12


def test_signal_defaults():
    s = Signal(article_id="abc", ticker="SBER", event_type=EventType.EARNINGS)
    assert s.impact == ImpactDirection.UNCERTAIN
    assert len(s.signal_id) == 12


def test_tool_error_frozen():
    te = ToolError(code="test", message="msg", suggestion="fix it")
    assert te.code == "test"
    try:
        te.code = "other"  # type: ignore[misc]
        assert False, "Should be frozen"
    except AttributeError:
        pass


def test_enum_values():
    assert EventType.EARNINGS.value == "earnings_release"
    assert ImpactDirection.POSITIVE.value == "positive"
    assert SuppressionReason.DUPLICATE.value == "duplicate"
