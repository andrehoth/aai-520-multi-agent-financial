"""News specialist agent for the Multi-Agent Financial Analysis System."""

from agents.base_agent import BaseAgent


class NewsAnalyzer(BaseAgent):
    """Analyze financial news relevant to the selected stock."""

    temperature = 0.2

    @property
    def system_prompt(self) -> str:
        """Return the system instructions for financial news analysis."""
        return (
            f"You are a financial news analyst researching {self.ticker}. "
            "Analyze relevant news objectively and identify material developments "
            "that may affect the company or its stock. Distinguish reported facts "
            "from speculation, and do not invent facts or sources."
        )

    def run(self, analysis: dict, processed_news: str = "") -> dict:
        """
        Analyze processed financial news and populate news_analysis.

        Args:
            analysis: Shared analysis dictionary.
            processed_news: News content produced by NewsProcessingChain.

        Returns:
            The shared analysis dictionary with news_analysis populated.
        """
        if not processed_news:
            analysis["news_analysis"] = (
                "No relevant news was available for analysis."
            )
            return analysis

        prompt = (
            f"Analyze the following processed financial news for {self.ticker}.\n\n"
            f"{processed_news}\n\n"
            "Provide a concise narrative covering the most material developments, "
            "their potential implications for the company or stock, and any "
            "important uncertainty. Distinguish facts from speculation."
        )

        analysis["news_analysis"] = self.call(prompt)

        return analysis