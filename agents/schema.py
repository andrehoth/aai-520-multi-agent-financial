# agents/schema.py
"""
Inter-agent data schema for the Multi-Agent Financial Analysis System.

This module defines the shared data structure passed between all agents
and workflows. A narrative dict is used rather than a typed structured
schema. See docs/architecture.md for the design decision and tradeoffs.

All fields are strings except evaluation_score (float) and timestamp (str, ISO format).
"""

from enum import Enum


class ContentType(Enum):
    """
    Content type enum for routing dispatch.

    The router dispatches on content_type, not on data source, so an earnings
    article retrieved via NewsAPI correctly routes to EarningsAnalyzer rather
    than NewsAnalyzer.
    """
    NEWS     = "NEWS"
    EARNINGS = "EARNINGS"
    MARKET   = "MARKET"
    MACRO    = "MACRO"

# Schema definition used as a reference and for initializing empty analysis dicts.
# Not enforced at runtime; all fields are populated progressively as the pipeline runs.

ANALYSIS_SCHEMA = {
    "ticker": str,              # Stock symbol, e.g., "AAPL"
    "earnings_analysis": str,   # EarningsAnalyzer narrative output
    "news_analysis": str,       # NewsAnalyzer narrative output
    "market_analysis": str,     # MarketAnalyzer narrative output
    "synthesis": str,           # InvestmentResearchAgent synthesis narrative
    "evaluation_score": float,  # EvaluatorOptimizer score, 0-10
                                # 0-10 chosen over 0-100 based on research showing
                                # 1-100 scales produce round-number bias and range
                                # underutilization in LLM evaluators
                                # (Doosterlinck et al., 2024; EvidentlyAI, 2024).
    "evaluation_feedback": str, # EvaluatorOptimizer narrative feedback
    "reflection": str,          # Self-reflection narrative, persisted to memory
                                # so the planner can address prior gaps on the
                                # next run
    "timestamp": str,           # ISO 8601 format, e.g., "2026-09-21T10:30:00"
}


def empty_analysis(ticker: str) -> dict:
    """
    Return an empty analysis dict for a given ticker.

    All fields are initialized upfront rather than added progressively so that:
    - Downstream stages can safely reference any key without checking existence
    - The dict at any pipeline stage shows exactly which fields are populated
      and which are still empty, making the pipeline state inspectable
    - A falsy check (e.g., if analysis["synthesis"]) reliably indicates whether
      a stage has run, without risking a KeyError

    Fields are populated by each pipeline stage in order:
        1. empty_analysis()         -- initializes all fields
        2. EarningsAnalyzer         -- populates earnings_analysis
        3. NewsAnalyzer             -- populates news_analysis
        4. MarketAnalyzer           -- populates market_analysis
        5. InvestmentResearchAgent  -- populates synthesis, timestamp
        6. EvaluatorOptimizer       -- populates evaluation_score, evaluation_feedback
        7. InvestmentResearchAgent  -- populates reflection

    Args:
        ticker: Stock symbol (e.g., "AAPL")

    Returns:
        Dict with all schema fields initialized to empty values
    """
    return {
        "ticker": ticker,
        "earnings_analysis": "",
        "news_analysis": "",
        "market_analysis": "",
        "synthesis": "",
        "evaluation_score": 0.0,
        "evaluation_feedback": "",
        "reflection": "",
        "timestamp": "",
    }