# Hybrid LLM Router

Routes incoming prompts to a small or large model based on task classification
and Artificial Analysis benchmark scores.

## Setup
```bash
pip install -r requirements.txt
cp .env .env.local  # fill in your keys
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
- `startup.py`        — env loading + connectivity checks (Bedrock, Datadog, Neo4j)
- `adapters/`         — Bedrock adapter (swap for Gemini/local on Saturday)
- `tools/`            — mocked demo tools
- `observability.py`  — Datadog metrics + Neo4j graph logging
- `app.py`            — Streamlit UI
- `fetch_capabilities.py` — Script to fetch latest benchmark data from Artificial Analysis API
