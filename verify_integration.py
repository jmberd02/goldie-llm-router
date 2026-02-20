#!/usr/bin/env python3
"""Quick verification that integration is complete."""

import sys

print("=== Integration Verification ===\n")

# Step 1: Verify all imports
print("1. Checking imports...")
try:
    from models import Classification, CompletionResult, TASK_TO_EVAL
    print("   ✓ models")
except ImportError as e:
    print(f"   ✗ models: {e}")
    sys.exit(1)

try:
    from capability_file import CAPABILITY_FILE
    print("   ✓ capability_file")
except ImportError as e:
    print(f"   ✗ capability_file: {e}")
    sys.exit(1)

try:
    from adapters.bedrock import BedrockAdapter
    print("   ✓ bedrock adapter")
except ImportError as e:
    print(f"   ✗ bedrock adapter: {e}")
    sys.exit(1)

try:
    from tools import TOOL_REGISTRY
    print(f"   ✓ tools ({len(TOOL_REGISTRY)} registered)")
except ImportError as e:
    print(f"   ✗ tools: {e}")
    sys.exit(1)

try:
    from router import route, pick_model
    print("   ✓ router")
except ImportError as e:
    print(f"   ✗ router: {e}")
    sys.exit(1)

try:
    from observability import log_routing_decision, log_to_neo4j
    print("   ✓ observability")
except ImportError as e:
    print(f"   ✗ observability: {e}")
    sys.exit(1)

try:
    from prompt_helper import suggest_prompt_rewrite
    print("   ✓ prompt_helper")
except ImportError as e:
    print(f"   ✗ prompt_helper: {e}")
    sys.exit(1)

try:
    from demo_prompts import DEMO_PROMPTS
    print(f"   ✓ demo_prompts ({len(DEMO_PROMPTS)} prompts)")
except ImportError as e:
    print(f"   ✗ demo_prompts: {e}")
    sys.exit(1)

# Step 2: Verify router uses BedrockAdapter
print("\n2. Checking router integration...")
import inspect
router_source = inspect.getsource(route)
if "BedrockAdapter" in router_source:
    print("   ✓ Router uses BedrockAdapter")
else:
    print("   ✗ Router doesn't use BedrockAdapter")
    sys.exit(1)

if "log_routing_decision" in router_source and "log_to_neo4j" in router_source:
    print("   ✓ Observability integrated")
else:
    print("   ✗ Observability not integrated")
    sys.exit(1)

# Step 3: Verify app.py integration
print("\n3. Checking app.py integration...")
with open("app.py", "r") as f:
    app_source = f.read()

if "import startup" in app_source and "startup.run()" in app_source:
    print("   ✓ Startup checks integrated")
else:
    print("   ✗ Startup checks missing")
    sys.exit(1)

if "from router import route" in app_source:
    print("   ✓ Real router imported")
else:
    print("   ✗ Real router not imported")
    sys.exit(1)

# Step 4: Check for stub usage
print("\n4. Checking for stub usage...")
if "from stub_adapter import" not in router_source:
    print("   ✓ No stub_adapter imports in router")
else:
    print("   ✗ Router still imports stub_adapter")
    sys.exit(1)

print("\n=== ✓ Integration Complete ===")
print("\nNext steps:")
print("  1. Run: python3 startup.py")
print("  2. Run: python3 integration_test.py")
print("  3. Run: streamlit run app.py")
print("  4. Delete stub_adapter.py after tests pass")
