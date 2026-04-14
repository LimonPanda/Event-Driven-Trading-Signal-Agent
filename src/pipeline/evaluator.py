"""Post-event evaluation: fetch MOEX ISS prices and compute actual movement vs predicted impact."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from src.models import ImpactDirection, Signal
from src.tools.moex_iss import fetch_share_daily_bars

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    signal_id: str
    ticker: str
    predicted_impact: str
    close_before: float | None
    close_after: float | None
    actual_return_pct: float | None
    actual_direction: str
    correct: bool | None


def evaluate_signal(
    signal: Signal,
    *,
    event_date: date | None = None,
    horizon_days: int = 3,
) -> EvalResult:
    """
    Compare predicted impact against actual price movement.

    Looks up the closing price on event_date and event_date + horizon_days
    from MOEX ISS daily bars.
    """
    if event_date is None:
        event_date = date.today() - timedelta(days=1)

    date_from = event_date - timedelta(days=5)
    date_till = event_date + timedelta(days=horizon_days + 5)

    try:
        bars = fetch_share_daily_bars(
            signal.ticker, date_from, date_till, timeout=30.0
        )
    except Exception as exc:
        logger.warning("MOEX ISS fetch failed for %s: %s", signal.ticker, exc)
        return EvalResult(
            signal_id=signal.signal_id,
            ticker=signal.ticker,
            predicted_impact=signal.impact.value,
            close_before=None,
            close_after=None,
            actual_return_pct=None,
            actual_direction="unknown",
            correct=None,
        )

    close_map: dict[str, float] = {}
    for bar in bars:
        trade_date = bar.get("TRADEDATE", "")
        close = bar.get("CLOSE") or bar.get("LEGALCLOSEPRICE")
        if trade_date and close is not None:
            close_map[trade_date] = float(close)

    event_str = event_date.isoformat()
    after_date = event_date + timedelta(days=horizon_days)
    after_str = after_date.isoformat()

    close_before = _nearest_close(close_map, event_str, direction=-1)
    close_after = _nearest_close(close_map, after_str, direction=1)

    if close_before is None or close_after is None or close_before == 0:
        return EvalResult(
            signal_id=signal.signal_id,
            ticker=signal.ticker,
            predicted_impact=signal.impact.value,
            close_before=close_before,
            close_after=close_after,
            actual_return_pct=None,
            actual_direction="unknown",
            correct=None,
        )

    ret_pct = ((close_after - close_before) / close_before) * 100.0
    if ret_pct > 0.5:
        actual = "positive"
    elif ret_pct < -0.5:
        actual = "negative"
    else:
        actual = "neutral"

    predicted = signal.impact.value
    if predicted == "uncertain":
        correct = None
    else:
        correct = predicted == actual

    return EvalResult(
        signal_id=signal.signal_id,
        ticker=signal.ticker,
        predicted_impact=predicted,
        close_before=close_before,
        close_after=close_after,
        actual_return_pct=round(ret_pct, 3),
        actual_direction=actual,
        correct=correct,
    )


def _nearest_close(
    close_map: dict[str, float], target: str, direction: int = -1
) -> float | None:
    """Find the nearest close price to target date, searching backwards (direction=-1) or forwards."""
    if target in close_map:
        return close_map[target]
    target_date = date.fromisoformat(target)
    for offset in range(1, 10):
        d = target_date + timedelta(days=offset * direction)
        if d.isoformat() in close_map:
            return close_map[d.isoformat()]
    return None
