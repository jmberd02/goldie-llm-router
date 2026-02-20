from __future__ import annotations
import json
import os
import time
from models import Classification, CompletionResult, TASK_TO_EVAL
from capability_file import CAPABILITY_FILE
from observability import log_routing_decision, log_to_neo4j
from dotenv import load_dotenv

load_dotenv()


CLASSIFICATION_PROMPT_TEMPLATE = """Analyze this request and respond in JSON only. No markdown, no explanation, just the JSON object.

Request: {prompt}

First, list the subtasks required to fully complete this request.
Then fill out the classification.

Respond with exactly this structure:
{{
  "subtasks": ["task1", "task2", ...],
  "task_categories": {{
    "math": 0.0,
    "code_operation": 0.0,
    "multi_step_reasoning": 0.0,
    "agentic_tool_use": 0.0,
    "long_context": 0.0,
    "general_qa": 0.0
  }},
  "difficulty": 0.0,
  "dominant_category": "one of: math, code_operation, multi_step_reasoning, agentic_tool_use, long_context, general_qa",
  "escalate": false
}}

IMPORTANT: dominant_category must be exactly one of these values:
- math
- code_operation
- multi_step_reasoning
- agentic_tool_use
- long_context
- general_qa

Difficulty guide: 0.2=simple lookup, 0.4=simple reasoning, 0.6=multi-step, 0.8=complex analysis, 1.0=frontier research
Escalation rule: if subtasks > 2 OR difficulty >= 0.7, set escalate: true
"""


# Threshold mapping: category -> env var name (used as defaults)
THRESHOLD_ENV_VARS = {
    "math": "ROUTING_THRESHOLD_MATH",
    "code_operation": "ROUTING_THRESHOLD_CODE",
    "multi_step_reasoning": "ROUTING_THRESHOLD_REASONING",
    "agentic_tool_use": "ROUTING_THRESHOLD_AGENTIC",
    "long_context": "ROUTING_THRESHOLD_LONG_CONTEXT",
    "general_qa": "ROUTING_THRESHOLD_GENERAL_QA",
}

# Default thresholds from .env or fallback values
DEFAULT_THRESHOLDS = {
    "math": float(os.getenv("ROUTING_THRESHOLD_MATH", "0.40")),
    "code_operation": float(os.getenv("ROUTING_THRESHOLD_CODE", "0.40")),
    "multi_step_reasoning": float(os.getenv("ROUTING_THRESHOLD_REASONING", "0.40")),
    "agentic_tool_use": float(os.getenv("ROUTING_THRESHOLD_AGENTIC", "0.40")),
    "long_context": float(os.getenv("ROUTING_THRESHOLD_LONG_CONTEXT", "0.40")),
    "general_qa": float(os.getenv("ROUTING_THRESHOLD_GENERAL_QA", "0.40")),
}


def get_threshold(category: str, ui_thresholds: dict = None) -> float:
    """Get threshold for a category from UI or env vars (defaults)."""
    if ui_thresholds and category in ui_thresholds:
        return ui_thresholds[category]
    return DEFAULT_THRESHOLDS.get(category, 0.40)


def pick_model(classification: Classification, ui_thresholds: dict = None) -> tuple[str, str]:
    """
    Returns (model_id, reason) based on classification and capability file.
    
    Routing rules:
    1. If classification.escalate is True → sonnet
    2. Check if small model's benchmark score clears the difficulty-adjusted threshold
    3. Check frontier difficulty gate (difficulty > 0.8 AND hle < 0.05)
    4. Return small if it clears, otherwise sonnet
    
    Threshold tuning:
    - Base threshold: 0.40 (lower for small local model - qwen3:8b)
    - Difficulty multiplier: 0.2 (how much difficulty increases threshold)
    - Ollama qwen3:8b scores (estimated):
      * mmlu_pro (general_qa): 0.45 - passes for simple questions
      * aime_25 (math): 0.15 - only basic arithmetic
      * livecodebench (code): 0.20 - minimal coding
      * gpqa (reasoning): 0.25 - weak reasoning
      * tau2 (agentic): 0.15 - minimal agentic capability
    """
    # Rule 1: Hard escalation from classification
    if classification.escalate:
        return "sonnet", "classification flagged escalation (subtasks > 2 or difficulty >= 0.7)"
    
    # Rule 2: Look up eval key and get threshold from UI or env defaults
    # Note: difficulty score is unreliable (self-assessed confidence problem)
    # The subtask count and escalate flag are the trustworthy signals
    category = classification.dominant_category
    
    # Safety check: if category is invalid, default to sonnet
    if category not in TASK_TO_EVAL:
        return "sonnet", f"invalid category '{category}' returned by classifier, defaulting to large model"
    
    eval_key = TASK_TO_EVAL[category]
    threshold = get_threshold(category, ui_thresholds)
    
    small_score = CAPABILITY_FILE["small"].get(eval_key, 0.0)
    small_hle = CAPABILITY_FILE["small"]["hle"]
    
    # Rule 3: Frontier difficulty gate
    is_frontier_task = classification.difficulty > 0.8 and small_hle < 0.05
    
    # Rule 4: Check if small model clears threshold
    if small_score >= threshold and not is_frontier_task:
        return "haiku", f"small model score {small_score:.3f} >= threshold {threshold:.3f} for {category}"
    
    # Otherwise escalate to sonnet
    if is_frontier_task:
        reason = f"frontier difficulty {classification.difficulty:.2f} with low HLE {small_hle:.3f}"
    else:
        reason = f"small model score {small_score:.3f} < threshold {threshold:.3f} for {category}"
    
    return "sonnet", reason


