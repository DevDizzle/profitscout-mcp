# MCP Server Spec for GammaRips GPT

## 1) MCP Server Overview

*   **Server name & version:** `gammarips-mcp` v1.0.0
*   **Transport:**
    *   **SSE (Server-Sent Events):** `https://gammarips-mcp-2lshkth7qq-uc.a.run.app/sse`
    *   **POST (JSON-RPC):** `https://gammarips-mcp-2lshkth7qq-uc.a.run.app/messages`
*   **Discovery:** Standard MCP Model Context Protocol discovery via `tools/list`.
*   **Health tool:** None specific, but `get_winners_dashboard` with `limit=1` is a good connectivity check.
*   **Auth:**
    *   **Method:** API Key
    *   **Header Name:** `X-API-Key`
    *   **Token Format:** String (SHA-256 hash verified on server)
    *   **Refresh Flow:** None (static keys).
*   **Rate limits:**
    *   Global: 60 requests/minute per IP.
    *   Per-User: Dependent on subscription tier (checked via Firestore).
*   **Timeouts:** 30s default, 60s max for deep-dive tools.
*   **Data freshness:**
    *   **Options/Market Data:** End-of-Day (EOD) updates (~5 PM EST).
    *   **News/Sentiment:** Real-time (via Web Search) or Daily (via Headline analysis).
    *   **Timezone:** US/Eastern (market time).
*   **SLA:** 99.5% Availability. Latency < 2s for cached analysis; < 10s for live BigQuery aggregations.

## 2) Tool Inventory

### `get_winners_dashboard` (Maps to: `options-signals`)
*   **Purpose:** Retrieves the top daily options setups based on "High Gamma" logic (Trend + Volatility + Quality).
*   **Input Schema:**
    ```json
    {
      "limit": { "type": "integer", "default": 10, "maximum": 50 },
      "option_type": { "type": "string", "enum": ["CALL", "PUT"] },
      "min_quality": { "type": "string", "enum": ["High", "Medium", "Low"] }
    }
    ```
*   **Output Schema (Simplified):**
    ```json
    {
      "as_of": "2026-02-03",
      "signals": [
        {
          "ticker": "NVDA",
          "option_type": "CALL",
          "strike": 145.0,
          "expiration": "2026-02-21",
          "setup_quality_signal": "High",
          "stock_price_trend_signal": "Aligned",
          "volatility_comparison_signal": "Favorable",
          "weighted_score": 95, // Derived on backend
          "analysis_summary": "Strong trend alignment with low IV rank."
        }
      ]
    }
    ```

### `analyze_market_structure`
*   **Purpose:** Deep dive into options flow (Volume/OI Walls) for a specific ticker. Crucial for finding Support/Resistance levels defined by positioning.
*   **Input Schema:**
    ```json
    {
      "ticker": { "type": "string" },
      "as_of": { "type": "string", "description": "YYYY-MM-DD or 'latest'" }
    }
    ```

### `get_technical_analysis` (Maps to: `technicals`)
*   **Purpose:** Returns technical indicators (RSI, MACD, SMA), trend analysis, and key levels.
*   **Input Schema:**
    ```json
    {
      "ticker": { "type": "string" },
      "as_of": { "type": "string", "default": "latest" }
    }
    ```
*   **Output Fields:** `trend_signal`, `rsi_14`, `support_levels`, `resistance_levels`, `moving_averages`.

### `get_news_analysis` (Maps to: `news-analysis`)
*   **Purpose:** Sentiment analysis of recent headlines.
*   **Input Schema:** `{"ticker": "string", "as_of": "string"}`
*   **Output Fields:** `sentiment_score` (-1 to 1), `sentiment_label` (Bullish/Bearish), `key_catalysts`.

### `get_transcript_analysis` (Maps to: `transcript-analysis`)
*   **Purpose:** AI-generated summary of the latest Earnings Call.
*   **Input Schema:** `{"ticker": "string"}`
*   **Output Fields:** `summary_md`, `executive_sentiment`, `guidance_outlook`.

### `get_fundamental_analysis` (Maps to: `fundamentals-analysis`)
*   **Purpose:** Valuation and growth metrics.
*   **Input Schema:** `{"ticker": "string"}`
*   **Output Fields:** `pe_ratio`, `ev_to_ebitda`, `revenue_growth_yoy`, `profit_margins`.

### `get_financial_analysis` (Maps to: `financials-analysis`)
*   **Purpose:** Deep dive into Balance Sheet and Cash Flow.
*   **Input Schema:** `{"ticker": "string"}`
*   **Output Fields:** `debt_to_equity`, `free_cash_flow`, `liquidity_ratios`.

### `get_stock_analysis` (Master Tool)
*   **Purpose:** Aggregates ALL the above into a single report. Use this for "Tell me everything about AAPL".
*   **Input Schema:**
    ```json
    {
      "ticker": { "type": "string" },
      "include_sections": { "type": "array", "items": { "type": "string", "enum": ["business", "technicals", "fundamentals", "financials", "news"] } }
    }
    ```

## 3) Field Dictionary

| Field Name | Type | Notes |
| :--- | :--- | :--- |
| `setup_quality_signal` | Enum (High/Med/Low) | Proprietary ML score based on win-rate probability. |
| `volatility_comparison_signal` | Enum (Favorable/Neutral/High) | Compares current IV to historical IV (IV Rank). |
| `stock_price_trend_signal` | Enum (Aligned/Divergent) | Checks if price action supports the option direction (e.g. Price > SMA20 for CALLs). |
| `strike` | Float | The option strike price. |
| `gamma_exposure` | Float | (In Market Structure) Estimated dealer hedging flows. |
| `sentiment_score` | Float | -1.0 (Bearish) to 1.0 (Bullish). |

## 4) Authentication & Security

*   **Credentials:** Users must obtain an API Key from the GammaRips dashboard (subscription required).
*   **Header:** `X-API-Key: <your_key_here>`
*   **Security:** Keys are hashed (SHA-256) at rest.
*   **Sandboxing:** Non-prod keys available for testing (Prefix: `TEST_`).

## 5) Error Handling

*   **401 Unauthorized:** Invalid or missing API Key.
*   **402 Payment Required:** Subscription expired.
*   **404 Not Found:** Ticker not tracked or no data for date.
*   **429 Too Many Requests:** Rate limit exceeded. Retry after `Retry-After` header value.

## 6) Example End-to-End Flows

**User:** "Find me the best Call options for today."
**Assistant:** Calls `get_winners_dashboard(option_type="CALL", min_quality="High")`.

**User:** "Analyze the risk for AAPL."
**Assistant:** Calls `get_stock_analysis(ticker="AAPL", include_sections=["technicals", "news", "financials"])`.

**User:** "What are the whales doing in TSLA?"
**Assistant:** Calls `analyze_market_structure(ticker="TSLA")` to check Volume/OI walls.

## 7) Source & Attribution

*   **Source Label:** "Data provided by GammaRips Intelligence Engine."
*   **Legal:** "All signals are for educational purposes only. Options trading involves significant risk."
