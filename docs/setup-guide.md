# Setup & Usage Guide

This guide walks through every step needed to run the Event-Driven Trading Signal Agent — from getting API keys to running the full pipeline.

---

## Prerequisites

- Python 3.12+ installed
- A DeepSeek account with API key (the only paid component)
- (Optional) A Telegram bot for receiving signal alerts

---

## Step 1: Install Dependencies

```bash
cd Event-Driven-Trading-Signal-Agent
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

---

## Step 2: Get Your DeepSeek API Key

1. Go to [https://platform.deepseek.com/](https://platform.deepseek.com/)
2. Sign up or log in
3. Navigate to **API Keys** in the dashboard
4. Click **Create new API key**
5. Copy the key — it looks like `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

The DeepSeek API is OpenAI-compatible, so we use the `openai` Python SDK pointed at `https://api.deepseek.com`. The model name is `deepseek-chat`.

**Cost:** With the PoC workload (small article batches), expect well under $1/month. The $20/month budget ceiling is extremely conservative.

---

## Step 3: Create a Telegram Bot (Optional)

If you want to receive signal alerts in Telegram:

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts — choose a name and username for your bot
4. BotFather will reply with a **bot token** like `7123456789:AAH...` — save this
5. Now find your **chat ID**:
   - Start a chat with your new bot (send it any message like `/start`)
   - Open this URL in a browser (replace `YOUR_BOT_TOKEN`):
     ```
     https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
     ```
   - Look for `"chat":{"id":123456789}` in the JSON response — that number is your `chat_id`

If you skip this step, the pipeline still works — signals are stored in SQLite and printed to the console, just no Telegram notifications.

---

## Step 4: Configure the `.env` File

```bash
cp .env.example .env
```

Now edit `.env` with your real values:

```ini
# REQUIRED — paste your DeepSeek key here
DEEPSEEK_API_KEY=sk-your-actual-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# OPTIONAL — paste your Telegram bot token and chat ID
# Leave the placeholder values if you don't want Telegram notifications
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789

# These defaults are fine for PoC
LLM_MODEL=deepseek-chat
CLASSIFY_MIN_CONFIDENCE=0.4
IMPACT_MIN_CONFIDENCE=0.3
LLM_TIMEOUT=30.0

# Paths (no need to change)
FEEDS_CONFIG=config/feeds.yaml
TICKERS_CONFIG=config/tickers.yaml
DB_PATH=data/signals.db
```

The `.env` file is in `.gitignore` so your keys are never committed.

---

## Step 5: Enable RSS Feeds

Edit `config/feeds.yaml` and set `enabled: true` on the feeds you want:

```yaml
feeds:
  - url: https://www.interfax.ru/rss.asp
    name: Interfax general
    enabled: true           # <-- change to true

  - url: https://tass.ru/rss/v2.xml
    name: TASS main feed
    enabled: true           # <-- change to true

  # Enable any others you want...
```

All feeds are public and free. Not every feed will have MOEX-relevant articles every day — that's normal; the pipeline filters by ticker universe.

---

## Step 6: Run the Pipeline

### Option A: Run tests first (no API key needed)

All LLM calls are mocked in tests:

```bash
python -m pytest tests/ -v
```

Expected output: `47 passed`.

### Option B: Dry run (no LLM calls, no API key needed)

Fetches feeds and resolves tickers, but doesn't call DeepSeek:

```bash
python -m src.cli --dry-run
```

Output shows which articles were found and which tickers were matched:

```
[DRY RUN] 12 articles ingested:
  [SBER] Сбербанк отчитался за первый квартал...
  [GAZP] Газпром увеличил поставки...
  [???]  Apple представила новый iPhone...
```

### Option C: Full pipeline on fixture data (needs DeepSeek key)

Uses the built-in 5-article Sberbank demo set:

```bash
python -m src.cli --fixture tests/fixtures/sberbank_demo.json
```

Expected output:

