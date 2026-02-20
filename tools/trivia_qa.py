def answer_trivia(params: dict) -> str:
    """Answer a simple factual question."""
    question = params.get("question", "")
    
    # Hardcoded responses for common demo questions
    responses = {
        "what year was the eiffel tower built": "The Eiffel Tower was built in 1889.",
        "when was the eiffel tower built": "The Eiffel Tower was built in 1889.",
        "who wrote hamlet": "William Shakespeare wrote Hamlet around 1600.",
        "what is the capital of france": "The capital of France is Paris.",
        "how many planets are in the solar system": "There are 8 planets in the solar system.",
    }
    
    # Normalize question for lookup
    normalized = question.lower().strip().rstrip("?")
    
    if normalized in responses:
        return responses[normalized]
    
    # Generic fallback
    return f"Based on the question '{question}', the answer is: [factual response would appear here]"
