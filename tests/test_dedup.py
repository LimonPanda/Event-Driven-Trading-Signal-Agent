"""Tests for the deduplication module."""

from src.models import Article, ArticleStatus
from src.pipeline.dedup import deduplicate


def _make_articles() -> list[Article]:
    return [
        Article(title="Sberbank dividends", link="https://a.com/news/1", published="2024-04-01"),
        Article(title="Sberbank dividends", link="https://b.com/news/1", published="2024-04-01"),
        Article(title="Gazprom earnings", link="https://a.com/news/2", published="2024-04-02"),
        Article(title="Sberbank dividends", link="https://a.com/news/1", published="2024-04-01"),
    ]


def test_dedup_removes_url_dupes():
    arts = _make_articles()
    canonical = deduplicate(arts)
    # arts[0] and arts[3] share the same URL — only one should survive
    urls = [a.link for a in canonical]
    assert urls.count("https://a.com/news/1") == 1


def test_dedup_removes_title_date_dupes():
    arts = _make_articles()
    canonical = deduplicate(arts)
    # arts[0] and arts[1] share title+date — only one should survive
    assert len(canonical) == 2


def test_duplicate_articles_marked():
    arts = _make_articles()
    deduplicate(arts)
    dups = [a for a in arts if a.status == ArticleStatus.DUPLICATE]
    assert len(dups) == 2


def test_no_duplicates_all_unique():
    arts = [
        Article(title="A", link="https://a.com/1", published="2024-01-01"),
        Article(title="B", link="https://b.com/2", published="2024-01-02"),
    ]
    canonical = deduplicate(arts)
    assert len(canonical) == 2
