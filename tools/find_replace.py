def find_replace(params: dict) -> str:
    """Find and replace text in a code snippet or string."""
    text = params.get("text", "")
    find = params.get("find", "")
    replace = params.get("replace", "")
    
    if not find:
        return "Error: 'find' parameter is required"
    
    # Perform the replacement
    new_text = text.replace(find, replace)
    count = text.count(find)
    
    if count == 0:
        return f"No occurrences of '{find}' found in the text."
    
    # Format as diff-style output
    result = f"Before: {text}\n"
    result += f"After:  {new_text}\n"
    result += f"Replaced {count} occurrence(s) of '{find}' with '{replace}'"
    
    return result
