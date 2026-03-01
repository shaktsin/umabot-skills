---
name: finance
version: 1.0.0
description: Fetch finance market data from Google Finance via SerpAPI, including stock price, price movement, and basic market summary for stocks or funds.
allowed_tools:
  - skills.run_script
risk_level: green
triggers:
  - "finance"
  - "stock price"
  - "market price"
  - "quote"
  - "stock quote"
  - "finance update"

scripts:
  fetch:
    path: scripts/fetch_finance.py
    description: Fetch a Google Finance quote for a ticker or company query.
    when:
      intents: ["get quote", "stock price", "market price", "finance update", "quote"]
    input_schema:
      type: object
      properties:
        ticker:
          type: string
          description: "Ticker symbol, such as AAPL, TSLA, NVDA."
        query:
          type: string
          description: "Optional natural-language company or asset query if ticker is omitted."
        market:
          type: string
          description: "Optional exchange code such as NASDAQ or NYSE."
        window:
          type: string
          description: "Optional performance window such as 1D, 5D, 1M, 6M, YTD, 1Y, 5Y, MAX."
      additionalProperties: false
    arg_mapping:
      ticker: ["ticker", "symbol", "stock", "asset"]
      query: ["query", "q", "company", "name"]
      market: ["market", "exchange"]
      window: ["window", "range", "period", "timeframe"]
    examples:
      - input:
          ticker: "AAPL"
      - input:
          ticker: "TSLA"
          market: "NASDAQ"
          window: "1M"
      - input:
          query: "S&P 500"

install_config:
  args:
    default_market:
      type: string
      required: false
      default: ""
    default_window:
      type: string
      required: false
      default: "1D"
  env:
    SERPAPI_API_KEY:
      required: true
      secret: true
      default: ""

runtime:
  timeout_seconds: 30
  require_schema_validation: true
---

# Finance Skill

Fetches finance quotes and simple market summaries from Google Finance using SerpAPI.

## Configuration

- **default_market**: Optional exchange code used when no market is provided (for example `NASDAQ`).
- **default_window**: Default chart/performance window (default: `1D`).

## Environment Variables

- **SERPAPI_API_KEY** (required, secret): Your SerpAPI API key. Get one at https://serpapi.com/manage-api-key.

## Usage Examples

- "What is AAPL stock price?" - fetches the current quote for AAPL.
- "Give me a TSLA quote for the last month" - fetches TSLA with a `1M` window.
- "Finance update for S&P 500" - searches Google Finance using a free-form query.
