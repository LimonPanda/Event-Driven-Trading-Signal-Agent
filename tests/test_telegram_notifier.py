"""Tests for Telegram notifier (mocked HTTP)."""

from unittest.mock import MagicMock, patch

from src.models import EventType, ImpactDirection, Signal, ToolError
from src.pipeline.telegram_notifier import send_signal, _format_message


def test_format_message():
    s = Signal(
        ticker="SBER",
        event_type=EventType.EARNINGS,
        impact=ImpactDirection.POSITIVE,
        confidence=0.85,
        source_url="https://example.com/news/1",
        published="2024-04-01",
    )
    msg = _format_message(s)
    assert "SBER" in msg
    assert "Earnings Release" in msg
    assert "85%" in msg


@patch("src.pipeline.telegram_notifier.httpx.Client")
def test_send_success(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    s = Signal(ticker="SBER", event_type=EventType.EARNINGS, impact=ImpactDirection.POSITIVE, confidence=0.8)
    result = send_signal(s, bot_token="fake", chat_id="123")
    assert result is True


@patch("src.pipeline.telegram_notifier.httpx.Client")
def test_send_failure(mock_client_cls):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = ConnectionError("down")
    mock_client_cls.return_value = mock_client

    s = Signal(ticker="SBER", event_type=EventType.EARNINGS, impact=ImpactDirection.POSITIVE, confidence=0.8)
    result = send_signal(s, bot_token="fake", chat_id="123")
    assert isinstance(result, ToolError)
    assert result.code == "telegram_send_failed"
