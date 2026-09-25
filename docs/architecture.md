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
    memory/
        __init__.py
        agent_memory.py        # JSON-backed persistent memory across runs
    docs/
        architecture.md        # This document
    fixtures/                  # Shared JSON fixtures for development and testing
    tests/
        __init__.py
        test_schema_contract.py    # Validates inter-agent schema contract
        test_router.py             # Validates routing dispatch by content type
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

## 10. Testing Approach

Tests live in tests/ and use shared JSON fixtures from fixtures/. Both teammates
maintain fixtures so that Ken's prompt chain output and Andre's router and agent
interfaces are validated against the same contract.

### test_schema_contract.py

Validates the inter-agent data schema defined in agents/schema.py:
- All required fields present in empty_analysis() output
- evaluation_score initialized as float
- All string fields initialized as empty strings
- Schema keys match ANALYSIS_SCHEMA keys

### test_router.py

Validates that the ContentRouter dispatches correctly by content type:
- NEWS content routes to NewsAnalyzer
- EARNINGS content routes to EarningsAnalyzer
- MARKET content routes to MarketAnalyzer
- MACRO content routes to MarketAnalyzer
- Router dispatches on content, not on data source

The router tests use fixture files from fixtures/ so that both teammates
can validate routing behavior against the same synthetic inputs without
making live API or LLM calls.

### Fixture conventions

- All fixtures are synthetic -- label clearly in the fixture file
- File names follow the pattern: {content_type}_{ticker}_{index}.json
  e.g., news_aapl_001.json, earnings_aapl_001.json
- Mock runs use the same fixture contract as live runs
- Fixtures are committed to the repo and shared between teammates

---

## 11. References

Doosterlinck, K., et al. (2024). Evaluating the consistency of LLM evaluators.
https://arxiv.org/html/2412.00543v1

EvidentlyAI. (2024). LLM-as-a-judge guide.
https://www.evidentlyai.com/llm-evaluation/llm-as-a-judge

Mokhtari Jadid, K. (2026, September). [Response to student question on RAG
requirement]. AAI-520 course Slack channel, University of San Diego.

## 12. Implementation Guide for Specialist Agents

Each specialist agent follows the same pattern. Inherit from BaseAgent, override
system_prompt and temperature, implement run() to populate the correct schema
field, and return the analysis dict.

### Pattern

    from agents.base_agent import BaseAgent

    class EarningsAnalyzer(BaseAgent):
        temperature = 0.7  # override if needed; use 0.2 for extraction tasks

        @property
        def system_prompt(self) -> str:
            return (
                f"You are a financial earnings analyst specializing in {self.ticker}. "
                f"Analyze earnings trends, revenue growth, and profit margins. "
                f"Be factual, concise, and grounded in the data provided."
            )

        def run(self, analysis: dict) -> dict:
            # 1. Fetch data using the relevant tool
            from tools.fundamentals import fetch_earnings, fetch_income_statement
            earnings = fetch_earnings(self.ticker)
            income = fetch_income_statement(self.ticker)

            # 2. Build a prompt with the fetched data
            prompt = (
                f"Analyze the following earnings and income data for {self.ticker}:\n\n"
                f"Earnings history:\n{earnings}\n\n"
                f"Income statements:\n{income}\n\n"
                f"Provide a concise narrative analysis covering earnings trends, "
                f"revenue growth, profit margins, and any notable surprises."
            )

            # 3. Call the LLM via self.call() -- uses self.system_prompt and self.temperature
            analysis["earnings_analysis"] = self.call(prompt)

            # 4. Return the updated analysis dict
            return analysis

### Key rules

- Always call self.call(prompt) rather than importing call_llm directly
- Always populate exactly one schema field per specialist -- see agents/schema.py
- Always return the full analysis dict, not just the field value
- Import tools inside run() rather than at module level to keep dependencies explicit
- Temperature 0.7 for narrative analysis; 0.2 for extraction or structured output

### News agent specifics

news_agent.py receives its input from the prompt chain output, not directly
from tools/news_data.py. The prompt chain processes raw articles through five
stages (Ingest, Preprocess, Classify, Extract, Summarize) and returns a processed
summary. The news agent's run() method receives the analysis dict after the
prompt chain has already populated context, and produces analysis["news_analysis"].

The prompt chain (workflows/prompt_chain.py) is Ken's primary ownership and
should be implemented before news_agent.py, since the news agent depends on
its output.

### Schema reference

    Field to populate      Owner agent
    earnings_analysis      EarningsAnalyzer
    news_analysis          NewsAnalyzer
    market_analysis        MarketAnalyzer
    synthesis              InvestmentResearchAgent
    evaluation_score       EvaluatorOptimizer
    evaluation_feedback    EvaluatorOptimizer
    reflection             InvestmentResearchAgent

### Workflow implementation pattern

Workflows follow the same dict-passing pattern but are not subclasses of BaseAgent.
They import call_llm directly from tools/llm.py and accept and return the
analysis dict.

    from tools.llm import call_llm

    class NewsProcessingChain:
        def __init__(self, ticker: str):
            self.ticker = ticker

        def run(self, articles: list[dict]) -> str:
            # Each stage passes output to the next
            preprocessed = self._preprocess(articles)
            classified   = self._classify(preprocessed)
            extracted    = self._extract(classified)
            summary      = self._summarize(extracted)
            return summary

        def _preprocess(self, articles: list[dict]) -> str:
            prompt = f"Clean and normalize the following articles:\n{articles}"
            return call_llm(prompt, temperature=0.2)

        # remaining stages follow the same pattern


