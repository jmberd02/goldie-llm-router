# Hybrid LLM Router

Routes incoming prompts between:
- **Small model**: Ollama (qwen2.5:1.5b) - free, local
- **Large model**: AWS Bedrock (Claude 3.5 Sonnet) - cloud, paid

Routing decisions based on task classification and Artificial Analysis benchmark scores.

## Prerequisites

1. **Ollama** - Install and run locally:
   ```bash
   # Install Ollama (see https://ollama.ai)
   ollama serve
   ollama pull qwen2.5:1.5b
   ```

2. **AWS Credentials** - For Bedrock access (large model only)

## Setup
```bash
pip install -r requirements.txt
cp .env .env.local  # fill in your AWS keys
```

### Fetch Latest Capability Data (Optional)

The router includes default capability scores, but you can fetch the latest benchmark data from Artificial Analysis:

1. Get a free API key from https://artificialanalysis.ai/api-access-preview
2. Add it to your `.env` file:
   ```
   ARTIFICIAL_ANALYSIS_API_KEY=your_key_here
   ```
3. Run the fetch script:
   ```bash
   python fetch_capabilities.py
   ```

This creates `capability_data.json` with the latest scores (not committed to git).

## Run
```bash
streamlit run app.py
```

## Structure
- `models.py`         — shared dataclasses (Classification, CompletionResult)
- `capability_file.py`— Artificial Analysis benchmark scores per model
- `router.py`         — classification prompt + routing decision logic
- `startup.py`        — env loading + connectivity checks (Ollama, Bedrock)
- `adapters/`         — HybridAdapter (Ollama + Bedrock), OllamaAdapter, BedrockAdapter
- `tools/`            — mocked demo tools
- `observability.py`  — stdout + optional Datadog (metrics + logs when DD_API_KEY set)
- `docs/DATADOG_OBSERVABILITY_PLAN.md` — Datadog design and implementation plan
- `app.py`            — Streamlit UI
- `fetch_capabilities.py` — Script to fetch latest benchmark data from Artificial Analysis API

## Model Routing

The router uses a three-step process:
1. **Classify** - Small model (Ollama) analyzes the prompt and returns JSON classification
2. **Route** - Decision logic picks small or large based on difficulty and capability scores
3. **Execute** - Chosen model generates the actual response

Cost savings: Ollama is free and local, so simple queries cost $0 instead of ~$0.001-0.01 per request.

## Observability

By default each routing decision is logged to stdout. For production we use **Option B — HTTP API** (plan §4.2): Metrics API v2 for metrics and HTTP Logs Intake for logs. Set `DD_API_KEY` in `.env` (and optionally `DD_APP_KEY`, `DD_SITE`, `DD_SERVICE`, `DD_ENV` per plan §4.1) to send metrics (`llm_router.*`) and one structured log per request to Datadog. No PII is sent; prompt content is not logged. See `docs/DATADOG_OBSERVABILITY_PLAN.md` for schema, tagging, and best practices.
