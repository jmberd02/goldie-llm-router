import re


def solve_math(params: dict) -> str:
    """Solve a math problem."""
    problem = params.get("problem", "")
    
    # Try to detect simple arithmetic expressions
    # Strip to only safe characters: digits, operators, parentheses, spaces
    safe_expr = re.sub(r'[^0-9+\-*/().\s]', '', problem)
    
    # Check if it looks like a simple expression
    if safe_expr and len(safe_expr) < 100:
        try:
            result = eval(safe_expr)
            # Format with commas for readability
            if isinstance(result, (int, float)):
                if result == int(result):
                    formatted = f"{int(result):,}"
                else:
                    formatted = f"{result:,.2f}"
                return f"{safe_expr.strip()} = {formatted}"
        except:
            pass
    
    # Complex problem — return mock step-by-step solution
    return f"""Step 1: Identify the problem structure
Problem: {problem}

Step 2: Break down into components
- This requires multi-step reasoning
- Variables need to be identified
- Relationships need to be established

Step 3: Apply appropriate mathematical principles
- Set up equations based on constraints
- Solve systematically

Answer: 42

(Note: This is a mocked solution for demonstration purposes)"""
