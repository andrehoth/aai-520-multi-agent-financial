# tests/test_specialist_agents.py
"""
Tests for the data-availability guards in the specialist agents.

When a specialist has no data at all, it must skip the LLM call and store a short
unavailability note. Otherwise the model would be asked to analyze empty lists,
and its reply asking the user for data would be stored as the analysis and flow
into the synthesis. All fetches and LLM calls are patched, so no API is used.
Run with:

    python -m pytest tests/test_specialist_agents.py -v
"""

from unittest.mock import patch

import pandas as pd

from agents.earnings_agent import EarningsAnalyzer
from agents.market_agent import MarketAnalyzer
from agents.schema import empty_analysis

EMPTY_SUMMARY = {
    "ticker": "AAPL",
    "current_price": None,
    "week_52_high": None,
    "week_52_low": None,
    "avg_volume": None,
    "market_cap": None,
}
EMPTY_MACRO = {"fed_funds_rate": [], "cpi": [], "unemployment_rate": []}


def test_earnings_analyzer_skips_llm_when_no_data():
    """With no earnings and no income data, no LLM call is made and the note
    says the data was unavailable."""
    agent = EarningsAnalyzer("AAPL")
    with patch("agents.earnings_agent.fetch_earnings", return_value=[]), \
         patch("agents.earnings_agent.fetch_income_statement", return_value=[]), \
         patch.object(agent, "call") as mock_call:
        result = agent.run(empty_analysis("AAPL"))

    mock_call.assert_not_called()
    assert "unavailable" in result["earnings_analysis"]


def test_earnings_analyzer_calls_llm_when_some_data_exists():
    """If only one dataset is missing, the LLM is still asked to analyze the
    data that exists."""
    agent = EarningsAnalyzer("AAPL")
    with patch("agents.earnings_agent.fetch_earnings",
               return_value=[{"fiscalDateEnding": "2026-06-30"}]), \
         patch("agents.earnings_agent.fetch_income_statement", return_value=[]), \
         patch.object(agent, "call", return_value="analysis text") as mock_call:
        result = agent.run(empty_analysis("AAPL"))

    mock_call.assert_called_once()
    assert result["earnings_analysis"] == "analysis text"


def test_market_analyzer_skips_llm_when_no_data():
    """With no price data and no macro data, no LLM call is made and the note
    says the data was unavailable."""
    agent = MarketAnalyzer("AAPL")
    with patch("agents.market_agent.fetch_price_history", return_value=pd.DataFrame()), \
         patch("agents.market_agent.fetch_price_summary", return_value=dict(EMPTY_SUMMARY)), \
         patch("agents.market_agent.fetch_macro_indicators", return_value=dict(EMPTY_MACRO)), \
         patch.object(agent, "call") as mock_call:
        result = agent.run(empty_analysis("AAPL"))

    mock_call.assert_not_called()
    assert "unavailable" in result["market_analysis"]


def test_market_analyzer_calls_llm_when_some_data_exists():
    """If prices are available but macro data is not, the LLM is still asked to
    analyze what exists."""
    prices = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5], "Volume": [100]}
    )
    agent = MarketAnalyzer("AAPL")
    with patch("agents.market_agent.fetch_price_history", return_value=prices), \
         patch("agents.market_agent.fetch_price_summary", return_value=dict(EMPTY_SUMMARY)), \
         patch("agents.market_agent.fetch_macro_indicators", return_value=dict(EMPTY_MACRO)), \
         patch.object(agent, "call", return_value="analysis text") as mock_call:
        result = agent.run(empty_analysis("AAPL"))

    mock_call.assert_called_once()
    assert result["market_analysis"] == "analysis text"
