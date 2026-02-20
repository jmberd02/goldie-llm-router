#!/usr/bin/env python3
"""
Test script for BedrockAdapter.
Run this to verify Bedrock integration before handing off to other agents.
"""
import os
from dotenv import load_dotenv
from adapters.bedrock import BedrockAdapter

def main():
    # Load environment
    load_dotenv()
    
    print("=== Testing BedrockAdapter ===\n")
    
    # Initialize adapter
    region = os.getenv("AWS_REGION", "us-east-1")
    print(f"Initializing BedrockAdapter (region={region})...")
    adapter = BedrockAdapter(region=region)
    
    # Test with Haiku
    print("\n--- Testing Haiku ---")
    result = adapter.complete("What is 2 + 2?", "haiku")
    print(f"Response: {result.response}")
    print(f"Cost: ${result.cost_usd:.6f}")
    print(f"Latency: {result.latency_ms:.0f}ms")
    print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
    
    # Test with Sonnet
    print("\n--- Testing Sonnet ---")
    result = adapter.complete("Explain binary search in one sentence.", "sonnet")
    print(f"Response: {result.response}")
    print(f"Cost: ${result.cost_usd:.6f}")
    print(f"Latency: {result.latency_ms:.0f}ms")
    print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
    
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    main()
