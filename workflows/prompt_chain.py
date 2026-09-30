"""Five-stage financial news processing workflow."""

from tools.news_data import fetch_news
from tools.llm import call_llm

class NewsProcessingChain:
    """Retrieve and process financial news for a stock ticker."""

    def __init__(self, ticker: str):
        self.ticker = ticker

    def ingest(self) -> list[dict]:
        """Retrieve recent news articles using the shared NewsAPI tool."""
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
    def run(self) -> str:
        """Run the complete five-stage news processing chain."""
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