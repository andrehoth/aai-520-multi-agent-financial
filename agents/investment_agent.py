# agents/investment_agent.py
"""
Orchestrator for the Multi-Agent Financial Analysis System.

Coordinates the full research pipeline for a given ticker symbol:
    1. Planning      -- read prior memory, generate a research plan
    2. Routing       -- fetch articles, classify each with ContentRouter,
                        split into NEWS / EARNINGS / MARKET buckets
    3. News chain    -- run the five-stage prompt chain on NEWS articles only
    4. Analysis      -- call all three specialist agents; EARNINGS and MARKET
                        buckets are forwarded as extra_context to their
                        respective specialists
    5. Synthesis     -- combine specialist outputs into a final analysis
    6. Evaluation    -- run the evaluator-optimizer
    7. Reflection    -- score and critique the final output
    8. Memory        -- persist the completed analysis for future runs

Populates all fields in the shared analysis dict (agents/schema.py).

Routing design (Option A):
    Classification happens before the news chain so that the chain processes
    only NEWS-classified articles. This keeps the chain output focused and
    positions the pipeline for plan-driven dispatch (Option 2) in a future
    branch, where routing order relative to chain execution matters for
    control flow.

    MACRO articles are treated as MARKET for dispatch purposes; both route
    to MarketAnalyzer as extra_context (ContentRouter maps MACRO ->
    MarketAnalyzer via the specialists dict).
"""

from datetime import datetime

from agents.base_agent import BaseAgent
from agents.earnings_agent import EarningsAnalyzer
from agents.news_agent import NewsAnalyzer
from agents.market_agent import MarketAnalyzer
from agents.schema import empty_analysis, ContentType
from memory.agent_memory import load_memory, save_memory
from workflows.prompt_chain import NewsProcessingChain
from workflows.router import ContentRouter
from workflows.evaluator_optimizer import EvaluatorOptimizer


