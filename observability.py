import os
import logging
import json
from datetime import datetime
from models import CompletionResult

# Set up file-based logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Create logger
logger = logging.getLogger("llm_router")
logger.setLevel(logging.INFO)

# File handler with rotation-friendly naming
log_file = os.path.join(LOG_DIR, f"routing_{datetime.now().strftime('%Y%m%d')}.log")
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Console handler (for when running outside Streamlit)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# JSON formatter - just output the message (which will be JSON)
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_routing_decision(result: CompletionResult, prompt: str) -> None:
    """
    Log routing decision metrics to file and stdout.
    (Datadog integration disabled for now)
    
    Args:
        result: CompletionResult containing routing decision and metrics
        prompt: Original user prompt (for context)
    """
    _log_to_file(result, prompt)


def _log_to_file(result: CompletionResult, prompt: str) -> None:
    """Log routing decision to file as formatted JSON."""
    
    # Build comprehensive log data
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "routing_decision",
        "prompt": {
            "text": prompt,
            "preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "length": len(prompt)
        },
        "routing": {
            "model_used": result.model_used,
            "model_id": result.model_id,
            "escalated": result.escalated,
            "reason": result.routing_reason
        },
        "classification": {
            "dominant_category": result.classification.dominant_category if result.classification else None,
            "difficulty": result.classification.difficulty if result.classification else None,
            "subtasks": result.classification.subtasks if result.classification else [],
            "task_categories": result.classification.task_categories if result.classification else {}
        } if result.classification else None,
        "metrics": {
            "cost_usd": round(result.cost_usd, 8),
            "latency_ms": round(result.latency_ms, 2),
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "total_tokens": result.input_tokens + result.output_tokens
        },
        "response": {
            "preview": result.response[:200] + "..." if len(result.response) > 200 else result.response,
            "length": len(result.response)
        }
    }
    
    # Log as formatted JSON (indent=2 for readability)
    logger.info(json.dumps(log_data, indent=2))


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
