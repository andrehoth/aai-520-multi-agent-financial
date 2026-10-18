# workflows/prompt_chain.py
"""
Five-stage financial news processing workflow.

Implements a sequential news processing chain where the output of each
stage is passed as input to the next:
    Ingest > Preprocess > Classify > Extract > Summarize

Each stage is a separate LLM call. In the pipeline, article ingestion and
routing happen in the orchestrator (agents/investment_agent.py) before the
chain is called, so run() accepts an articles parameter and processes only
the NEWS-classified subset. ingest() remains on the class for standalone use
and the notebook demonstration.

See agents/schema.py for the shared analysis dict definition.
"""

from tools.news_data import fetch_news
from tools.llm import call_llm


class NewsProcessingChain:
    """Retrieve and process financial news for a stock ticker."""

    def __init__(self, ticker: str):
        self.ticker = ticker

    def ingest(self) -> list[dict]:
        """
        Retrieve recent news articles using the shared NewsAPI tool.

        In the pipeline this is called by the orchestrator before routing
        so that all articles are available for classification. It is also
        available here for standalone use and the notebook demonstration.
        """
        return fetch_news(self.ticker)

    def preprocess(self, articles: list[dict]) -> str:
        """Convert retrieved news articles into clean text for LLM processing."""
        processed_articles = []

        for article in articles:
            title = article.get("title") or ""
            description = article.get("description") or ""
            content = article.get("content") or ""
            source = article.get("source") or ""
            published_at = article.get("published_at") or ""

            article_text = (
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Published: {published_at}\n"
                f"Description: {description}\n"
                f"Content: {content}"
            )

            processed_articles.append(article_text)

        return "\n\n---\n\n".join(processed_articles)

    def classify(self, processed_news: str) -> str:
        """Classify retrieved news for relevance to the target stock."""
        if not processed_news:
            return ""

        prompt = (
            f"Review the following retrieved news for ticker {self.ticker}.\n\n"
            f"{processed_news}\n\n"
            "Identify which items are relevant to an investment analysis of "
            f"{self.ticker}. Exclude unrelated or coincidental matches. "
            "Return only the relevant news items, preserving their key facts, "
            "sources, and publication dates."
        )

        return call_llm(
            prompt=prompt,
            system=(
                "You are a financial news relevance classifier. "
                "Filter retrieved news conservatively and do not invent information."
            ),
            temperature=0.2,
        )

    def extract(self, classified_news: str) -> str:
        """Extract investment-relevant facts from classified financial news."""
        if not classified_news:
            return ""

        prompt = (
            f"Extract the most important investment-relevant facts for "
            f"{self.ticker} from the following classified news.\n\n"
            f"{classified_news}\n\n"
            "For each material development, identify:\n"
            "- the event or development\n"
            "- key factual details\n"
            "- the source and publication date when available\n"
            "- any explicitly reported financial or business impact\n\n"
            "Do not add conclusions, predictions, or facts that are not present "
            "in the supplied news."
        )

        return call_llm(
            prompt=prompt,
            system=(
                "You are a financial information extraction specialist. "
                "Extract only information supported by the supplied news."
            ),
            temperature=0.2,
        )

    def summarize(self, extracted_news: str) -> str:
        """Summarize extracted news facts for downstream analysis."""
        if not extracted_news:
            return ""

        prompt = (
            f"Summarize the following extracted financial news facts for "
            f"{self.ticker}.\n\n"
            f"{extracted_news}\n\n"
            "Produce a concise factual summary of the material developments. "
            "Preserve important quantitative details, sources, and dates when "
            "available. Do not provide an investment recommendation, predict "
            "stock performance, or introduce facts not contained in the input."
        )

        return call_llm(
            prompt=prompt,
            system=(
                "You are a financial news summarization specialist. "
                "Produce concise, factual summaries grounded only in the "
                "supplied information."
            ),
            temperature=0.2,
        )

    def run(self, articles: list[dict] = None) -> str:
        """
        Run the complete five-stage news processing chain.

        When called from the pipeline, articles are provided by the
        orchestrator after routing so that only NEWS-classified articles
        pass through the chain. When called standalone (for example, in
        the notebook demonstration), articles defaults to None and the
        chain fetches all articles itself via ingest().

        Args:
            articles: Pre-fetched and pre-filtered article list, or None to
                      fetch all articles via ingest().

        Returns:
            Summarized news string, or empty string if no articles survive
            any stage of the chain.
        """
        # Fetch all articles when called standalone (notebook or direct use)
        if articles is None:
            articles = self.ingest()

        if not articles:
            return ""

        processed = self.preprocess(articles)

        if not processed:
            return ""

        classified = self.classify(processed)

        if not classified:
            return ""

        extracted = self.extract(classified)

        if not extracted:
            return ""

        return self.summarize(extracted)
