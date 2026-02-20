# Hybrid LLM Router - Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACE                                    │
│                                  (Streamlit App)                                     │
│                                                                                       │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────────┐   │
│  │   Input Panel       │  │  Prompt Helper       │  │   Results Panel         │   │
│  │                     │  │  (Agent 5)           │  │                         │   │
│  │ • Demo Prompts      │  │                      │  │ • Response Display      │   │
│  │ • Custom Input      │  │ • Analyze Prompt     │  │ • Routing Decision      │   │
│  │ • Submit Button     │  │ • Suggest Rewrite    │  │ • Cost Breakdown        │   │
│  │ • Force Escalate    │  │ • Predict Route      │  │ • Token Metrics         │   │
│  │                     │  │ • Cost Optimization  │  │ • Latency Stats         │   │
│  └──────────┬──────────┘  └──────────┬───────────┘  └─────────▲───────────────┘   │
│             │                        │                          │                   │
└─────────────┼────────────────────────┼──────────────────────────┼───────────────────┘
              │                        │                          │
              │                        │                          │
              ▼                        ▼                          │
┌─────────────────────────────────────────────────────────────────┴───────────────────┐
│                              ROUTING ORCHESTRATION                                   │
│                                  (router.py)                                         │
│                                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                         THREE-STEP ROUTING FLOW                                │  │
│  │                                                                                │  │
│  │  Step 1: CLASSIFY                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │  │
│  │  │ • Send classification prompt to small model (Haiku/Ollama)          │     │  │
│  │  │ • Extract: subtasks, task_categories, difficulty, dominant_category │     │  │
│  │  │ • Parse JSON response                                                │     │  │
│  │  └─────────────────────────────────────────────────────────────────────┘     │  │
│  │                                    ▼                                           │  │
│  │  Step 2: ROUTE (pick_model)                                                   │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │  │
│  │  │ Decision Logic:                                                      │     │  │
│  │  │ 1. Force escalate? → Sonnet                                          │     │  │
│  │  │ 2. classification.escalate == True? → Sonnet                         │     │  │
│  │  │ 3. Calculate threshold = 0.40 + (difficulty × 0.2)                   │     │  │
│  │  │ 4. Lookup small model score from CAPABILITY_FILE                     │     │  │
│  │  │ 5. Frontier task check (difficulty > 0.8 AND hle < 0.05)? → Sonnet  │     │  │
│  │  │ 6. small_score >= threshold? → Haiku/Ollama : Sonnet                 │     │  │
│  │  └─────────────────────────────────────────────────────────────────────┘     │  │
│  │                                    ▼                                           │  │
│  │  Step 3: EXECUTE                                                              │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │  │
│  │  │ • Send original prompt to chosen model                               │     │  │
│  │  │ • Combine classification + execution costs                           │     │  │
│  │  │ • Return CompletionResult with full metrics                          │     │  │
│  │  └─────────────────────────────────────────────────────────────────────┘     │  │
│  │                                                                                │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                       │
└───────────────────────────────┬───────────────────────────────────────────────────┬─┘
                                │                                                   │
                                ▼                                                   │
