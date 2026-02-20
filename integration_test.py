#!/usr/bin/env python3
"""Integration test — run all 8 demo prompts through the real router."""

from router import route
from demo_prompts import DEMO_PROMPTS

print("\n=== Integration Test ===\n")
passed = 0
failed = 0

for p in DEMO_PROMPTS:
    result = route(p["prompt"])
    expected = p["expected_route"]
    actual = result.model_used
    ok = actual == expected
    status = "✓" if ok else "✗"
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"{status} [{p['label'][:40]}]")
    print(f"  Expected: {expected} | Got: {actual} ({result.model_id})")
    print(f"  Category: {result.classification.dominant_category if result.classification else '—'}")
    print(f"  Difficulty: {result.classification.difficulty if result.classification else '—'}")
    print(f"  Cost: ${result.cost_usd:.6f} | Latency: {result.latency_ms:.0f}ms")
    print()

print(f"=== {passed} passed, {failed} failed ===")
