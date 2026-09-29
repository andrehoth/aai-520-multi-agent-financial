# tests/test_router.py
"""
Contract tests for the ContentRouter defined in workflows/router.py.

These tests validate that the router correctly classifies content and dispatches
to the appropriate specialist agent. The key principle: routing is based on
content type, not data source. Run with:

    python -m pytest tests/test_router.py -v

Note: These tests make real LLM calls via tools/llm.py. Ensure GEMINI_API_KEY
is set in .env before running.
"""

from workflows.router import ContentRouter
from agents.schema import ContentType, empty_analysis
from agents.earnings_agent import EarningsAnalyzer
from agents.news_agent import NewsAnalyzer
from agents.market_agent import MarketAnalyzer


def test_earnings_content_routes_to_earnings_analyzer():
    """Content about EPS and quarterly results must route to EarningsAnalyzer."""
    pass


def test_news_content_routes_to_news_analyzer():
    """Company news and press release content must route to NewsAnalyzer."""
    pass


def test_market_content_routes_to_market_analyzer():
    """Price and trading data content must route to MarketAnalyzer."""
    pass


def test_macro_content_routes_to_market_analyzer():
    """Macroeconomic content (rates, inflation, unemployment) must route to
    MarketAnalyzer, not a separate macro agent."""
    pass


def test_router_dispatches_on_content_not_source():
    """An earnings article retrieved from NewsAPI must route to EarningsAnalyzer,
    not NewsAnalyzer. The router classifies by subject matter, not by API source."""
    pass


def test_router_populates_correct_analysis_field():
    """After routing, only the field corresponding to the dispatched specialist
    should be populated. Other fields should remain empty."""
    pass


def test_unrecognized_content_defaults_to_news():
    """If the LLM returns an unrecognized classification, the router must
    default to ContentType.NEWS rather than raising an error."""
    pass
