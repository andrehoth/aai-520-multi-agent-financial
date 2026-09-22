# agents/base_agent.py
"""
Base agent class for the Multi-Agent Financial Analysis System.

All specialist agents and the investment agent inherit from BaseAgent.
Shared structure and behavior is defined here so subclasses only need
to implement their own run() method and system prompt.

Pipeline pattern: each agent receives the full analysis dict, populates
its assigned field, and returns the dict. The orchestrator passes the
dict through agents in sequence:

    analysis = empty_analysis(ticker)
    analysis = earnings_agent.run(analysis)
    analysis = news_agent.run(analysis)
    analysis = market_agent.run(analysis)
"""

from tools.llm import call_llm
from agents.schema import empty_analysis


class BaseAgent:
    """
    Base class for all agents in the system.

    Subclasses must implement:
        run(analysis: dict) -> dict
        system_prompt (property or class attribute)
    """

    # Default temperature for this agent type. Subclasses override as needed.
    # Planning and summarization: 0.7
    # Extraction and evaluation: 0.2
    temperature: float = 0.7

    def __init__(self, ticker: str):
        """
        Initialize the agent with a ticker symbol.

        Args:
            ticker: Stock symbol to research (e.g., "AAPL")
        """
        self.ticker = ticker

    def run(self, analysis: dict) -> dict:
        """
        Execute the agent's analysis and populate its field in the analysis dict.
        All subclasses must implement this method.

        Args:
            analysis: Shared analysis dict (see agents/schema.py)

        Returns:
            The same analysis dict with this agent's field populated
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run(analysis: dict) -> dict"
        )

    def call(self, prompt: str, temperature: float = None) -> str:
        """
        Make an LLM call using this agent's system prompt.
        Convenience wrapper around call_llm() so subclasses do not
        import it directly.

        Args:
            prompt:      User-turn prompt content
            temperature: Override this agent's default temperature if needed

        Returns:
            Model response as a plain string
        """
        return call_llm(
            prompt=prompt,
            system=self.system_prompt,
            temperature=temperature or self.temperature,
        )

    @property
    def system_prompt(self) -> str:
        """
        System prompt defining this agent's role and behavior.
        Subclasses should override this property or define it as a class attribute.
        """
        return (
            f"You are a financial research assistant analyzing {self.ticker}. "
            f"Provide clear, factual, and concise analysis."
        )