# System Design

## 1. Purpose and Scope

This document fixes the PoC architecture for the Event-Driven Trading Signal Agent before implementation.
The design is focused on MOEX equities, RSS/Atom ingestion, DeepSeek-powered semantic steps, and read-only Telegram delivery.

Out of scope:
- trade execution;
- portfolio optimization;
- low-latency production infra;
- paid market/news data vendors beyond DeepSeek.

## 2. Key Architecture Decisions

### 2.1 Pattern choice: deterministic workflow, not autonomous agent

The pipeline processes news through a fixed sequence of stages (ingest -> dedup -> link -> classify -> impact -> validate -> store -> notify -> evaluate). Every stage and its transitions are known at design time. There is no open-ended tool selection or autonomous goal pursuit.

This makes the system a **deterministic workflow with LLM augmentation at specific steps**, not a free-form agent or multi-agent system. Per the project's design guidelines:
- A workflow is preferred over an agent when the task is predictable and repetitive.
- A single orchestrator is preferred over multiple agents unless concrete tool/context/safety separation demands it.
- Adding agent autonomy would increase cost, latency, and debugging difficulty without improving quality for this fixed pipeline.

LLM calls (event classification, impact estimation, entity disambiguation) are embedded as **tool-like substeps** inside the workflow, not as autonomous decision-makers that choose their own next action.

### 2.2 Reasoning pattern: DVF for LLM steps

Each LLM-augmented step follows a **Draft-Verify-Fix (DVF)** cycle:
1. **Draft:** send a compact prompt with truncated article context; request structured JSON output.
2. **Verify:** validate the response against a strict JSON schema + policy rules (ticker in universe, event type in taxonomy, confidence within range).
3. **Fix:** if validation fails, re-prompt once in strict mode; if still invalid, suppress with an explicit reason code.

The top-level orchestrator itself does not use ReAct or PAR — it is a linear workflow with deterministic branching (valid/invalid/error). DVF is applied only at the LLM boundary where non-determinism exists.

### 2.3 Domain decisions

- **Market scope:** MOEX-listed equities only.
- **Ingestion scope:** allowlisted public RSS/Atom feeds from `config/feeds.yaml`.
- **LLM provider:** DeepSeek (OpenAI-compatible API).
- **Evaluation prices:** MOEX ISS historical data.
- **Delivery channel:** read-only Telegram bot to allowlisted `chat_id`.
- **Safety model:** LLM cannot call external tools directly; deterministic code mediates all tool/API calls.
- **Signal policy:** emit only when schema validation and confidence thresholds pass; otherwise fallback or no-signal.

## 3. Module Inventory

1. **Ingestion Module**
   - Pulls RSS/Atom feeds, normalizes entries, persists raw ingestion metadata.
2. **Deduplication Module**
   - Collapses syndicated duplicates using URL/hash/title-time heuristics.
3. **Entity Linking Module**
   - Maps mentions to MOEX tickers using dictionary + LLM disambiguation when needed.
4. **Event Classification Module (LLM)**
   - Classifies event type into controlled taxonomy.
5. **Impact Estimation Module (LLM)**
   - Predicts directional impact (positive/negative/neutral/uncertain).
6. **Validation and Policy Module**
   - Validates structured output schema, ticker universe, confidence, and guardrails.
7. **Signal Store Module**
   - Stores accepted signals and trace metadata for eval/monitoring.
8. **Telegram Notifier Module**
   - Sends read-only alerts; ignores/blocks command semantics.
9. **Evaluation Module**
   - Fetches MOEX ISS prices, computes post-event movement labels/metrics.
10. **Observability and Evals Module**
   - Logs, traces, offline/online metrics, quality checks, alerting.

## 4. Canonical Execution Workflow

1. Fetch feed entries from allowlisted sources.
2. Normalize and deduplicate entries.
3. Extract candidate issuer mentions.
4. Resolve ticker (deterministic first, LLM-assisted on ambiguity).
5. Run LLM event classification.
6. Run LLM impact estimation.
7. Validate schema + policy + confidence.
8. If valid, persist signal and notify Telegram.
9. If invalid/low confidence, apply fallback path (retry, degrade, or suppress).
10. Run evaluation jobs against MOEX ISS asynchronously.

## 5. State, Memory, and Context Handling

### 5.1 State
- `ingestion_state`: fetched IDs/URLs, source timestamps, fetch status.
- `dedup_state`: canonical article mapping, duplicate clusters.
- `pipeline_state`: per-article stage status, retry counters, error class.
- `signal_state`: accepted/suppressed signals with reasons.

### 5.2 Memory policy
- No long-term conversational memory is required for end users in PoC.
- Operational memory is task-state only (pipeline progress, retries, caches).
- Model outputs retained for eval window per governance retention policy.

### 5.3 Context engineering policy

Context is a scarce resource: longer inputs increase cost, latency, and degrade output quality. Each LLM call receives a dynamically assembled payload containing only what that specific step needs.

