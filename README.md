# Multi-Agent Financial Analysis System

This project is a part of the AAI-520 Natural Language Processing and GenAI course
in the Applied Artificial Intelligence Program at the University of San Diego (USD).

**Project Status:** Active

## Project Intro / Objective

This system implements an agentic AI that researches financial markets using
multiple specialized LLM agents. Given a stock ticker, the agent plans its
research, retrieves financial, news, and macroeconomic data, analyzes it with
specialist agents, synthesizes an investment analysis, evaluates and refines its
own output, and saves a reflection to memory for the next run. It demonstrates
three workflow patterns (prompt chaining, routing, and evaluator-optimizer) and
four agent functions (planning, dynamic tool use, self-reflection, and memory
across runs).

## Team Members

- Andre Hoth
- Ken Lai

## Methods Used

- LLM-based agents: planning, dynamic tool use, self-reflection, and memory
- Prompt chaining, routing, and evaluator-optimizer workflows
- LLM-as-a-judge evaluation
- Data visualization

## Technologies

- Python
- Google Gemini API
- yfinance, NewsAPI, Alpha Vantage, and FRED API
- pandas and matplotlib
- pytest and Jupyter

## Project Description

The InvestmentResearchAgent runs a seven-stage pipeline: it plans its research
using the memory of prior runs, processes news through a five-stage prompt chain,
runs earnings, news, and market specialist agents, synthesizes their output,
evaluates and refines the synthesis, and then writes a self-reflection and saves
the result to memory. The content router (Workflow 2) is implemented and
demonstrated separately; the pipeline calls the specialist agents directly.

- Notebook: `AAI520_MultiAgent_Financial_Analysis.ipynb`, with an exported copy
  that includes outputs in `AAI520_MultiAgent_Financial_Analysis.html`
- Design decisions and test approach: `docs/architecture.md`

## Installation

```bash
# Clone the repository
git clone https://github.com/andrehoth/aai-520-multi-agent-financial.git
cd aai-520-multi-agent-financial

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add your API keys to .env

# Install nbstripout Git hook (each collaborator must run this)
nbstripout --install
```

## API Keys and Usage Limits

| Key | Source | Notes |
|---|---|---|
| GEMINI_API_KEY | aistudio.google.com | A full notebook run makes dozens of LLM calls; check your quota or spend cap first |
| NEWSAPI_KEY | newsapi.org | |
| ALPHA_VANTAGE_KEY | alphavantage.co | The free key allows 25 requests per day and 1 per second; responses are cached and requests spaced, so a full run uses about 2 requests |
| FRED_API_KEY | fred.stlouisfed.org | |

Two optional settings, `LLM_PROVIDER` (default `gemini`, the only implemented
provider) and `LLM_MODEL` (default `gemini-3.6-flash`), are documented in
`.env.example`.

## Usage

Run the notebook: open `AAI520_MultiAgent_Financial_Analysis.ipynb` in VS Code or
Jupyter, select the `venv` kernel, restart the kernel, and run all cells. Memory
is stored in `data/agent_memory.json`, which is created at runtime and is not
tracked by Git.

Run the agent directly:

```python
from agents.investment_agent import InvestmentResearchAgent

agent = InvestmentResearchAgent("AAPL")
analysis = agent.run()
print(analysis["synthesis"])
```

Run the tests (no API keys or network access are needed):

```bash
python -m pytest -v
```

## Data Sources

- Yahoo Finance (yfinance): price and market data
- NewsAPI: financial news articles
- Alpha Vantage: earnings and income statement data
- FRED API: macroeconomic indicators

## Repository Structure

```
aai-520-multi-agent-financial/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── investment_agent.py
│   ├── earnings_agent.py
│   ├── news_agent.py
│   ├── market_agent.py
│   └── schema.py
├── workflows/
│   ├── __init__.py
│   ├── prompt_chain.py
│   ├── router.py
│   └── evaluator_optimizer.py
├── tools/
│   ├── __init__.py
│   ├── llm.py
│   ├── price_data.py
│   ├── news_data.py
│   ├── fundamentals.py
│   └── macro_data.py
├── memory/
│   ├── __init__.py
│   └── agent_memory.py
├── tests/
│   ├── __init__.py
│   ├── README.md
│   ├── test_schema_contract.py
│   ├── test_router.py
│   ├── test_evaluator_optimizer.py
│   ├── test_llm.py
│   ├── test_news_data.py
│   ├── test_price_data.py
│   ├── test_fundamentals.py
│   ├── test_macro_data.py
│   └── test_specialist_agents.py
├── docs/
│   └── architecture.md
├── .env.example
├── .gitignore
├── LICENSE
├── requirements.txt
├── README.md
├── AAI520_MultiAgent_Financial_Analysis.ipynb
└── AAI520_MultiAgent_Financial_Analysis.html
```

## AI Use Disclosure

Claude (Anthropic) was used throughout this project to help design and write code
and tests, debug failures, write documentation, and review outputs. See the AI Use
Disclosure in the notebook for details.

## License

See the LICENSE file.

## Acknowledgments

Dr. Kahila Mokhtari Jadid and AAI-520 course materials, University of San Diego.
