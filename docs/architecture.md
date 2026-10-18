# Architecture: Multi-Agent Financial Analysis System

AAI-520 Final Project | University of San Diego | Andre Hoth & Ken Lai

---

## 1. Project Objective

Given a stock ticker symbol, the system autonomously plans a research strategy,
retrieves financial and news data from multiple sources, analyzes it with
specialized analyst agents, synthesizes a coherent investment analysis, evaluates
and refines its own output, and retains memory across runs to improve future
analyses. The system satisfies the four agent functions and three workflow patterns
defined in the AAI-520 course rubric. Content routing (Workflow 2) is implemented
and demonstrated separately; the pipeline calls the specialists directly (see
Section 6.8).

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

    Note: The ContentRouter (Workflow 2, workflows/router.py) is not part of this
    flow. The orchestrator calls the three specialists directly (see Section 6.8).

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
    data/                      # Runtime memory storage -- gitignored; created on first run
        agent_memory.json      # Analysis history keyed by ticker
    docs/
        architecture.md        # This document
    tests/
        __init__.py
        README.md                      # How to run the tests
        test_schema_contract.py        # Validates inter-agent schema contract
        test_router.py                 # Validates routing dispatch by content type
        test_evaluator_optimizer.py    # Validates evaluator-optimizer loop behavior
        test_llm.py                    # Validates LLM wrapper retry behavior
        test_news_data.py              # Validates news tool error handling
        test_price_data.py             # Validates price tool error handling
        test_fundamentals.py           # Validates fundamentals tool error handling
        test_macro_data.py             # Validates macro tool error handling
        test_specialist_agents.py      # Validates specialist data-availability guards
    .env.example               # Required environment variable names
    .gitignore
    LICENSE
    requirements.txt
    README.md
    AAI520_MultiAgent_Financial_Analysis.ipynb  # Primary graded deliverable
    AAI520_MultiAgent_Financial_Analysis.html   # Exported notebook with outputs (submission copy)

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
without risking a KeyError. A specialist that has no data stores a short
unavailability note instead of an analysis (see Section 6.7), so a populated
field means the stage ran, not that it produced analysis.

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

Decision: The EvaluatorOptimizer scores analyses on a 0-10 scale. Scores are
parsed as floats, so half-point values such as 8.5 occur.

Rationale: A 10-point interval scale was selected because interval scales
(5-point and 10-point) produced more self-consistent LLM evaluations than Likert
or binary scales for most of the models compared by Lee et al. (2024). That
study did not test a 0-100 scale, so this decision does not rest on evidence that
0-100 scales perform worse. The evaluator also runs at a low sampling temperature
(0.2), since lower temperatures increased self-consistency for the open-source
model tested in the same study.

Limitation: LLM evaluator scores can vary between calls on identical text, so
small score differences between runs are not treated as evidence of improvement
or degradation.

Note: A rubric with anchor descriptions at each score level is defined in
workflows/evaluator_optimizer.py to constrain how scores are assigned.

### 6.3 Provider-Independent LLM Wrapper

Decision: All agents and workflows call tools/llm.py:call_llm() rather than
a provider SDK directly.

Rationale: Swapping providers requires updating one file only, with no changes
to agent or workflow code. Provider and model are configured via environment
variables (LLM_PROVIDER, LLM_MODEL).

Current provider: Google Gemini (gemini-3.6-flash). Only the gemini provider is
implemented; supporting another requires a new _call_<provider>() function and a
matching branch in call_llm().

Retry behavior: call_llm() makes up to three attempts when a provider function
reports a transient failure by raising TransientLLMError (for Gemini: server
errors, rate limits, and connection failures), waiting 5s and then 10s between
attempts (exponential backoff) before raising the last error. Configuration
errors, invalid API keys, unknown model names, and an exhausted spending cap
are not retried and fail immediately. Each provider function decides which of
its own errors are transient, so the retry policy stays in one place and works
for any provider. This was added after a real-world 503 from the Gemini API
during development demonstrated the need.

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
by the course instructor to not require a RAG implementation (Mokhtari Jadid,
K., personal communication, September 2026). Retrieval is provided by the four
live data tools, and development focused on the required agent functions
(planning, dynamic tool use, self-reflection, and memory) and workflow patterns.

### 6.6 NewsProcessingChain and NewsAnalyzer Interface

Decision: NewsProcessingChain is self-contained; news retrieval occurs inside
ingest() via tools/news_data.fetch_news(). The chain takes no arguments in run().

NewsAnalyzer.run() accepts processed_news as a parameter rather than fetching
news internally. The orchestrator runs the chain first and passes the output:

    chain = NewsProcessingChain(ticker)
    processed_news = chain.run()
    analysis = news_agent.run(analysis, processed_news=processed_news)

Rationale: Separating chain execution from agent analysis allows the chain output
to be inspected independently, which is useful for the notebook demonstration of
Workflow 1. The chain handles all five stages internally and returns a single
narrative string to the news agent. Ingest retrieves articles and Preprocess
formats them as text; Classify, Extract, and Summarize are the three LLM calls,
all at temperature 0.2.