┌───────────────────────────────────────────────────────────────┐                   │
│                    CAPABILITY SCORING                          │                   │
│                  (capability_file.py)                          │                   │
│                                                                 │                   │
│  ┌──────────────────────────────────────────────────────────┐ │                   │
│  │  CAPABILITY_FILE (Benchmark Scores)                      │ │                   │
│  │                                                           │ │                   │
│  │  Small Model (Ollama qwen2.5:1.5b):                      │ │                   │
│  │    • mmlu_pro: 0.45        (general_qa)                  │ │                   │
│  │    • livecodebench: 0.20   (code_operation)              │ │                   │
│  │    • gpqa: 0.25            (multi_step_reasoning)        │ │                   │
│  │    • tau2: 0.15            (agentic_tool_use)            │ │                   │
│  │    • lcr: 0.30             (long_context)                │ │                   │
│  │    • aime_25: 0.15         (math)                        │ │                   │
│  │    • hle: 0.01             (human-level eval)            │ │                   │
│  │    • cost: $0.00/1M tokens (FREE - local)                │ │                   │
│  │                                                           │ │                   │
│  │  Haiku (Claude 3 Haiku):                                 │ │                   │
│  │    • mmlu_pro: 0.71        • tau2: 0.35                  │ │                   │
│  │    • livecodebench: 0.378  • lcr: 0.55                   │ │                   │
│  │    • gpqa: 0.41            • aime_25: 0.30               │ │                   │
│  │    • hle: 0.03                                           │ │                   │
│  │    • cost: $0.80/$4.00 per 1M tokens (in/out)            │ │                   │
│  │                                                           │ │                   │
│  │  Sonnet (Claude 3.5 Sonnet):                             │ │                   │
│  │    • mmlu_pro: 0.90        • tau2: 0.62                  │ │                   │
│  │    • livecodebench: 0.72   • lcr: 0.82                   │ │                   │
│  │    • gpqa: 0.65            • aime_25: 0.55               │ │                   │
│  │    • hle: 0.08                                           │ │                   │
│  │    • cost: $3.00/$15.00 per 1M tokens (in/out)           │ │                   │
│  └──────────────────────────────────────────────────────────┘ │                   │
│                                                                 │                   │
│  ┌──────────────────────────────────────────────────────────┐ │                   │
│  │  TASK_TO_EVAL Mapping:                                   │ │                   │
│  │    general_qa → mmlu_pro                                 │ │                   │
│  │    code_operation → livecodebench                        │ │                   │
│  │    multi_step_reasoning → gpqa                           │ │                   │
│  │    agentic_tool_use → tau2                               │ │                   │
│  │    long_context → lcr                                    │ │                   │
│  │    math → aime_25                                        │ │                   │
│  └──────────────────────────────────────────────────────────┘ │                   │
│                                                                 │                   │
│  Data Source: Artificial Analysis API (fetch_capabilities.py)  │                   │
│  Fallback: DEFAULT_CAPABILITIES (hardcoded)                    │                   │
└─────────────────────────────────────────────────────────────────┘                   │
                                                                                      │
                                ┌─────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              ADAPTER LAYER                                         │
│                          (adapters/hybrid.py)                                      │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         HybridAdapter                                        │  │
│  │                                                                              │  │
│  │  complete(prompt, model_id) → CompletionResult                              │  │
│  │                                                                              │  │
│  │  Routing:                                                                    │  │
│  │    • model_id in ["haiku", "small"] → OllamaAdapter                         │  │
│  │    • model_id == "sonnet" → BedrockAdapter                                  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│         ┌───────────────────────────────────┬─────────────────────────────────┐   │
│         │                                   │                                 │   │
│         ▼                                   ▼                                 │   │
│  ┌──────────────────────┐          ┌──────────────────────┐                  │   │
│  │  OllamaAdapter       │          │  BedrockAdapter      │                  │   │
│  │  (ollama.py)         │          │  (bedrock.py)        │                  │   │
│  │                      │          │                      │                  │   │
│  │ • Local inference    │          │ • AWS Bedrock API    │                  │   │
│  │ • qwen2.5:1.5b       │          │ • Claude 3 Haiku     │                  │   │
│  │ • Free ($0)          │          │ • Claude 3.5 Sonnet  │                  │   │
│  │ • Fast (local)       │          │ • Paid (per token)   │                  │   │
│  │                      │          │ • Cloud latency      │                  │   │
│  │ Endpoint:            │          │                      │                  │   │
│  │ localhost:11434      │          │ Model IDs:           │                  │   │
│  │                      │          │ • haiku: claude-3-   │                  │   │
│  │ Returns:             │          │   haiku-20240307     │                  │   │
│  │ • response text      │          │ • sonnet: claude-3-5-│                  │   │
│  │ • token counts       │          │   sonnet-20241022    │                  │   │
│  │ • cost ($0)          │          │                      │                  │   │
│  │ • latency            │          │ Returns:             │                  │   │
│  └──────────┬───────────┘          │ • response text      │                  │   │
│             │                      │ • token counts       │                  │   │
│             │                      │ • calculated cost    │                  │   │
│             │                      │ • latency            │                  │   │
│             │                      └──────────┬───────────┘                  │   │
│             │                                 │                              │   │
└─────────────┼─────────────────────────────────┼──────────────────────────────┼───┘
              │                                 │                              │
              ▼                                 ▼                              │
┌──────────────────────────┐      ┌──────────────────────────┐                │
│   Ollama Server          │      │   AWS Bedrock            │                │
│   (Local)                │      │   (Cloud)                │                │
│                          │      │                          │                │
│ • Model: qwen2.5:1.5b    │      │ • Claude 3 Haiku         │                │
│ • Port: 11434            │      │ • Claude 3.5 Sonnet      │                │
│ • API: /api/generate     │      │ • API: Converse          │                │
│ • Free, fast, local      │      │ • Region: us-east-1      │                │
└──────────────────────────┘      └──────────────────────────┘                │
                                                                               │
                                                                               │
