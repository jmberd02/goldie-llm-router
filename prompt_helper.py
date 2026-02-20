from __future__ import annotations
import json
import boto3

HELPER_SYSTEM_PROMPT = """You are a prompt clarity assistant for an LLM routing system.

The router classifies prompts into these task categories:
- general_qa: factual lookups, explanations, trivia
- code_operation: writing, editing, reviewing, or testing code
- multi_step_reasoning: analysis requiring multiple reasoning steps
- agentic_tool_use: requests that require using tools or taking actions
- long_context: tasks requiring reading or summarizing long documents
- math: arithmetic, algebra, calculations

The router also estimates difficulty from 0.0 to 1.0:
- 0.2 = simple lookup
- 0.4 = simple reasoning
- 0.6 = multi-step
- 0.8 = complex analysis
- 1.0 = frontier research

Escalation to the large model happens when:
- difficulty >= 0.7, OR
- the request requires more than 2 subtasks

Your job: given a user prompt, suggest a clearer rewrite that will route more accurately.
A good rewrite makes the task type and scope explicit without changing the user's intent.

Respond in JSON only:
{
  "rewrite": "the improved prompt",
  "category": "what task category this maps to",
  "predicted_difficulty": 0.0,
  "predicted_route": "small or large",
  "explanation": "one sentence explaining what you changed and why"
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
    return {
        "rewrite": f"Please provide a direct answer to this general knowledge question: {prompt}",
        "category": "general_qa",
        "predicted_difficulty": 0.2,
        "predicted_route": "small",
        "explanation": "Made the task type explicit so the classifier assigns general_qa confidently."
    }
