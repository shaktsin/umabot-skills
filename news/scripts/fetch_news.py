#!/usr/bin/env python3
"""Fetch latest news from Google News via SerpAPI."""
from __future__ import annotations

from common import emit_error, emit_ok, get_api_key, load_request

# Google News encoded topic tokens (locale: en/us)
TOPIC_TOKENS = {
    "us": "CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE",
    "world": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
    "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
    "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
    "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlnQVAB",
    "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
    "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB",
    "health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ",
}


def fetch_topic(api_key: str, topic_token: str, country: str, language: str, limit: int) -> list[dict]:
    """Fetch news for a Google News topic tab."""
    from serpapi import GoogleSearch

    params = {
        "engine": "google_news",
        "topic_token": topic_token,
        "gl": country,
        "hl": language,
        "api_key": api_key,
    }
    results = GoogleSearch(params).get_dict()
    return _extract_articles(results, limit)


def fetch_query(api_key: str, query: str, country: str, language: str, limit: int) -> list[dict]:
    """Fetch news matching a search query."""
    from serpapi import GoogleSearch

    params = {
        "engine": "google_news",
        "q": query,
        "gl": country,
        "hl": language,
        "api_key": api_key,
    }
    results = GoogleSearch(params).get_dict()
    return _extract_articles(results, limit)


def _extract_articles(results: dict, limit: int) -> list[dict]:
    """Pull out the relevant fields from SerpAPI response."""
    articles = []
    news_results = results.get("news_results", [])
    for item in news_results[:limit]:
        # Google News results can have two formats:
        # 1. highlight + stories (homepage / topic feeds)
        # 2. flat title/link/source (search query results)
        highlight = item.get("highlight")
        if highlight and isinstance(highlight, dict):
            article = _parse_item(highlight)
        else:
            article = _parse_item(item)

        # If no link from primary item, try first sub-story
        stories = item.get("stories", [])
        if stories and not article["link"]:
            first = stories[0]
            fallback = _parse_item(first)
            article["title"] = fallback["title"] or article["title"]
            article["link"] = fallback["link"]
            article["source"] = fallback["source"] or article["source"]
            article["date"] = fallback["date"] or article["date"]

        if article["title"]:
            articles.append(article)
    return articles


def _parse_item(item: dict) -> dict:
    """Extract standard fields from a single news item."""
    return {
        "title": item.get("title", ""),
        "source": _get_source_name(item),
        "link": item.get("link", ""),
        "date": item.get("date", item.get("iso_date", "")),
        "snippet": item.get("snippet", ""),
    }


def _get_source_name(item: dict) -> str:
    source = item.get("source", {})
    if isinstance(source, dict):
        return source.get("name", "")
    return str(source) if source else ""


def main() -> None:
    req_input, req_cfg = load_request()
    api_key = get_api_key()

    query = str(req_input.get("query", "")).strip()
    topic = str(req_input.get("topic", "")).strip().lower()
    limit = min(max(int(req_input.get("limit", 10)), 1), 20)
    country = str(req_cfg.get("country", "us")).strip()
    language = str(req_cfg.get("language", "en")).strip()
    interests = str(req_cfg.get("interests", "technology,science,business")).strip()

    all_articles: list[dict] = []

    if query:
        all_articles = fetch_query(api_key, query, country, language, limit)
    elif topic:
        token = TOPIC_TOKENS.get(topic)
        if not token:
            # Unknown topic — fall back to search query
            all_articles = fetch_query(api_key, topic, country, language, limit)
        else:
            all_articles = fetch_topic(api_key, token, country, language, limit)
    else:
        # No query/topic — use configured interests
        topics = [t.strip() for t in interests.split(",") if t.strip()]
        if not topics:
            emit_error("No query, topic, or configured interests provided.")

        per_topic = max(1, limit // len(topics))
        for t in topics:
            token = TOPIC_TOKENS.get(t.lower())
            if token:
                all_articles.extend(fetch_topic(api_key, token, country, language, per_topic))
            else:
                all_articles.extend(fetch_query(api_key, t, country, language, per_topic))
        all_articles = all_articles[:limit]

    if not all_articles:
        emit_ok("No news articles found.", articles=[], count=0)
        return

    lines = []
    for a in all_articles:
        line = f"- {a['title']}"
        if a.get("source"):
            line += f" ({a['source']})"
        if a.get("date"):
            line += f" [{a['date']}]"
        if a.get("link"):
            line += f"\n  {a['link']}"
        lines.append(line)

    message = "Latest News:\n\n" + "\n".join(lines)
    emit_ok(message, articles=all_articles, count=len(all_articles))


if __name__ == "__main__":
    main()
