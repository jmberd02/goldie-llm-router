import os
from models import CompletionResult


def log_routing_decision(result: CompletionResult, prompt: str) -> None:
    """
    Log routing decision metrics to stdout.
    (Datadog integration disabled for now)
    
    Args:
        result: CompletionResult containing routing decision and metrics
        prompt: Original user prompt (for context)
    """
    _log_to_stdout(result, prompt)


def _log_to_stdout(result: CompletionResult, prompt: str) -> None:
    """Fallback stdout logging when Datadog is unavailable."""
    task_cat = result.classification.dominant_category if result.classification else "unknown"
    print(f"[METRICS] model={result.model_id} cost=${result.cost_usd:.6f} "
          f"latency={result.latency_ms:.0f}ms escalated={result.escalated} "
          f"tokens_in={result.input_tokens} tokens_out={result.output_tokens} "
          f"task={task_cat}")


def log_to_neo4j(prompt: str, result: CompletionResult) -> None:
    """
    Store routing decision as a graph in Neo4j.
    (Neo4j integration disabled for now)
    
    Args:
        prompt: Original user prompt
        result: CompletionResult containing routing decision
    """
    # Disabled for now - just pass silently
    pass
