DEMO_PROMPTS = [
    {
        "label": "🟢 Trivia — What year was the Eiffel Tower built?",
        "prompt": "What year was the Eiffel Tower built?",
        "tool": "answer_trivia",
        "expected_route": "small",
        "expected_category": "general_qa",
    },
    {
        "label": "🟢 Find & Replace — rename a function",
        "prompt": "In this code, replace all instances of 'foo' with 'bar': def foo(): return foo()",
        "tool": "find_replace",
        "expected_route": "small",
        "expected_category": "code_operation",
    },
    {
        "label": "🟢 Reminder — set a simple reminder",
        "prompt": "Remind me to call the dentist at 3pm tomorrow",
        "tool": "set_reminder",
        "expected_route": "small",
        "expected_category": "agentic_tool_use",
    },
    {
        "label": "🟢 Math — simple multiplication",
        "prompt": "What is 847 times 23?",
        "tool": "solve_math",
        "expected_route": "small",
        "expected_category": "math",
    },
    {
        "label": "🟢 Florida Man — summarize article",
        "prompt": "Summarize this article: A Florida man was arrested after attempting to cash a check made out to 'Cash Money' for $1 million that he wrote himself. He told police he had 'invented a new type of banking.' He was released on a $500 bond, which he also tried to pay with a handwritten check.",
        "tool": "summarize_article",
        "expected_route": "small",
        "expected_category": "general_qa",
    },
    {
        "label": "🔴 Calendar — find free time + set reminder",
        "prompt": "Check my calendar and find the next free 2-hour block this week, then schedule a reminder for my dentist appointment in that slot",
        "tool": "multi_tool_chain",
        "expected_route": "large",
        "expected_category": "agentic_tool_use",
    },
    {
        "label": "🔴 Unit Tests — complex function with edge cases",
        "prompt": """Generate comprehensive unit tests for this function including edge cases, error states, and mocked dependencies:

def process_payment(user_id: str, amount: float, currency: str, retry_count: int = 0) -> dict:
    \"\"\"Process a payment with retry logic and currency conversion.\"\"\"
    if amount <= 0:
        raise ValueError('Amount must be positive')
    if retry_count > 3:
        raise RuntimeError('Max retries exceeded')""",
        "tool": "generate_unit_tests",
        "expected_route": "large",
        "expected_category": "code_operation",
    },
    {
        "label": "🔴 Multi-tool — calendar + reminder + math",
        "prompt": "Find a free hour on my calendar tomorrow, set a reminder for my team standup prep 15 minutes before it, and tell me how many hours away that is",
        "tool": "multi_tool_chain",
        "expected_route": "large",
        "expected_category": "agentic_tool_use",
    },
]
