from __future__ import annotations
import json
import os
from pathlib import Path

# Default fallback capabilities if capability_data.json doesn't exist
DEFAULT_CAPABILITIES: dict[str, dict] = {
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
    Load capability data from capability_data.json if it exists,
    otherwise use default fallback values.
    
    To update with latest data from Artificial Analysis:
        export ARTIFICIAL_ANALYSIS_API_KEY=your_key
        python fetch_capabilities.py
    """
    capability_file = Path(__file__).parent / "capability_data.json"
    
    if capability_file.exists():
        try:
            with open(capability_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return DEFAULT_CAPABILITIES


CAPABILITY_FILE: dict[str, dict] = load_capability_file()
