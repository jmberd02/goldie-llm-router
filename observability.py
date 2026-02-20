import os
import logging
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

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
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
    """Log routing decision to file."""
    task_cat = result.classification.dominant_category if result.classification else "unknown"
    
    log_msg = (
        f"[METRICS] model={result.model_id} cost=${result.cost_usd:.6f} "
        f"latency={result.latency_ms:.0f}ms escalated={result.escalated} "
        f"tokens_in={result.input_tokens} tokens_out={result.output_tokens} "
        f"task={task_cat} prompt_preview={prompt[:50]}..."
    )
    
    logger.info(log_msg)


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
