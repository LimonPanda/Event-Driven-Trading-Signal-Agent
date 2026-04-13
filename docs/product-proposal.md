# Product Proposal

**Event-Driven Trading Signal Agent for the Russian Equity Market**

---

# 1. Problem Statement

The Russian equity market reacts strongly to **corporate and macroeconomic events**, including:

* earnings releases
* dividend announcements
* sanctions and geopolitical developments
* regulatory decisions
* mergers and acquisitions
* management changes

These events are typically reported through **unstructured text sources**, such as financial news articles, press releases, and corporate disclosures.

For analysts and quantitative researchers working with stocks listed on the **Moscow Exchange (MOEX)**, quickly identifying market-relevant events is critical. However, the current workflow has several challenges:

* News arrives from multiple heterogeneous sources.
* The news stream contains duplicates and irrelevant articles.
* Mapping textual mentions to specific stock tickers requires manual interpretation.
* Evaluating the potential market impact of events takes time.

As a result, analysts often spend significant effort manually scanning news feeds to identify events that may affect stock prices.

This project proposes a **Proof-of-Concept (PoC) agent-based system** that automatically processes financial news related to companies listed on the **Moscow Exchange** and converts relevant events into structured trading signals.

The system acts as an **event intelligence layer** between raw news data and trading research workflows.

---

# 2. Project Goals and Success Metrics

## 2.1 Project Goal

The goal of the project is to design and implement a PoC agent system that:

1. Collects financial news related to Russian public companies
2. Detects corporate or macroeconomic events described in the news
3. Links the event to specific companies and MOEX tickers
4. Classifies the type of event
5. Estimates the potential impact on stock prices
6. Generates structured event signals for downstream analysis

The system focuses on companies listed on the **Moscow Exchange**, such as:

* Sberbank (SBER)
* Gazprom (GAZP)
* Lukoil (LKOH)
* Yandex (YNDX / external listings)
* Norilsk Nickel (GMKN)

---

## 2.2 Product Metrics

Product metrics measure whether the system provides useful signals for analysts.

**Signal Precision**

Share of generated signals that correspond to meaningful market events.

**Event Coverage**

Number of detected events relative to manually observed events.

**Duplicate Filtering Rate**

Percentage of duplicate news articles correctly detected and merged.

**PoC targets (fixed evaluation set)**

Metrics below are measured against a **manually labeled evaluation set** of news articles for the chosen MOEX universe (same methodology for interim and final PoC review).

* **Signal Precision > 70%** — among emitted signals, the share that match a human-judged market-relevant event for the linked ticker.
* **Event Coverage > 80%** — among human-identified market-relevant events in the evaluation set, the share the system surfaces as at least one signal (after deduplication).

---

## 2.3 Agent / Model Metrics

These metrics evaluate the performance of LLM-based components.

**Event Classification Accuracy**

Accuracy of identifying event types such as:

* earnings release
* dividend announcement
* sanctions
* government regulation
* corporate restructuring

**PoC baseline (held-out test set)**

* **Event Classification Accuracy > 75%** on a **test set of 50 articles** with gold labels for event type (articles disjoint from training/prompt-tuning material where applicable).

**Entity Linking Accuracy**

Correct mapping between company mentions and MOEX tickers.

**Impact Classification Accuracy**

Accuracy of predicted event impact:

* positive
* negative
* neutral
* uncertain

---

## 2.4 Technical Metrics

Technical metrics measure system performance.

**Latency**

Time between receiving a news article and generating a signal.

Target for PoC:

* p95 latency < 30 seconds

**Processing Throughput**

Number of articles processed per minute.

**Deduplication Efficiency**

Ability to detect duplicate articles from different news sources.

**Availability (PoC SLO)**

During the **PoC evaluation and testing window**, the pipeline (ingestion through signal generation) and the **Telegram notifier** should be **available ≥ 95%** of the time. “Up” means the service can process a test article batch and deliver alerts; this is not an HFT or production SLA.

---

# 3. Usage Scenarios

## 3.0 Demo path (concrete)

Aligned with the live demo narrative:

1. Ingest **five news articles about Sberbank**, including overlapping coverage from multiple outlets.
2. **Deduplication** collapses syndicated items into one logical story where appropriate.
3. The pipeline detects **one market-relevant event**, maps it to **SBER**, classifies event type and impact, and builds a **structured signal**.
4. The signal is sent to **Telegram** as a **read-only** notification to a configured chat (no user-triggered trades or actions).

## 3.1 Basic Scenario

1. A new article appears in a financial news feed.
2. The system ingests the article.
3. Duplicate detection is performed.
4. The system identifies whether the article contains a market-relevant event.
5. The company mentioned in the article is mapped to a MOEX ticker.
6. The event type is classified.
7. The system estimates the potential market impact.
8. A structured signal is generated.

Example output:

```id="moexsignal"
Ticker: SBER  
Event: dividend announcement  
Expected impact: positive  
Confidence: 0.74  
Source: Interfax
```

---

## 3.2 Scenario: Duplicate News

Financial news is often syndicated across multiple sources.

Example:

* Interfax publishes a story.
* The same story appears on RBC.
* Several aggregator websites repost the article.

The system should detect duplicates and generate **a single signal for the event**.

---

## 3.3 Scenario: Ambiguous Company Mentions

Russian financial news often refers to companies using different naming conventions.

Examples:

* "Сбер"
* "Сбербанк"
* "Sberbank"

The system must correctly map these references to the ticker **SBER**.

---

## 3.4 Scenario: Non-Market-Relevant News

Some articles mention companies but contain no price-relevant events.

Examples:

