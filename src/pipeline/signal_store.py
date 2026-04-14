"""SQLite-backed signal store: accepted signals + suppression log."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from src.models import Article, Signal, SuppressionReason

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS signals (
    signal_id   TEXT PRIMARY KEY,
    article_id  TEXT NOT NULL,
    ticker      TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    impact      TEXT NOT NULL,
    confidence  REAL NOT NULL,
    source_url  TEXT,
    source_name TEXT,
    published   TEXT,
    created_at  TEXT NOT NULL,
    prompt_version TEXT,
    model_name  TEXT
);

CREATE TABLE IF NOT EXISTS suppressions (
    article_id  TEXT PRIMARY KEY,
    reason      TEXT NOT NULL,
    detail      TEXT,
    created_at  TEXT NOT NULL
);
"""


class SignalStore:
    def __init__(self, db_path: str | Path = "data/signals.db") -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    def save_signal(self, signal: Signal) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO signals VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                signal.signal_id,
                signal.article_id,
                signal.ticker,
                signal.event_type.value,
                signal.impact.value,
                signal.confidence,
                signal.source_url,
                signal.source_name,
                signal.published,
                signal.created_at,
                signal.prompt_version,
                signal.model_name,
            ),
        )
        self._conn.commit()

    def save_suppression(
        self,
        article: Article,
        reason: SuppressionReason,
        detail: str = "",
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO suppressions VALUES (?,?,?,?)",
            (
                article.article_id,
                reason.value,
                detail,
                datetime.now(UTC).isoformat(),
            ),
        )
        self._conn.commit()

    def get_signal(self, signal_id: str) -> dict | None:
        cur = self._conn.execute(
            "SELECT * FROM signals WHERE signal_id = ?", (signal_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))

    def recent_signals(self, limit: int = 20) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self) -> None:
        self._conn.close()
