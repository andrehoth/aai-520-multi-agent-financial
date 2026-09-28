# memory/agent_memory.py
"""
Persistent memory for the Multi-Agent Financial Analysis System.

Reads and writes a JSON file that persists analysis results across runs.
The planner reads prior memory before generating a research plan, allowing
the agent to address gaps identified in previous analyses.

Memory file location: data/agent_memory.json (gitignored -- runtime state only)

Memory structure:
    {
        "AAPL": [
            {
                "ticker": "AAPL",
                "synthesis": "...",
                "evaluation_score": 8.5,
                "reflection": "...",
                "timestamp": "2026-09-21T10:30:00"
            },
            ...
        ]
    }

Each ticker maps to a list of prior analyses, most recent first.
The planner receives the most recent entry for the requested ticker.
"""

import json
import os
from pathlib import Path

# Memory file lives in data/ which is gitignored runtime state
MEMORY_DIR  = Path("data")
MEMORY_FILE = MEMORY_DIR / "agent_memory.json"

# Maximum number of prior runs to retain per ticker.
# Older entries are dropped to keep the memory file manageable
# and the planner context focused on recent analyses.
MAX_ENTRIES_PER_TICKER = 5


def load_memory(ticker: str) -> dict | None:
    """
    Load the most recent memory entry for a given ticker.

    Args:
        ticker: Stock symbol (e.g., "AAPL")

    Returns:
        Most recent analysis dict for the ticker, or None if no prior run exists
    """
    if not MEMORY_FILE.exists():
        return None

    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

    entries = memory.get(ticker.upper(), [])
    return entries[0] if entries else None


def save_memory(analysis: dict) -> None:
    """
    Save a completed analysis dict to memory for the given ticker.

    Prepends the new entry to the ticker's history and trims to
    MAX_ENTRIES_PER_TICKER to keep the memory file manageable.

    Args:
        analysis: Completed analysis dict (see agents/schema.py)
    """
    # Create data/ directory if it does not exist
    MEMORY_DIR.mkdir(exist_ok=True)

    # Load existing memory or start fresh
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
    else:
        memory = {}

    ticker = analysis["ticker"].upper()

    # Prepend new entry and trim to max entries
    entries = memory.get(ticker, [])
    entries.insert(0, analysis)
    memory[ticker] = entries[:MAX_ENTRIES_PER_TICKER]

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def clear_memory(ticker: str = None) -> None:
    if not MEMORY_FILE.exists():
        return

    if ticker is None:
        with open(MEMORY_FILE, "w") as f:
            json.dump({}, f, indent=2)
        return

    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

    memory.pop(ticker.upper(), None)

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)