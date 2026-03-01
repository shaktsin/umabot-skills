#!/usr/bin/env python3
"""Fetch finance quote data from Google Finance via SerpAPI."""
from __future__ import annotations

from typing import Any, Dict

from common import emit_error, emit_ok, get_api_key, load_request

VALID_WINDOWS = {"1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"}


def _normalize_market(market: str) -> str:
    normalized = str(market or "").strip().upper()
    # Country codes like "US" are commonly entered by mistake from the news skill.
    # Google Finance ticker queries expect an exchange code (e.g. NASDAQ), not a locale.
    if len(normalized) <= 2:
        return ""
    return normalized


def _build_search_query(*, ticker: str, query: str, market: str) -> str:
    if query:
        return query
    if not ticker:
        return ""
    if market:
        return f"{ticker}:{market}"
    return ticker


def fetch_quote(api_key: str, *, ticker: str, query: str, market: str, window: str) -> Dict[str, Any]:
    from serpapi import GoogleSearch

    search_query = _build_search_query(ticker=ticker, query=query, market=market)
    params: Dict[str, Any] = {
        "engine": "google_finance",
        "api_key": api_key,
        "q": search_query,
    }
    if window:
        params["window"] = window
    return GoogleSearch(params).get_dict()


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value).strip()
        if text:
            return text
    return ""


def _extract_summary(results: Dict[str, Any]) -> Dict[str, str]:
    summary = results.get("summary") if isinstance(results.get("summary"), dict) else {}
    markets = results.get("markets") if isinstance(results.get("markets"), dict) else {}
    movement_data = summary.get("price_movement") if isinstance(summary.get("price_movement"), dict) else {}

    price = _first_non_empty(
        summary.get("price"),
        summary.get("extracted_price"),
        summary.get("current_price"),
        summary.get("value"),
        results.get("price"),
    )
    currency = _first_non_empty(
        summary.get("currency"),
        summary.get("price_currency"),
        results.get("currency"),
    )
    movement = _first_non_empty(
        movement_data.get("movement"),
        summary.get("movement"),
        results.get("price_movement"),
    )
    change = _first_non_empty(
        movement_data.get("value"),
        summary.get("price_change"),
        summary.get("change"),
        markets.get("price_change"),
        results.get("price_change"),
    )
    percent = _first_non_empty(
        movement_data.get("percentage"),
        summary.get("price_change_percentage"),
        summary.get("percentage"),
        summary.get("change_percent"),
        results.get("price_change_percentage"),
    )
    title = _first_non_empty(
        summary.get("title"),
        summary.get("name"),
        summary.get("stock"),
        results.get("title"),
        results.get("name"),
    )
    exchange = _first_non_empty(
        summary.get("exchange"),
        summary.get("market"),
        results.get("market"),
    )
    ticker = _first_non_empty(
        summary.get("stock"),
        summary.get("ticker"),
        results.get("stock"),
        results.get("ticker"),
    )
    after_hours = summary.get("market") if isinstance(summary.get("market"), dict) else {}
    after_hours_price = _first_non_empty(
        after_hours.get("price"),
        after_hours.get("extracted_price"),
        after_hours.get("value"),
    )
    return {
        "title": title,
        "ticker": ticker,
        "exchange": exchange,
        "price": price,
        "currency": currency,
        "movement": movement,
        "change": change,
        "percent": percent,
        "after_hours_price": after_hours_price,
    }


def _extract_from_suggestions(results: Dict[str, Any]) -> Dict[str, str]:
    suggestions = results.get("suggestions")
    if not isinstance(suggestions, list) or not suggestions:
        return {}
    first = suggestions[0] if isinstance(suggestions[0], dict) else {}
    stock_ref = _first_non_empty(first.get("stock"))
    ticker = stock_ref
    exchange = ""
    if ":" in stock_ref:
        ticker, exchange = stock_ref.split(":", 1)
    movement_data = first.get("price_movement") if isinstance(first.get("price_movement"), dict) else {}
    return {
        "title": _first_non_empty(first.get("name"), first.get("title")),
        "ticker": ticker,
        "exchange": exchange,
        "price": _first_non_empty(first.get("price"), first.get("extracted_price")),
        "currency": _first_non_empty(first.get("currency")),
        "movement": _first_non_empty(movement_data.get("movement")),
        "change": _first_non_empty(movement_data.get("value")),
        "percent": _first_non_empty(movement_data.get("percentage")),
        "after_hours_price": "",
    }


def _format_message(summary: Dict[str, str], requested_window: str) -> str:
    label_parts = [part for part in [summary["title"], summary["ticker"]] if part]
    label = " ".join(label_parts).strip() or "Finance Quote"

    header = label
    if summary["exchange"]:
        header += f" ({summary['exchange']})"

    lines = [header]

    if summary["price"]:
        price_line = "Price: "
        if summary["currency"]:
            price_line += f"{summary['currency']} "
        price_line += summary["price"]
        lines.append(price_line)

    movement_bits = [part for part in [summary["movement"], summary["change"], summary["percent"]] if part]
    if movement_bits:
        lines.append(f"Move ({requested_window}): " + " | ".join(movement_bits))

    if summary["after_hours_price"]:
        lines.append(f"After hours: {summary['after_hours_price']}")

    return "\n".join(lines)


def main() -> None:
    req_input, req_cfg = load_request()
    api_key = get_api_key()

    ticker = str(req_input.get("ticker", "")).strip().upper()
    query = str(req_input.get("query", "")).strip()
    market = _normalize_market(req_input.get("market", ""))
    window = str(req_input.get("window", "")).strip().upper()

    if not market:
        market = _normalize_market(req_cfg.get("default_market", ""))
    if not window:
        window = str(req_cfg.get("default_window", "1D")).strip().upper()

    if not ticker and not query:
        emit_error("Provide a ticker or query.")

    if window and window not in VALID_WINDOWS:
        emit_error("Invalid window. Use one of: 1D, 5D, 1M, 6M, YTD, 1Y, 5Y, MAX.")

    search_query = _build_search_query(ticker=ticker, query=query, market=market)
    try:
        # Network/library errors can include request URLs; do not echo them back.
        results = fetch_quote(api_key, ticker=ticker, query=query, market=market, window=window)
    except Exception:
        emit_error("Finance lookup failed. Check network connectivity and API configuration.")
    summary = _extract_summary(results)
    if not summary["price"] and not summary["title"] and not summary["ticker"]:
        summary = _extract_from_suggestions(results) or summary

    if not summary["price"] and not summary["title"] and not summary["ticker"]:
        emit_ok("No finance quote found.", quote=summary, raw=results)
        return

    message = _format_message(summary, window or "1D")
    emit_ok(message, quote=summary, raw=results)


if __name__ == "__main__":
    main()