* product announcements
* general commentary
* interviews
* minor operational updates

The system should filter out such articles.

---

## 3.5 Scenario: Conflicting Information

Different sources may report inconsistent information.

Example:

* one article reports that dividends may increase
* another source reports that the decision is still under discussion

The system should mark such signals with **lower confidence**.

---

# 4. Constraints

## 4.1 Technical Constraints

This system is implemented as a **PoC prototype** and therefore has several limitations.

**Latency**

The system does not aim to provide ultra-low latency suitable for high-frequency trading.

Target latency:

* p95 < 30 seconds per processed article

**Scalability**

The PoC processes a limited set of sources and tickers.

**Model Dependence**

Some modules rely on LLM reasoning, which may introduce non-deterministic behavior.

**Availability**

Same as **§2.4**: target **≥ 95% uptime** during the PoC testing window for the processing pipeline and Telegram delivery path.

---

## 4.2 Operational Constraints

**Budget and external APIs (PoC)**

* **News — no paid news API.** Ingestion uses **RSS and Atom feeds only** from an **allowlisted** set of feed URLs maintained in repo config (see `config/feeds.yaml`). The team verifies that each feed is **publicly available** and used **according to publisher terms** (no paywalled scraping, no credential-gated APIs in PoC).
* **Market data — MOEX ISS, no key.** Post-event evaluation uses the **MOEX Informational & Statistical Server (ISS)** over HTTPS for **historical candles / settlement prices** as documented at [MOEX ISS reference](https://iss.moex.com/iss/reference/). Standard ISS access is used **without a commercial data subscription** where applicable; responses are **cached** to limit request volume.
* **LLM — DeepSeek only (paid component).** Semantic stages call the **DeepSeek API** through an **OpenAI-compatible** HTTP client (base URL and model name from environment). **LLM cost is bounded by PoC volume** (small ticker universe, truncated article text, batched calls) within the operator’s **existing DeepSeek plan** — no separate OpenAI or third-party LLM budget line in PoC.
* **Telegram — no API fee.** The Telegram Bot API is free; operational cost is **hosting only** (local machine or a free-tier host).

**Feed strategy (examples of what the allowlist may include)**

* Major Russian financial publishers **if** they publish a public RSS/Atom URL the team can rely on for the demo window.
* **Topic or section feeds** (e.g. “economy” / “companies”) rather than site-wide firehoses where that improves signal density for MOEX names.
* **Operational hygiene:** polite `User-Agent`, **per-domain rate limits**, and **ETag / If-Modified-Since** when supported.

**Scope**

The PoC will focus on a limited subset of MOEX tickers (e.g., 10–20 large-cap stocks).

## 4.3 Data source and coverage limitations

* **RSS coverage is incomplete** relative to “all news that could move a stock.” **Event Coverage** and related product metrics are measured **conditional on articles that entered the configured feeds**, not on the full market information set.
* **ISS granularity** (e.g. daily or coarse intraday bars, depending on engine and instrument) limits how finely the PoC can align price moves to headline timestamps; ultra-low-latency or tick-level evaluation is out of scope without paid market data.
* **Terms of use** must be respected for each feed and for MOEX interfaces; the PoC does not rely on circumventing paywalls or terms.

---

# 5. High-Level System Architecture

The system is implemented as a pipeline of agents and deterministic components.

Main modules include:

1. **News Ingestion Agent**

Collects financial news related to Russian companies from **allowlisted RSS/Atom feeds** (`config/feeds.yaml`); **no paid news API** in PoC.

2. **Deduplication Module**

Detects duplicate articles across different news sources.

3. **Entity Linking Agent**

Identifies company mentions and maps them to MOEX tickers.

4. **Event Classification Agent**

Determines the type of event described in the article.

5. **Impact Estimation Agent**

Estimates the potential market impact.

6. **Signal Generation Module**

Produces a structured event signal.

7. **Telegram Notification Bot**

Sends **read-only** structured alerts to a **single allowlisted `chat_id`** via the Telegram Bot API. Implements outbound notifications only; users cannot invoke trading or operational tools through the bot in the PoC (see [governance.md](governance.md)).

8. **Evaluation Module**

Analyzes price reactions after the event using **MOEX ISS** historical prices (cached).

---

# 6. Data Flow

The simplified system data flow:

```id="moexflow"
Russian News Sources
(RBC / Interfax / TASS / RSS)
        ↓
News Ingestion Agent
        ↓
Deduplication
        ↓
Entity Linking Agent
        ↓
Event Classification Agent
        ↓
Impact Estimation Agent
        ↓
Signal Generation
        ↓
Signal Storage
        ↓
Telegram Bot → allowlisted chat (read-only alerts)
        ↓
Market Data API (MOEX prices)
        ↓
Post-Event Evaluation
```

---

# 7. LLM vs Deterministic Components

The system uses LLM reasoning only for tasks that require semantic understanding.

## LLM Components

The PoC uses **DeepSeek** through an OpenAI-compatible API for:

* event detection
* event classification
* impact estimation
* resolving ambiguous company mentions

---

## Deterministic Components

Deterministic logic is used for:

* news ingestion
* deduplication
* ticker mapping
* signal storage
* **Telegram delivery** (formatting, allowlist `chat_id`, retries)
* market data retrieval

These tasks require predictable behavior and reliability.

---

# 8. Expected Outcome

The PoC should demonstrate that an agent-based system can:

* automatically ingest Russian financial news
* detect market-relevant events affecting MOEX-listed companies
* convert unstructured news into structured signals
* provide interpretable outputs for analysts

The system can serve as a prototype for **event-driven market intelligence tools for the Russian equity market**.
