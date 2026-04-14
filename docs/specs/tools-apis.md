# Spec: Tools and APIs

## Purpose

Define deterministic integration contracts for RSS, DeepSeek, MOEX ISS, and Telegram, including read/write classification and standardized error handling.

## Integration matrix

| Integration | Direction | Read/Write | Timeout | Retries | Error classes | Side effects |
| --- | --- | --- | --- | --- | --- | --- |
| RSS/Atom feeds | Outbound fetch | **Read-only** | 30s | 1 retry, exponential backoff | Network timeout, malformed XML, non-200 | Ingestion logs, queue records |
| DeepSeek API | Outbound inference | **Read-only** (no state mutation on provider side) | 30s | 1 retry for transient transport errors | Timeout, rate limit, invalid JSON, schema mismatch | Model output traces (metadata only) |
| MOEX ISS API | Outbound price lookup | **Read-only** | 30s | 2 retries on 5xx/network errors | Endpoint unavailable, empty bars, schema drift | Cached evaluation artifacts |
| Telegram Bot API | Outbound notification | **Write** (delivers message to external chat) | 10s | 2 retries for transient delivery errors | Invalid token, invalid `chat_id`, network timeout | Notification logs, dead-letter records |

### Read/write policy

- **Read-only** integrations (RSS, DeepSeek, MOEX ISS) can be retried and parallelized freely; they do not mutate external state.
- **Write** integrations (Telegram) are controlled more tightly: retries are bounded, delivery is idempotent where possible, and failures are recorded in a dead-letter log rather than silently dropped.

## Standard error contract

All tool/integration errors surfaced to the orchestrator follow a consistent shape:

```
code:        machine-readable error identifier
message:     human-readable description of what went wrong
suggestion:  actionable recovery hint for the orchestrator
```

### Error code examples

| Code | Message | Suggestion |
| --- | --- | --- |
| `RSS_TIMEOUT` | Feed fetch timed out after 30s | Retry once; if still failing, skip feed for this cycle |
| `RSS_PARSE_ERROR` | XML could not be parsed | Log and skip; do not retry parse on same bytes |
| `LLM_TIMEOUT` | DeepSeek request timed out | Retry once; suppress article if still failing |
| `LLM_SCHEMA_INVALID` | Response JSON does not match expected schema | Re-prompt in strict mode; suppress if still invalid |
| `LLM_RATE_LIMIT` | Rate limit exceeded | Back off and retry after delay |
| `ISS_UNAVAILABLE` | MOEX ISS returned 5xx or network error | Retry with backoff; postpone eval if persistent |
| `ISS_EMPTY_BARS` | No price data returned for requested range | Log warning; eval cannot complete for this window |
| `TG_SEND_FAILED` | Telegram message delivery failed | Retry twice; write to dead-letter queue if still failing |
| `TG_INVALID_CONFIG` | Bot token or chat_id is invalid | Alert operator; do not retry |

## Security and guardrails

- LLM cannot call tools directly; all tool invocations are orchestrator-owned and policy-gated.
- Telegram is a write-only output channel; inbound commands are ignored.
- Secrets (API keys, bot tokens) are loaded from environment variables; never committed to repo or logged.

## Acceptance checks

- Every integration has explicit timeout, retry policy, and error mapping.
- Read-only vs write classification is documented and respected in retry/parallelism logic.
- All errors surfaced to the orchestrator use the standard `code / message / suggestion` shape.
- Side effects are documented and traceable in logs.
