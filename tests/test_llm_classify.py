"""Tests for LLM event classification (mocked, no real API calls)."""

from unittest.mock import MagicMock, patch

from src.models import Article, EventType, LLMClassificationResult, ToolError
from src.pipeline.llm_classify import classify_event


def _mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_valid_classification():
    client = MagicMock()
    client.chat.completions.create.return_value = _mock_response(
        '{"event_type": "earnings_release", "confidence": 0.85}'
    )
    art = Article(title="Сбербанк отчитался за Q1", ticker="SBER")
    result = classify_event(client, art)
    assert isinstance(result, LLMClassificationResult)
    assert result.event_type == EventType.EARNINGS
    assert result.confidence == 0.85


def test_markdown_wrapped_json():
    client = MagicMock()
    client.chat.completions.create.return_value = _mock_response(
        '```json\n{"event_type": "dividend_announcement", "confidence": 0.9}\n```'
    )
    art = Article(title="Дивиденды Газпрома", ticker="GAZP")
    result = classify_event(client, art)
    assert isinstance(result, LLMClassificationResult)
    assert result.event_type == EventType.DIVIDEND


def test_invalid_event_type_retries_then_fails():
    client = MagicMock()
    client.chat.completions.create.return_value = _mock_response(
        '{"event_type": "totally_fake", "confidence": 0.5}'
    )
    art = Article(title="Test")
    result = classify_event(client, art)
    assert isinstance(result, ToolError)
    assert result.code == "schema_invalid"


def test_llm_exception_retries():
    client = MagicMock()
    client.chat.completions.create.side_effect = TimeoutError("timeout")
    art = Article(title="Test")
    result = classify_event(client, art)
    assert isinstance(result, ToolError)
    assert result.code == "llm_timeout"
    assert client.chat.completions.create.call_count == 2
