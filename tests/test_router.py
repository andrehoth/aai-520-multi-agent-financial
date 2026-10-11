# tests/test_router.py

from unittest.mock import Mock, patch

"""
Contract tests for the ContentRouter defined in workflows/router.py.

These tests validate that the router correctly classifies content and dispatches
to the appropriate specialist agent. The key principle: routing is based on
content type, not data source. Run with:

    python -m pytest tests/test_router.py -v

Note: External LLM and specialist-agent behavior is mocked so these tests
remain deterministic and do not require API calls.
"""

from workflows.router import ContentRouter
from agents.schema import ContentType, empty_analysis
from agents.earnings_agent import EarningsAnalyzer
from agents.news_agent import NewsAnalyzer
from agents.market_agent import MarketAnalyzer


def test_earnings_content_routes_to_earnings_analyzer():
    """Content about EPS and quarterly results must route to EarningsAnalyzer."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.EARNINGS)

    earnings_agent = Mock(spec=EarningsAnalyzer)
    earnings_agent.run.return_value = empty_analysis("AAPL")

    router.specialists[ContentType.EARNINGS] = earnings_agent

    analysis = empty_analysis("AAPL")
    content = "Apple reported quarterly EPS and revenue above expectations."

    result = router.route(content, analysis)

    router.classify.assert_called_once_with(content)
    earnings_agent.run.assert_called_once_with(analysis)

    assert result == earnings_agent.run.return_value


def test_news_content_routes_to_news_analyzer():
    """Company news and press release content must route to NewsAnalyzer."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.NEWS)

    news_agent = Mock(spec=NewsAnalyzer)
    news_agent.run.return_value = empty_analysis("AAPL")

    router.specialists[ContentType.NEWS] = news_agent

    analysis = empty_analysis("AAPL")
    content = "Apple announced a new product in a company press release."

    result = router.route(content, analysis)

    router.classify.assert_called_once_with(content)
    news_agent.run.assert_called_once_with(analysis)

    assert result == news_agent.run.return_value


def test_market_content_routes_to_market_analyzer():
    """Price and trading data content must route to MarketAnalyzer."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.MARKET)

    market_agent = Mock(spec=MarketAnalyzer)
    market_agent.run.return_value = empty_analysis("AAPL")

    router.specialists[ContentType.MARKET] = market_agent

    analysis = empty_analysis("AAPL")
    content = "Apple shares rose 3% on increased trading volume."

    result = router.route(content, analysis)

    router.classify.assert_called_once_with(content)
    market_agent.run.assert_called_once_with(analysis)

    assert result == market_agent.run.return_value


def test_macro_content_routes_to_market_analyzer():
    """Macroeconomic content (rates, inflation, unemployment) must route to
    MarketAnalyzer, not a separate macro agent."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.MACRO)

    market_agent = Mock(spec=MarketAnalyzer)
    market_agent.run.return_value = empty_analysis("AAPL")

    router.specialists[ContentType.MACRO] = market_agent

    analysis = empty_analysis("AAPL")
    content = "The Federal Reserve held interest rates steady as inflation eased."

    result = router.route(content, analysis)

    router.classify.assert_called_once_with(content)
    market_agent.run.assert_called_once_with(analysis)

    assert result == market_agent.run.return_value


def test_router_dispatches_on_content_not_source():
    """An earnings article retrieved from NewsAPI must route to EarningsAnalyzer,
    not NewsAnalyzer. The router classifies by subject matter, not by API source."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.EARNINGS)

    earnings_agent = Mock(spec=EarningsAnalyzer)
    earnings_agent.run.return_value = empty_analysis("AAPL")

    news_agent = Mock(spec=NewsAnalyzer)

    router.specialists[ContentType.EARNINGS] = earnings_agent
    router.specialists[ContentType.NEWS] = news_agent

    analysis = empty_analysis("AAPL")

    # Represents an earnings article retrieved through a news source such as NewsAPI.
    content = (
        "Apple reported quarterly EPS of $2.10 and revenue of "
        "$95 billion, exceeding analyst expectations."
    )

    result = router.route(content, analysis)

    router.classify.assert_called_once_with(content)
    earnings_agent.run.assert_called_once_with(analysis)
    news_agent.run.assert_not_called()

    assert result == earnings_agent.run.return_value


def test_router_populates_correct_analysis_field():
    """After routing, only the field corresponding to the dispatched specialist
    should be populated. Other fields should remain empty."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.EARNINGS)

    def populate_earnings(analysis):
        analysis["earnings_analysis"] = "Mock earnings analysis."
        return analysis

    earnings_agent = Mock(spec=EarningsAnalyzer)
    earnings_agent.run.side_effect = populate_earnings

    router.specialists[ContentType.EARNINGS] = earnings_agent

    analysis = empty_analysis("AAPL")
    content = "Apple reported quarterly earnings results."

    result = router.route(content, analysis)

    assert result["earnings_analysis"] == "Mock earnings analysis."
    assert result["news_analysis"] == ""
    assert result["market_analysis"] == ""

    earnings_agent.run.assert_called_once_with(analysis)


def test_unrecognized_content_defaults_to_news():
    """If the LLM returns an unrecognized classification, the router must
    default to ContentType.NEWS rather than raising an error."""
    with patch("workflows.router.call_llm", return_value="UNKNOWN"):
        router = ContentRouter("AAPL")

        result = router.classify(
            "Content that does not clearly match a supported category."
        )

    assert result == ContentType.NEWS
