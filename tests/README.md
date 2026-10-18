# Tests

Automated tests for the Multi-Agent Financial Analysis System. The LLM provider
and every data API are mocked, so the suite needs no API keys and makes no
network calls.

Run from the repository root:

```bash
python -m pytest -v
```

| File | Covers |
|---|---|
| test_schema_contract.py | Inter-agent schema and the ContentType enum |
| test_router.py | ContentRouter dispatch by content type |
| test_evaluator_optimizer.py | Evaluator loop threshold and iteration limit |
| test_llm.py | call_llm retry behavior |
| test_news_data.py, test_price_data.py, test_macro_data.py | Data tool error handling |
| test_fundamentals.py | Alpha Vantage error handling, API key redaction, caching, and request spacing |
| test_specialist_agents.py | Specialist agents skipping the LLM call when no data is available |

See Section 10 of `docs/architecture.md` for details.
