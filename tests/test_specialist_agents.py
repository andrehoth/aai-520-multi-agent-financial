# tests/test_specialist_agents.py
"""
Tests for the data-availability guards and extra_context handling in the
specialist agents.

When a specialist has no data at all, it must skip the LLM call and store a
short unavailability note. Otherwise the model would be asked to analyze empty
lists, and its reply asking the user for data would be stored as the analysis
and flow into the synthesis. All fetches and LLM calls are patched, so no API
is used. Run with:

    python -m pytest tests/test_specialist_agents.py -v
"""

from unittest.mock import patch, call

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


# ---------------------------------------------------------------------------
# Data-availability guard tests (unchanged behavior)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# extra_context tests
# ---------------------------------------------------------------------------

def test_earnings_analyzer_includes_extra_context_in_prompt():
    """When extra_context is provided, the LLM prompt must include the routed
    article text so the specialist can incorporate it into its analysis."""
    agent = EarningsAnalyzer("AAPL")
    extra = "Apple beat Q3 EPS estimates by 15%, reporting $2.10 vs $1.83 expected."

    with patch("agents.earnings_agent.fetch_earnings",
               return_value=[{"fiscalDateEnding": "2026-06-30"}]), \
         patch("agents.earnings_agent.fetch_income_statement", return_value=[]), \
         patch.object(agent, "call", return_value="analysis text") as mock_call:
        agent.run(empty_analysis("AAPL"), extra_context=extra)

    # Confirm the extra context text reached the prompt passed to call()
    prompt_used = mock_call.call_args[0][0]
    assert extra in prompt_used


def test_earnings_analyzer_omits_extra_context_section_when_empty():
    """When extra_context is empty (the default), the prompt must not include
    the extra context label, keeping the prompt identical to the pre-routing
    behavior."""
    agent = EarningsAnalyzer("AAPL")

    with patch("agents.earnings_agent.fetch_earnings",
               return_value=[{"fiscalDateEnding": "2026-06-30"}]), \
         patch("agents.earnings_agent.fetch_income_statement", return_value=[]), \
         patch.object(agent, "call", return_value="analysis text") as mock_call:
        agent.run(empty_analysis("AAPL"))

    prompt_used = mock_call.call_args[0][0]
    assert "Related Earnings News" not in prompt_used


def test_market_analyzer_includes_extra_context_in_prompt():
    """When extra_context is provided, the LLM prompt must include the routed
    article text so the specialist can incorporate it into its analysis."""
    prices = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5], "Volume": [100]}
    )
    agent = MarketAnalyzer("AAPL")
    extra = "The Federal Reserve signaled a rate cut may come in Q4 2026."

    with patch("agents.market_agent.fetch_price_history", return_value=prices), \
         patch("agents.market_agent.fetch_price_summary", return_value=dict(EMPTY_SUMMARY)), \
         patch("agents.market_agent.fetch_macro_indicators", return_value=dict(EMPTY_MACRO)), \
         patch.object(agent, "call", return_value="analysis text") as mock_call:
        agent.run(empty_analysis("AAPL"), extra_context=extra)

    prompt_used = mock_call.call_args[0][0]
    assert extra in prompt_used


def test_market_analyzer_omits_extra_context_section_when_empty():
    """When extra_context is empty (the default), the prompt must not include
    the extra context label, keeping the prompt identical to the pre-routing
    behavior."""
    prices = pd.DataFrame(
        {"Open": [1.0], "High": [2.0], "Low": [0.5], "Close": [1.5], "Volume": [100]}
    )
    agent = MarketAnalyzer("AAPL")

    with patch("agents.market_agent.fetch_price_history", return_value=prices), \
         patch("agents.market_agent.fetch_price_summary", return_value=dict(EMPTY_SUMMARY)), \
         patch("agents.market_agent.fetch_macro_indicators", return_value=dict(EMPTY_MACRO)), \
         patch.object(agent, "call", return_value="analysis text") as mock_call:
        agent.run(empty_analysis("AAPL"))

    prompt_used = mock_call.call_args[0][0]
    assert "Related Market and Macro News" not in prompt_used


def test_earnings_analyzer_skips_llm_even_with_extra_context_when_no_data():
    """extra_context must not bypass the data-availability guard. If no
    structured data is available, the LLM call is still skipped even when
    extra_context is provided."""
    agent = EarningsAnalyzer("AAPL")
    extra = "Apple beat Q3 EPS estimates by 15%."

    with patch("agents.earnings_agent.fetch_earnings", return_value=[]), \
         patch("agents.earnings_agent.fetch_income_statement", return_value=[]), \
         patch.object(agent, "call") as mock_call:
        result = agent.run(empty_analysis("AAPL"), extra_context=extra)

    mock_call.assert_not_called()
    assert "unavailable" in result["earnings_analysis"]
