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

agents/ # Agent class definitions
workflows/ # Prompt chain, router, evaluator-optimizer
tools/ # API and data wrappers
memory/ # Persistent memory manager
fixtures/ # Mock data for development
notebook.ipynb # Final deliverable


## Acknowledgments

Dr. Kahila Mokhtari and AAI-520 course materials, University of San Diego.