class InvestmentResearchAgent(BaseAgent):
    """
    Top-level orchestrator that coordinates all pipeline stages for a
    given ticker symbol and produces a final investment analysis.
    """

    temperature = 0.7

    @property
    def system_prompt(self) -> str:
        return (
            f"You are a senior investment research analyst specializing in "
            f"{self.ticker}. Synthesize earnings, news, and market data into "
            f"a coherent, balanced investment analysis. Ground all conclusions "
            f"in the provided data. Distinguish facts from speculation."
        )

    def plan(self, prior_memory: dict | None) -> str:
        """
        Generate a research plan for the current ticker.
        Reads prior memory to address gaps from previous analyses.

        Args:
            prior_memory: Most recent analysis dict from memory, or None

        Returns:
            Research plan as a narrative string
        """
        memory_context = ""
        if prior_memory:
            memory_context = (
                f"\n\nPrior analysis summary (from {prior_memory.get('timestamp', 'unknown date')}):\n"
                f"Evaluation score: {prior_memory.get('evaluation_score', 0)}/10\n"
                f"Synthesis: {prior_memory.get('synthesis', '')[:500]}\n"
                f"Reflection (gaps to address): {prior_memory.get('reflection', '')[:500]}\n\n"
                f"IMPORTANT: Your research plan must explicitly address the gaps and "
                f"weaknesses identified in the prior reflection above. The goal is to "
                f"produce a measurably stronger analysis than the prior run."
            )

        prompt = (
            f"Generate a focused research plan for analyzing {self.ticker}. "
            f"The plan should cover: earnings and financial performance, "
            f"recent news and developments, and market and macro context."
            f"{memory_context}\n\n"
            f"If prior analysis exists, identify any gaps or areas to investigate "
            f"more thoroughly this time. Keep the plan concise and actionable."
        )

        return self.call(prompt)

    def _bucket_articles(
        self, articles: list[dict], labels: list[ContentType]
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """
        Split classified articles into three specialist buckets.

        MACRO is folded into the MARKET bucket because both route to
        MarketAnalyzer. This keeps the bucket structure aligned with the
        three specialist agents rather than the four ContentType values.

        Args:
            articles: Raw article dicts from fetch_news()
            labels:   ContentType label for each article, in the same order

        Returns:
            Tuple of (news_articles, earnings_articles, market_articles)
        """
        news_articles     = []
        earnings_articles = []
        market_articles   = []

        for article, label in zip(articles, labels):
            if label == ContentType.EARNINGS:
                earnings_articles.append(article)
            elif label in (ContentType.MARKET, ContentType.MACRO):
                # MACRO and MARKET both dispatch to MarketAnalyzer
                market_articles.append(article)
            else:
                # ContentType.NEWS and any unexpected value go to the chain
                news_articles.append(article)

        return news_articles, earnings_articles, market_articles

    def _articles_to_text(self, articles: list[dict]) -> str:
        """
        Concatenate a list of article dicts into a plain text block for use
        as extra_context in a specialist prompt.

        Uses the same field set as NewsProcessingChain.preprocess() so the
        format is consistent across the pipeline.

        Args:
            articles: List of article dicts (title, description, content,
                      source, published_at)

        Returns:
            Articles joined by separator lines, or empty string if no articles
        """
        if not articles:
            return ""

        blocks = []
        for article in articles:
            title        = article.get("title") or ""
            description  = article.get("description") or ""
            content      = article.get("content") or ""
            source       = article.get("source") or ""
            published_at = article.get("published_at") or ""

            blocks.append(
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Published: {published_at}\n"
                f"Description: {description}\n"
                f"Content: {content}"
            )

        return "\n\n---\n\n".join(blocks)

    def synthesize(self, analysis: dict) -> str:
        """
        Synthesize the three specialist analyses into a coherent
        final investment analysis.

        Args:
            analysis: Shared analysis dict with all three specialist fields populated

        Returns:
            Synthesis narrative as a string
        """
        prompt = (
            f"Synthesize the following specialist analyses for {self.ticker} "
            f"into a coherent investment analysis.\n\n"
            f"Earnings Analysis:\n{analysis['earnings_analysis']}\n\n"
            f"News Analysis:\n{analysis['news_analysis']}\n\n"
            f"Market Analysis:\n{analysis['market_analysis']}\n\n"
            f"Produce a balanced synthesis covering financial performance, "
            f"recent developments, market context, key risks, and overall "
            f"investment considerations. Do not introduce facts not present "
            f"in the specialist analyses."
        )

        return self.call(prompt)

    def reflect(self, analysis: dict) -> str:
        """
        Reflect on the quality of the completed analysis, identifying
        strengths, gaps, and areas for improvement in future runs.

        Args:
            analysis: Completed analysis dict with synthesis and evaluation fields

        Returns:
            Reflection narrative as a string
        """
        prompt = (
            f"Reflect on the following investment analysis for {self.ticker}.\n\n"
            f"Synthesis:\n{analysis['synthesis']}\n\n"
            f"Evaluation Score: {analysis['evaluation_score']}/10\n"
            f"Evaluation Feedback:\n{analysis['evaluation_feedback']}\n\n"
            f"Identify: what was covered well, what data or perspectives were "
            f"missing, and what should be prioritized in the next analysis run. "
            f"Be specific and constructive."
        )

        return self.call(prompt)

    def run(self, analysis: dict = None) -> dict:
        """
        Execute the full research pipeline for the ticker.

        Pipeline stages:
            1. Planning      -- read memory, generate research plan
            2. Routing       -- fetch articles, classify with ContentRouter,
                                split into NEWS / EARNINGS / MARKET buckets
            3. News chain    -- process NEWS bucket through the five-stage chain
            4. Specialist    -- run all three specialists; pass EARNINGS and
                                MARKET bucket text as extra_context
            5. Synthesis     -- combine specialist outputs
            6. Evaluation    -- evaluator-optimizer loop
            7. Reflection    -- self-critique for future improvement
            8. Memory        -- persist completed analysis

        Args:
            analysis: Optional pre-initialized analysis dict. If None,
                      a fresh dict is created via empty_analysis().

        Returns:
            Completed analysis dict with all fields populated
        """
        if analysis is None:
            analysis = empty_analysis(self.ticker)

        # Stage 1: Planning -- read prior memory and generate research plan
        print(f"[1/8] Planning research for {self.ticker}...")
        prior_memory = load_memory(self.ticker)
        plan = self.plan(prior_memory)
        print(f"      Research plan generated ({len(plan)} characters)")

        # Stage 2: Routing -- fetch articles, classify in one batch call,
        # then split into specialist buckets.
        #
        # Classification happens before the news chain (Option A) so the chain
        # operates only on NEWS-classified articles. EARNINGS and MARKET articles
        # are routed directly to their specialist as extra context rather than
        # passing through a general-purpose news summarization chain that would
        # strip the structured signals those specialists need.
        print("[2/8] Fetching and routing articles...")
        router   = ContentRouter(self.ticker)
        chain    = NewsProcessingChain(self.ticker)
        articles = chain.ingest()

        if articles:
            labels = router.classify_batch(articles)
            news_articles, earnings_articles, market_articles = self._bucket_articles(
                articles, labels
            )
            print(
                f"      {len(articles)} articles classified -- "
                f"NEWS: {len(news_articles)}, "
                f"EARNINGS: {len(earnings_articles)}, "
                f"MARKET: {len(market_articles)}"
            )
        else:
            # No articles returned; all buckets are empty and the chain will
            # return an empty string, matching the pre-routing behavior
            news_articles     = []
            earnings_articles = []
            market_articles   = []
            print("      No articles retrieved")

        # Stage 3: News chain -- run the five-stage chain on NEWS articles only
        print("[3/8] Running news processing chain on NEWS articles...")
        processed_news = chain.run(articles=news_articles)
        print(f"      Chain output: {len(processed_news)} characters")

        # Convert EARNINGS and MARKET bucket article lists to plain text for
        # use as extra_context in the specialist prompts
        earnings_context = self._articles_to_text(earnings_articles)
        market_context   = self._articles_to_text(market_articles)

        # Stage 4: Specialist analyses -- call all three agents directly.
        # EARNINGS and MARKET buckets are forwarded as extra_context so each
        # specialist receives routed articles alongside its structured data.
        print("[4/8] Running EarningsAnalyzer...")
        analysis = EarningsAnalyzer(self.ticker).run(
            analysis, extra_context=earnings_context
        )

        print("[5/8] Running NewsAnalyzer...")
        analysis = NewsAnalyzer(self.ticker).run(
            analysis, processed_news=processed_news
        )

        print("[6/8] Running MarketAnalyzer...")
        analysis = MarketAnalyzer(self.ticker).run(
            analysis, extra_context=market_context
        )

        # Stage 5: Synthesis -- combine specialist outputs
        print("[7/8] Synthesizing analysis...")
        analysis["synthesis"] = self.synthesize(analysis)
        analysis["timestamp"] = datetime.now().isoformat()
        print(f"      Synthesis: {len(analysis['synthesis'])} characters")

        # Stage 6: Evaluation and optimization
        print("[8/8] Evaluating and optimizing...")
        evaluator = EvaluatorOptimizer(self.ticker)
        analysis  = evaluator.run(analysis)

        # Raise immediately if evaluation failed silently rather than returning
        # a misleading 0.0
        if analysis["evaluation_score"] == 0.0 and not analysis["evaluation_feedback"]:
            raise RuntimeError(
                "Evaluator returned no score -- check evaluator_optimizer.py"
            )

        # Stage 7: Self-reflection
        analysis["reflection"] = self.reflect(analysis)

        # Stage 8: Persist to memory for future runs
        save_memory(analysis)
        print(f"      Analysis complete. Score: {analysis['evaluation_score']}/10")

        return analysis
