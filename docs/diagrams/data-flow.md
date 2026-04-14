# Data Flow Diagram

```mermaid
flowchart LR
  RSS["RSSEntry(title,link,body,published)"] --> RawQueue["IngestionStateStore"]
  RawQueue --> Deduped["CanonicalArticleStore"]
  Deduped --> LLMIn["LLMRequestPayload"]
  LLMIn --> LLMOut["LLMStructuredOutput"]
  LLMOut --> Validator["PolicyValidator"]
  Validator -->|"accepted"| SignalStore["SignalStore"]
  Validator -->|"rejected"| RejectLog["SuppressionLog"]
  SignalStore --> Telegram["TelegramAlerts"]
  SignalStore --> EvalJob["EvaluationJobQueue"]
  EvalJob --> MoexData["MOEXISSBars"]
  MoexData --> EvalMetrics["EvalMetricsStore"]
  SignalStore --> AuditLog["ProcessingLog"]
  RejectLog --> AuditLog
```

Stored artifacts:
- ingestion metadata and dedup mappings;
- validated signals and suppression reasons;
- evaluation metrics and operational logs.

Logging policy and retention follow `docs/governance.md`.
