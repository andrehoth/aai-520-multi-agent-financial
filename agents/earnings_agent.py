# agents/earnings_agent.py
"""
Earnings specialist agent for the Multi-Agent Financial Analysis System.

Receives quarterly earnings and income statement data from Alpha Vantage
via tools/fundamentals.py and produces a narrative analysis covering
earnings trends, revenue growth, profit margins, and notable surprises.

When the pipeline routes EARNINGS-classified articles to this agent via
extra_context, those articles are appended to the prompt as supplementary
context alongside the structured Alpha Vantage data.

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

    def run(self, analysis: dict, extra_context: str = "") -> dict:
        """
        Fetch earnings and income statement data, analyze with LLM, and
        populate analysis["earnings_analysis"].

        If neither dataset is available (for example, the Alpha Vantage daily
        request limit was reached), the LLM call is skipped and a short
        unavailability note is stored instead.

        When extra_context is provided (EARNINGS-classified articles routed
        from the pipeline), it is appended to the prompt as a labeled section
        after the structured data. The existing system prompt instruction to
        stay grounded in the supplied data applies to this section as well.

        Args:
            analysis:      Shared analysis dict (see agents/schema.py)
            extra_context: Optional EARNINGS-classified news articles routed
                           from the pipeline via ContentRouter.classify_batch().
                           Appended to the prompt when non-empty.

        Returns:
            Updated analysis dict with earnings_analysis populated
        """
        # Fetch the 8 most recent quarters of earnings and income data
        earnings = fetch_earnings(self.ticker)
        income   = fetch_income_statement(self.ticker)

        # Sending empty lists to the model produced a reply asking the user to
        # supply the data. That reply would be stored as the analysis and flow
        # into the synthesis, evaluation, reflection, and memory. A short factual
        # note lets the synthesis acknowledge the gap instead, matching how
        # NewsAnalyzer handles missing news.
        if not earnings and not income:
            print(f"      Warning: no earnings data for {self.ticker}; skipping LLM analysis")
            analysis["earnings_analysis"] = (
                "Earnings and income statement data were unavailable for analysis."
            )
            return analysis

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

        # Append routed earnings articles when provided. Labeled clearly so
        # the model treats them as supplementary news context, not structured
        # data, and does not conflate article figures with Alpha Vantage data.
        if extra_context:
            prompt += (
                f"\n\nRelated Earnings News (routed articles for additional context):\n"
                f"{extra_context}"
            )

        analysis["earnings_analysis"] = self.call(prompt)
        return analysis
