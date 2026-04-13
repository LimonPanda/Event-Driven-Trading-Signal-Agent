"""Offline parse of sample RSS (no network)."""

from pathlib import Path

from src.tools.rss_feeds import parse_rss_bytes


def test_parse_minimal_fixture() -> None:
    xml_path = Path(__file__).parent / "fixtures" / "minimal_feed.xml"
    entries = parse_rss_bytes(xml_path.read_bytes(), "https://example.com/news/rss.xml")
    assert len(entries) == 1
    assert "Сбербанк" in entries[0].title
    assert entries[0].link.endswith("sber-dividends")
