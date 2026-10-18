# tests/test_fundamentals.py
"""
Contract tests for the fundamentals tool defined in tools/fundamentals.py.

Validates error handling, API key redaction, and session caching without making
live API calls. Run with:

    python -m pytest tests/test_fundamentals.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

from tools import fundamentals
from tools.fundamentals import clear_cache, fetch_earnings, fetch_income_statement

API_KEY = "TESTKEY123456"

# Mirrors the shape of Alpha Vantage's real quota message, which echoes the key
RATE_LIMIT_MESSAGE = (
    f"We have detected your API key as {API_KEY} and our standard API rate "
    "limit is 25 requests per day. Please subscribe to any of the premium plans."
)

EARNINGS_PAYLOAD = {
    "quarterlyEarnings": [
        {
            "fiscalDateEnding": "2026-06-30",
            "reportedEPS": "2.02",
            "estimatedEPS": "1.88",
            "surprise": "0.14",
            "surprisePercentage": "7.4468",
        }
    ]
}


@pytest.fixture(autouse=True)
def isolate_module_state(monkeypatch):
    """Start every test with an empty session cache and a reset request timer,
    and record sleeps instead of waiting, so tests are independent and fast.
    The fixture yields the list of requested sleep durations."""
    clear_cache()
    fundamentals._last_request_time = 0.0
    sleeps = []
    monkeypatch.setattr("tools.fundamentals.time.sleep", sleeps.append)
    yield sleeps
    clear_cache()


def mock_response(payload):
    """Build a stand-in for a requests response that returns the given JSON."""
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_fetch_earnings_returns_empty_list_on_api_failure():
    """fetch_earnings should return an empty list on API failure rather than
    raising an exception and halting the pipeline."""
    with patch("tools.fundamentals.requests.get", side_effect=Exception("API error")):
        assert fetch_earnings("AAPL", api_key=API_KEY) == []


def test_fetch_income_statement_returns_empty_list_on_api_failure():
    """fetch_income_statement should return an empty list on API failure rather
    than raising an exception and halting the pipeline."""
    with patch("tools.fundamentals.requests.get", side_effect=Exception("API error")):
        assert fetch_income_statement("AAPL", api_key=API_KEY) == []


def test_fetch_earnings_returns_list_on_success():
    """fetch_earnings should return a list of quarterly earnings dicts."""
    with patch("tools.fundamentals.requests.get",
               return_value=mock_response(EARNINGS_PAYLOAD)):
        result = fetch_earnings("AAPL", api_key=API_KEY, quarters=1)

    assert len(result) == 1
    assert result[0]["reportedEPS"] == "2.02"


def test_fetch_income_statement_returns_expected_keys_on_success():
    """fetch_income_statement should return dicts with all expected keys."""
    payload = {
        "quarterlyReports": [
            {
                "fiscalDateEnding": "2026-06-30",
                "totalRevenue": "94000000000",
                "grossProfit": "43000000000",
                "operatingIncome": "29000000000",
                "netIncome": "25000000000",
            }
        ]
    }
    with patch("tools.fundamentals.requests.get", return_value=mock_response(payload)):
        result = fetch_income_statement("AAPL", api_key=API_KEY, quarters=1)

    assert len(result) == 1
    assert result[0]["totalRevenue"] == "94000000000"
    assert result[0]["fiscalDateEnding"] == "2026-06-30"


def test_quota_message_is_reported_and_key_is_redacted(capsys):
    """Alpha Vantage reports an exhausted quota as HTTP 200 with a message and
    no data. The tool should return an empty list, show the reason, and keep the
    API key out of the printed output."""
    response = mock_response({"Information": RATE_LIMIT_MESSAGE})
    with patch("tools.fundamentals.requests.get", return_value=response):
        result = fetch_earnings("AAPL", api_key=API_KEY)

    output = capsys.readouterr().out
    assert result == []
    assert "rate limit" in output
    assert "[redacted]" in output
    assert API_KEY not in output


def test_exception_text_does_not_leak_api_key(capsys):
    """requests exceptions include the full request URL, so the warning must
    redact the key from the exception text."""
    error = Exception(
        f"Max retries exceeded with url: /query?function=EARNINGS&apikey={API_KEY}"
    )
    with patch("tools.fundamentals.requests.get", side_effect=error):
        result = fetch_earnings("AAPL", api_key=API_KEY)

    output = capsys.readouterr().out
    assert result == []
    assert "fetch failed" in output
    assert API_KEY not in output


def test_successful_results_are_cached_and_isolated():
    """A second call for the same data should not hit the API, and changing a
    returned result must not change what later calls receive."""
    response = mock_response(EARNINGS_PAYLOAD)
    with patch("tools.fundamentals.requests.get", return_value=response) as mock_get:
        first = fetch_earnings("AAPL", api_key=API_KEY, quarters=1)
        second = fetch_earnings("AAPL", api_key=API_KEY, quarters=1)
        first[0]["reportedEPS"] = "changed"
        third = fetch_earnings("AAPL", api_key=API_KEY, quarters=1)

    assert mock_get.call_count == 1
    assert second == third
    assert third[0]["reportedEPS"] == "2.02"


def test_empty_results_are_not_cached():
    """A rate-limited call must be retried on the next request, not frozen as an
    empty answer for the rest of the session."""
    limited = mock_response({"Information": RATE_LIMIT_MESSAGE})
    recovered = mock_response(EARNINGS_PAYLOAD)
    with patch("tools.fundamentals.requests.get",
               side_effect=[limited, recovered]) as mock_get:
        first = fetch_earnings("AAPL", api_key=API_KEY, quarters=1)
        second = fetch_earnings("AAPL", api_key=API_KEY, quarters=1)

    assert first == []
    assert len(second) == 1
    assert mock_get.call_count == 2


def test_back_to_back_requests_are_spaced_for_the_burst_limit(isolate_module_state):
    """The free tier allows 1 request per second, and the earnings and income
    statement calls run back to back, so the second must wait."""
    response = mock_response(EARNINGS_PAYLOAD)
    # Two monotonic() reads per request; the second request starts 0.2s after
    # the first, so it must wait about 1.0s to reach the 1.2s spacing.
    clock = [100.0, 100.0, 100.2, 101.2]
    with patch("tools.fundamentals.requests.get", return_value=response), \
         patch("tools.fundamentals.time.monotonic", side_effect=clock):
        fetch_earnings("AAPL", api_key=API_KEY)
        fetch_income_statement("AAPL", api_key=API_KEY)

    assert len(isolate_module_state) == 1
    assert isolate_module_state[0] == pytest.approx(1.0, abs=0.05)


def test_requests_far_apart_do_not_wait(isolate_module_state):
    """No sleep is needed when enough time has already passed."""
    response = mock_response(EARNINGS_PAYLOAD)
    clock = [100.0, 100.0, 105.0, 105.0]
    with patch("tools.fundamentals.requests.get", return_value=response), \
         patch("tools.fundamentals.time.monotonic", side_effect=clock):
        fetch_earnings("AAPL", api_key=API_KEY)
        fetch_income_statement("AAPL", api_key=API_KEY)

    assert isolate_module_state == []
