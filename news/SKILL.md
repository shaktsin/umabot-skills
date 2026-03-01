---
name: news
version: 1.0.0
description: Fetch latest news from Google News via SerpAPI, filtered by configured topics of interest.
allowed_tools:
  - skills.run_script
risk_level: green
triggers:
  - "news"
  - "latest news"
  - "headlines"
  - "what's happening"
  - "top stories"
  - "news update"

scripts:
  fetch:
    path: scripts/fetch_news.py
    description: Fetch latest news headlines, optionally filtered by topic or custom query.
    when:
      intents: ["get news", "latest news", "headlines", "what's happening", "news update"]
    input_schema:
      type: object
      properties:
        query: { type: string, description: "Custom search query. If omitted, uses configured topics." }
        topic:
          type: string
          description: "A preconfigured topic from interests list, or a Google News topic token (e.g. TECHNOLOGY, SPORTS, BUSINESS)."
        limit: { type: integer, minimum: 1, maximum: 20 }
      additionalProperties: false
    arg_mapping:
      query: ["query", "q", "search", "keyword"]
      topic: ["topic", "category", "section"]
    examples:
      - input:
          topic: "technology"
          limit: 5
      - input:
          query: "artificial intelligence"
      - input: {}

install_config:
  args:
    interests:
      type: string
      required: false
      default: "technology,science,business"
    country:
      type: string
      required: false
      default: "us"
    language:
      type: string
      required: false
      default: "en"
  env:
    SERPAPI_API_KEY:
      required: true
      secret: true
      default: ""

runtime:
  timeout_seconds: 30
  require_schema_validation: true
---

# News Skill

Fetches the latest news headlines from Google News using [SerpAPI](https://serpapi.com/).

## Configuration

- **interests**: Comma-separated list of topics you care about (e.g. `technology,science,AI,climate`). Used when no specific query or topic is provided.
- **country**: Two-letter country code for localized news (default: `us`).
- **language**: Two-letter language code (default: `en`).

## Environment Variables

- **SERPAPI_API_KEY** (required, secret): Your SerpAPI API key. Get one at https://serpapi.com/manage-api-key.

## Usage Examples

- "What's the latest news?" — fetches headlines for all configured interests.
- "News about AI" — searches Google News for "AI".
- "Technology headlines" — fetches the TECHNOLOGY topic feed.
