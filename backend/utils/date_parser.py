"""
Date/Time Parser - Parse natural language dates and times
"""

from datetime import datetime, timedelta
import re


def parse_natural_date(text: str) -> str:
    """
    Parse natural language date/time expressions into ISO format
    
    Args:
        text: Natural language date/time string (e.g., "in 5 minutes", "tomorrow at 3pm")
        
    Returns:
        ISO format datetime string, or the original text if unparseable
    """
    if not text or not isinstance(text, str):
        return text
    
    text = text.lower().strip()
    now = datetime.now()
    
    try:
        # "in X minutes/hours/days"
        match = re.search(r'in\s+(\d+)\s+(minute|minutes|min|hour|hours|hr|day|days)', text)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if 'min' in unit:
                target = now + timedelta(minutes=amount)
            elif 'hour' in unit or 'hr' in unit:
                target = now + timedelta(hours=amount)
            elif 'day' in unit:
                target = now + timedelta(days=amount)
            else:
                return text
            
            return target.isoformat()
        
        # "tomorrow" with optional time
        if 'tomorrow' in text:
            target = now + timedelta(days=1)
            
            # Check for time specification
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)
                
                if meridiem and meridiem.lower() == 'pm' and hour < 12:
                    hour += 12
                elif meridiem and meridiem.lower() == 'am' and hour == 12:
                    hour = 0
                
                target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # Default to 9 AM tomorrow if no time specified
                target = target.replace(hour=9, minute=0, second=0, microsecond=0)
            
            return target.isoformat()
        
        # "today" with time
        if 'today' in text:
            target = now
            
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                meridiem = time_match.group(3)
                
                if meridiem and meridiem.lower() == 'pm' and hour < 12:
                    hour += 12
                elif meridiem and meridiem.lower() == 'am' and hour == 12:
                    hour = 0
                
                target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return target.isoformat()
        
        # Specific time today (e.g., "at 5pm", "at 3:30")
        time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?', text)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            
            if meridiem and meridiem.lower() == 'pm' and hour < 12:
                hour += 12
            elif meridiem and meridiem.lower() == 'am' and hour == 12:
                hour = 0
            
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the time has already passed today, assume tomorrow
            if target < now:
                target = target + timedelta(days=1)
            
            return target.isoformat()
        
        # Day of week (e.g., "monday", "next friday")
        days_of_week = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        for day_name, day_num in days_of_week.items():
            if day_name in text:
                current_day = now.weekday()
                days_ahead = day_num - current_day
                
                # If "next" is specified, or if the day has passed this week
                if 'next' in text or days_ahead <= 0:
                    days_ahead += 7
                
                target = now + timedelta(days=days_ahead)
                target = target.replace(hour=9, minute=0, second=0, microsecond=0)
                
                return target.isoformat()
        
        # Try to parse as ISO format directly
        try:
            datetime.fromisoformat(text)
            return text
        except ValueError:
            pass
        
        # If nothing matches, return original text
        return text
        
    except Exception as e:
        print(f"[DATE PARSER] Error parsing date: {e}")
        return text


def format_reminder_time(iso_string: str) -> str:
    """
    Format ISO datetime string into human-readable format
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        Human-readable date/time string
    """
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        now = datetime.now()
        
        # Calculate difference
        diff = dt - now
        
        if diff.total_seconds() < 0:
            return "Overdue"
        elif diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(diff.total_seconds() / 60)
            return f"in {minutes} minute{'s' if minutes != 1 else ''}"
        elif diff.days == 0:  # Today
            return f"Today at {dt.strftime('%I:%M %p')}"
        elif diff.days == 1:  # Tomorrow
            return f"Tomorrow at {dt.strftime('%I:%M %p')}"
        elif diff.days < 7:  # This week
            return dt.strftime('%A at %I:%M %p')
        else:
            return dt.strftime('%B %d at %I:%M %p')
            
    except Exception:
        return iso_string
