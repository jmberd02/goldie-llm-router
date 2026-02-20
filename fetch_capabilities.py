#!/usr/bin/env python3
"""
Fetch model capability data from Artificial Analysis API and generate capability_data.json.
Run this script to update the capability file with latest benchmark data.

Usage:
    export ARTIFICIAL_ANALYSIS_API_KEY=your_key_here
    python fetch_capabilities.py
"""
import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Mapping from AA metrics to our task categories
TASK_CATEGORY_MAPPING = {
    "general_qa": "mmlu_pro",
    "code_operation": "livecodebench",
    "multi_step_reasoning": "gpqa",
    "agentic_tool_use": "tau2",
    "long_context": "lcr",
    "math": "aime_25",
}


def main():
    # Get API key from environment
    api_key = os.getenv("ARTIFICIAL_ANALYSIS_API_KEY")
    if not api_key:
        print("Error: ARTIFICIAL_ANALYSIS_API_KEY environment variable not set")
        print("Get your API key from: https://artificialanalysis.ai/api-access-preview")
        return 1
    
    print("Fetching model data from Artificial Analysis API...")
    try:
        model_data = requests.get(
            "https://artificialanalysis.ai/api/v2/data/llms/models",
            headers={"x-api-key": api_key}
        ).json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return 1
    
    # Save raw data for reference
    with open("capability_data_raw.json", "w") as f:
        json.dump(model_data, f, indent=2)
    print(f"✓ Saved raw data to capability_data_raw.json")
    
    # Build name-indexed capability data with structured format
    capabilities = {}
    
    for model_entry in model_data.get("data", []):
        model_name = model_entry.get("name", "")
        if not model_name:
            continue
            
        evals = model_entry.get("evaluations", {})
        pricing = model_entry.get("pricing", {})
        
        # Extract AA metrics
        aa_metrics = {
            "mmlu_pro": evals.get("mmlu_pro") or 0.0,
            "livecodebench": evals.get("livecodebench") or 0.0,
            "gpqa": evals.get("gpqa") or 0.0,
            "tau2": evals.get("tau2") or 0.0,
            "lcr": evals.get("lcr") or 0.0,
            "aime_25": evals.get("aime_25") or evals.get("math_500") or evals.get("aime") or 0.0,
            "hle": evals.get("hle") or 0.0,
        }
        
        # Map to task categories
        task_categories = {}
        for task_name, metric_name in TASK_CATEGORY_MAPPING.items():
            task_categories[task_name] = aa_metrics.get(metric_name, 0.0)
        
        capabilities[model_name] = {
            "aa_metrics": aa_metrics,
            "price": {
                "price_per_1m_input": pricing.get("price_1m_input_tokens") or 0.0,
                "price_per_1m_output": pricing.get("price_1m_output_tokens") or 0.0,
            },
            "slug": model_entry.get("slug", ""),
            "task_categories": task_categories,
        }
    
    # Save processed capabilities indexed by name
    with open("capability_data.json", "w") as f:
        json.dump(capabilities, f, indent=2)
    
    print(f"\n✓ Saved capability data to capability_data.json")
    print(f"  Total models: {len(capabilities)}")
    
    # Print some examples
    print("\nExample models available:")
    for i, name in enumerate(list(capabilities.keys())[:10]):
        print(f"  - {name}")
    print(f"  ... and {len(capabilities) - 10} more")
    
    return 0


if __name__ == "__main__":
    exit(main())
