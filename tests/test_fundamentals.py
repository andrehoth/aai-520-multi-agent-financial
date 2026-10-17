# tests/test_fundamentals.py
"""
Contract tests for the fundamentals tool defined in tools/fundamentals.py.

Validates error handling behavior without making live API calls.
Run with:

    python -m pytest tests/test_fundamentals.py -v
"""

from unittest.mock import patch, MagicMock


def test_fetch_earnings_returns_empty_list_on_api_failure():
    """fetch_earnings should return an empty list on API failure rather than
    raising an exception and halting the pipeline."""
    with patch("tools.fundamentals.requests.get", side_effect=Exception("API error")):
        from tools.fundamentals import fetch_earnings

        result = fetch_earnings("AAPL", api_key="test_key")
        assert result == []


def test_fetch_income_statement_returns_empty_list_on_api_failure():
    """fetch_income_statement should return an empty list on API failure rather
    than raising an exception and halting the pipeline."""
    with patch("tools.fundamentals.requests.get", side_effect=Exception("API error")):
        from tools.fundamentals import fetch_income_statement

        result = fetch_income_statement("AAPL", api_key="test_key")
        assert result == []


def test_fetch_earnings_returns_list_on_success():
    """fetch_earnings should return a list of quarterly earnings dicts."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
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
    mock_response.raise_for_status.return_value = None
    with patch("tools.fundamentals.requests.get", return_value=mock_response):
        from tools.fundamentals import fetch_earnings

        result = fetch_earnings("AAPL", api_key="test_key", quarters=1)
        assert len(result) == 1
        assert result[0]["reportedEPS"] == "2.02"


def test_fetch_income_statement_returns_expected_keys_on_success():
    """fetch_income_statement should return dicts with all expected keys."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
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
    mock_response.raise_for_status.return_value = None
    with patch("tools.fundamentals.requests.get", return_value=mock_response):
        from tools.fundamentals import fetch_income_statement

        result = fetch_income_statement("AAPL", api_key="test_key", quarters=1)
        assert len(result) == 1
        assert result[0]["totalRevenue"] == "94000000000"
        assert result[0]["fiscalDateEnding"] == "2026-06-30"
