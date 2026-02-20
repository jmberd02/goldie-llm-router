#!/usr/bin/env python3
"""Simple test script to run a prompt through the LLM router."""

from router import route
from demo_prompts import DEMO_PROMPTS
from stub_adapter import StubAdapter

def test_prompt(prompt: str, description: str = "", use_stub: bool = True):
    """Test a single prompt through the router."""
    print(f"\n{'='*80}")
    if description:
        print(f"Test: {description}")
    print(f"Prompt: {prompt}")
    print(f"{'='*80}\n")
    
    try:
        adapter = StubAdapter() if use_stub else None
        result = route(prompt, adapter=adapter)
        
        print(f"✓ Routing completed successfully!\n")
        print(f"Model Used: {result.model_used} ({result.model_id})")
        print(f"Routing Reason: {result.routing_reason}")
        print(f"Escalated: {result.escalated}")
        
        if result.classification:
            print(f"\nClassification:")
            print(f"  Dominant Category: {result.classification.dominant_category}")
            print(f"  Difficulty: {result.classification.difficulty:.2f}")
            print(f"  Subtasks: {', '.join(result.classification.subtasks)}")
        
        print(f"\nMetrics:")
        print(f"  Input Tokens: {result.input_tokens}")
        print(f"  Output Tokens: {result.output_tokens}")
        print(f"  Cost: ${result.cost_usd:.6f}")
        print(f"  Latency: {result.latency_ms:.0f}ms")
        
        print(f"\nResponse:")
        print(f"  {result.response[:200]}{'...' if len(result.response) > 200 else ''}")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with a simple prompt from demo prompts
    simple_prompt = DEMO_PROMPTS[0]  # Eiffel Tower question
    test_prompt(simple_prompt["prompt"], simple_prompt["label"])
    
    # Test with a complex prompt
    complex_prompt = DEMO_PROMPTS[5]  # Calendar + reminder
    test_prompt(complex_prompt["prompt"], complex_prompt["label"])
