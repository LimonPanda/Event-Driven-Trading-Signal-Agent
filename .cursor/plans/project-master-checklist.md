# Project Master Checklist (Private)

## Status Legend

- [ ] pending
- [~] in progress
- [x] done

Owner shorthand:
- `U` = user
- `A` = assistant
- `Team` = collaborative

## Milestone Roadmap

### M1 — Project framing and governance
- [x] README aligned to MOEX scope (`Team`)
- [x] Product metrics and model baseline targets defined (`Team`)
- [x] Governance risk scoring, retention, access control, read-only policy documented (`Team`)

### M2 — Architecture lock (current)
- [~] `docs/system-design.md` finalized (`A`)
- [~] `docs/diagrams/` architecture views finalized (`A`)
- [~] `docs/specs/` module contracts finalized (`A`)
- [ ] Final architecture review pass by user (`U`)

### M3 — Implementation baseline
- [ ] Build orchestrator pipeline skeleton (`Team`)
- [ ] Integrate RSS ingestion + dedup (`Team`)
- [ ] Implement entity mapping + LLM classification pipeline (`Team`)
- [ ] Add validation/policy gate + suppression logic (`Team`)
- [ ] Add Telegram notifier and retry queue (`Team`)
- [ ] Add MOEX ISS evaluation worker (`Team`)

### M4 — Quality hardening and demo readiness
- [ ] Offline eval pipeline (classification + precision/coverage) (`Team`)
- [ ] Prompt/version regression checks (`Team`)
- [ ] SLO dashboard for latency/availability (`Team`)
- [ ] Demo dry-run on Sberbank 5-article scenario (`Team`)

## Architecture-to-Implementation Checklist

### Orchestrator
- [ ] Define stage enum and terminal statuses (`emitted`, `suppressed`, `failed`)
- [ ] Encode retry policies per API call
- [ ] Emit reason codes for every suppression/failure path

### Validation and Guardrails
- [ ] Create strict JSON schema for LLM outputs
- [ ] Add confidence thresholds by event type
- [ ] Add injection sanitization before LLM calls
- [ ] Ensure no direct LLM tool execution path

### Storage and State
- [ ] Ingestion state store
- [ ] Dedup canonical map
- [ ] Signal store with metadata version fields
- [ ] Eval metrics store

### Observability and Evals
- [ ] Track invalid-output and suppression-rate metrics
- [ ] Weekly quality report template
- [ ] Manual audit sampling checklist

## Risk Watchlist

| Risk | Trigger | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- |
| RSS source instability | frequent feed failures | source redundancy + retries | Team | open |
| LLM schema drift | invalid JSON increase | strict parser + re-prompt | Team | open |
| Confidence miscalibration | low precision in eval | threshold tuning + audit samples | Team | open |
| ISS latency/outage | eval backlog growth | cache + async retries | Team | open |
| Telegram delivery failures | delivery success drop | dead-letter queue + retries | Team | open |

## Definition of Done Gates

### Gate A: Before main coding
- [ ] System design + specs + diagrams approved by user
- [ ] Config and secrets policy agreed
- [ ] Acceptance metrics agreed (precision, coverage, accuracy, latency, uptime)

### Gate B: Before milestone demo
- [ ] End-to-end run succeeds on fixed sample
- [ ] Guardrail suppression paths demonstrated
- [ ] Read-only Telegram behavior verified
- [ ] Eval outputs reproducible and logged
