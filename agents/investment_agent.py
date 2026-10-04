# agents/investment_agent.py
"""
Orchestrator for the Multi-Agent Financial Analysis System.

Coordinates the full research pipeline for a given ticker symbol:
    1. Planning      -- read prior memory, generate a research plan
    2. Data and News -- run the five-stage prompt chain
    3. Analysis      -- call all three specialist agents
    4. Synthesis     -- combine specialist outputs into a final analysis
    5. Evaluation    -- run the evaluator-optimizer
    6. Reflection    -- score and critique the final output
    7. Memory        -- persist the completed analysis for future runs

Populates all fields in the shared analysis dict (agents/schema.py).
Specialist agents are called directly rather than through the router
because the investment agent always requires all three specialists in
a known order. The router is used for dynamic dispatch of unknown content
and is demonstrated separately in workflows/router.py.
"""

from datetime import datetime

from agents.base_agent import BaseAgent
from agents.earnings_agent import EarningsAnalyzer
from agents.news_agent import NewsAnalyzer
from agents.market_agent import MarketAnalyzer
from agents.schema import empty_analysis
from memory.agent_memory import load_memory, save_memory
from workflows.prompt_chain import NewsProcessingChain
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

        Args:
            analysis: Optional pre-initialized analysis dict. If None,
                      a fresh dict is created via empty_analysis().

        Returns:
            Completed analysis dict with all fields populated
        """
        if analysis is None:
            analysis = empty_analysis(self.ticker)

        # Stage 1: Planning -- read prior memory and generate research plan
        print(f"[1/7] Planning research for {self.ticker}...")
        prior_memory = load_memory(self.ticker)
        plan = self.plan(prior_memory)
        print(f"      Research plan generated ({len(plan)} characters)")

        # Stage 2: News processing -- run the five-stage prompt chain
        print("[2/7] Running news processing chain...")
        chain = NewsProcessingChain(self.ticker)
        processed_news = chain.run()
        print(f"      Chain output: {len(processed_news)} characters")

        # Stage 3: Specialist analyses -- call all three agents directly
        print("[3/7] Running EarningsAnalyzer...")
        analysis = EarningsAnalyzer(self.ticker).run(analysis)

        print("[4/7] Running NewsAnalyzer...")
        analysis = NewsAnalyzer(self.ticker).run(
            analysis, processed_news=processed_news
        )

        print("[5/7] Running MarketAnalyzer...")
        analysis = MarketAnalyzer(self.ticker).run(analysis)

        # Stage 4: Synthesis -- combine specialist outputs
        print(f"[6/7] Synthesizing analysis...")
        analysis["synthesis"] = self.synthesize(analysis)
        analysis["timestamp"] = datetime.now().isoformat()
        print(f"      Synthesis: {len(analysis['synthesis'])} characters")

        # Stage 5: Evaluation and optimization
        print("[7/7] Evaluating and optimizing...")
        evaluator = EvaluatorOptimizer(self.ticker)
        analysis = evaluator.run(analysis)

        # Raise immediately if evaluation failed silently rather than returning a misleading 0.0
        if analysis["evaluation_score"] == 0.0 and not analysis["evaluation_feedback"]:
            raise RuntimeError(
                "Evaluator returned no score -- check evaluator_optimizer.py"
            )

        # Stage 6: Self-reflection
        analysis["reflection"] = self.reflect(analysis)

        # Stage 7: Persist to memory for future runs
        save_memory(analysis)
        print(f"      Analysis complete. Score: {analysis['evaluation_score']}/10")

        return analysis
