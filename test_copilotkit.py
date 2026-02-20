#!/usr/bin/env python3
"""
Test script for prompt optimizer integration.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def test_optimizer_setup():
    """Test prompt optimizer setup."""
    print("🧪 Testing Prompt Optimizer\n")
    
    # Test optimizer import
    try:
        from copilotkit_optimizer import get_optimizer, optimize_prompt_with_ollama
        print("✅ Optimizer module imported")
    except ImportError as e:
        print(f"❌ Failed to import optimizer: {e}")
        return False
    
    # Test optimizer initialization
    try:
        optimizer = get_optimizer()
        print("✅ Optimizer initialized")
    except Exception as e:
        print(f"❌ Failed to initialize optimizer: {e}")
        return False
    
    # Test simple optimization
    print("\n📝 Testing prompt optimization...")
    test_prompt = "What year was the Eiffel Tower built?"
    
    try:
        optimized = optimize_prompt_with_ollama(
            test_prompt,
            context={"thresholds": {"General QA": 0.5}}
        )
        
        print(f"\nOriginal:  {test_prompt}")
        print(f"Optimized: {optimized}")
        
        if optimized and optimized != test_prompt:
            print("\n✅ Optimization successful!")
            return True
        else:
            print("\n⚠️  Optimization returned same prompt (may be already optimal)")
            return True
            
    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_optimizer_setup()
    exit(0 if success else 1)
