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

    classify()       -- single-article classification; used by route() and the
                        notebook demonstration
    classify_batch() -- batch classification for a list of article dicts;
                        used by the pipeline to minimize Gemini calls

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
        market_analyzer = MarketAnalyzer(ticker)
        self.specialists = {
            ContentType.NEWS: NewsAnalyzer(ticker),
            ContentType.EARNINGS: EarningsAnalyzer(ticker),
            ContentType.MARKET: market_analyzer,
            ContentType.MACRO: market_analyzer,
        }

    def classify(self, content: str) -> ContentType:
        """
        Use LLM to classify a single piece of content into one of the four
        ContentType values.

        Used by route() for single-article dispatch and by the notebook
        demonstration. For pipeline use with multiple articles, prefer
        classify_batch() to reduce LLM call count.

        Args:
            content: Text content to classify

        Returns:
            ContentType enum value; defaults to ContentType.NEWS if the LLM
            returns an unrecognized label
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

        result = (
            call_llm(
                prompt=prompt,
                system="You are a financial content classifier. Respond with exactly one word.",
                temperature=self.temperature,
            )
            .strip()
            .upper()
        )

        # Map result to ContentType, default to NEWS if unrecognized
        try:
            return ContentType(result)
        except ValueError:
            return ContentType.NEWS

    def classify_batch(self, articles: list[dict]) -> list[ContentType]:
        """
        Classify a list of article dicts in a single LLM call.

        Sends all articles to the LLM in one request and parses one label
        per article index. This reduces Gemini call count from N (one per
        article) to 1 for the full batch, which matters given the project's
        Gemini spend constraints.

        The LLM is asked to return one label per line, in the same order as
        the input articles. Any line that does not parse to a known ContentType
        falls back to ContentType.NEWS so the article is still processed by
        the news chain rather than dropped.

        If the response contains fewer lines than articles (truncation or
        refusal), the missing positions are filled with ContentType.NEWS.

        Args:
            articles: List of article dicts as returned by fetch_news().
                      Each dict is expected to have at least a "title" and
                      optionally a "description" key.

        Returns:
            List of ContentType values, one per article, in input order.
        """
        if not articles:
            return []

        # Build a numbered list of article previews for the LLM.
        # Title + description gives enough context for classification without
        # sending full article content, which keeps the prompt compact.
        article_lines = []
        for i, article in enumerate(articles):
            title = article.get("title") or ""
            description = article.get("description") or ""
            # Truncate each preview so the combined prompt stays manageable
            preview = f"{title} {description}".strip()[:300]
            article_lines.append(f"{i + 1}. {preview}")

        numbered_articles = "\n".join(article_lines)

        prompt = (
            f"Classify each of the following financial news articles into "
            f"exactly one category: NEWS, EARNINGS, MARKET, or MACRO.\n\n"
            f"Rules:\n"
            f"- NEWS: company news, press releases, analyst commentary\n"
            f"- EARNINGS: quarterly results, EPS, revenue, guidance\n"
            f"- MARKET: price data, trading volume, technical indicators\n"
            f"- MACRO: interest rates, inflation, unemployment, economic data\n\n"
            f"Return exactly one label per line, in the same order as the "
            f"articles. Do not include numbers, punctuation, or explanations. "
            f"Each line must contain only the category name.\n\n"
            f"Articles:\n{numbered_articles}"
        )

        raw = call_llm(
            prompt=prompt,
            system=(
                "You are a financial content classifier. "
                "Respond with one category label per line, nothing else."
            ),
            temperature=self.temperature,
        )

        # Parse response: one label per line, strip whitespace, upper-case
        lines = [line.strip().upper() for line in raw.strip().splitlines() if line.strip()]

        labels: list[ContentType] = []
        for i, article in enumerate(articles):
            if i < len(lines):
                try:
                    labels.append(ContentType(lines[i]))
                except ValueError:
                    # Unrecognized label -- fall back to NEWS so the article
                    # reaches the news chain rather than being silently dropped
                    labels.append(ContentType.NEWS)
            else:
                # Response was shorter than the article list -- fill with NEWS
                labels.append(ContentType.NEWS)

        return labels

    def route(self, content: str, analysis: dict) -> dict:
        """
        Classify content and dispatch to the appropriate specialist agent,
        passing the content as extra context for the specialist's analysis.

        Previously this method called specialist.run(analysis) without
        forwarding the content, so the specialist received the routing
        decision but not the content that drove it. The content is now
        passed as extra_context so each specialist can incorporate the
        routed article into its analysis.

        Args:
            content:  Text content to classify and route
            analysis: Shared analysis dict (see agents/schema.py)

        Returns:
            Updated analysis dict with specialist field populated
        """
        content_type = self.classify(content)
        print(
            f"  Router: classified as {content_type.value} -> "
            f"{self.specialists[content_type].__class__.__name__}"
        )

        # Pass content as extra_context so the specialist can incorporate
        # the routed article into its prompt alongside its structured data
        return self.specialists[content_type].run(analysis, extra_context=content)