┌──────────────────────────────────────────────────────────────────────────────┼───┐
│                           DATA MODELS                                        │   │
│                          (models.py)                                         │   │
│                                                                               │   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │   │
│  │  Classification (from small model)                                      │ │   │
│  │    • subtasks: list[str]                                                │ │   │
│  │    • task_categories: dict[str, float]                                  │ │   │
│  │    • difficulty: float (0.0-1.0)                                        │ │   │
│  │    • dominant_category: str                                             │ │   │
│  │    • escalate: bool                                                     │ │   │
│  └─────────────────────────────────────────────────────────────────────────┘ │   │
│                                                                               │   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │   │
│  │  CompletionResult (final output)                                        │ │   │
│  │    • response: str                                                      │ │   │
│  │    • model_used: str ("small" | "large")                                │ │   │
│  │    • model_id: str (actual model name)                                  │ │   │
│  │    • routing_reason: str                                                │ │   │
│  │    • escalated: bool                                                    │ │   │
│  │    • input_tokens: int                                                  │ │   │
│  │    • output_tokens: int                                                 │ │   │
│  │    • cost_usd: float                                                    │ │   │
│  │    • latency_ms: float                                                  │ │   │
│  │    • classification: Optional[Classification]                           │ │   │
│  └─────────────────────────────────────────────────────────────────────────┘ │   │
└───────────────────────────────────────────────────────────────────────────────┘   │
                                                                                    │
                                                                                    │
┌───────────────────────────────────────────────────────────────────────────────────┘
│
│  ┌─────────────────────────────────────────────────────────────────────────────┐
│  │                        OBSERVABILITY & MONITORING                            │
│  │                          (observability.py)                                  │
│  │                                                                               │
│  │  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  │  log_routing_decision(result, prompt)                                  │ │
│  │  │    • Logs to stdout (console)                                          │ │
│  │  │    • Metrics: model, cost, latency, escalation, tokens, task category  │ │
│  │  │    • Format: [METRICS] model=X cost=$Y latency=Zms ...                 │ │
│  │  └────────────────────────────────────────────────────────────────────────┘ │
│  │                                                                               │
│  │  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  │  log_to_neo4j(prompt, result)                                          │ │
│  │  │    • Graph database logging (DISABLED)                                 │ │
│  │  │    • Would store: prompt → classification → model → response           │ │
│  │  └────────────────────────────────────────────────────────────────────────┘ │
│  │                                                                               │
│  │  Future integrations: Datadog, Prometheus, CloudWatch                        │
│  └───────────────────────────────────────────────────────────────────────────────┘
│
│
│  ┌─────────────────────────────────────────────────────────────────────────────┐
│  │                        TOOLS & UTILITIES                                     │
│  │                          (tools/)                                            │
│  │                                                                               │
│  │  Demo tools for testing agentic capabilities:                                │
│  │    • calendar.py          - Mock calendar operations                         │
│  │    • reminder.py          - Mock reminder setting                            │
│  │    • find_replace.py      - Text find/replace                                │
│  │    • math_solver.py       - Basic math operations                            │
│  │    • trivia_qa.py         - Factual Q&A                                      │
│  │    • summarizer.py        - Text summarization                               │
│  │    • unit_test_gen.py     - Unit test generation                             │
│  │    • multi_tool_chain.py  - Multi-step tool orchestration                    │
│  │                                                                               │
│  │  Note: Tools are mocked for demo purposes, not integrated into routing       │
│  └───────────────────────────────────────────────────────────────────────────────┘
│
│
│  ┌─────────────────────────────────────────────────────────────────────────────┐
│  │                        STARTUP & CONFIGURATION                               │
│  │                          (startup.py)                                        │
│  │                                                                               │
│  │  Initialization checks:                                                      │
│  │    1. Load environment variables (.env)                                      │
│  │    2. Verify Ollama connectivity (localhost:11434)                           │
│  │    3. Verify AWS credentials for Bedrock                                     │
│  │    4. Display startup status in Streamlit UI                                 │
│  │                                                                               │
│  │  Environment variables:                                                      │
│  │    • AWS_ACCESS_KEY_ID                                                       │
│  │    • AWS_SECRET_ACCESS_KEY                                                   │
│  │    • AWS_SESSION_TOKEN (optional, for AWS Academy)                           │
│  │    • ARTIFICIAL_ANALYSIS_API_KEY (optional, for capability updates)          │
│  └───────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST FLOW EXAMPLE                                │
└─────────────────────────────────────────────────────────────────────────────────┘

User Input: "What year was the Eiffel Tower built?"

1. Streamlit UI receives prompt
   └─> Calls router.route(prompt, force_escalate=False)

