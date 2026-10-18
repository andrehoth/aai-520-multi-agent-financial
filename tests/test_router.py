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


# ---------------------------------------------------------------------------
# route() dispatch tests
# Note: route() now passes content as extra_context to the specialist so each
# run() assertion includes extra_context=content. Tests that previously
# asserted run(analysis) have been updated to match the corrected behavior.
# ---------------------------------------------------------------------------

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
    earnings_agent.run.assert_called_once_with(analysis, extra_context=content)

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
    news_agent.run.assert_called_once_with(analysis, extra_context=content)

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
    market_agent.run.assert_called_once_with(analysis, extra_context=content)

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
    market_agent.run.assert_called_once_with(analysis, extra_context=content)

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
    earnings_agent.run.assert_called_once_with(analysis, extra_context=content)
    news_agent.run.assert_not_called()

    assert result == earnings_agent.run.return_value


def test_router_populates_correct_analysis_field():
    """After routing, only the field corresponding to the dispatched specialist
    should be populated. Other fields should remain empty."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.EARNINGS)

    def populate_earnings(analysis, extra_context=""):
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

    earnings_agent.run.assert_called_once_with(analysis, extra_context=content)


def test_unrecognized_content_defaults_to_news():
    """If the LLM returns an unrecognized classification, the router must
    default to ContentType.NEWS rather than raising an error."""
    with patch("workflows.router.call_llm", return_value="UNKNOWN"):
        router = ContentRouter("AAPL")

        result = router.classify(
            "Content that does not clearly match a supported category."
        )

    assert result == ContentType.NEWS


# ---------------------------------------------------------------------------
# route() extra_context forwarding tests
# ---------------------------------------------------------------------------

def test_route_passes_content_as_extra_context():
    """route() must forward the content string as extra_context to the
    specialist so the specialist can incorporate the routed article into
    its analysis prompt."""
    router = ContentRouter("AAPL")

    router.classify = Mock(return_value=ContentType.EARNINGS)

    earnings_agent = Mock(spec=EarningsAnalyzer)
    earnings_agent.run.return_value = empty_analysis("AAPL")
    router.specialists[ContentType.EARNINGS] = earnings_agent

    analysis = empty_analysis("AAPL")
    content = "Apple beat EPS estimates by 15% in Q3 2026."

    router.route(content, analysis)

    # Confirm extra_context was forwarded, not dropped
    _, kwargs = earnings_agent.run.call_args
    assert kwargs.get("extra_context") == content


# ---------------------------------------------------------------------------
# classify_batch() tests
# ---------------------------------------------------------------------------

def test_classify_batch_parses_well_formed_response():
    """classify_batch() must return one ContentType per article when the LLM
    returns a clean label-per-line response in input order."""
    articles = [
        {"title": "Apple Q3 earnings beat estimates", "description": "EPS of $2.10"},
        {"title": "Apple shares rise on volume", "description": "Trading up 3%"},
        {"title": "Fed holds rates steady", "description": "Inflation data mixed"},
        {"title": "Apple launches new product", "description": "Press release issued"},
    ]

    # Simulate a clean LLM response: one label per line
    mock_response = "EARNINGS\nMARKET\nMACRO\nNEWS"

    with patch("workflows.router.call_llm", return_value=mock_response):
        router = ContentRouter("AAPL")
        labels = router.classify_batch(articles)

    assert labels == [
        ContentType.EARNINGS,
        ContentType.MARKET,
        ContentType.MACRO,
        ContentType.NEWS,
    ]


def test_classify_batch_falls_back_to_news_on_unrecognized_label():
    """Any line that does not match a known ContentType must be replaced with
    ContentType.NEWS rather than raising an error."""
    articles = [
        {"title": "Apple earnings beat", "description": ""},
        {"title": "Something unclear", "description": ""},
    ]

    # Second label is not a valid ContentType
    mock_response = "EARNINGS\nGARBAGE"

    with patch("workflows.router.call_llm", return_value=mock_response):
        router = ContentRouter("AAPL")
        labels = router.classify_batch(articles)

    assert labels[0] == ContentType.EARNINGS
    assert labels[1] == ContentType.NEWS  # fallback


def test_classify_batch_fills_missing_lines_with_news():
    """If the LLM response is shorter than the article list, the missing
    positions must be filled with ContentType.NEWS."""
    articles = [
        {"title": "Apple earnings", "description": ""},
        {"title": "Apple news", "description": ""},
        {"title": "Apple market", "description": ""},
    ]

    # Only one label returned for three articles
    mock_response = "EARNINGS"

    with patch("workflows.router.call_llm", return_value=mock_response):
        router = ContentRouter("AAPL")
        labels = router.classify_batch(articles)

    assert len(labels) == 3
    assert labels[0] == ContentType.EARNINGS
    assert labels[1] == ContentType.NEWS  # filled
    assert labels[2] == ContentType.NEWS  # filled


def test_classify_batch_returns_empty_list_for_no_articles():
    """classify_batch() must return an empty list without making an LLM call
    when given an empty article list."""
    with patch("workflows.router.call_llm") as mock_llm:
        router = ContentRouter("AAPL")
        labels = router.classify_batch([])

    assert labels == []
    mock_llm.assert_not_called()


def test_classify_batch_makes_single_llm_call():
    """classify_batch() must make exactly one LLM call regardless of how many
    articles are provided, to minimize Gemini API usage."""
    articles = [
        {"title": f"Article {i}", "description": ""} for i in range(8)
    ]

    mock_response = "\n".join(["NEWS"] * 8)

    with patch("workflows.router.call_llm", return_value=mock_response) as mock_llm:
        router = ContentRouter("AAPL")
        router.classify_batch(articles)

    assert mock_llm.call_count == 1
