# agents/earnings_agent.py
"""
Earnings specialist agent for the Multi-Agent Financial Analysis System.

Receives quarterly earnings and income statement data from Alpha Vantage
via tools/fundamentals.py and produces a narrative analysis covering
earnings trends, revenue growth, profit margins, and notable surprises.

Populates analysis["earnings_analysis"] in the shared analysis dict.
See agents/schema.py for the full schema definition.
"""

from agents.base_agent import BaseAgent
from tools.fundamentals import fetch_earnings, fetch_income_statement


class EarningsAnalyzer(BaseAgent):
    """
    Specialist agent that analyzes quarterly earnings and income statement data.
    Dispatched by ContentRouter when content_type is EARNINGS.
    """
    
    @property
    def system_prompt(self) -> str:
        return (
            f"You are a financial earnings analyst specializing in {self.ticker}. "
            f"Analyze earnings trends, revenue growth, and profit margins based "
            f"on the data provided. Be factual, concise, and grounded in the "
            f"numbers. Highlight notable earnings surprises and any trend changes."
        )

    def run(self, analysis: dict) -> dict:
        """
        Fetch earnings and income statement data, analyze with LLM, and
        populate analysis["earnings_analysis"].

        Args:
            analysis: Shared analysis dict (see agents/schema.py)

        Returns:
            Updated analysis dict with earnings_analysis populated
        """
        # Fetch the 8 most recent quarters of earnings and income data
        earnings = fetch_earnings(self.ticker)
        income   = fetch_income_statement(self.ticker)

        prompt = (
            f"Analyze the following earnings and income statement data for "
            f"{self.ticker}. Provide a concise narrative covering: earnings "
            f"trends over the past 8 quarters, revenue and profit margin "
            f"trajectory, and any notable earnings surprises.\n\n"
            f"Quarterly Earnings (most recent first):\n"
            f"{earnings}\n\n"
            f"Quarterly Income Statements (most recent first):\n"
            f"{income}"
        )

        analysis["earnings_analysis"] = self.call(prompt)
        return analysis