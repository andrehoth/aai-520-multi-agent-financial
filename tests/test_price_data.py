# tests/test_price_data.py
"""
Contract tests for the price data tool defined in tools/price_data.py.

Validates error handling behavior without making live API calls.
Run with:

    python -m pytest tests/test_price_data.py -v
"""

import pandas as pd
from unittest.mock import patch, MagicMock


def test_fetch_price_history_returns_empty_dataframe_on_failure():
    """fetch_price_history should return an empty DataFrame on API failure
    rather than raising an exception and halting the pipeline."""
    with patch("tools.price_data.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.history.side_effect = Exception("API error")
        from tools.price_data import fetch_price_history

        result = fetch_price_history("AAPL")
        assert isinstance(result, pd.DataFrame)
        assert result.empty


def test_fetch_price_summary_returns_none_values_on_failure():
    """fetch_price_summary should return a dict with None values on API failure
    rather than raising an exception and halting the pipeline."""
    with patch("tools.price_data.yf.Ticker", side_effect=Exception("API error")):
        from tools.price_data import fetch_price_summary

        result = fetch_price_summary("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["current_price"] is None
        assert result["market_cap"] is None


def test_fetch_price_summary_returns_expected_keys_on_success():
    """fetch_price_summary should return a dict with all expected keys."""
    mock_info = {
        "currentPrice": 333.69,
        "fiftyTwoWeekHigh": 345.34,
        "fiftyTwoWeekLow": 243.42,
        "averageVolume": 46000000,
        "marketCap": 4870000000000,
    }
    with patch("tools.price_data.yf.Ticker") as mock_ticker:
        mock_ticker.return_value.info = mock_info
        from tools.price_data import fetch_price_summary

        result = fetch_price_summary("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["current_price"] == 333.69
        assert result["week_52_high"] == 345.34
