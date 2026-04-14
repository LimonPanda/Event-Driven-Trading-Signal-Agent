"""Deterministic entity linker: maps company mentions in text to MOEX tickers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class TickerDictionary:
    """In-memory lookup from company aliases to MOEX tickers."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._alias_to_ticker: dict[str, str] = {}
        self._tickers: set[str] = set()
        for rec in records:
            ticker = rec["ticker"].upper()
            self._tickers.add(ticker)
            for alias in rec.get("aliases", []):
                self._alias_to_ticker[alias.lower()] = ticker
            self._alias_to_ticker[ticker.lower()] = ticker
            company = rec.get("company", "")
            if company:
                self._alias_to_ticker[company.lower()] = ticker

    @classmethod
    def from_yaml(cls, path: str | Path) -> TickerDictionary:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls(raw.get("tickers", []))

    @property
    def universe(self) -> set[str]:
        return set(self._tickers)

    def resolve(self, text: str) -> str | None:
        """Return the first matching ticker found in text, or None.

        Uses substring matching (longest alias first) to handle
        Russian case declensions (Сбербанк → Сбербанка, Сбербанку, …).
        """
        lower = text.lower()
        for alias, ticker in sorted(
            self._alias_to_ticker.items(), key=lambda x: -len(x[0])
        ):
            if alias in lower:
                return ticker
        return None
