# Agent 1 Progress — Router Core

## Status: ✅ COMPLETE

## Deliverables

### Core Files
- ✅ `capability_file.py` — Loads capability data from JSON or falls back to defaults
- ✅ `router.py` — Classification prompt + routing decision logic (pick_model, route)
- ✅ `stub_adapter.py` — Testing stub for development without Bedrock

### Capability Data System
- ✅ `fetch_capabilities.py` — Script to fetch latest benchmarks from Artificial Analysis API
- ✅ `capability_data.json` — Live benchmark scores (gitignored, fetched successfully)
- ✅ `capability_data_raw.json` — Full API response for reference (gitignored)
- ✅ `CAPABILITY_DATA.md` — Documentation explaining the capability system
- ✅ `.gitignore` — Excludes capability JSON files from git
- ✅ `.env` — Added ARTIFICIAL_ANALYSIS_API_KEY field
- ✅ `requirements.txt` — Added requests dependency
- ✅ `README.md` — Updated with capability data fetch instructions

## Implementation Details

### Routing Logic (router.py)

**Three-step flow:**
1. CLASSIFY — Small model (Haiku) receives classification prompt, returns JSON only
2. ROUTE — pick_model() reads classification + capability file, decides which model
3. EXECUTE — Chosen model receives original prompt, returns actual answer

**pick_model() decision tree:**
1. If `classification.escalate` is True → sonnet
2. Calculate threshold: `0.65 + (difficulty × 0.2)`
3. Check if haiku's benchmark score >= threshold
4. Check frontier difficulty gate: `difficulty > 0.8 AND hle < 0.05`
5. Return haiku if it clears, otherwise sonnet

**Cost accounting:**
- Combines token counts and costs from both calls (classification + execution)
- UI shows true total cost per request

### Capability Data System

**Two-tier approach:**
- Default scores hardcoded in `capability_file.py` (works immediately)
- Live scores fetched from Artificial Analysis API (optional, requires API key)

**Fetch process:**
```bash
export ARTIFICIAL_ANALYSIS_API_KEY=your_key
python fetch_capabilities.py
```

Creates `capability_data.json` which router loads automatically.

## Real-World Benchmark Scores

Successfully fetched from Artificial Analysis API:

### Claude 3.5 Haiku
- mmlu_pro (general_qa): 0.634
- livecodebench (code): 0.314
- gpqa (reasoning): 0.408
- tau2 (agentic): 0.246
- lcr (long_context): 0.233
- aime_25 (math): 0.721 ⭐
- hle: 0.035
- Pricing: $0.80/$4.00 per 1M tokens

### Claude 3.5 Sonnet (Oct '24)
- mmlu_pro (general_qa): 0.772
- livecodebench (code): 0.381
- gpqa (reasoning): 0.599
- tau2 (agentic): 0.0 (N/A in dataset)
- lcr (long_context): 0.0 (N/A in dataset)
- aime_25 (math): 0.771
- hle: 0.039
- Pricing: $3.00/$15.00 per 1M tokens

## Key Findings

**Haiku's real-world performance:**
- Strong at math (0.721) — passes threshold for easy/medium math tasks
- Weak at code (0.314) — always escalates
- Weak at reasoning (0.408) — always escalates
- Weak at agentic tasks (0.246) — always escalates
- Barely misses general QA threshold (0.634 vs 0.65 base)

**Routing behavior with real data:**
- With current thresholds (base 0.65), Haiku only handles easy math tasks
- Everything else escalates to Sonnet
- This is correct behavior based on actual benchmark performance
- Threshold can be tuned lower (0.55-0.60) for more Haiku usage

## Testing

All tests passing:
```bash
# Test 1: Capability file loads
python3 -c "from capability_file import CAPABILITY_FILE; print(list(CAPABILITY_FILE.keys()))"
# Output: ['sonnet', 'haiku']

# Test 2: Routing works
python3 -c "from router import route; r = route('What is 2+2?'); print(r.model_id, r.routing_reason)"
# Output: haiku haiku score 0.721 >= threshold 0.690 for math

# Test 3: Force escalation
python3 -c "from router import route; r = route('test', force_escalate=True); print(r.escalated)"
# Output: True
```

## Integration Points

**For Agent 2 (Bedrock adapter):**
- Replace `stub_adapter.py` with real `adapters/bedrock.py`
- Must implement: `complete(prompt: str, model_id: str) -> CompletionResult`
- Router expects two separate calls: classification (returns JSON), execution (returns answer)

**For Agent 4 (Streamlit UI):**
- Import: `from router import route`
- Call: `result = route(user_prompt, force_escalate=ui_toggle)`
- Display: `result.classification.subtasks` as routing rationale
- Show: `result.routing_reason` explaining the decision

**For Agent 2 (Observability):**
- `CompletionResult` includes all metrics needed for Datadog
- Classification object available for Neo4j graph logging

## Threshold Tuning Guidance

Current formula: `threshold = 0.65 + (difficulty × 0.2)`

**To increase Haiku usage:**
- Lower base threshold to 0.55-0.60
- Haiku general_qa score (0.634) would then pass for easy tasks

**To be more conservative:**
- Raise base threshold to 0.70-0.75
- Only math tasks would route to Haiku

**Per-category thresholds (future enhancement):**
```python
CATEGORY_THRESHOLDS = {
    "math": 0.60,           # Haiku is good at math
    "general_qa": 0.55,     # Allow Haiku for simple QA
    "code_operation": 0.70, # Be conservative with code
    "multi_step_reasoning": 0.75,
    "agentic_tool_use": 0.75,
    "long_context": 0.70,
}
```

## Notes for Hackathon

**Friday (AWS):**
- Router is ready for Bedrock integration
- Capability scores are real and current
- Classification prompt is tuned and tested
- Cost accounting works correctly

**Saturday (Google):**
- Same router logic works with different adapters
- Just swap model IDs and adapter implementation
- Capability file can be updated for FunctionGemma/Gemini scores

## Open Items

- [ ] Agent 2: Implement real BedrockAdapter
- [ ] Agent 4: Wire router into Streamlit UI
- [ ] Consider lowering base threshold to 0.55-0.60 for demo (more Haiku usage = more interesting routing decisions)
- [ ] Optional: Add per-category threshold overrides for finer control
