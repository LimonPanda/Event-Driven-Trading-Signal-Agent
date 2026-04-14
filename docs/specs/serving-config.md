# Spec: Serving and Config

## Purpose

Define runtime model, environment configuration, secrets policy, and versioning.

## Runtime model

- Batch or periodic polling loop for feed ingestion.
- Deterministic orchestration service with pluggable modules.
- Optional worker for asynchronous evaluation and notification retries.

## Required config

- `DEEPSEEK_API_KEY` (required)
- `DEEPSEEK_BASE_URL` (optional)
- `TELEGRAM_BOT_TOKEN` (required for notifications)
- `TELEGRAM_CHAT_ID` (allowlisted destination)
- feed config path (`config/feeds.yaml`)
- quality thresholds (`min_confidence`, `max_retries`, `llm_timeout_s`)

## Secrets policy

- Secrets in environment variables or secret manager only.
- Never store secrets in markdown, source files, or logs.

## Versioning policy

- Pin model name in runtime config.
- Track prompt template version and schema version in signal metadata.
- Tag releases when prompt/model/threshold changes affect output semantics.

## Operational constraints

- p95 latency target: < 30s.
- PoC availability target: 95% during testing window.
- Paid external API: DeepSeek only.

## Acceptance checks

- System starts with missing-secret validation.
- Config has sane defaults for non-secret values.
- Version fields present in emitted signal metadata.
