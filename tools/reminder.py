# In-memory store — persists for the session
_reminders: list[dict] = []


def set_reminder(params: dict) -> str:
    """Set a reminder for a specific time."""
    message = params.get("message", "")
    datetime = params.get("datetime", "")
    
    if not message:
        return "Error: 'message' parameter is required"
    
    reminder = {
        "message": message,
        "datetime": datetime or "unspecified time"
    }
    _reminders.append(reminder)
    
    return f"✓ Reminder set: '{message}' for {datetime or 'unspecified time'}"


def list_reminders(params: dict) -> str:
    """List all reminders set this session."""
    if not _reminders:
        return "No reminders set yet."
    
    result = "Your reminders:\n"
    for i, reminder in enumerate(_reminders, 1):
        result += f"{i}. {reminder['message']} — {reminder['datetime']}\n"
    
    return result.rstrip()
