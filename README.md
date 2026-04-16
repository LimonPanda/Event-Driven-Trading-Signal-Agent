# Event-Driven Trading Signal Agent

## Overview

Event-Driven Trading Signal Agent is an agent-based system that analyzes streams of financial news and corporate disclosures about **companies listed on the Moscow Exchange (MOEX)** to detect events that may influence their stock prices and convert them into structured trading signals.

The PoC is scoped to **MOEX-listed Russian equities** (a limited set of large-cap tickers). It is designed for anyone who needs to quickly identify market-moving events in that universe and evaluate their potential impact (quantitative researchers, algorithmic trading developers, financial analysts, and similar roles).

This repository contains a Proof-of-Concept (PoC) implementation demonstrating an end-to-end pipeline: from news ingestion to event detection, signal generation, delivery via **Telegram**, and post-event evaluation against MOEX price data.

---

# Problem

The **Russian equity market (MOEX)** reacts strongly to **events**, such as:

* earnings releases
* dividend announcements
* sanctions or regulatory actions
* mergers and acquisitions
* management changes
* major corporate disclosures

However, information about these events:

* arrives from multiple heterogeneous sources
* often contains duplicates and noise
* may be ambiguous or incomplete
* requires manual interpretation

Analysts and traders working on **MOEX names** frequently spend significant time scanning news feeds to determine:

* whether a piece of news relates to a tradable company in their universe
* whether the event is new or already known
* how important the event is
* whether it may affect the price of a particular ticker

This manual process leads to:

* delays in reacting to information
* missed signals
* excessive time spent filtering irrelevant content.

---

# Project Goal

The goal of this project is to build a **PoC agent-based system** that automatically:

1. collects news from multiple sources relevant to **MOEX-listed companies**
2. detects events related to those issuers
3. links events to specific **MOEX tickers**
4. classifies the type of event
5. estimates the potential impact on price
6. generates structured trading signals

The system acts as an **event intelligence layer** between raw news data and trading research workflows focused on the **MOEX** universe.

---

# Target Users

The primary users of the system include:

* analysts and researchers covering **MOEX-listed stocks**
* quantitative researchers
* algorithmic trading developers
* financial analysts
* market intelligence teams

The system is intended as a **decision-support tool**, not as a fully autonomous trading system.

---

# What the PoC Demonstrates

The PoC demonstrates an end-to-end pipeline consisting of the following steps.

### Demo scenario (concrete example)

For a live demo, the team runs the pipeline on a small batch—for example, **five news articles about Sberbank** (including syndicated duplicates from more than one source). The system **deduplicates** the items, **detects one market-relevant corporate event**, maps it to ticker **SBER**, classifies the event type and impact, emits a **structured signal**, and delivers it to a **Telegram** chat as a read-only notification. No trades or other actions are executed.

### 1. News Ingestion

The system collects news articles and corporate announcements from allowlisted **RSS/Atom feeds** focused on Russian financial news and MOEX-relevant issuers.

### 2. Deduplication

Duplicate news items from different sources are detected and merged.

### 3. Entity Linking

The system identifies which company or **MOEX ticker** the news refers to.

### 4. Event Classification

The detected event is classified into categories such as:

* earnings release
* dividend announcement
* sanctions
* mergers & acquisitions
* management changes
* and others

### 5. Impact Estimation

The system estimates the likely market impact:

* positive
* negative
* neutral
* uncertain


### 6. Signal Generation

A structured event signal is generated containing:

* ticker
* event type
* expected impact
* confidence score
* source reference

### 7. Alerting

Relevant signals are delivered via a **Telegram bot** to a configured chat (see [docs/governance.md](docs/governance.md) for access control). Outputs are **read-only**; the user cannot initiate trades or other side effects through the bot.

### 8. Post-Event Evaluation

The system evaluates whether the detected event was followed by a meaningful price move using **MOEX** market data.

---

# Out of Scope (Not Implemented in PoC)

The following features are **explicitly out of scope** for this PoC:

* full trading strategies
* advanced price prediction models
* high-frequency trading infrastructure
* ultra-low latency systems
* large-scale production data pipelines
* **full market coverage** (non-MOEX venues, broad global universes)

The PoC focuses specifically on **event detection and signal generation** for a **limited MOEX ticker set**, not on building a complete trading system.

---

# Why an Agent-Based System

The problem naturally decomposes into multiple stages:

* data ingestion
* entity recognition
* event classification
* impact estimation
* signal generation
* evaluation

Each stage can be implemented as an independent agent or module with specialized responsibilities.

An agent-based architecture allows the system to:

* separate reasoning tasks from deterministic processing
* handle ambiguity and conflicting information
* integrate LLM reasoning where semantic interpretation is required
* maintain state across the event processing pipeline.

---

# Repository Structure

