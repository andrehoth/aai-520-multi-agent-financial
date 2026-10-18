# tools/llm.py
"""
Provider-independent LLM wrapper for the Multi-Agent Financial Analysis System.

All agents and workflows call call_llm() rather than the provider SDK directly.
Swapping providers requires updating this file only, with no changes to agent or
workflow code. Only the "gemini" provider is currently implemented; adding
another requires a new _call_<provider>() function and a matching branch in
call_llm().

Configuration is read from environment variables (see .env.example):
    GEMINI_API_KEY: required for the gemini provider
    LLM_PROVIDER:   optional, defaults to "gemini"
    LLM_MODEL:      optional, defaults to "gemini-3.6-flash"; passed to the
                    provider API as-is

Temperature is passed per call because pipeline stages have meaningfully
different needs. Planning, synthesis, and specialist analysis benefit from
higher values while classification, extraction, and evaluation benefit from
lower values for consistency.

Retry behavior: call_llm() makes up to 3 attempts, waiting 5s and then 10s
between attempts (exponential backoff), before the last error is raised. Only
failures that a provider function raises as TransientLLMError are retried (for
Gemini: server errors, rate limits, and connection failures). Configuration
errors, invalid API keys, unknown model names, and an exhausted spending cap
fail immediately.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

USING_MOCK = False

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")


class TransientLLMError(Exception):
    """
    Raised by a provider function (such as _call_gemini) for failures that are
    worth retrying, for example an overloaded server or a rate limit. call_llm()
    retries only this type, so each provider decides what counts as transient
    while the retry policy stays in one place.
    """


def call_llm(prompt: str, system: str = None, temperature: float = 0.7) -> str:
    """
    Make a single LLM call and return the response as a plain string.

    Args:
        prompt:      User-turn content sent to the model
        system:      Optional system prompt defining the agent role or behavior
        temperature: Sampling temperature (0.0 to 1.0). Higher values produce
                     more varied output; lower values produce more deterministic
                     output. Values used by stage:
                         Planning, synthesis, specialist analysis: 0.7
                         Classification, extraction, evaluation:   0.2

    Returns:
        Model response as a plain string

    A call that fails with TransientLLMError is attempted up to 3 times,
    waiting 5s and then 10s between attempts (exponential backoff), before the
    last error is raised. Any other exception, such as a configuration error,
    an invalid API key, or an unknown model, propagates immediately.
    """

    if USING_MOCK:
        return _mock_response(prompt)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            if LLM_PROVIDER == "gemini":
                return _call_gemini(prompt, system, temperature)
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. "
                f"Supported providers: gemini"
            )
        except TransientLLMError as e:
            # Only failures a provider marked as transient are retried. Every
            # other exception (ValueError for configuration, an invalid key,
            # an unknown model) propagates immediately.
            if attempt < max_retries - 1:
                wait = 5 * (2**attempt)  # 5s after attempt 1, 10s after attempt 2
                print(
                    f"      LLM call failed (attempt {attempt + 1}/{max_retries}): "
                    f"{e}. Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                raise


def _call_gemini(prompt: str, system: str, temperature: float) -> str:
    """
    Call the Google Gemini API and return the response text.
    Requires GEMINI_API_KEY in environment.
    AFC (automatic function calling) is explicitly disabled since this
    wrapper makes simple text generation calls with no tools.

    Server errors (5xx), rate limits (429), and connection failures are
    re-raised as TransientLLMError so call_llm() retries them. Other client
    errors, such as an invalid API key, an unknown model, or an exhausted
    spending cap (also reported as 429), propagate unchanged so they fail
    immediately.
    """
    import httpx
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system if system else None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
    )
    try:
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=config,
        )
    except (errors.ServerError, httpx.TransportError) as e:
        # 5xx responses and connection-level failures (reset, timeout, DNS)
        raise TransientLLMError(f"{type(e).__name__}: {e}") from e
    except errors.ClientError as e:
        # 429 usually means a short-lived rate limit, which is worth retrying.
        # The API also reports an exhausted spending cap as 429, and waiting a
        # few seconds cannot fix that, so it propagates immediately. Other 4xx
        # errors (invalid key, unknown model) are configuration problems that
        # retrying cannot fix either.
        is_rate_limit = getattr(e, "code", None) == 429
        if is_rate_limit and "spending cap" not in str(e).lower():
            raise TransientLLMError(f"{type(e).__name__}: {e}") from e
        raise
    return response.text


def _mock_response(prompt: str) -> str:
    """
    Return a shape-correct stub response for development without API calls.
    """
    return f"[MOCK RESPONSE] Received prompt of {len(prompt)} characters."
