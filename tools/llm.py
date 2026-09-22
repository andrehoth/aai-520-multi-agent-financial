# tools/llm.py
"""
Provider-independent LLM wrapper for the Multi-Agent Financial Analysis System.

All agents and workflows call call_llm() rather than the provider SDK directly.
Swapping providers requires updating this file only, with no changes to agent or
workflow code.

Provider is configured via environment variables:
    LLM_PROVIDER: gemini (default)
    LLM_MODEL:    gemini-3.6-flash (default if not set)

Temperature is passed per call because pipeline stages have meaningfully
different needs. Planning and summarization benefit from higher values
while evaluation and extraction benefit from lower values for consistency.
"""

import os
from dotenv import load_dotenv

load_dotenv()

USING_MOCK = False

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")


def call_llm(prompt: str, system: str = None, temperature: float = 0.7) -> str:
    """
    Make a single LLM call and return the response as a plain string.

    Args:
        prompt:      User-turn content sent to the model
        system:      Optional system prompt defining the agent role or behavior
        temperature: Sampling temperature (0.0 to 1.0). Higher values produce
                     more varied output; lower values produce more deterministic
                     output. Recommended values by stage:
                         Planning, summarization: 0.7
                         Extraction, evaluation:  0.2

    Returns:
        Model response as a plain string
    """
    if USING_MOCK:
        return _mock_response(prompt)
    if LLM_PROVIDER == "gemini":
        return _call_gemini(prompt, system, temperature)
    raise ValueError(
        f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. "
        f"Supported providers: gemini"
    )


def _call_gemini(prompt: str, system: str, temperature: float) -> str:
    """
    Call the Google Gemini API and return the response text.
    Requires GEMINI_API_KEY in environment.
    """
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system if system else None,
    )
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=config,
    )
    return response.text


def _mock_response(prompt: str) -> str:
    """
    Return a shape-correct stub response for development without API calls.
    """
    return f"[MOCK RESPONSE] Received prompt of {len(prompt)} characters."