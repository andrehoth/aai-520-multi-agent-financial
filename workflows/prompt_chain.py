# workflows/prompt_chain.py
"""
Workflow 1: Prompt Chaining -- News Processing Pipeline

Implements a five-stage news processing chain:
    Ingest > Preprocess > Classify > Extract > Summarize

STUB IMPLEMENTATION: This stub performs a single LLM summarization call
on the raw articles to unblock pipeline development. Ken Lai will replace
this with the full five-stage chain implementation.

Interface contract (must be preserved in final implementation):
    - Accepts: list of article dicts from tools/news_data.py
    - Returns: str narrative summary of processed news content
"""

from tools.llm import call_llm


class NewsProcessingChain:
    """
    Five-stage news processing chain for a given ticker.
    Dispatched by InvestmentResearchAgent before routing to NewsAnalyzer.

    Stages (stub combines into single call; Ken implements each separately):
        1. Ingest    -- receive raw articles from NewsAPI
        2. Preprocess -- clean and normalize article text
        3. Classify  -- categorize articles by financial topic
        4. Extract   -- identify key financial signals and data points
        5. Summarize -- produce concise narrative summary
    """

    # Lower temperature for extraction and classification stages
    temperature = 0.2

    def __init__(self, ticker: str):
        """
        Args:
            ticker: Stock symbol being researched (e.g., "AAPL")
        """
        self.ticker = ticker

    def run(self, articles: list[dict]) -> str:
        """
        Process raw news articles through the chain and return a summary.

        Args:
            articles: List of article dicts from tools/news_data.fetch_news()
                      Each dict has keys: title, description, content,
                      source, published_at

        Returns:
            Narrative string summarizing processed news content
        """
        if not articles:
            return f"No recent news articles found for {self.ticker}."

        # STUB: single LLM call combining all five stages
        # Ken replaces this with five separate stage methods
        formatted = "\n\n".join([
            f"Title: {a.get('title', '')}\n"
            f"Source: {a.get('source', '')}\n"
            f"Published: {a.get('published_at', '')}\n"
            f"Content: {a.get('description', '') or a.get('content', '')}"
            for a in articles
        ])

        prompt = (
            f"The following are recent news articles about {self.ticker}. "
            f"Preprocess, classify by financial topic, extract key financial "
            f"signals, and produce a concise narrative summary of the most "
            f"relevant news.\n\n{formatted}"
        )

        return call_llm(
            prompt=prompt,
            system=(
                f"You are a financial news analyst specializing in {self.ticker}. "
                f"Extract and summarize only the most financially relevant "
                f"information. Be factual and concise."
            ),
            temperature=self.temperature
        )