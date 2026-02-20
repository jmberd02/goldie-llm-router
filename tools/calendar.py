# Hardcoded calendar — make this feel realistic
CALENDAR = [
    {"title": "Standup",        "day": "Monday",    "start": "9:00 AM",  "end": "9:30 AM"},
    {"title": "Design Review",  "day": "Monday",    "start": "2:00 PM",  "end": "3:30 PM"},
    {"title": "1:1 with Maya",  "day": "Tuesday",   "start": "10:00 AM", "end": "10:30 AM"},
    {"title": "Sprint Planning","day": "Tuesday",   "start": "1:00 PM",  "end": "3:00 PM"},
    {"title": "Lunch with Alex","day": "Wednesday", "start": "12:00 PM", "end": "1:00 PM"},
    {"title": "Team Demo",      "day": "Thursday",  "start": "4:00 PM",  "end": "5:00 PM"},
    {"title": "Standup",        "day": "Friday",    "start": "9:00 AM",  "end": "9:30 AM"},
]


def _parse_time(time_str: str) -> int:
    """Convert time string like '9:00 AM' to minutes since midnight."""
    time_part, period = time_str.split()
    hour, minute = map(int, time_part.split(':'))
    
    if period == 'PM' and hour != 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    
    return hour * 60 + minute


def find_free_time(params: dict) -> str:
    """Find a free time slot on the calendar."""
    duration_minutes = params.get("duration_minutes", 60)
    target_day = params.get("day", "").strip()
    
    # Group events by day
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    if target_day and target_day not in days:
        return f"Error: '{target_day}' is not a valid weekday"
    
    search_days = [target_day] if target_day else days
    
    for day in search_days:
        day_events = [e for e in CALENDAR if e["day"] == day]
        day_events.sort(key=lambda e: _parse_time(e["start"]))
        
        # Check gaps between events
        work_start = 9 * 60  # 9:00 AM
        work_end = 17 * 60   # 5:00 PM
        
        # Check before first event
        if day_events:
            first_event_start = _parse_time(day_events[0]["start"])
            if first_event_start - work_start >= duration_minutes:
                hours = duration_minutes // 60
                return f"Found a free {hours}-hour block on {day} from 9:00 AM – {day_events[0]['start']}"
        
        # Check gaps between events
        for i in range(len(day_events) - 1):
            current_end = _parse_time(day_events[i]["end"])
            next_start = _parse_time(day_events[i + 1]["start"])
            gap = next_start - current_end
            
            if gap >= duration_minutes:
                hours = duration_minutes // 60
                return f"Found a free {hours}-hour block on {day} from {day_events[i]['end']} – {day_events[i + 1]['start']}"
        
        # Check after last event
        if day_events:
            last_event_end = _parse_time(day_events[-1]["end"])
            if work_end - last_event_end >= duration_minutes:
                hours = duration_minutes // 60
                return f"Found a free {hours}-hour block on {day} from {day_events[-1]['end']} – 5:00 PM"
    
    return f"No free {duration_minutes}-minute blocks found this week"
