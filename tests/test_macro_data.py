# tests/test_macro_data.py
"""
Contract tests for the macro data tool defined in tools/macro_data.py.

Validates error handling behavior without making live API calls.
Run with:

    python -m pytest tests/test_macro_data.py -v
"""

from unittest.mock import patch, MagicMock


def test_fetch_macro_indicators_returns_empty_lists_on_total_failure():
    """fetch_macro_indicators should return a dict with empty lists on total
    FRED client failure rather than raising an exception."""
    with patch("tools.macro_data.Fred", side_effect=Exception("API error")):
        from tools.macro_data import fetch_macro_indicators

        result = fetch_macro_indicators(api_key="test_key")
        assert result["fed_funds_rate"] == []
        assert result["cpi"] == []
        assert result["unemployment_rate"] == []


def test_fetch_macro_indicators_returns_empty_list_on_series_failure():
    """fetch_macro_indicators should return empty list for a failing series
    while still returning data for successful series."""
    mock_fred = MagicMock()
    mock_fred.get_series.side_effect = Exception("Series unavailable")

    with patch("tools.macro_data.Fred", return_value=mock_fred):
        from tools.macro_data import fetch_macro_indicators

        result = fetch_macro_indicators(api_key="test_key")
        assert result["fed_funds_rate"] == []
        assert result["cpi"] == []
        assert result["unemployment_rate"] == []


def test_fetch_macro_indicators_returns_expected_keys_on_success():
    """fetch_macro_indicators should return a dict with all three indicator keys."""
    import pandas as pd

    mock_series = pd.Series([3.75], index=pd.to_datetime(["2026-09-01"]))
    mock_fred = MagicMock()
    mock_fred.get_series.return_value = mock_series

    with patch("tools.macro_data.Fred", return_value=mock_fred):
        from tools.macro_data import fetch_macro_indicators

        result = fetch_macro_indicators(api_key="test_key")
        assert "fed_funds_rate" in result
        assert "cpi" in result
        assert "unemployment_rate" in result
        assert result["fed_funds_rate"][0]["value"] == 3.75