def route(prompt: str, force_escalate: bool = False, adapter=None, ui_thresholds: dict = None) -> CompletionResult:
    """
    Main routing entry point. Three-step flow:
    1. CLASSIFY  — small model returns JSON classification (no answer)
    2. ROUTE     — pick_model() decides which model to use
    3. EXECUTE   — chosen model returns actual answer
    
    Args:
        prompt: User's request
        force_escalate: If True, skip classification and go straight to sonnet
        adapter: Model adapter (BedrockAdapter or stub). Must have complete(prompt, model_id) method.
    
    Returns:
        CompletionResult with combined token counts and costs from both calls
    """
    start_time = time.time()
    
    # Use HybridAdapter (Ollama + Bedrock) if no adapter provided
    if adapter is None:
        from adapters.hybrid import HybridAdapter
        adapter = HybridAdapter()
    
    # Step 1: Handle force escalation
    if force_escalate:
        result = adapter.complete(prompt, "sonnet")
        result.escalated = True
        result.routing_reason = "user forced escalation"
        result.classification = None
        # Log observability
        try:
            log_routing_decision(result, prompt)
            log_to_neo4j(prompt, result)
        except Exception as e:
            print(f"[observability] warning: {e}")
        return result
    
    # Step 2: Classification call (Haiku returns JSON only)
    classification_prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(prompt=prompt)
    classification_result = adapter.complete(classification_prompt, "haiku")
    
    # Step 3: Parse classification JSON
    try:
        # Strip markdown code blocks if present
        response_text = classification_result.response.strip()
        if response_text.startswith("```"):
            # Extract JSON from markdown code block
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
        
        classification_data = json.loads(response_text)
        classification = Classification(
            subtasks=classification_data["subtasks"],
            task_categories=classification_data["task_categories"],
            difficulty=classification_data["difficulty"],
            dominant_category=classification_data["dominant_category"],
            escalate=classification_data["escalate"]
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Parse failed — default to sonnet
        result = adapter.complete(prompt, "sonnet")
        result.escalated = True
        result.routing_reason = f"classification parse failed ({type(e).__name__}), defaulting to large model"
        result.classification = None
        # Add classification call costs
        result.input_tokens += classification_result.input_tokens
        result.output_tokens += classification_result.output_tokens
        result.cost_usd += classification_result.cost_usd
        result.latency_ms = (time.time() - start_time) * 1000
        # Log observability
        try:
            log_routing_decision(result, prompt)
            log_to_neo4j(prompt, result)
        except Exception as e:
            print(f"[observability] warning: {e}")
        return result
    
    # Step 4: Route based on classification
    model_id, routing_reason = pick_model(classification, ui_thresholds)
    
    # Step 5: Execution call (chosen model returns actual answer)
    execution_result = adapter.complete(prompt, model_id)
    
    # Step 6: Build final result with combined costs
    execution_result.routing_reason = routing_reason
    execution_result.escalated = (model_id == "sonnet")
    execution_result.classification = classification
    execution_result.input_tokens += classification_result.input_tokens
    execution_result.output_tokens += classification_result.output_tokens
    execution_result.cost_usd += classification_result.cost_usd
    execution_result.latency_ms = (time.time() - start_time) * 1000
    
    # Log observability
    try:
        log_routing_decision(execution_result, prompt)
        log_to_neo4j(prompt, execution_result)
    except Exception as e:
        print(f"[observability] warning: {e}")
    
    return execution_result
