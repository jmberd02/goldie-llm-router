# Hybrid LLM Router

Routes incoming prompts to a small or large model based on task classification
and Artificial Analysis benchmark scores.

## Setup
```
pip install -r requirements.txt
cp .env .env.local  # fill in your keys
```

## Run
```
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
