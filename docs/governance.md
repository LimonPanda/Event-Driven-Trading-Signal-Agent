# Governance and Risk Management

**Event-Driven Trading Signal Agent (MOEX)**

---

# 1. Governance Overview

The Event-Driven Trading Signal Agent processes unstructured financial news to generate structured event signals for companies listed on the Moscow Exchange (MOEX).

Because the system relies on external data sources and LLM-based reasoning, it introduces several operational and model-related risks. This document describes:

* potential system risks
* mitigation strategies
* logging and monitoring policies
* safeguards against prompt injection and misuse

The system is designed as a **decision-support tool for research purposes**, not as an automated trading system.

---

# 2. Risk Register

**Scoring:** **Probability (P)** and **Impact (I)** are each rated on a **1–5** scale (1 = lowest, 5 = highest). **Risk score = P × I** (range **1–25**). Ratings are qualitative estimates for the PoC.

| Risk | P (1–5) | I (1–5) | Risk score (P×I) | Detection | Mitigation | Residual risk |
| ---- | ------- | ------- | ---------------- | --------- | ---------- | ------------- |
| Incorrect event classification by LLM | 3 | 3 | 9 | Monitoring classification outputs | Confidence scoring and manual inspection during evaluation | Medium |
| Incorrect ticker mapping (entity linking error) | 3 | 4 | 12 | Validation against ticker dictionary | Deterministic ticker lookup rules and entity normalization | Medium |
| Duplicate news generating multiple signals | 4 | 2 | 8 | Deduplication monitoring | Text similarity checks and clustering | Low |
| False positive signals (irrelevant news) | 3 | 3 | 9 | Signal review logs | Event relevance filtering | Medium |
| Hallucinated information from LLM | 2 | 3 | 6 | Output validation checks | Restrict LLM prompts and enforce structured output | Low |
| Prompt injection through external news text | 2 | 3 | 6 | Input validation and prompt sanitization | Strip instructions and restrict tool access | Low |
| Incorrect impact prediction | 3 | 2 | 6 | Post-event evaluation | Confidence thresholds and uncertainty labels | Medium |
| API failures or data source outages | 3 | 2 | 6 | API error monitoring | Retry logic and fallback sources | Low |

---

# 3. Logging Policy

The system maintains structured logs to ensure traceability and facilitate debugging.

The following events should be logged:

**News ingestion logs**

* source
* timestamp
* article ID

**Processing logs**

* event classification result
* detected entities
* impact classification
* confidence score

**System logs**

* API failures
* parsing errors
* agent execution steps

Logs should include timestamps and identifiers to enable event reconstruction during debugging or evaluation.

**Retention:** application and processing **logs are retained for 30 days**, then **deleted** (or rotated off) unless a shorter period is required by the host environment.

Sensitive data should not be stored in logs (see **§4**).

---

# 4. Data Handling Policy

The system processes **publicly available financial news**.

Data sources include:

* financial news websites
* RSS feeds
* public corporate announcements

The PoC does **not** implement a separate product that collects end-user profiles; **operator-chosen** configuration (e.g. Telegram `chat_id`) is not treated as “news PII” but must be kept out of public logs.

**External APIs (PoC):** the only **paid** external API expected in PoC is the **LLM provider (DeepSeek)**. News ingestion uses **free RSS/Atom feeds**; market evaluation uses **MOEX ISS** public interfaces without a commercial data subscription where applicable; **Telegram Bot API** has no per-call fee.

## 4.1 Retention (PoC)

| Data class | Retention |
| ---------- | --------- |
| Application and processing **logs** | **30 days**, then deletion |
| **Full raw article text** (if stored at all for debugging) | **30 days maximum**, then **deleted**; prefer processing in memory and storing only short excerpts + hashes where possible |
| **Structured signals** and **article metadata** (title, URL, source, timestamp, ticker, labels) | **90 days** for PoC evaluation and reproducibility, then review for deletion or export |
| **Model outputs** retained for evals | Same as signals **or** 90 days, whichever policy the team fixes for the run; default **90 days** |

If raw text storage is disabled, the table still applies to any transient buffers and log payloads.

## 4.2 Names and related content in news (PII-adjacent)

Responses from news APIs and RSS bodies may include **personal names** (e.g. journalists, executives, officials) and **quotes**. This is **third-party content**, not user-supplied PII.

Handling for the PoC:

* **No PII enrichment** — the system does not look up or merge external databases of individuals.
* **LLM use** — article text may be sent to the LLM **only for event extraction and classification**; prompts should not ask the model to retain or infer sensitive attributes unrelated to the market event.
* **Stored signals** — persist **tickers, event type, impact, confidence, source URL, title, timestamps**; **avoid storing person names in the long-lived signal record** unless needed for a specific audit sample (if stored, apply the same **90-day** review/deletion cycle).
* **Logs** — **metadata-first** logging (IDs, URLs, tickers); **do not log full article bodies** in production-style logs; redact obvious name-heavy snippets if they must appear in debug traces.

## 4.3 Access control (PoC)

* **No multi-user authentication** — the PoC is a single-tenant pipeline plus notifier, not a shared SaaS product.
* **Telegram bot** — inbound updates are ignored for command-style trading actions; outbound alerts go **only** to a **configured allowlisted `chat_id`**. The bot token and `chat_id` live in **private config** (e.g. environment variables), not in the repository.

---

# 5. Prompt Injection Protection

External news content is considered **untrusted input**.

Prompt injection attacks may attempt to manipulate LLM behavior through malicious instructions embedded in text.

Example malicious content:

* instructions such as "ignore previous instructions"
* attempts to extract system prompts
* attempts to trigger unintended tool usage

Mitigation strategies include:

**Prompt isolation**

User or external text is never inserted directly into system prompts without context.

**Instruction stripping**

Potential instructions embedded in input text are removed or ignored.

**Tool access restriction**

LLMs do not have direct access to system tools or external APIs.

All tool calls are mediated by deterministic code.

---

# 6. Action Safeguards and User Interaction

The system does **not execute trades automatically**.

Generated signals are **read-only** informational outputs: they describe a detected event and are delivered (e.g. via Telegram) for human review. **The user cannot initiate trades, orders, bank transfers, or any other operational or financial action through the PoC.** There is **no command surface** in the Telegram bot (or elsewhere in the PoC) that would invoke trading APIs, move funds, or mutate external systems—**outbound notifications only** to the allowlisted `chat_id`.

Safeguards include:

* no trading API integration
* no automated financial decisions
* alerts labeled as informational signals
* ignore or reject inbound bot commands that imply execution (if the Telegram integration receives updates at all)

This reduces the risk of unintended financial consequences.

---

# 7. Monitoring and Evaluation

System performance is evaluated through:

* signal precision
* classification accuracy
* duplicate detection rate
* post-event price reaction analysis

Periodic evaluation helps identify systematic errors and improve agent prompts or models.

---

# 8. Future Governance Considerations

If the system were deployed in a production environment, additional safeguards would be required:

* stricter monitoring infrastructure
* human-in-the-loop validation
* stronger data source verification
* model auditing and version control
* automated anomaly detection

These measures are beyond the scope of the current PoC but should be considered in future iterations.
