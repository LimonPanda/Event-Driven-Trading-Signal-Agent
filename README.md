# Event-Driven Trading Signal Agent

## Overview

Event-Driven Trading Signal Agent is an agent-based system that analyzes streams of financial news and corporate disclosures to detect events that may influence stock prices and convert them into structured trading signals.

The system is designed for anyone who needs to quickly identify market-moving events and evaluate their potential impact on traded assets (quantitative researchers, algorithmic trading developers, financial analysts etc.).

This repository contains a Proof-of-Concept (PoC) implementation demonstrating an end-to-end pipeline: from news ingestion to event detection, signal generation, and post-event evaluation.

---

# Problem

Financial markets react strongly to **events**, such as:

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

Analysts and traders frequently spend significant time scanning news feeds to determine:

* whether a piece of news relates to a tradable company
* whether the event is new or already known
* how important the event is
* whether it may affect the price of a particular asset

This manual process leads to:

* delays in reacting to information
* missed signals
* excessive time spent filtering irrelevant content.

---

# Project Goal

The goal of this project is to build a **PoC agent-based system** that automatically:

1. collects news from multiple sources
2. detects events related to public companies
3. links events to specific stock tickers
4. classifies the type of event
5. estimates the potential impact on price
6. generates structured trading signals

The system acts as an **event intelligence layer** between raw news data and trading research workflows.

---

# Target Users

The primary users of the system include:

* anyone interested who holds stocks
* quantitative researchers
* algorithmic trading developers
* financial analysts
* market intelligence teams

The system is intended as a **decision-support tool**, not as a fully autonomous trading system.

---

# What the PoC Demonstrates

The PoC demonstrates an end-to-end pipeline consisting of the following steps.

### 1. News Ingestion

The system collects news articles and corporate announcements from multiple sources (e.g., RSS feeds or news APIs).

### 2. Deduplication

Duplicate news items from different sources are detected and merged.

### 3. Entity Linking

The system identifies which company or ticker the news refers to.

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

Relevant signals can be delivered via a notification channel (for now Telegram bot).

### 8. Post-Event Evaluation

The system evaluates whether the detected event was followed by a meaningful price move.

---

# Out of Scope (Not Implemented in PoC)

The following features are **explicitly out of scope** for this PoC:

* full trading strategies
* advanced price prediction models
* high-frequency trading infrastructure
* ultra-low latency systems
* large-scale production data pipelines
* full market coverage

The PoC focuses specifically on **event detection and signal generation**, not on building a complete trading system.

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
/docs
    product-proposal.md
    governance.md

/src
    agents/
    pipelines/
    tools/

README.md
```

---

# Planned Technology Stack

The PoC will likely use the following stack:

* Python
* LangGraph
* LLM API
* News API / RSS feeds
* Market data API
* PostgreSQL or lightweight state storage
* Telegram Bot API for notifications

Probably final stack will include only free technologies

---

# Project Status

Current stage: **design / early PoC development**

This repository contains the initial project proposal and system design documentation.
