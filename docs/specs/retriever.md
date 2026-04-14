# Spec: Retriever

## Purpose

Ingest market-relevant text context for MOEX event detection from public RSS/Atom sources.

## Sources

- Allowlisted URLs in `config/feeds.yaml`.
- Public feeds only; no paywalled scraping.

## Interfaces

- `load_feed_config(path) -> list[FeedRecord]`
- `fetch_feed_entries(feed_url) -> list[RssEntry]`
- `parse_rss_bytes(xml_bytes, source_feed_url) -> list[RssEntry]`

`RssEntry` contract:
- `title: str`
- `link: str`
- `summary: str`
- `published: str | None`
- `source_feed: str`

## Retrieval logic

1. Pull enabled feeds.
2. Parse entries to normalized structure.
3. Build canonical article key (`link` primary, title/time hash secondary).
4. Send canonical articles to dedup + pipeline queue.

## Constraints

- Per-feed timeout: 30s.
- Respect feed terms, rate limits, and polite user agent.
- Incomplete coverage is expected and documented.

## Failure handling

- Parse failure: log and skip entry/feed.
- Feed timeout: retry with backoff once per cycle.
- Empty feed: no hard failure; emit health warning metric.

## Acceptance checks

- At least one fixture-based parser test passes offline.
- Duplicate URLs map to one canonical article.
- Ingestion logs include source, timestamp, article ID/link.
