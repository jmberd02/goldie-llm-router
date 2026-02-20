# Capability Data System

## Overview

The router uses benchmark scores from [Artificial Analysis](https://artificialanalysis.ai) to make routing decisions. These scores tell us which models can handle which types of tasks.

## How It Works

1. **Default scores** are hardcoded in `capability_file.py` as fallback values
2. **Live scores** can be fetched from the Artificial Analysis API using `fetch_capabilities.py`
3. The router loads from `capability_data.json` if it exists, otherwise uses defaults
4. `capability_data.json` is gitignored — each developer fetches their own copy

## Fetching Latest Data

```bash
# 1. Get a free API key from https://artificialanalysis.ai/api-access-preview
# 2. Add to .env file:
echo "ARTIFICIAL_ANALYSIS_API_KEY=your_key_here" >> .env

# 3. Run the fetch script:
python fetch_capabilities.py
```

This creates two files (both gitignored):
- `capability_data.json` — processed scores used by the router
- `capability_data_raw.json` — full API response for reference

## Benchmark Mapping

The router maps task categories to specific Artificial Analysis benchmarks:

| Task Category | Benchmark | Description |
|---|---|---|
| `general_qa` | `mmlu_pro` | Graduate-level knowledge questions |
| `code_operation` | `livecodebench` | Real-world coding tasks |
| `multi_step_reasoning` | `gpqa` | PhD-level reasoning problems |
| `agentic_tool_use` | `tau2` | Multi-turn tool coordination |
| `long_context` | `lcr` | 10k-100k token reasoning |
| `math` | `aime_25` | Advanced math problems |

## Routing Logic

For each request:

1. Small model classifies the task → returns dominant category + difficulty (0.0-1.0)
2. Router calculates threshold: `0.65 + (difficulty × 0.2)`
3. Router checks if small model's benchmark score ≥ threshold
4. If yes → route to small model, if no → escalate to large model

Example:
```
Task: "What is a binary search tree?"
Classification: general_qa, difficulty 0.2
Threshold: 0.65 + (0.2 × 0.2) = 0.69
Haiku mmlu_pro score: 0.71
Decision: 0.71 ≥ 0.69 → route to Haiku ✓
```

## Why Not Commit capability_data.json?

1. **API rate limits** — 1,000 requests/day shared across all users
2. **Freshness** — benchmarks update as new models are released
3. **Flexibility** — developers can test with different model combinations
4. **Defaults work** — the hardcoded fallback values are recent and functional

## Updating Default Scores

If you want to update the hardcoded defaults in `capability_file.py`:

1. Fetch latest data: `python fetch_capabilities.py`
2. Copy values from `capability_data.json` into `DEFAULT_CAPABILITIES` dict
3. Commit the updated `capability_file.py`

This should be done periodically (monthly?) to keep defaults current.
