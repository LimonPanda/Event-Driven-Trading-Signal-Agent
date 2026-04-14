"""CLI entrypoint: run the trading signal pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from openai import OpenAI

from src.config import AppConfig
from src.models import Article
from src.pipeline.entity_linker import TickerDictionary
from src.pipeline.orchestrator import PipelineConfig, RunStats, run_pipeline
from src.tools.rss_feeds import fetch_feed_entries, load_feed_config

logger = logging.getLogger("signal_agent")


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _ingest_feeds(cfg: AppConfig) -> list[Article]:
    feed_records = load_feed_config(cfg.feeds_config)
    if not feed_records:
        logger.warning("No enabled feeds in %s", cfg.feeds_config)
        return []
    articles: list[Article] = []
    for rec in feed_records:
        url = rec["url"]
        logger.info("Fetching feed: %s", url)
        try:
            entries = fetch_feed_entries(url, timeout=30.0)
            for e in entries:
                articles.append(
                    Article(
                        title=e.title,
                        link=e.link,
                        summary=e.summary,
                        published=e.published,
                        source_feed=e.source_feed,
                    )
                )
            logger.info("  got %d entries from %s", len(entries), url)
        except Exception as exc:
            logger.error("Feed fetch failed for %s: %s", url, exc)
    return articles


def _print_stats(stats: RunStats) -> None:
    print("\n=== Pipeline Run Summary ===")
    print(f"  Ingested:        {stats.total_ingested}")
    print(f"  Duplicates:      {stats.duplicates}")
    print(f"  No ticker:       {stats.no_ticker}")
    print(f"  LLM errors:      {stats.llm_errors}")
    print(f"  Suppressed:      {stats.suppressed}")
    print(f"  Emitted signals: {stats.emitted}")
    print(f"  Notify failures: {stats.notify_failures}")
    if stats.articles_detail:
        print("\n--- Article Details ---")
        for d in stats.articles_detail:
            print(f"  {d.get('title', '?')[:60]:60s}  →  {d.get('outcome', '?')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Event-Driven Trading Signal Agent — run pipeline"
    )
    parser.add_argument("--env", default=".env", help="Path to .env file")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ingest feeds but skip LLM calls (prints articles found)",
    )
    parser.add_argument(
        "--fixture",
        type=str,
        default=None,
        help="Path to JSON fixture file instead of live feeds",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    cfg = AppConfig.from_env(args.env)

    errors = cfg.validate()
    if errors and not args.dry_run:
        for e in errors:
            logger.error("Config error: %s", e)
        return 1

    ticker_dict = TickerDictionary.from_yaml(cfg.tickers_config)
    logger.info("Ticker universe: %s", sorted(ticker_dict.universe))

    if args.fixture:
        logger.info("Loading fixture: %s", args.fixture)
        with open(args.fixture, encoding="utf-8") as f:
            raw = json.load(f)
        articles = [
            Article(
                title=item.get("title", ""),
                link=item.get("link", ""),
                summary=item.get("summary", ""),
                published=item.get("published"),
                source_feed=item.get("source_feed", "fixture"),
            )
            for item in raw
        ]
    else:
        articles = _ingest_feeds(cfg)

    if not articles:
        logger.warning("No articles to process.")
        return 0

    logger.info("Ingested %d articles total", len(articles))

    if args.dry_run:
        print(f"\n[DRY RUN] {len(articles)} articles ingested:")
        for a in articles:
            t = ticker_dict.resolve(f"{a.title} {a.summary[:200]}")
            print(f"  [{t or '???'}] {a.title[:80]}")
        return 0

    llm_client = OpenAI(
        api_key=cfg.deepseek_api_key,
        base_url=cfg.deepseek_base_url.rstrip("/"),
    )

    pipe_cfg = PipelineConfig(
        model=cfg.llm_model,
        classify_min_confidence=cfg.classify_min_confidence,
        impact_min_confidence=cfg.impact_min_confidence,
        llm_timeout=cfg.llm_timeout,
        telegram_bot_token=cfg.telegram_bot_token,
        telegram_chat_id=cfg.telegram_chat_id,
        notify_enabled=bool(cfg.telegram_bot_token and cfg.telegram_chat_id),
        db_path=cfg.db_path,
    )

    stats = run_pipeline(
        articles,
        llm_client=llm_client,
        ticker_dict=ticker_dict,
        config=pipe_cfg,
    )

    _print_stats(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
