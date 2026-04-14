"""End-to-end demo test: 5 Sberbank articles through the full pipeline (mocked LLM)."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from src.models import Article
from src.pipeline.entity_linker import TickerDictionary
from src.pipeline.orchestrator import PipelineConfig, run_pipeline

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sberbank_demo.json"


def _mock_llm_client():
    client = MagicMock()
    call_count = {"n": 0}

    responses = [
        ('{"event_type": "dividend_announcement", "confidence": 0.92}',
         '{"impact": "positive", "confidence": 0.88}'),
        ('{"event_type": "earnings_release", "confidence": 0.87}',
         '{"impact": "positive", "confidence": 0.75}'),
        ('{"event_type": "other", "confidence": 0.55}',
         '{"impact": "neutral", "confidence": 0.60}'),
        ('{"event_type": "management_change", "confidence": 0.45}',
         '{"impact": "negative", "confidence": 0.50}'),
    ]

    def _create(**kwargs):
        messages = kwargs.get("messages", [])
        system_text = messages[0]["content"] if messages else ""
        idx = min(call_count["n"] // 2, len(responses) - 1)

        msg = MagicMock()
        if "event classifier" in system_text.lower():
            msg.content = responses[idx][0]
        else:
            msg.content = responses[idx][1]
            call_count["n"] += 2
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = _create
    return client


def test_sberbank_demo(tmp_path):
    """
    Demo scenario from README:
    5 articles about Sberbank -> dedup -> entity linking -> classify -> impact -> signal
    """
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    articles = [
        Article(
            title=item["title"],
            link=item["link"],
            summary=item.get("summary", ""),
            published=item.get("published"),
            source_feed=item.get("source_feed", "fixture"),
        )
        for item in raw
    ]
    assert len(articles) == 5

    td = TickerDictionary([
        {"ticker": "SBER", "company": "Sberbank", "aliases": ["Сбербанк", "Сбер", "Sberbank"]},
        {"ticker": "GAZP", "company": "Gazprom", "aliases": ["Газпром"]},
    ])

    cfg = PipelineConfig(
        db_path=str(tmp_path / "demo.db"),
        notify_enabled=False,
    )

    stats = run_pipeline(
        articles,
        llm_client=_mock_llm_client(),
        ticker_dict=td,
        config=cfg,
    )

    assert stats.total_ingested == 5
    assert stats.duplicates >= 1, "Article 5 is a title+date dupe of article 1"
    assert stats.emitted >= 1, "At least one Sberbank signal should be emitted"
    assert stats.no_ticker == 0, "All articles mention Sberbank"

    for detail in stats.articles_detail:
        assert detail.get("ticker") == "SBER"
        assert detail.get("outcome") is not None

    print("\n=== E2E Demo Results ===")
    print(f"  Total: {stats.total_ingested}, Dupes: {stats.duplicates}, "
          f"Emitted: {stats.emitted}, Suppressed: {stats.suppressed}")
    for d in stats.articles_detail:
        print(f"  {d.get('title', '?')[:50]:50s} → {d.get('outcome')}")