```
=== Pipeline Run Summary ===
  Ingested:        5
  Duplicates:      1
  No ticker:       0
  LLM errors:      0
  Suppressed:      0
  Emitted signals: 4
  Notify failures: 0

--- Article Details ---
  Сбербанк объявил дивиденды...                            →  emitted
  Сбербанк отчитался за первый квартал...                   →  emitted
  ...
```

If Telegram is configured, you'll also receive alerts in your chat.

### Option D: Full pipeline on live feeds (needs DeepSeek key + enabled feeds)

```bash
python -m src.cli
```

Or with verbose logging:

```bash
python -m src.cli -v
```

---

## What Happens During a Pipeline Run

```
1. Fetch RSS/Atom feeds (or load fixture JSON)
2. Normalize into Article objects
3. Deduplicate (URL + title/date hash)
4. For each unique article:
   a. Sanitize text (strip prompt injection patterns)
   b. Resolve ticker from title+summary using config/tickers.yaml
      → No match? Suppress with "no_ticker"
   c. Call DeepSeek: classify event type (DVF: try once, validate, retry if bad)
      → Invalid response? Suppress with "schema_invalid"
   d. Call DeepSeek: estimate impact direction (DVF: same pattern)
   e. Validate: confidence thresholds, ticker in universe
      → Low confidence? Suppress with "low_confidence"
   f. Save signal to SQLite (data/signals.db)
   g. Send Telegram alert (if configured)
5. Print summary
```

---

## Where Data Is Stored

| What | Location | Retention |
|---|---|---|
| Accepted signals | `data/signals.db` → `signals` table | Until you delete the DB |
| Suppressed articles | `data/signals.db` → `suppressions` table | Until you delete the DB |
| Configuration | `.env` + `config/*.yaml` | Permanent |
| Logs | stdout/stderr | Ephemeral (pipe to a file if needed) |

You can inspect the database directly:

```bash
sqlite3 data/signals.db "SELECT ticker, event_type, impact, confidence, created_at FROM signals ORDER BY created_at DESC LIMIT 10;"
```

---

## Adding Custom Tickers

Edit `config/tickers.yaml` to add companies to the universe:

```yaml
tickers:
  - ticker: SBER
    company: Sberbank
    aliases: ["Сбербанк", "Сбер", "Sberbank"]

  # Add a new one:
  - ticker: POLY
    company: Polymetal
    aliases: ["Полиметалл", "Polymetal"]
```

The entity linker does substring matching, so Russian declensions (Сбербанка, Газпрому, etc.) are handled automatically.

---

## Adding Custom RSS Feeds

Add any RSS/Atom feed URL to `config/feeds.yaml`:

```yaml
feeds:
  - url: https://your-source.ru/rss/finance.xml
    name: My custom source
    enabled: true
```

The parser handles both RSS 2.0 and Atom formats.

---

## Adjusting Confidence Thresholds

In `.env`:

```ini
# Lower = more signals (more noise). Higher = fewer signals (stricter).
CLASSIFY_MIN_CONFIDENCE=0.4    # Event must be classified with >= 40% confidence
IMPACT_MIN_CONFIDENCE=0.3      # Impact must be estimated with >= 30% confidence
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Config error: DEEPSEEK_API_KEY is not set` | Missing or empty key in `.env` | Add your real key to `.env` |
| `No enabled feeds` | All feeds have `enabled: false` | Set at least one to `true` in `config/feeds.yaml` |
| `Feed fetch failed` | RSS source is down or blocking | Try another feed, or use `--fixture` for testing |
| `0 articles ingested` | Feeds returned empty content | Normal for some feeds; try enabling more sources |
| `All articles suppressed:no_ticker` | Articles don't mention any company in your ticker universe | Add more tickers/aliases to `config/tickers.yaml` |
| Telegram alerts not arriving | Wrong token or chat_id | Re-check with the BotFather URL method above |
| `llm_timeout` on many articles | DeepSeek API slow or rate-limited | Increase `LLM_TIMEOUT` or reduce batch size |
