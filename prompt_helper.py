from __future__ import annotations
import json
import boto3

HELPER_SYSTEM_PROMPT = """You are a prompt optimization assistant for a hybrid LLM routing system.

Your goal: rewrite prompts to work well with a SMALL, FAST, LOCAL MODEL (Haiku-class).

The router escalates to a large model when:
- difficulty >= 0.7, OR
- the request requires more than 2 subtasks

Task categories:
- general_qa: factual lookups, explanations, trivia (GOOD for small model)
- code_operation: simple edits, formatting, basic code tasks (GOOD for small model)
- math: basic arithmetic, simple calculations (GOOD for small model)
- multi_step_reasoning: complex analysis requiring multiple steps (BAD for small model)
- agentic_tool_use: requires using tools or taking actions (BAD for small model)
- long_context: reading/summarizing long documents (BAD for small model)

Optimization strategies:
1. Break complex requests into single, focused questions
2. Make the task concrete and specific (avoid vague "help me with X")
3. Remove multi-step requirements — ask for ONE thing at a time
4. Simplify language and reduce ambiguity
5. For code: ask for specific edits, not "refactor" or "improve"
6. Avoid requests that need external tools, calendar access, or multi-step planning

Respond in JSON only:
{
  "rewrite": "the optimized prompt for small model",
  "category": "predicted task category",
  "predicted_difficulty": 0.0,
  "predicted_route": "small or large",
  "explanation": "one sentence explaining what you changed to optimize for small model",
  "will_save_cost": true/false
}"""


def suggest_prompt_rewrite(prompt: str) -> dict:
    """
    Call Haiku to suggest a clearer rewrite of the user's prompt.
    Returns a dict with keys: rewrite, category, predicted_difficulty,
    predicted_route, explanation. Returns None on failure.
    """
    try:
        client = boto3.client("bedrock-runtime", region_name="us-east-1")
        response = client.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            system=[{"text": HELPER_SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": f"Prompt to improve:\n\n{prompt}"}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.3},
        )
        text = response["output"]["message"]["content"][0]["text"]
        # Strip markdown fences if present
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except Exception as e:
        return None


def stub_suggest(prompt: str) -> dict:
    """Stub for development — use this until Bedrock is wired up."""
    # Simple heuristic: if prompt mentions multiple steps or complex tasks, suggest simplification
    is_complex = any(word in prompt.lower() for word in ["and then", "after that", "calendar", "schedule", "complex", "comprehensive"])
    
    if is_complex:
        return {
            "rewrite": f"What is {prompt.split()[0:5]}?",  # Take first few words and make it a simple question
            "category": "general_qa",
            "predicted_difficulty": 0.3,
            "predicted_route": "small",
            "explanation": "Simplified to a single focused question to avoid escalation to large model.",
            "will_save_cost": True
        }
    else:
        return {
            "rewrite": prompt,
            "category": "general_qa",
            "predicted_difficulty": 0.2,
            "predicted_route": "small",
            "explanation": "Prompt is already optimized for small model — no changes needed.",
            "will_save_cost": False
        }
