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

The system collects news articles and corporate announcements from multiple sources (e.g., RSS feeds or news APIs) focused on Russian financial news and MOEX-relevant issuers.

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
/config
    feeds.yaml

/docs
    product-proposal.md
    governance.md

/src
    agents/
    pipelines/
    tools/
        rss_feeds.py
        moex_iss.py
        deepseek_client.py

/tests
    fixtures/
    test_rss_fixture.py

requirements.txt
README.md
```

---

# Planned Technology Stack

The PoC will likely use the following stack:

* Python
* LangGraph
* **DeepSeek API** (via **OpenAI-compatible** client — see [docs/product-proposal.md](docs/product-proposal.md) §4.2)
* **News:** **RSS/Atom feeds** only (allowlisted URLs in `config/feeds.yaml`; no paid news API)
* **Prices / evaluation:** **MOEX ISS** (public HTTPS API, no key for standard PoC usage)
* PostgreSQL or lightweight state storage
* Telegram Bot API for notifications (no API fee)

**Cost profile:** no paid external APIs except **DeepSeek**; RSS, MOEX ISS, and Telegram Bot API are $0 at API level (hosting only).

---

# Project Status

Current stage: **design / early PoC development**

This repository contains the initial project proposal and system design documentation.
