"""Shared data models, enums, and error contract used across all modules."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EventType(str, enum.Enum):
    EARNINGS = "earnings_release"
    DIVIDEND = "dividend_announcement"
    SANCTIONS = "sanctions"
    REGULATION = "government_regulation"
    RESTRUCTURING = "corporate_restructuring"
    MA = "mergers_and_acquisitions"
    MANAGEMENT = "management_change"
    OTHER = "other"
    NONE = "no_event"


class ImpactDirection(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class ArticleStatus(str, enum.Enum):
    INGESTED = "ingested"
    DUPLICATE = "duplicate"
    PROCESSING = "processing"
    EMITTED = "emitted"
    SUPPRESSED = "suppressed"
    FAILED = "failed"


class SuppressionReason(str, enum.Enum):
    DUPLICATE = "duplicate"
    NO_TICKER = "no_ticker"
    TICKER_AMBIGUOUS = "ticker_ambiguous"
    NO_EVENT = "no_event"
    LLM_TIMEOUT = "llm_timeout"
    SCHEMA_INVALID = "schema_invalid"
    LOW_CONFIDENCE = "low_confidence"
    SANITIZATION_BLOCK = "sanitization_block"
    PIPELINE_ERROR = "pipeline_error"


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

@dataclass
class Article:
    """Normalized article flowing through the pipeline."""

    article_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    link: str = ""
    summary: str = ""
    published: str | None = None
    source_feed: str = ""
    ingested_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    canonical_key: str = ""
    status: ArticleStatus = ArticleStatus.INGESTED
    ticker: str | None = None
    suppression_reason: SuppressionReason | None = None


@dataclass
class LLMClassificationResult:
    """Structured output from the event classification LLM step."""

    event_type: EventType = EventType.NONE
    confidence: float = 0.0
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMImpactResult:
    """Structured output from the impact estimation LLM step."""

    impact: ImpactDirection = ImpactDirection.UNCERTAIN
    confidence: float = 0.0
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class Signal:
    """Accepted trading signal ready for storage and notification."""

    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    article_id: str = ""
    ticker: str = ""
    event_type: EventType = EventType.NONE
    impact: ImpactDirection = ImpactDirection.UNCERTAIN
    confidence: float = 0.0
    source_url: str = ""
    source_name: str = ""
    published: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    prompt_version: str = "v1"
    model_name: str = ""


# ---------------------------------------------------------------------------
# Standard error contract (code / message / suggestion)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolError:
    """Machine-readable error surfaced to the orchestrator."""

    code: str
    message: str
    suggestion: str