```
config/
    feeds.yaml              # Allowlisted RSS/Atom feed URLs
    tickers.yaml            # MOEX ticker dictionary with aliases

docs/
    product-proposal.md
    governance.md
    system-design.md
    diagrams/               # C4, workflow, data-flow (Mermaid)
    specs/                  # Module-level technical specs

src/
    models.py               # Shared data models, enums, error contract
    config.py               # Centralized config loader (.env)
    cli.py                  # CLI entrypoint (python -m src.cli)
    pipeline/
        orchestrator.py     # Deterministic pipeline coordinator
        entity_linker.py    # Ticker dictionary + entity resolution
        dedup.py            # URL + title/date deduplication
        sanitizer.py        # Prompt injection stripping
        llm_classify.py     # Event classification (DVF cycle)
        llm_impact.py       # Impact estimation (DVF cycle)
        validator.py        # Confidence gate + ticker universe check
        signal_store.py     # SQLite-backed signal + suppression store
        telegram_notifier.py # Outbound-only Telegram alerts
        evaluator.py        # Post-event MOEX ISS price evaluation
    tools/
        rss_feeds.py        # RSS/Atom feed loading and parsing
        moex_iss.py         # MOEX ISS historical data client
        deepseek_client.py  # OpenAI-compatible DeepSeek client

tests/
    fixtures/
        minimal_feed.xml    # Minimal RSS fixture
        sberbank_demo.json  # 5-article Sberbank demo set
    test_models.py
    test_entity_linker.py
    test_dedup.py
    test_sanitizer.py
    test_llm_classify.py
    test_llm_impact.py
    test_validator.py
    test_signal_store.py
    test_telegram_notifier.py
    test_orchestrator.py
    test_e2e_demo.py        # Full pipeline e2e on Sberbank fixtures
    test_config.py
    test_rss_fixture.py

.env.example                # Template for environment variables
requirements.txt
pyproject.toml
README.md
```

---

# System Design (Milestone 2)

Architecture artifacts for Milestone 2:

- `docs/system-design.md` — source-of-truth architecture document (modules, workflow, state, retrieval, integrations, guardrails, failure/fallback paths).
- `docs/diagrams/c4-context.md`
- `docs/diagrams/c4-container.md`
- `docs/diagrams/c4-component-core.md`
- `docs/diagrams/workflow-graph.md`
- `docs/diagrams/data-flow.md`
- `docs/specs/retriever.md`
- `docs/specs/tools-apis.md`
- `docs/specs/memory-context.md`
- `docs/specs/agent-orchestrator.md`
- `docs/specs/serving-config.md`
- `docs/specs/observability-evals.md`

These files define implementation contracts before coding and align with product/governance constraints.

---

# Technology Stack

* **Python 3.12+**
* **DeepSeek API** (via OpenAI-compatible client) — the only paid API
* **RSS/Atom feeds** — public, free news sources
* **MOEX ISS** — public HTTPS API for historical prices (no key required)
* **Telegram Bot API** — free, outbound-only signal delivery
* **SQLite** — lightweight signal/suppression store
* **pytest** — test suite with mocked LLM calls

**Cost profile:** $0 except DeepSeek API (< $20/month target).

---

# Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd Event-Driven-Trading-Signal-Agent
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env: set DEEPSEEK_API_KEY (required), TELEGRAM_BOT_TOKEN/CHAT_ID (optional)

# 3. Run tests (no API key needed — all LLM calls mocked)
python -m pytest tests/ -v

# 4. Dry run (ingests feeds, resolves tickers, no LLM calls)
python -m src.cli --dry-run

# 5. Full pipeline with fixture data
python -m src.cli --fixture tests/fixtures/sberbank_demo.json

# 6. Full pipeline on live feeds (enable feeds in config/feeds.yaml first)
python -m src.cli
```

---

# Run with Docker

If you don't want to install Python locally, you can run everything in a container. You only need **Docker** and **Docker Compose** installed.

```bash
# 1. Clone the repo
git clone <repo-url> && cd Event-Driven-Trading-Signal-Agent

# 2. Configure — create your .env from the template
cp .env.example .env
# Edit .env: set DEEPSEEK_API_KEY (required), TELEGRAM_BOT_TOKEN/CHAT_ID (optional)

# 3. Build the image (one-time, ~1 minute)
docker compose build

# 4. Run commands — same CLI flags as native, just prefixed
docker compose run --rm agent --dry-run
docker compose run --rm agent --fixture tests/fixtures/sberbank_demo.json
docker compose run --rm agent                 # live run
docker compose run --rm agent -v              # verbose

# 5. Run tests inside the container
docker compose run --rm --entrypoint pytest agent tests/ -v
```

### How it works

* **API keys**: your `.env` file stays on the host and is injected into the container at runtime via `env_file` in `docker-compose.yml`. Keys are never baked into the image.
* **Configs (`config/feeds.yaml`, `config/tickers.yaml`)**: mounted as a volume, so edits take effect on the next run — **no rebuild needed**.
* **SQLite database (`data/signals.db`)**: persisted on the host via a volume mount, so signals survive between runs.
* **Rebuild the image** only when you change `requirements.txt` or `src/` code:

  ```bash
  docker compose build
  ```

### Inspect the signals database

```bash
sqlite3 data/signals.db "SELECT ticker, event_type, action, confidence FROM signals ORDER BY created_at DESC LIMIT 20;"
```

---

# Project Status

Current stage: **Milestone 3 — implementation complete, tests passing**

The full deterministic pipeline is built and tested: ingestion, dedup, entity linking, LLM classification/impact (DVF), validation, SQLite storage, Telegram notification, and MOEX ISS evaluation.