2. Router Step 1: CLASSIFY
   └─> Sends classification prompt to HybridAdapter.complete(prompt, "haiku")
       └─> HybridAdapter routes to OllamaAdapter (small model)
           └─> Ollama returns JSON:
               {
                 "subtasks": ["look up historical fact"],
                 "task_categories": {"general_qa": 0.9, ...},
                 "difficulty": 0.2,
                 "dominant_category": "general_qa",
                 "escalate": false
               }

3. Router Step 2: ROUTE (pick_model)
   └─> Lookup: TASK_TO_EVAL["general_qa"] = "mmlu_pro"
   └─> Calculate threshold: 0.40 + (0.2 × 0.2) = 0.44
   └─> Check small model score: CAPABILITY_FILE["small"]["mmlu_pro"] = 0.45
   └─> Decision: 0.45 >= 0.44 → Use small model (Haiku/Ollama)
   └─> Reason: "small model score 0.450 >= threshold 0.440 for general_qa"

4. Router Step 3: EXECUTE
   └─> Sends original prompt to HybridAdapter.complete(prompt, "haiku")
       └─> HybridAdapter routes to OllamaAdapter
           └─> Ollama returns: "The Eiffel Tower was built in 1889."

5. Router combines results
   └─> CompletionResult:
       • response: "The Eiffel Tower was built in 1889."
       • model_used: "small"
       • model_id: "qwen2.5:1.5b"
       • routing_reason: "small model score 0.450 >= threshold 0.440 for general_qa"
       • escalated: false
       • input_tokens: 120 (classification + execution)
       • output_tokens: 80 (classification + execution)
       • cost_usd: $0.00 (Ollama is free)
       • latency_ms: 450
       • classification: <Classification object>

6. Observability logs metrics
   └─> [METRICS] model=qwen2.5:1.5b cost=$0.000000 latency=450ms escalated=False ...

7. Streamlit UI displays result
   └─> Shows response, routing decision, cost breakdown, metrics


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ESCALATION FLOW EXAMPLE                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

User Input: "Check my calendar and find the next free 2-hour block, then set a 
             dentist reminder in that slot"

1. Streamlit UI receives prompt
   └─> Calls router.route(prompt, force_escalate=False)

2. Router Step 1: CLASSIFY
   └─> Ollama returns JSON:
       {
         "subtasks": ["check calendar", "find free slot", "set reminder"],
         "task_categories": {"agentic_tool_use": 0.8, "multi_step_reasoning": 0.2},
         "difficulty": 0.75,
         "dominant_category": "agentic_tool_use",
         "escalate": true  ← More than 2 subtasks!
       }

3. Router Step 2: ROUTE (pick_model)
   └─> Check: classification.escalate == true
   └─> Decision: Escalate to Sonnet
   └─> Reason: "classification flagged escalation (subtasks > 2 or difficulty >= 0.7)"

4. Router Step 3: EXECUTE
   └─> Sends original prompt to HybridAdapter.complete(prompt, "sonnet")
       └─> HybridAdapter routes to BedrockAdapter
           └─> AWS Bedrock (Claude 3.5 Sonnet) returns comprehensive response

5. Router combines results
   └─> CompletionResult:
       • model_used: "large"
       • model_id: "sonnet"
       • escalated: true
       • cost_usd: $0.003500 (Bedrock pricing)
       • latency_ms: 1800

6. Streamlit UI shows:
   └─> 🔴 Large model badge
   └─> Cost comparison: "Small model would cost: $0.00 (saved $0.003500)"


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         KEY DESIGN DECISIONS                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

1. Three-Step Routing (Classify → Route → Execute)
   • Separates task analysis from execution
   • Always uses small model for classification (fast, cheap)
   • Routing decision based on benchmark scores + difficulty

2. Hybrid Adapter Pattern
   • Abstracts model differences (Ollama vs Bedrock)
   • Unified interface: complete(prompt, model_id) → CompletionResult
   • Easy to add new model providers

3. Capability-Based Routing
   • Uses real benchmark scores from Artificial Analysis
   • Dynamic threshold calculation: base + (difficulty × multiplier)
   • Task-specific evaluation metrics (MMLU, GPQA, TAU2, etc.)

4. Cost Optimization
   • Small model (Ollama) is free and local
   • Only escalate when necessary (difficulty, subtasks, capability gaps)
   • Transparent cost tracking and comparison

5. Observability
   • Logs every routing decision with full metrics
   • Tracks: model, cost, latency, tokens, task category, escalation
   • Ready for integration with Datadog, Neo4j, CloudWatch

6. Prompt Helper Agent (Agent 5)
   • Proactively suggests prompt rewrites
   • Optimizes for small model to save costs
   • Shows predicted route and difficulty before submission
```
