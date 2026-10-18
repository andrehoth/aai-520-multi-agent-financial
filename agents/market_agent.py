# agents/market_agent.py
"""
Market specialist agent for the Multi-Agent Financial Analysis System.

Receives price history and summary statistics from yfinance via
tools/price_data.py, and macroeconomic indicators from FRED via
tools/macro_data.py. Produces a narrative analysis covering price
trends, momentum, and macro context.

Populates analysis["market_analysis"] in the shared analysis dict.
See agents/schema.py for the full schema definition.
"""

from agents.base_agent import BaseAgent
from tools.price_data import fetch_price_history, fetch_price_summary
from tools.macro_data import fetch_macro_indicators


class MarketAnalyzer(BaseAgent):
    """
    Specialist agent that analyzes price trends and macroeconomic context.
    Dispatched by ContentRouter when content_type is MARKET or MACRO.
    """

    @property
    def system_prompt(self) -> str:
        return (
            f"You are a market analyst specializing in {self.ticker}. "
            f"Analyze price trends, momentum, and macroeconomic context "
            f"based on the data provided. Be factual and concise. "
            f"Relate the macro environment to the stock where relevant."
        )

    def run(self, analysis: dict) -> dict:
        """
        Fetch price and macro data, analyze with LLM, and populate
        analysis["market_analysis"].

        If neither price nor macroeconomic data is available, the LLM call is
        skipped and a short unavailability note is stored instead.

        Args:
            analysis: Shared analysis dict (see agents/schema.py)

        Returns:
            Updated analysis dict with market_analysis populated
        """
        # Fetch price history, summary statistics, and macro indicators
        price_history = fetch_price_history(self.ticker, period="3mo")
        price_summary = fetch_price_summary(self.ticker)
        macro         = fetch_macro_indicators()

        # On failure the price tools return an empty DataFrame and a summary of
        # None values (the ticker key is always present), and the macro tool
        # returns empty lists. With no data at all, skip the LLM call so the
        # model is not asked to analyze nothing.
        no_prices = price_history.empty and all(
            value is None for key, value in price_summary.items() if key != "ticker"
        )
        no_macro = not any(macro.values())
        if no_prices and no_macro:
            print(f"      Warning: no market data for {self.ticker}; skipping LLM analysis")
            analysis["market_analysis"] = (
                "Price and macroeconomic data were unavailable for analysis."
            )
            return analysis

        prompt = (
            f"Analyze the following market and macroeconomic data for "
            f"{self.ticker}. Provide a concise narrative covering: price "
            f"trend and momentum over the past 3 months, position relative "
            f"to 52-week range, and how the current macro environment "
            f"(interest rates, inflation, unemployment) relates to the stock.\n\n"
            f"Price Summary:\n{price_summary}\n\n"
            f"Price History (3 months, OHLCV):\n"
            f"{price_history.tail(10).to_string()}\n\n"
            f"Macroeconomic Indicators:\n{macro}"
        )

        analysis["market_analysis"] = self.call(prompt)
        return analysis
