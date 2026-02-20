"""Stub adapter for testing router.py without Agent 2's BedrockAdapter.
Delete this file once adapters/bedrock.py is ready.
"""
import time
import json
from models import CompletionResult

STUB_CLASSIFICATION_JSON = json.dumps({
    "subtasks": ["look up fact"],
    "task_categories": {"general_qa": 0.9, "math": 0.0, "code_operation": 0.0,
                        "multi_step_reasoning": 0.1, "agentic_tool_use": 0.0, "long_context": 0.0},
    "difficulty": 0.2,
    "dominant_category": "general_qa",
    "escalate": False
})

class StubAdapter:
    def complete(self, prompt: str, model_id: str) -> CompletionResult:
        time.sleep(0.1)
        # Classification calls contain the classification prompt — return JSON only
        is_classification = "Respond with exactly this structure" in prompt
        response = STUB_CLASSIFICATION_JSON if is_classification else f"Stub answer for: {prompt[:50]}"
        return CompletionResult(
            response=response,
            model_used="small" if model_id == "haiku" else "large",
            model_id=model_id,
            routing_reason="stub",
            escalated=False,
            input_tokens=80 if is_classification else 120,
            output_tokens=60 if is_classification else 90,
            cost_usd=0.00005 if is_classification else 0.0002,
            latency_ms=80.0 if is_classification else 150.0,
            classification=None,
        )
