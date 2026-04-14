"""Deduplication: collapse syndicated duplicates by URL and title+date hash."""

from __future__ import annotations

import hashlib
from src.models import Article, ArticleStatus, SuppressionReason


def _canonical_url(url: str) -> str:
    return url.strip().rstrip("/").lower()


def _title_date_hash(title: str, published: str | None) -> str:
    key = (title.strip().lower() + "|" + (published or "")).encode()
    return hashlib.sha256(key).hexdigest()[:16]


def deduplicate(articles: list[Article]) -> list[Article]:
    """Mark duplicates in-place and return only canonical (non-duplicate) articles."""
    seen_urls: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}
    canonical: list[Article] = []

    for art in articles:
        curl = _canonical_url(art.link)
        thash = _title_date_hash(art.title, art.published)
        art.canonical_key = curl or thash

        if curl and curl in seen_urls:
            art.status = ArticleStatus.DUPLICATE
            art.suppression_reason = SuppressionReason.DUPLICATE
            continue

        if thash in seen_hashes:
            art.status = ArticleStatus.DUPLICATE
            art.suppression_reason = SuppressionReason.DUPLICATE
            continue

        if curl:
            seen_urls[curl] = art.article_id
        seen_hashes[thash] = art.article_id
        canonical.append(art)

    return canonical
