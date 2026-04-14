"""Tests for LLM impact estimation (mocked, no real API calls)."""

from unittest.mock import MagicMock

from src.models import Article, EventType, ImpactDirection, LLMImpactResult, ToolError
from src.pipeline.llm_impact import estimate_impact


def _mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_valid_impact():
    client = MagicMock()
    client.chat.completions.create.return_value = _mock_response(
        '{"impact": "positive", "confidence": 0.75}'
    )
    art = Article(title="Сбербанк рекордные дивиденды", ticker="SBER")
    result = estimate_impact(client, art, EventType.DIVIDEND)
    assert isinstance(result, LLMImpactResult)
    assert result.impact == ImpactDirection.POSITIVE
    assert result.confidence == 0.75


def test_invalid_impact_direction():
    client = MagicMock()
    client.chat.completions.create.return_value = _mock_response(
        '{"impact": "maybe_good", "confidence": 0.5}'
    )
    art = Article(title="Test", ticker="SBER")
    result = estimate_impact(client, art, EventType.EARNINGS)
    assert isinstance(result, ToolError)
    assert result.code == "schema_invalid"


def test_llm_exception():
    client = MagicMock()
    client.chat.completions.create.side_effect = ConnectionError("down")
    art = Article(title="Test", ticker="SBER")
    result = estimate_impact(client, art, EventType.EARNINGS)
    assert isinstance(result, ToolError)
    assert result.code == "llm_timeout"
