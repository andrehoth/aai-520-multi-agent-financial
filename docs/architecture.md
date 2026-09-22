# Architecture: Multi-Agent Financial Analysis System

AAI-520 Final Project | University of San Diego | Andre Hoth & Ken Lai

---

## 1. Project Objective

Given a stock ticker symbol, the system autonomously plans a research strategy,
retrieves financial and news data from multiple sources, routes that content to
specialized analyst agents, synthesizes a coherent investment analysis, evaluates
and refines its own output, and retains memory across runs to improve future
analyses. The system satisfies the four agent functions and three workflow patterns
defined in the AAI-520 course rubric.

---

## 2. System Pipeline

    Ticker Input
         |
    InvestmentResearchAgent -- Planner       [Agent Function: Planning]
         |                          |
         |                    AgentMemory    [Agent Function: Memory]
         |
    Tools Layer                              [Agent Function: Dynamic Tool Use]
         |
    NewsProcessingChain                      [Workflow 1: Prompt Chaining]
    Ingest > Preprocess > Classify > Extract > Summarize
         |
    ContentRouter                            [Workflow 2: Routing]
         |
         |--------------|--------------|
    EarningsAnalyzer  NewsAnalyzer  MarketAnalyzer
         |--------------|--------------|
         |
    InvestmentResearchAgent -- Synthesis
         |
    EvaluatorOptimizer                       [Workflow 3: Evaluator-Optimizer]
    Generate > Evaluate > Feedback > Refine
         |
    InvestmentResearchAgent -- Self-Reflection  [Agent Function: Self-Reflection]
         |
    Final Investment Analysis Report

---

## 3. Repository Structure

    aai-520-multi-agent-financial/
    agents/
        __init__.py
        base_agent.py          # Base Agent class
        investment_agent.py    # Orchestrator: planning, synthesis, reflection, memory
        earnings_agent.py      # Specialist: earnings and income statement analysis
        news_agent.py          # Specialist: news content analysis
        market_agent.py        # Specialist: price and macroeconomic analysis
        schema.py              # Inter-agent data schema and empty_analysis initializer
    workflows/
        __init__.py
        prompt_chain.py        # Workflow 1: five-stage news processing chain
        router.py              # Workflow 2: content classification and dispatch
        evaluator_optimizer.py # Workflow 3: generate-evaluate-refine loop
    tools/
        __init__.py
        llm.py                 # Provider-independent LLM wrapper
        price_data.py          # yfinance: OHLCV history and price summary
        news_data.py           # NewsAPI: financial news articles
        fundamentals.py        # Alpha Vantage: earnings and income statements
        macro_data.py          # FRED API: fed funds rate, CPI, unemployment
        retrieval.py           # FAISS: vector store and semantic retrieval (stub)
    memory/
        __init__.py
        agent_memory.py        # JSON-backed persistent memory across runs
    docs/
        architecture.md        # This document
    fixtures/                  # Mock data for development
    .env.example               # Required environment variable names
    .gitignore
    requirements.txt
    README.md
    notebook.ipynb             # Primary graded deliverable

---

## 4. Data Sources and Rubric Mapping

Data source selection is driven directly by the rubric's three specialist agents.
Domain boundaries follow agent responsibilities, not arbitrary groupings.

| Rubric Requirement  | Specialist Agent  | Data Domain    | Tool            | Source        |
|---------------------|-------------------|----------------|-----------------|---------------|
| Routing: Earnings   | EarningsAnalyzer  | Fundamentals   | fundamentals.py | Alpha Vantage |
| Routing: News       | NewsAnalyzer      | Financial news | news_data.py    | NewsAPI       |
| Routing: Market     | MarketAnalyzer    | Price data     | price_data.py   | yfinance      |
| Routing: Market     | MarketAnalyzer    | Macro context  | macro_data.py   | FRED API      |

All sources are drawn from the assignment brief's recommended list.

---

## 5. Inter-Agent Data Schema

Defined in agents/schema.py. A narrative dict is used rather than a typed
structured schema. See Section 6 for the design decision and tradeoffs.

    {
        "ticker":               str,    # Stock symbol, e.g., "AAPL"
        "earnings_analysis":    str,    # EarningsAnalyzer narrative output
        "news_analysis":        str,    # NewsAnalyzer narrative output
        "market_analysis":      str,    # MarketAnalyzer narrative output
        "synthesis":            str,    # InvestmentResearchAgent synthesis narrative
        "evaluation_score":     float,  # EvaluatorOptimizer score, 0-10
        "evaluation_feedback":  str,    # EvaluatorOptimizer narrative feedback
        "reflection":           str,    # Self-reflection narrative
        "timestamp":            str,    # ISO 8601, e.g., "2026-09-21T10:30:00"
    }

The dict is initialized via empty_analysis(ticker) at the start of each run.
All fields are populated in sequence as the pipeline progresses. Empty string
fields reliably indicate stages that have not yet run, allowing safe falsy checks
without risking a KeyError.

---

## 6. Design Decisions

