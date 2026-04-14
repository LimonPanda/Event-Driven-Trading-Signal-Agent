# Spec: Agent / Orchestrator

## Purpose

Define orchestration steps, transition rules, retry/fallback behavior, and stop conditions.

## Main steps

1. Ingest feed entries.
2. Deduplicate entries.
3. Resolve ticker/entity.
4. Classify event (LLM).
5. Estimate impact (LLM).
6. Validate schema and policy.
7. Persist accepted signal.
8. Notify Telegram (read-only).
9. Trigger asynchronous evaluation.

## Transition rules

- Proceed to next step only if current step status is `ok`.
- On transient API failure, retry up to configured limit.
- On permanent validation failure, transition to `suppressed`.
- On critical storage failure, transition to `error` and alert operator.

## Stop conditions

- `emitted`: accepted signal persisted successfully.
- `suppressed`: guardrail/policy/quality gate failed.
- `failed`: unrecoverable error after retries.

## Retry and fallback policy

- LLM timeout: one retry, then suppress with reason `llm_timeout`.
- Schema failure: one strict re-prompt, then suppress with `schema_invalid`.
- Ambiguous ticker: deterministic fallback attempt; if unresolved, suppress with `ticker_ambiguous`.
- Telegram failure: keep emitted signal, queue retry for notification.

## Guardrails

- Enforce strict JSON schema for LLM outputs.
- Confidence threshold gate before notify.
- Prompt injection sanitization before model calls.
- No tool execution privileges for LLM.

## Acceptance checks

- Every terminal state has explicit reason code.
- Retry counts are bounded and logged.
- Workflow matches `docs/diagrams/workflow-graph.md`.
