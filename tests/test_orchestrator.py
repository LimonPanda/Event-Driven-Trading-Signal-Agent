"""Integration test for the orchestrator pipeline (mocked LLM, real dedup/validator/store)."""

from unittest.mock import MagicMock

from src.models import Article
from src.pipeline.entity_linker import TickerDictionary
from src.pipeline.orchestrator import PipelineConfig, run_pipeline


def _mock_llm_client():
    """Mock that returns valid classification then valid impact for every call."""
    client = MagicMock()

    def _create(**kwargs):
        messages = kwargs.get("messages", [])
        system_text = messages[0]["content"] if messages else ""

        msg = MagicMock()
        if "event classifier" in system_text.lower():
            msg.content = '{"event_type": "earnings_release", "confidence": 0.85}'
        else:
            msg.content = '{"impact": "positive", "confidence": 0.75}'
        choice = MagicMock()
        choice.message = msg
        resp = MagicMock()
        resp.choices = [choice]
        return resp

    client.chat.completions.create.side_effect = _create
    return client


def test_pipeline_emits_signal(tmp_path):
    articles = [
        Article(title="Сбербанк отчитался за первый квартал", link="https://a.com/1"),
        Article(title="Сбербанк отчитался за первый квартал", link="https://b.com/1"),
    ]
    td = TickerDictionary([
        {"ticker": "SBER", "company": "Sberbank", "aliases": ["Сбербанк"]},
    ])
    cfg = PipelineConfig(
        db_path=str(tmp_path / "test.db"),
        notify_enabled=False,
    )
    stats = run_pipeline(articles, llm_client=_mock_llm_client(), ticker_dict=td, config=cfg)

    assert stats.total_ingested == 2
    assert stats.duplicates >= 0
    assert stats.emitted >= 1


def test_pipeline_suppresses_no_ticker(tmp_path):
    articles = [
        Article(title="Apple releases new iPhone", link="https://a.com/apple"),
    ]
    td = TickerDictionary([
        {"ticker": "SBER", "company": "Sberbank", "aliases": ["Сбербанк"]},
    ])
    cfg = PipelineConfig(
        db_path=str(tmp_path / "test.db"),
        notify_enabled=False,
    )
    stats = run_pipeline(articles, llm_client=_mock_llm_client(), ticker_dict=td, config=cfg)

    assert stats.no_ticker == 1
    assert stats.emitted == 0
