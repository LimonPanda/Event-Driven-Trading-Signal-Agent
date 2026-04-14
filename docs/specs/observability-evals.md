# Spec: Observability and Evals

## Purpose

Define metrics, logs, traces, evaluation checks, and the minimum eval suite required for LLM-centric quality control.

## Metrics

### Product metrics
- Signal precision (target > 70%).
- Event coverage (target > 80%).
- Duplicate filtering rate.

### Model metrics
- Event classification accuracy (baseline target > 75% on 50-article test set).
- Entity linking accuracy.
- Impact classification accuracy.
- Invalid LLM output rate (schema validation failures).

### Technical metrics
- p95 pipeline latency (target < 30s).
- Pipeline availability (target >= 95% during test window).
- API error rate by provider.
- Telegram delivery success rate.

## Logs and traces

- **Ingestion log:** source, article ID/link, timestamp, fetch status.
- **Pipeline trace:** stage transitions, retry count, terminal status, reason code.
- **Validation log:** schema failures and suppression reasons.
- **Notification log:** send attempts and final delivery status.
- **LLM call trace:** request payload hash, response latency, token count, schema pass/fail.

## Eval record schema

Each evaluation run produces records with the following structure:

| Field | Description |
| --- | --- |
| `eval_id` | Unique identifier for this eval run |
| `task_input` | Article ID/link and source metadata |
| `environment_state` | Pipeline config snapshot (model version, prompt version, thresholds) |
| `trajectory` | Ordered list of stage transitions with timestamps |
| `tool_calls` | Log of external API calls (RSS, DeepSeek, ISS, Telegram) with latencies |
| `llm_outputs` | Raw structured outputs from each LLM step |
| `final_outcome` | Terminal status: `emitted` / `suppressed` / `failed` with reason code |
| `grading_result` | Deterministic grader verdict (correct/incorrect/partial) against gold label |
| `latency_ms` | Total pipeline time for this article |
| `token_usage` | Prompt + completion tokens consumed across LLM calls |
| `cost_estimate` | Estimated DeepSeek API cost for this article |

## Eval loops

### Offline
- Fixed labeled set of 50 articles with gold event-type labels (held-out from prompt tuning).
- Signal precision and event coverage measured against a manually labeled evaluation sample.
- Re-run eval suite after any prompt, model, or threshold change.
- Compare results against stored baselines to detect regressions.

### Online
- Monitor drift in suppression rate and confidence distribution across runs.
- Sample manual audits of emitted signals (small curated subset per week).
- Track invalid-output rate trend over time.

## Minimum eval suite checklist

The project must ship with:

- [ ] **Benchmark task set:** at least 50 labeled articles with gold event types.
- [ ] **Deterministic graders:** schema validator, event-type matcher, ticker-universe checker.
- [ ] **Trace logging:** every pipeline run produces eval records per the schema above.
- [ ] **Token, cost, and latency metrics:** captured per article and aggregated per run.
- [ ] **Optional LLM judge:** for subjective quality dimensions (explanation clarity, impact reasoning).
- [ ] **Small human-reviewed subset:** 10-20 signals manually verified per eval cycle to calibrate automated metrics.

## Guardrail checks

- Prompt injection detection/sanitization events logged.
- Schema validator pass rate tracked per run.
- No unauthorized side-effect action path (verified by absence of write-tool calls outside notify step).

## Acceptance checks

- Metrics are emitted per run and aggregated weekly.
- Every emitted/suppressed signal is explainable via logs and traces.
- Eval records conform to the schema above.
- Regression comparison against baselines is automated.
- Alerts exist for major SLO breaches (latency, availability, error rate).
