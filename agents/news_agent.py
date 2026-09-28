# agents/news_agent.py
"""
News specialist agent for the Multi-Agent Financial Analysis System.

Receives processed news content from workflows/prompt_chain.py and
produces a narrative analysis covering sentiment, key themes, and
material risks or catalysts identified in recent coverage.

Populates analysis["news_analysis"] in the shared analysis dict.
See agents/schema.py for the full schema definition.

STUB IMPLEMENTATION: This stub passes prompt chain output directly to
a single LLM analysis call. Ken Lai will replace this with the full
implementation incorporating classification confidence and sentiment scoring.
"""

from agents.base_agent import BaseAgent
from tools.news_data import fetch_news
from workflows.prompt_chain import NewsProcessingChain


class NewsAnalyzer(BaseAgent):
    """
    Specialist agent that analyzes processed financial news content.
    Dispatched by ContentRouter when content_type is NEWS.

    Depends on NewsProcessingChain output -- prompt chain must run
    before this agent is called.
    """

    @property
    def system_prompt(self) -> str:
        return (
            f"You are a financial news analyst specializing in {self.ticker}. "
            f"Analyze the provided news summary for sentiment, key themes, "
            f"material risks, and potential catalysts. Be factual and concise. "
            f"Ground all observations in the provided content."
        )

    def run(self, analysis: dict) -> dict:
        """
        Fetch news, run through prompt chain, analyze with LLM, and
        populate analysis["news_analysis"].

        Args:
            analysis: Shared analysis dict (see agents/schema.py)

        Returns:
            Updated analysis dict with news_analysis populated
        """
        # Fetch raw articles and process through prompt chain
        articles = fetch_news(self.ticker)
        chain = NewsProcessingChain(self.ticker)
        chain_output = chain.run(articles)

        prompt = (
            f"Based on the following processed news summary for {self.ticker}, "
            f"provide a concise analysis covering: overall sentiment (positive, "
            f"negative, or mixed), key themes driving recent coverage, material "
            f"risks identified, and any potential catalysts.\n\n"
            f"Processed News Summary:\n{chain_output}"
        )

        analysis["news_analysis"] = self.call(prompt)
        return analysis