**What goes into an LLM request and why:**

| Field | Included | Rationale |
| --- | --- | --- |
| System prompt (step-specific) | Always | Sets task, output schema, constraints |
| Article title | Always | Primary signal for event detection |
| Article body excerpt (truncated) | Always | Supporting detail; capped at configured max chars |
| Source name and URL | Always | Provenance for confidence calibration |
| Published timestamp | Always | Recency signal |
| Ticker hint (if entity step resolved one) | When available | Reduces ambiguity for classification/impact steps |
| Few-shot examples | Optional, per step | Only if measurably improves accuracy in eval |

**What is never included:**

- Full raw article body beyond the truncation limit.
- Tool definitions, API credentials, or system internals.
- Conversation history (there is no multi-turn dialogue in this workflow).
- Outputs from unrelated pipeline runs or articles.

**Assembly rule:** each step's prompt builder constructs the payload from the current article record and pipeline state only. No global context dump.

## 6. Retrieval Contour

Retrieval in this PoC means data intake and candidate context assembly:
- RSS/Atom pull from allowlist.
- Candidate event extraction from normalized entry text.
- Deterministic ticker dictionary lookup.
- Optional LLM disambiguation when dictionary confidence is insufficient.

No vector database is required in PoC baseline.

## 7. Tool/API Integrations and Contracts

### 7.1 RSS feeds
- Input: allowlisted URLs from `config/feeds.yaml`.
- Timeout: 30s default.
- Error classes: network timeout, invalid XML, empty feed.
- Side effects: ingestion logs and queue records.

### 7.2 DeepSeek API
- Interface: OpenAI-compatible chat endpoint.
- Inputs: compact prompt + truncated article context + output schema instructions.
- Timeout: 30s per call; bounded retries.
- Error classes: timeout, malformed response, schema violation.

### 7.3 MOEX ISS API
- Interface: HTTPS JSON endpoints for historical prices.
- Timeout: 30s; retry with backoff.
- Error classes: endpoint unavailable, empty bars, schema drift.

### 7.4 Telegram Bot API
- Outbound-only notifications to allowlisted `chat_id`.
- Timeout: 10s; retry on transient failures.
- Side effects: message delivery logs.

## 8. Failure Modes, Fallbacks, and Guardrails

| Failure mode | Detection | Fallback | Final behavior |
| --- | --- | --- | --- |
| Feed unavailable | HTTP/network errors | Retry with backoff; continue other feeds | Partial ingestion, no hard stop |
| Duplicate explosion | High duplicate rate | Tighten dedup thresholds for run | Emit one canonical signal per cluster |
| Ticker ambiguity | Low linking confidence | LLM disambiguation attempt | Suppress signal if unresolved |
| LLM timeout | Client timeout | Retry once; then degrade path | No-signal with reason code |
| LLM malformed output | Schema validator fail | Re-prompt in strict JSON mode | Suppress if still invalid |
| Low confidence | Threshold check | Mark uncertain; optional manual review queue | No Telegram alert in strict mode |
| Prompt injection content | Input sanitization + policy checks | Strip malicious instruction patterns | Continue classification on sanitized text |
| MOEX ISS unavailable | API failure | Retry/backoff; postpone eval | Signal kept, eval delayed |
| Telegram send fail | API error | Retry; dead-letter queue | Signal stored even if notify fails |

Guardrails:
- strict output schema validation before persistence;
- deterministic policy gate before notify;
- tool isolation from LLM;
- read-only signal semantics;
- retention and PII handling per governance.

## 9. Quality Control and Evals

### 9.1 Offline checks
- Event classification accuracy on 50-article labeled set (target > 75%).
- Signal precision and coverage against labeled evaluation sample.
- Regression suite for prompt/model changes.

### 9.2 Online checks
- Invalid output rate.
- Suppression rate by guardrail reason.
- Telegram delivery success rate.
- p95 pipeline latency and availability window SLO.

### 9.3 Control points
- Pre-LLM: payload sanitization.
- Post-LLM: schema + policy validator.
- Pre-notify: confidence + read-only compliance gate.
- Post-run: eval and anomaly review.

## 10. Constraints (Technical and Operational)

- **Latency:** p95 under 30s from article intake to signal decision.
- **Reliability:** 95% availability during PoC test window.
- **Cost:** only DeepSeek is paid; RSS, MOEX ISS, Telegram API are free at API level.
- **Scope:** 10-20 MOEX tickers and limited source set.
- **Security:** no trade execution, no privileged tool calls from LLM, secrets from environment only.

## 11. Implementation Readiness Checklist

- module contracts are defined in `docs/specs/*`;
- workflow/failure/data views are documented in `docs/diagrams/*`;
- README links to Milestone 2 artifacts;
- no contradictions with `docs/product-proposal.md` and `docs/governance.md`.
