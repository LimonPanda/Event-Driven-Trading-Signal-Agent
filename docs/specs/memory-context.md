# Spec: Memory and Context

## Purpose

Define session, state, and memory boundaries and context rules for deterministic execution and LLM inputs.

## Session

A session is one pipeline run (batch or polling cycle) and the log/trace it produces.

- Session starts when the orchestrator begins a feed-fetch cycle.
- Session ends when all articles in the batch reach a terminal status (emitted / suppressed / failed).
- Session transcript is the ordered trace of stage transitions, LLM calls, and outcomes.
- Sessions are ephemeral: not carried forward into subsequent runs.

## State (current task scratchpad)

State is the working data for the active pipeline run. It is mutable during the session and discarded or archived after.

Domains:
- `ingestion_state`: fetched IDs, source, timestamps, fetch status per feed.
- `dedup_state`: canonical article key mappings and duplicate clusters for this batch.
- `pipeline_state`: per-article stage progress, retry counters, current error class.
- `signal_state`: accepted or suppressed signal records with reason codes.
- `eval_state`: pending and completed MOEX ISS evaluation jobs.

State is persisted only to the extent needed for crash recovery and post-run audit.

## Memory (durable persistent facts)

Memory holds facts that survive across sessions and are useful for future runs.

In the PoC, durable memory is minimal:
- **Ticker dictionary:** MOEX ticker-to-company mapping table (updated manually or via config).
- **Feed health history:** per-feed success/failure counters across runs (used for operational monitoring).
- **Evaluation baselines:** historical eval metrics for regression comparison.

Not stored as memory:
- Raw article text (retention per governance, not memory).
- Conversation history (there is no multi-turn user dialogue in the PoC workflow).
- Transient processing state from completed runs.

## Retention policy

Follow `docs/governance.md`:
- Logs: 30 days.
- Raw text (if persisted): up to 30 days.
- Signals/metadata/eval outputs: 90 days default.

## Context budget policy

- LLM payload includes only required fields (title, body excerpt, timestamp, source, optional ticker hints).
- Max text length per article is truncated before model call (see `docs/system-design.md` Section 5.3).
- Do not pass hidden system prompts, tool credentials, or unrelated article data in LLM content context.
- Each step's prompt builder assembles context from the current article record and pipeline state only.

## Acceptance checks

- Session, state, and memory are never collapsed into one store.
- Every stage transition records state and timestamp.
- Suppressed signals include explicit reason code.
- Retention constraints are enforceable through config.
- Memory entries have clear scope (ticker dict = application-level; feed health = application-level; eval baselines = application-level).
