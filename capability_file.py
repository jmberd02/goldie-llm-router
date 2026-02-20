from __future__ import annotations
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Default fallback capabilities if capability_data.json doesn't exist or models not found
DEFAULT_CAPABILITIES: dict[str, dict] = {
    "small": {  # Ollama qwen2.5:1.5b
        "mmlu_pro": 0.45,        # general_qa - basic factual knowledge
        "livecodebench": 0.20,   # code_operation - limited coding ability
        "gpqa": 0.25,            # multi_step_reasoning - weak reasoning
        "tau2": 0.15,            # agentic_tool_use - minimal agentic capability
        "lcr": 0.30,             # long_context - limited context handling
        "aime_25": 0.15,         # math - basic arithmetic only
        "hle": 0.01,             # very low human-level evaluation
        "price_per_1m_input": 0.0,   # Free (local)
        "price_per_1m_output": 0.0,  # Free (local)
    },
    "haiku": {
        "mmlu_pro": 0.71,        # general_qa
        "livecodebench": 0.378,  # code_operation
        "gpqa": 0.41,            # multi_step_reasoning
        "tau2": 0.35,            # agentic_tool_use
        "lcr": 0.55,             # long_context
        "aime_25": 0.30,         # math
        "hle": 0.03,
        "price_per_1m_input": 0.80,
        "price_per_1m_output": 4.00,
    },
    "sonnet": {
        "mmlu_pro": 0.90,
        "livecodebench": 0.72,
        "gpqa": 0.65,
        "tau2": 0.62,
        "lcr": 0.82,
        "aime_25": 0.55,
        "hle": 0.08,
        "price_per_1m_input": 3.00,
        "price_per_1m_output": 15.00,
    }
}


def load_capability_file() -> dict[str, dict]:
    """
    Load capability data from capability_data.json and map models based on env variables.
    
    Env variables:
    - SMALL_MODEL_NAME: Name of small model (e.g., "Gemma 3 1B Instruct") - also used for classification
    - LARGE_MODEL_NAME: Name of large model (e.g., "Claude 3.5 Sonnet (Oct '24)")
    
    To update with latest data from Artificial Analysis:
        export ARTIFICIAL_ANALYSIS_API_KEY=your_key
        python fetch_capabilities.py
    """
    capability_file = Path(__file__).parent / "capability_data.json"
    
    # Get model names from env
    small_model_name = os.getenv("SMALL_MODEL_NAME", "Gemma 3 1B Instruct")
    large_model_name = os.getenv("LARGE_MODEL_NAME", "Claude 3.5 Sonnet (Oct '24)")
    
    result = {}
    
    if capability_file.exists():
        try:
            with open(capability_file) as f:
                all_models = json.load(f)
                
                # Helper to flatten model data to old format for backward compatibility
                def flatten_model(model_data: dict) -> dict:
                    """Convert new structured format to flat format for router."""
                    aa_metrics = model_data.get("aa_metrics", {})
                    task_categories = model_data.get("task_categories", {})
                    price = model_data.get("price", {})
                    
                    # Provide both AA metric names and task category names for compatibility
                    return {
                        # AA metric names (mmlu_pro, livecodebench, etc.)
                        **aa_metrics,
                        # Task category names (general_qa, code_operation, etc.) - same values
                        **task_categories,
                        # Pricing
                        "price_per_1m_input": price.get("price_per_1m_input", 0.0),
                        "price_per_1m_output": price.get("price_per_1m_output", 0.0),
                    }
                
                # Map small model (also used for classification as "haiku")
                if small_model_name in all_models:
                    small_caps = flatten_model(all_models[small_model_name])
                    result["small"] = small_caps
                    result["haiku"] = small_caps  # Classification uses same model as small
                else:
                    print(f"Warning: Small model '{small_model_name}' not found, using defaults")
                    result["small"] = DEFAULT_CAPABILITIES["small"]
                    result["haiku"] = DEFAULT_CAPABILITIES["small"]
                
                # Map large model (sonnet)
                if large_model_name in all_models:
                    result["sonnet"] = flatten_model(all_models[large_model_name])
                else:
                    print(f"Warning: Large model '{large_model_name}' not found, using defaults")
                    result["sonnet"] = DEFAULT_CAPABILITIES["sonnet"]
                
                return result
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error loading capability_data.json: {e}")
    
    # Fall back to defaults
    return DEFAULT_CAPABILITIES


CAPABILITY_FILE: dict[str, dict] = load_capability_file()