### 6.7 Graceful Degradation in Data Tools

Decision: All four data tools return empty results on API failure rather than
raising exceptions and halting the pipeline.

Rationale: The tools are independent -- a NewsAPI failure should not prevent
price data or macro data from being retrieved. The synthesizer already handles
missing data explicitly by acknowledging gaps rather than fabricating figures,
so empty tool output is a valid input state.

Tradeoff accepted: A degraded run may produce a weaker analysis without surfacing
the root cause beyond a warning print statement. A production system would use
structured logging and alerting instead. The graceful degradation pattern was
chosen over fail-fast because transient API failures are common on free-tier
endpoints and should not invalidate an entire analysis run.

Silent failures: Alpha Vantage reports an exhausted daily quota (25 requests per
day on the free tier) as an HTTP 200 response carrying a message and no data, so
no exception is raised. fundamentals.py therefore inspects the response, prints
the message with the API key redacted (the message echoes the key, and requests
exceptions include the full request URL), and returns an empty list. Successful
responses are cached in memory for the session so a full notebook run requests
each endpoint once. Empty results are never cached, so a rate-limited call is
retried on the next request. The free tier also enforces a burst limit of 1
request per second, so live requests are spaced at least 1.2 seconds apart.

Specialist guard: when a specialist has no data at all, it skips the LLM call and
stores a short unavailability note, for example "Earnings and income statement
data were unavailable for analysis." Without the guard, the model is asked to
analyze empty lists and replies asking the user to supply the data. That reply
would be stored as the analysis and flow into the synthesis, evaluation,
reflection, and memory. The note matches how NewsAnalyzer handles missing news
and lets the synthesis acknowledge the gap. Partial data, such as earnings
without an income statement, is still sent to the model.

Return values on failure:
- price_data.py:   empty DataFrame (fetch_price_history), None values (fetch_price_summary)
- news_data.py:    empty list
- fundamentals.py: empty list
- macro_data.py:   dict with empty lists per indicator; individual series failures
                   do not block other series from being fetched

### 6.8 Routing Demonstrated Separately from the Pipeline

Decision: InvestmentResearchAgent calls the three specialists directly. The
ContentRouter (Workflow 2) is demonstrated separately in the notebook and covered
by tests, and is not invoked during agent.run().

Rationale: All three specialists run on every analysis in a known order, and each
retrieves its own data, so there is no mixed stream of content for a router to
classify at run time. Routing through the router would add an LLM classification
call whose result is known in advance.

Tradeoff accepted: Routing is implemented and demonstrated but not exercised by the
pipeline. Classifying retrieved news articles by content type and sending them to
the matching specialist is a possible extension.

---

## 7. LLM Temperature Guidelines

Temperature is passed per call rather than set globally, because pipeline stages
have meaningfully different needs.

| Stage                                              | Temperature | Rationale                                         |
|----------------------------------------------------|-------------|---------------------------------------------------|
| Planning, synthesis, reflection (InvestmentResearchAgent) | 0.7  | Varied research angles; narrative flexibility improves readability |
| Earnings and market analysis (specialists)         | 0.7         | BaseAgent default; narrative flexibility improves readability |
| News chain: classify, extract, summarize           | 0.2         | Consistent output from stage to stage             |
| News analysis (NewsAnalyzer)                       | 0.2         | Consistent reading of the news                    |
| Evaluation and refinement (EvaluatorOptimizer)     | 0.2         | Deterministic scoring for a stable loop           |
| Routing classification (ContentRouter)             | 0.2         | Deterministic classification                      |

These values were checked against the code by searching agents/ and workflows/
for temperature settings. EarningsAnalyzer and MarketAnalyzer set none, so they
inherit the BaseAgent default of 0.7.

---

## 8. Collaboration Approach

### Branching Strategy

- main: always stable and working
- feature branches per component area
- Pull requests merge into main as components complete

### Environment Setup

See README.md for full installation instructions. Key points:

- Virtual environment is created inside the repo at venv/ (gitignored)
- API keys go in .env (gitignored); key names are documented in .env.example
- nbstripout --install must be run inside the repo by each collaborator
- Dependencies are installed with pip install -r requirements.txt
- Tests run with python -m pytest -v (no API calls are made)

---

## 9. Implementation Status

