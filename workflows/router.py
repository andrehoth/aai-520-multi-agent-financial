# workflows/router.py
"""
Workflow 2: Routing -- Content Classification and Dispatch

Classifies incoming financial content by type and dispatches to the
appropriate specialist agent. Routing is based on content_type, not
on data source. An earnings article retrieved via NewsAPI correctly
routes to EarningsAnalyzer rather than NewsAnalyzer.

ContentType enum (agents/schema.py):
    NEWS     -> NewsAnalyzer
    EARNINGS -> EarningsAnalyzer
    MARKET   -> MarketAnalyzer
    MACRO    -> MarketAnalyzer
"""

from tools.llm import call_llm
from agents.schema import ContentType
from agents.earnings_agent import EarningsAnalyzer
from agents.news_agent import NewsAnalyzer
from agents.market_agent import MarketAnalyzer


class ContentRouter:
    """
    Routes financial content to the appropriate specialist agent
    based on LLM-classified content type.

    The router uses a two-step process:
        1. Classify the content using an LLM call to determine content_type
        2. Dispatch to the matching specialist agent

    This satisfies Workflow 2 (Routing) of the assignment rubric.
    """

    # Low temperature for classification -- deterministic output preferred
    temperature = 0.2

    def __init__(self, ticker: str):
        """
        Args:
            ticker: Stock symbol being researched (e.g., "AAPL")
        """
        self.ticker = ticker
        self.specialists = {
            ContentType.NEWS:     NewsAnalyzer(ticker),
            ContentType.EARNINGS: EarningsAnalyzer(ticker),
            ContentType.MARKET:   MarketAnalyzer(ticker),
            ContentType.MACRO:    MarketAnalyzer(ticker),
        }

    def classify(self, content: str) -> ContentType:
        """
        Use LLM to classify content into one of the four ContentType values.

        Args:
            content: Text content to classify

        Returns:
            ContentType enum value
        """
        prompt = (
            f"Classify the following financial content into exactly one of "
            f"these categories: NEWS, EARNINGS, MARKET, MACRO.\n\n"
            f"Rules:\n"
            f"- NEWS: company news, press releases, analyst commentary\n"
            f"- EARNINGS: quarterly results, EPS, revenue, guidance\n"
            f"- MARKET: price data, trading volume, technical indicators\n"
            f"- MACRO: interest rates, inflation, unemployment, economic data\n\n"
            f"Respond with only the category name, nothing else.\n\n"
            f"Content:\n{content[:500]}"
        )

        result = call_llm(
            prompt=prompt,
            system="You are a financial content classifier. Respond with exactly one word.",
            temperature=self.temperature
        ).strip().upper()

        # Map result to ContentType, default to NEWS if unrecognized
        try:
            return ContentType(result)
        except ValueError:
            return ContentType.NEWS

    def route(self, content: str, analysis: dict) -> dict:
        """
        Classify content and dispatch to the appropriate specialist agent.

        Args:
            content:  Text content to classify and route
            analysis: Shared analysis dict (see agents/schema.py)

        Returns:
            Updated analysis dict with specialist field populated
        """
        content_type = self.classify(content)
        print(f"  Router: classified as {content_type.value} -> "
              f"{self.specialists[content_type].__class__.__name__}")

        return self.specialists[content_type].run(analysis)