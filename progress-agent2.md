# Agent 2 Progress — Bedrock Adapter + Observability

## Completed Files

### `adapters/bedrock.py`
- ✓ `BedrockAdapter` class with `complete(prompt, model_id) -> CompletionResult`
- ✓ Uses Bedrock Converse API (cleaner than invoke_model)
- ✓ Model mapping: "haiku" → Claude 3 Haiku, "sonnet" → Claude 3.5 Sonnet
- ✓ Accurate pricing calculation per 1M tokens
- ✓ Returns CompletionResult with all required fields
- ✓ No side effects on import
- ✓ Credentials from AWS config/environment

### `observability.py`
- ✓ `log_routing_decision()` — emits Datadog custom metrics
  - Metrics: cost_usd, latency_ms, escalated, input_tokens, output_tokens
  - Tags: model_used, model_id, task_category, escalated
  - Fallback to stdout if Datadog unavailable
- ✓ `log_to_neo4j()` — stores routing decisions as graph
  - Creates: (:Request)-[:ROUTED_TO]->(:Model)
  - Includes: cost, latency, difficulty, routing reason
  - Non-fatal failures (logs warning, doesn't crash)
- ✓ All observability calls wrapped in try/except

### `startup.py`
- ✓ Loads .env and validates required environment variables
- ✓ `check_bedrock()` — fires test call to confirm credentials (FATAL if fails)
- ✓ `check_datadog()` — validates API keys (NON-FATAL)
- ✓ `check_neo4j()` — pings database (NON-FATAL)
- ✓ Clear error messages with ✓/✗ indicators
- ✓ Exits immediately on Bedrock failure

### `test_bedrock.py`
- ✓ Independent test script for BedrockAdapter
- ✓ Tests both Haiku and Sonnet
- ✓ Verifies response, cost, latency, token counts

## Integration Notes

The router (Agent 1) will:
1. Call `adapter.complete()` for classification (small model)
2. Parse the JSON response to extract Classification
3. Make routing decision based on capability file
4. Call `adapter.complete()` again for execution if needed
5. Combine token counts and costs from both calls
6. Call `log_routing_decision()` and `log_to_neo4j()` with final result

The adapter doesn't know whether a call is for classification or execution — it just sends prompts and returns results. The router owns that distinction.

## Testing

Run before integration:
```bash
cd llm-router
python test_bedrock.py
```

Expected output:
- Haiku response to "What is 2 + 2?"
- Sonnet response to binary search question
- Cost, latency, and token counts for both

## Environment Variables Required

```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
DD_API_KEY=...
DD_APP_KEY=...
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

## Dependencies

Already in requirements.txt:
- boto3
- python-dotenv
- datadog-api-client
- neo4j

## Handoff to Agent 4

Agent 4 needs to add these two lines to the top of `app.py`:
```python
import startup
startup.run()
```

This ensures environment validation and connectivity checks run before Streamlit starts.