### 6.1 Narrative Dict vs. Typed Structured Schema

Decision: Each specialist agent produces a narrative string rather than a
structured dict with typed fields.

Rationale: The total data volume across all four tools fits comfortably within
a single LLM context window. LLM synthesis benefits from coherent narrative input
over fragmented structured fields. Prompt quality and tool data richness drive
output quality, not schema format.

Tradeoffs accepted:
- Structured fields would make it easier to isolate weak specialist output
  programmatically, but with three specialists and a small number of demonstration
  runs, visual inspection of notebook output is sufficient
- Structured fields would simplify automated comparison across runs, but the
  system is designed for single-ticker demonstration, not high-volume analysis
- The evaluator-optimizer returns a numeric score alongside narrative feedback,
  covering the primary debugging use case without requiring schema enforcement

### 6.2 Evaluation Score Scale: 0-10

Decision: The EvaluatorOptimizer scores analyses on a 0-10 integer scale.

Rationale: Research shows 1-100 scales produce round-number bias and range
underutilization in LLM evaluators, with scores clustering in a narrow
high-scoring band regardless of actual output quality. A 1-10 scale achieves
higher inter-rater consistency (Doosterlinck et al., 2024; EvidentlyAI, 2024).

Note: A detailed rubric with anchor descriptions at each score level is required
for consistent results regardless of scale choice. This rubric is defined in
workflows/evaluator_optimizer.py.

### 6.3 Provider-Independent LLM Wrapper

Decision: All agents and workflows call tools/llm.py:call_llm() rather than
a provider SDK directly.

Rationale: Swapping providers requires updating one file only, with no changes
to agent or workflow code. Provider and model are configured via environment
variables (LLM_PROVIDER, LLM_MODEL).

Current provider: Google Gemini (gemini-3.6-flash), free tier.
Anthropic support can be added to _call_anthropic() in tools/llm.py if needed.

### 6.4 Module-First, Notebook-Last

Decision: All system logic lives in .py files. The notebook imports from
those files and serves as the orchestration and demonstration layer only.

Rationale: This eliminates notebook merge conflicts, produces a readable GitHub
history that reflects genuine collaboration, and yields a notebook that is clean
and well-commented for grading. The notebook is populated incrementally as
components are completed across Modules 4-6.

### 6.5 FAISS Retrieval

### 6.5 FAISS Retrieval

Decision: Not implemented.

The rubric phrase "dynamic tool use (APIs, datasets, retrieval)" was confirmed
by the course instructor to not require a RAG implementation. The focus should
be on the required agentic components: planning, dynamic tool use, routing, and
self-reflection. The four data tool API calls satisfy the retrieval requirement
in scope (Mokhtari Jadid, K., personal communication, September 2026).

---

## 7. LLM Temperature Guidelines

Temperature is passed per call rather than set globally, because pipeline stages
have meaningfully different needs.

| Stage          | Recommended Temperature | Rationale                               |
|----------------|-------------------------|-----------------------------------------|
| Planning       | 0.7                     | Varied research angles beneficial       |
| Summarization  | 0.7                     | Narrative flexibility improves readability |
| Extraction     | 0.2                     | Consistent signal identification        |
| Evaluation     | 0.2                     | Deterministic scoring for stable loop   |

---

## 8. Collaboration Approach

### Branching Strategy

- main: always stable and working
- feature branches per component area
- Pull requests merge into main as components complete

### Environment Setup

See README.md for full installation instructions. Key points:

- Virtual environment is created parallel to the repo, not inside it
- API keys go in .env (gitignored); key names are documented in .env.example
- nbstripout --install must be run inside the repo by each collaborator
- Dependencies are installed incrementally as modules are implemented

---

## 9. Implementation Status

| File                             | Status   |
|----------------------------------|----------|
| tools/price_data.py              | Complete |
| tools/news_data.py               | Complete |
| tools/fundamentals.py            | Complete |
| tools/macro_data.py              | Complete |
| tools/llm.py                     | Complete |
| tools/retrieval.py               | Stub     |
| agents/schema.py                 | Complete |
| agents/base_agent.py             | Complete |
| agents/investment_agent.py       | Stub     |
| agents/earnings_agent.py         | Stub     |
| agents/news_agent.py             | Stub     |
| agents/market_agent.py           | Stub     |
| workflows/prompt_chain.py        | Stub     |
| workflows/router.py              | Stub     |
| workflows/evaluator_optimizer.py | Stub     |
| memory/agent_memory.py           | Stub     |
| notebook.ipynb                   | Empty    |

---

## 10. References

Doosterlinck, K., et al. (2024). Evaluating the consistency of LLM evaluators.
https://arxiv.org/html/2412.00543v1

EvidentlyAI. (2024). LLM-as-a-judge guide.
https://www.evidentlyai.com/llm-evaluation/llm-as-a-judge

Mokhtari Jadid, K. (2026, September). [Response to student question on RAG
requirement]. AAI-520 course Slack channel, University of San Diego.
