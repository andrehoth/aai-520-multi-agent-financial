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
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

## Data Sources

- Yahoo Finance (`yfinance`) -- price and market data
- NewsAPI -- financial news
- Alpha Vantage -- earnings and fundamentals
- FRED API -- macroeconomic indicators

## Repository Structure

```
aai-520-multi-agent-financial/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── investment_agent.py
│   ├── earnings_agent.py
│   ├── news_agent.py
│   └── market_agent.py
├── workflows/
│   ├── __init__.py
│   ├── prompt_chain.py
│   └── router.py
│   └── evaluator_optimizer.py
├── tools/
│   ├── __init__.py
│   ├── price_data.py
│   ├── news_data.py
│   ├── fundamentals.py
│   ├── macro_data.py
│   └── retrieval.py
├── memory/
│   ├── __init__.py
│   └── agent_memory.py
├── fixtures/
│   ├── news_sample.json
│   ├── fundamentals_sample.json
│   └── macro_sample.json
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── notebook.ipynb
```


## Acknowledgments

Dr. Kahila Mokhtari and AAI-520 course materials, University of San Diego.