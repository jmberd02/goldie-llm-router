from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

TASK_TO_EVAL = {
    "general_qa":           "mmlu_pro",
    "code_operation":       "livecodebench",
    "multi_step_reasoning": "gpqa",
    "agentic_tool_use":     "tau2",
    "long_context":         "lcr",
    "math":                 "aime_25",
}

# UI-friendly names mapped to internal category names
UI_CATEGORY_NAMES = {
    "Math": "math",
    "Code Operations": "code_operation",
    "Reasoning": "multi_step_reasoning",
    "Agentic Tool Use": "agentic_tool_use",
    "Long Context": "long_context",
    "General QA": "general_qa",
}


@dataclass
class Classification:
    """Output of the small model's task classification call."""
    subtasks: list[str]
    task_categories: dict[str, float]
    difficulty: float
    dominant_category: str
    escalate: bool


@dataclass
class CompletionResult:
    """Returned by the router after every request."""
    response: str
    model_used: str
    model_id: str
    routing_reason: str
    escalated: bool
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    classification: Optional[Classification]
