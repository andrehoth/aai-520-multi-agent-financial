# tools/fundamentals.py
"""
Alpha Vantage earnings and income statement tool.

Alpha Vantage's free tier allows 25 requests per day and reports an exhausted
quota as an HTTP 200 response carrying a message instead of data, so this module
inspects the response body, prints the (redacted) message, and returns an empty
list rather than raising. Successful responses are cached for the session so a
full notebook run requests each endpoint once, and live requests are spaced to
respect the free tier's burst limit of 1 request per second.
"""

import copy
import os
import re
import time

import requests
from dotenv import load_dotenv

load_dotenv()

USING_MOCK = False

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# Session cache of successful responses, keyed by (endpoint, ticker, quarters).
# One full notebook run would otherwise request the same quarterly data many
# times against a 25-requests-per-day quota. Only non-empty results are stored,
# so a rate-limited or failed call is retried on the next request instead of
# being frozen as an empty answer. The cache lives in memory only, so each new
# Python process or kernel restart fetches live data again.
_cache: dict = {}


def clear_cache() -> None:
    """Empty the session cache (used by tests and to force a fresh fetch)."""
    _cache.clear()


# The free tier also enforces a burst limit of 1 request per second. The
# earnings and income statement calls are made back to back, so the second one
# was rejected. Live requests are spaced at least this many seconds apart (the
# margin over 1.0 covers timing jitter).
MIN_REQUEST_INTERVAL = 1.2
_last_request_time = 0.0


def _throttle() -> None:
    """Sleep long enough that consecutive live requests respect the burst limit."""
    global _last_request_time
    wait = MIN_REQUEST_INTERVAL - (time.monotonic() - _last_request_time)
    if wait > 0:
        time.sleep(wait)
    _last_request_time = time.monotonic()


def fetch_earnings(ticker: str, api_key: str = None, quarters: int = 8) -> list[dict]:
    """
    Fetch recent quarterly earnings for a given ticker via Alpha Vantage.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        api_key: Alpha Vantage key; falls back to ALPHA_VANTAGE_KEY env variable
        quarters: Number of most recent quarters to return (default 8)

    Returns:
        List of dicts with keys:
            fiscalDateEnding, reportedDate, reportedEPS, estimatedEPS,
            surprise, surprisePercentage, reportTime.
        Returns empty list on API failure or an exhausted daily quota rather
        than halting the pipeline. Successful results are cached per session.
    """
    if USING_MOCK:
        return _mock_earnings(ticker)
    return _live_earnings(ticker, api_key or os.getenv("ALPHA_VANTAGE_KEY"), quarters)


def fetch_income_statement(ticker: str, api_key: str = None, quarters: int = 8) -> list[dict]:
    """
    Fetch recent quarterly income statements for a given ticker via Alpha Vantage.

    Args:
        ticker: Stock symbol (e.g., "AAPL")
        api_key: Alpha Vantage key; falls back to ALPHA_VANTAGE_KEY env variable
        quarters: Number of most recent quarters to return (default 8)

    Returns:
        List of dicts with keys:
            fiscalDateEnding, totalRevenue, grossProfit, operatingIncome, netIncome.
        Returns empty list on API failure or an exhausted daily quota rather
        than halting the pipeline. Successful results are cached per session.
    """
    if USING_MOCK:
        return _mock_income_statement(ticker)
    return _live_income_statement(ticker, api_key or os.getenv("ALPHA_VANTAGE_KEY"), quarters)


def _redact(text, api_key: str = None) -> str:
    """
    Remove the API key from text before it is printed. Alpha Vantage echoes the
    key inside its rate-limit message, and requests exceptions include the full
    request URL, so either path could otherwise leak the key into notebook
    output that is later submitted.
    """
    text = str(text)
    if api_key:
        text = text.replace(api_key, "[redacted]")
    # Mask an echoed key even if it differs from the configured one
    text = re.sub(r"(?i)(api key as )\S+", r"\1[redacted]", text)
    text = re.sub(r"(?i)(apikey=)[^&\s]+", r"\1[redacted]", text)
    return text


def _request(function: str, ticker: str, api_key: str, label: str):
    """
    Request one Alpha Vantage endpoint.

    Returns the parsed JSON dict, or None if the request itself failed (a
    warning with the key redacted is printed in that case).
    """
    _throttle()
    try:
        response = requests.get(
            ALPHA_VANTAGE_URL,
            params={"function": function, "symbol": ticker, "apikey": api_key},
            timeout=30,  # without a timeout, requests can wait indefinitely
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}
    except Exception as e:
        print(f"      Warning: {label} fetch failed for {ticker} -- {_redact(e, api_key)}")
        return None


def _warn_no_data(label: str, ticker: str, data: dict, api_key: str) -> None:
    """
    Explain an empty result. Alpha Vantage reports quota and key problems with
    HTTP 200 and a message field, so there is no exception to catch.
    """
    message = data.get("Information") or data.get("Note") or data.get("Error Message")
    detail = f" -- {_redact(message, api_key)}" if message else ""
    print(f"      Warning: Alpha Vantage returned no {label} data for {ticker}{detail}")


def _live_earnings(ticker: str, api_key: str, quarters: int) -> list[dict]:
    """
    Returns empty list on failure rather than halting the pipeline.
    """
    cache_key = ("EARNINGS", ticker, quarters)
    if cache_key in _cache:
        return copy.deepcopy(_cache[cache_key])

    data = _request("EARNINGS", ticker, api_key, "earnings")
    if data is None:  # the request failed and a warning was already printed
        return []

    quarterly = (data.get("quarterlyEarnings") or [])[:quarters]
    if not quarterly:
        _warn_no_data("earnings", ticker, data, api_key)
        return []

    _cache[cache_key] = quarterly
    return copy.deepcopy(quarterly)


def _live_income_statement(ticker: str, api_key: str, quarters: int) -> list[dict]:
    """
    Returns empty list on failure rather than halting the pipeline.
    """
    cache_key = ("INCOME_STATEMENT", ticker, quarters)
    if cache_key in _cache:
        return copy.deepcopy(_cache[cache_key])

    data = _request("INCOME_STATEMENT", ticker, api_key, "income statement")
    if data is None:  # the request failed and a warning was already printed
        return []

    quarterly = (data.get("quarterlyReports") or [])[:quarters]
    if not quarterly:
        _warn_no_data("income statement", ticker, data, api_key)
        return []

    result = [
        {
            "fiscalDateEnding": r.get("fiscalDateEnding"),
            "totalRevenue": r.get("totalRevenue"),
            "grossProfit": r.get("grossProfit"),
            "operatingIncome": r.get("operatingIncome"),
            "netIncome": r.get("netIncome"),
        }
        for r in quarterly
    ]
    _cache[cache_key] = result
    return copy.deepcopy(result)


def _mock_earnings(ticker: str) -> list[dict]:
    return [
        {
            "fiscalDateEnding": "2026-06-30",
            "reportedDate": "2026-07-30",
            "reportedEPS": "2.02",
            "estimatedEPS": "1.88",
            "surprise": "0.14",
            "surprisePercentage": "7.4468",
            "reportTime": "post-market",
        }
    ]


def _mock_income_statement(ticker: str) -> list[dict]:
    return [
        {
            "fiscalDateEnding": "2026-06-30",
            "totalRevenue": "94000000000",
            "grossProfit": "43000000000",
            "operatingIncome": "29000000000",
            "netIncome": "25000000000",
        }
    ]