| File                             | Status      |
|----------------------------------|-------------|
| tools/price_data.py              | Complete    |
| tools/news_data.py               | Complete    |
| tools/fundamentals.py            | Complete    |
| tools/macro_data.py              | Complete    |
| tools/llm.py                     | Complete    |
| agents/schema.py                 | Complete    |
| agents/base_agent.py             | Complete    |
| agents/investment_agent.py       | Complete    |
| agents/earnings_agent.py         | Complete    |
| agents/news_agent.py             | Complete    |
| agents/market_agent.py           | Complete    |
| data/agent_memory.json           | Runtime (gitignored) |
| workflows/prompt_chain.py        | Complete    |
| workflows/router.py              | Complete    |
| workflows/evaluator_optimizer.py | Complete    |
| memory/agent_memory.py           | Complete    |
| tests/test_schema_contract.py     | Complete   |
| tests/test_router.py              | Complete   |
| tests/test_evaluator_optimizer.py | Complete   |
| tests/test_llm.py                 | Complete   |
| tests/test_news_data.py           | Complete   |
| tests/test_price_data.py          | Complete   |
| tests/test_fundamentals.py        | Complete   |
| tests/test_macro_data.py          | Complete   |
| tests/test_specialist_agents.py   | Complete   |
| AAI520_MultiAgent_Financial_Analysis.ipynb | Complete |
| AAI520_MultiAgent_Financial_Analysis.html  | Exported from a full run |

---

## 10. Testing Approach

Tests live in tests/. All tests use mocks rather than fixtures so no live API
or LLM calls are required.

### test_schema_contract.py

Validates the inter-agent data schema defined in agents/schema.py:
- All required fields present in empty_analysis() output
- evaluation_score initialized as float
- All string fields initialized as empty strings
- Schema keys match ANALYSIS_SCHEMA keys
- ContentType enum contains all four required values
- ContentType values are uppercase strings

### test_router.py

Validates that the ContentRouter dispatches correctly by content type.
classify() and specialist agents are mocked per test -- no LLM or API calls made:
- NEWS content routes to NewsAnalyzer
- EARNINGS content routes to EarningsAnalyzer
- MARKET content routes to MarketAnalyzer
- MACRO content routes to MarketAnalyzer
- Router dispatches on content subject matter, not on data source
- Only the dispatched specialist's schema field is populated after routing
- Unrecognized LLM classification defaults to ContentType.NEWS

### test_evaluator_optimizer.py

Validates the EvaluatorOptimizer loop behavior. evaluate() and refine() are
mocked to return controlled scores without LLM calls:
- Stops immediately when threshold is already met on the first pass
- Refines and terminates early when threshold is reached on a subsequent evaluation
- Terminates at max iterations when threshold is not reached

### test_llm.py

Validates the call_llm() retry behavior. time.sleep and the provider function
are mocked so no real API calls or wait times occur:
- Succeeds when the provider recovers within three attempts, waiting 5s and then 10s
- Raises after exhausting all three attempts
- Does not retry configuration errors (unsupported provider)
- Does not retry non-transient errors such as an invalid API key

### test_news_data.py, test_price_data.py, test_fundamentals.py, test_macro_data.py

Validate graceful degradation behavior for each data tool:
- Returns empty result on API failure rather than raising
- Returns correct data structure on success

### test_fundamentals.py (Alpha Vantage specific coverage)

Beyond graceful degradation, validates the behavior specific to Alpha Vantage:
- An HTTP 200 quota message returns an empty list, reports the reason, and keeps
  the API key out of the printed output
- Exception text containing the request URL does not leak the API key
- Successful results are cached for the session and returned as independent copies
- Empty results are not cached, so a rate-limited call is retried
- Back-to-back requests are spaced to respect the 1-request-per-second burst limit

### test_specialist_agents.py

Validates the data-availability guards in EarningsAnalyzer and MarketAnalyzer,
with all fetches and LLM calls patched:
- With no data at all, the LLM call is skipped and an unavailability note is stored
- With partial data, the LLM is still called on the data that exists

---

## 11. References

Lee, N., Hong, J., & Thorne, J. (2024). Evaluating the consistency of LLM
evaluators. arXiv. https://arxiv.org/abs/2412.00543

---

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
            # 1. Fetch data using the relevant tool (module-level or local import)
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
- Temperature 0.7 for narrative analysis; 0.2 for extraction or structured output
- Tool imports may be at module level or inside run() -- both are acceptable
- If a specialist has no data at all, skip the LLM call and store a short
  unavailability note (see Section 6.7)

### News agent calling pattern

NewsAnalyzer has a different calling pattern from the other specialists.
The orchestrator must run the prompt chain first and pass the output explicitly:

    chain = NewsProcessingChain(ticker)
    processed_news = chain.run()
    analysis = news_agent.run(analysis, processed_news=processed_news)

See Section 6.6 for the full rationale.

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

Workflows are not subclasses of BaseAgent and import call_llm directly from
tools/llm.py. The router and evaluator-optimizer accept and return the analysis
dict; the news chain returns a narrative string that the orchestrator passes to
NewsAnalyzer (see Section 6.6).

    from tools.llm import call_llm

    class NewsProcessingChain:
        def __init__(self, ticker: str):
            self.ticker = ticker

        def run(self) -> str:
            # Each stage passes output to the next; ingest() fetches internally
            articles = self.ingest()
            preprocessed = self.preprocess(articles)
            classified = self.classify(preprocessed)
            extracted = self.extract(classified)
            return self.summarize(extracted)

        def ingest(self) -> list[dict]:
            from tools.news_data import fetch_news
            return fetch_news(self.ticker)

        # remaining stages follow the same pattern
