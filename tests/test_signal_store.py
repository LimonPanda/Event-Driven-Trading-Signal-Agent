"""Tests for SQLite signal store."""

from src.models import Article, EventType, ImpactDirection, Signal, SuppressionReason
from src.pipeline.signal_store import SignalStore


def test_save_and_retrieve_signal(tmp_path):
    db = tmp_path / "test.db"
    store = SignalStore(db_path=db)
    s = Signal(
        signal_id="sig001",
        article_id="art001",
        ticker="SBER",
        event_type=EventType.EARNINGS,
        impact=ImpactDirection.POSITIVE,
        confidence=0.85,
    )
    store.save_signal(s)
    loaded = store.get_signal("sig001")
    assert loaded is not None
    assert loaded["ticker"] == "SBER"
    assert loaded["event_type"] == "earnings_release"
    store.close()


def test_recent_signals(tmp_path):
    db = tmp_path / "test.db"
    store = SignalStore(db_path=db)
    for i in range(5):
        store.save_signal(Signal(
            signal_id=f"sig{i:03d}",
            article_id=f"art{i:03d}",
            ticker="SBER",
            event_type=EventType.EARNINGS,
            impact=ImpactDirection.POSITIVE,
            confidence=0.8,
        ))
    recent = store.recent_signals(limit=3)
    assert len(recent) == 3
    store.close()


def test_save_suppression(tmp_path):
    db = tmp_path / "test.db"
    store = SignalStore(db_path=db)
    art = Article(article_id="art999", title="Test")
    store.save_suppression(art, SuppressionReason.LOW_CONFIDENCE, "conf=0.1")
    store.close()


def test_missing_signal_returns_none(tmp_path):
    db = tmp_path / "test.db"
    store = SignalStore(db_path=db)
    assert store.get_signal("nonexistent") is None
    store.close()
