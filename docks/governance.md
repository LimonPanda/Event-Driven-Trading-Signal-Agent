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

| Risk                                            | Probability | Impact | Detection                                | Mitigation                                                 | Residual Risk |
| ----------------------------------------------- | ----------- | ------ | ---------------------------------------- | ---------------------------------------------------------- | ------------- |
| Incorrect event classification by LLM           | Medium      | Medium | Monitoring classification outputs        | Confidence scoring and manual inspection during evaluation | Medium        |
| Incorrect ticker mapping (entity linking error) | Medium      | High   | Validation against ticker dictionary     | Deterministic ticker lookup rules and entity normalization | Medium        |
| Duplicate news generating multiple signals      | High        | Low    | Deduplication monitoring                 | Text similarity checks and clustering                      | Low           |
| False positive signals (irrelevant news)        | Medium      | Medium | Signal review logs                       | Event relevance filtering                                  | Medium        |
| Hallucinated information from LLM               | Low         | Medium | Output validation checks                 | Restrict LLM prompts and enforce structured output         | Low           |
| Prompt injection through external news text     | Low         | Medium | Input validation and prompt sanitization | Strip instructions and restrict tool access                | Low           |
| Incorrect impact prediction                     | Medium      | Low    | Post-event evaluation                    | Confidence thresholds and uncertainty labels               | Medium        |
| API failures or data source outages             | Medium      | Low    | API error monitoring                     | Retry logic and fallback sources                           | Low           |

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

Sensitive data should not be stored in logs.

---

# 4. Data Handling Policy

The system processes **publicly available financial news**.

Data sources include:

* financial news websites
* RSS feeds
* public corporate announcements

No personal data or private user information is intentionally collected or processed.

Data storage policies:

* store article metadata
* store generated signals
* store model outputs for evaluation

Full raw news text may optionally be stored for debugging but should be minimized.

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

# 6. Action Safeguards

The system does **not execute trades automatically**.

Generated signals are informational outputs intended for research or monitoring.

Safeguards include:

* no trading API integration
* no automated financial decisions
* alerts labeled as informational signals

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
