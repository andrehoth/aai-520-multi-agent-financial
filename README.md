# Multi-Agent Financial Analysis System

This project is a part of the AAI-520 Natural Language Processing and GenAI course
in the Applied Artificial Intelligence Program at the University of San Diego (USD).

**Project Status:** Active

## Project Intro / Objective

This system implements an agentic AI that researches financial markets using
multiple specialized LLM agents. It demonstrates three workflow patterns
(prompt chaining, routing, and evaluator-optimizer) and four agent functions
(planning, dynamic tool use, self-reflection, and memory across runs).

## Team Members

- Andre Hoth
- Ken Lai

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

## API Keys Required

All keys are free tier and require no credit card.

| Key | Source |
|---|---|
| GEMINI_API_KEY | aistudio.google.com |
| NEWSAPI_KEY | newsapi.org |
| ALPHA_VANTAGE_KEY | alphavantage.co |
| FRED_API_KEY | fred.stlouisfed.org |

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
│   ├── test_schema_contract.py
│   └── test_router.py
├── fixtures/
├── docs/
│   └── architecture.md
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── notebook.ipynb
```

## Acknowledgments

Dr. Kahila Mokhtari and AAI-520 course materials, University of San Diego.
