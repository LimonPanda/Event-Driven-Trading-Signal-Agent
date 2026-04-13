"""Fetch historical daily bars from MOEX ISS (no API key for standard JSON endpoints)."""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx

ISS_BASE = "https://iss.moex.com/iss"


def fetch_share_daily_bars(
    security: str,
    date_from: date,
    date_till: date,
    *,
    engine: str = "stock",
    market: str = "shares",
    board: str = "TQBR",
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """
    Return list of row dicts for MOEX daily history (OHLCV columns depend on ISS schema).

    Caches nothing here — persist in DB/SQLite in the full pipeline.
    """
    # See https://iss.moex.com/iss/reference/
    url = (
        f"{ISS_BASE}/history/engines/{engine}/markets/{market}/"
        f"boards/{board}/securities/{security}.json"
    )
    params = {
        "from": date_from.isoformat(),
        "till": date_till.isoformat(),
    }
    headers = {"User-Agent": "EventDrivenTradingSignalAgent/0.1"}
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        payload = response.json()

    history = payload.get("history", {})
    columns = history.get("columns") or []
    data_rows = history.get("data") or []
    out: list[dict[str, Any]] = []
    for row in data_rows:
        out.append(dict(zip(columns, row)))
    return out
