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


def fetch_model_data(api_key: str) -> dict:
    """Fetch model data from Artificial Analysis API."""
    url = "https://artificialanalysis.ai/api/v2/data/llms/models"
    headers = {"x-api-key": api_key}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_model_capabilities(model_data: dict, model_name: str) -> Optional[dict]:
    """Extract relevant capability scores for a specific model."""
    # Find the model in the data
    model = None
    for m in model_data.get("data", []):
        if model_name.lower() in m.get("model", "").lower():
            model = m
            break
    
    if not model:
        return None
    
    # Extract evaluation scores
    evals = model.get("evals", {})
    
    # Helper to get math score with fallback chain
    def get_math_score():
        return (
            evals.get("aime_25") or
            evals.get("math_500") or
            evals.get("aime") or
            (evals.get("artificial_analysis_math_index", 0) / 100)
        )
    
    # Extract pricing (convert to per-1M tokens)
    pricing = model.get("pricing", {})
    price_input = pricing.get("input", 0) * 1_000_000  # Convert from per-token to per-1M
    price_output = pricing.get("output", 0) * 1_000_000
    
    return {
        "mmlu_pro": evals.get("mmlu_pro", 0.0),
        "livecodebench": evals.get("livecodebench", 0.0),
        "gpqa": evals.get("gpqa", 0.0),
        "tau2": evals.get("tau2", 0.0),
        "lcr": evals.get("lcr", 0.0),
        "aime_25": get_math_score(),
        "hle": evals.get("hle", 0.0),
        "price_per_1m_input": price_input,
        "price_per_1m_output": price_output,
        "model_name": model.get("model", ""),
        "quality_index": evals.get("artificial_analysis_intelligence_index", 0) / 100,
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
    
    # Extract capabilities for our models
    # Look for Claude Haiku 3.5 and Claude Sonnet 3.5/4
    capabilities = {}
    
    for model_entry in model_data.get("data", []):
        model_name = model_entry.get("name", "").lower()
        
        # Match Haiku 3.5 (there's only one version)
        if "haiku" in model_name and "3.5" in model_name:
            evals = model_entry.get("evaluations", {})
            pricing = model_entry.get("pricing", {})
            
            capabilities["haiku"] = {
                "mmlu_pro": evals.get("mmlu_pro") or 0.0,
                "livecodebench": evals.get("livecodebench") or 0.0,
                "gpqa": evals.get("gpqa") or 0.0,
                "tau2": evals.get("tau2") or 0.0,
                "lcr": evals.get("lcr") or 0.0,
                "aime_25": evals.get("aime_25") or evals.get("math_500") or evals.get("aime") or 0.0,
                "hle": evals.get("hle") or 0.0,
                "price_per_1m_input": pricing.get("price_1m_input_tokens") or 0.0,
                "price_per_1m_output": pricing.get("price_1m_output_tokens") or 0.0,
                "model_name": model_entry.get("name", ""),
            }
            print(f"✓ Found {model_entry.get('name')}")
        
        # Match Sonnet 3.5 Oct '24 (most recent stable version on Bedrock)
        if "sonnet" in model_name and "3.5" in model_name and "oct" in model_name:
            evals = model_entry.get("evaluations", {})
            pricing = model_entry.get("pricing", {})
            
            capabilities["sonnet"] = {
                "mmlu_pro": evals.get("mmlu_pro") or 0.0,
                "livecodebench": evals.get("livecodebench") or 0.0,
                "gpqa": evals.get("gpqa") or 0.0,
                "tau2": evals.get("tau2") or 0.0,
                "lcr": evals.get("lcr") or 0.0,
                "aime_25": evals.get("aime_25") or evals.get("math_500") or evals.get("aime") or 0.0,
                "hle": evals.get("hle") or 0.0,
                "price_per_1m_input": pricing.get("price_1m_input_tokens") or 0.0,
                "price_per_1m_output": pricing.get("price_1m_output_tokens") or 0.0,
                "model_name": model_entry.get("name", ""),
            }
            print(f"✓ Found {model_entry.get('name')}")
    
    if not capabilities:
        print("Error: Could not find Haiku or Sonnet models in API data")
        print("Available Claude models:")
        for m in model_data.get("data", []):
            name = m.get("name", "")
            if "claude" in name.lower():
                print(f"  - {name}")
        return 1
    
    # Save processed capabilities
    with open("capability_data.json", "w") as f:
        json.dump(capabilities, f, indent=2)
    
    print(f"\n✓ Saved capability data to capability_data.json")
    print(f"  Models: {', '.join(capabilities.keys())}")
    
    # Print summary
    print("\nCapability Summary:")
    for model_id, caps in capabilities.items():
        print(f"\n{model_id.upper()} ({caps['model_name']}):")
        print(f"  General QA (mmlu_pro):     {caps['mmlu_pro']:.3f}")
        print(f"  Code (livecodebench):      {caps['livecodebench']:.3f}")
        print(f"  Reasoning (gpqa):          {caps['gpqa']:.3f}")
        print(f"  Agentic (tau2):            {caps['tau2']:.3f}" if caps['tau2'] else "  Agentic (tau2):            N/A")
        print(f"  Math (aime_25):            {caps['aime_25']:.3f}")
        print(f"  Pricing: ${caps['price_per_1m_input']:.2f}/${caps['price_per_1m_output']:.2f} per 1M tokens")
    
    return 0


if __name__ == "__main__":
    exit(main())
