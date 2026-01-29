"""
Reminder Service - Create, manage, and retrieve reminders/tasks
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
REMINDERS_FILE = DATA_DIR / "reminders.json"

# Import date parser
try:
    from utils.date_parser import parse_natural_date
except ImportError:
    # Fallback if import fails
    def parse_natural_date(text):
        return text


class Reminder(BaseModel):
    """Reminder/Task model"""
    id: str
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = None  # ISO format datetime string
    created_at: str
    completed: bool = False
    priority: Optional[str] = "medium"  # low, medium, high
    notified: bool = False  # Track if user has been notified
    last_notified_at: Optional[str] = None  # Last notification timestamp


class ReminderService:
    """Service to manage reminders"""
    
    def __init__(self):
        # Ensure data directory exists
        DATA_DIR.mkdir(exist_ok=True)
        
        # Initialize reminders file if it doesn't exist
        if not REMINDERS_FILE.exists():
            self._save_reminders([])
    
    def _load_reminders(self) -> List[Dict]:
        """Load reminders from JSON file"""
        try:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading reminders: {e}")
            return []
    
    def _save_reminders(self, reminders: List[Dict]):
        """Save reminders to JSON file"""
        try:
            with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(reminders, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving reminders: {e}")
    
    def _generate_id(self) -> str:
        """Generate unique reminder ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"reminder_{timestamp}"
    
    def create_reminder(
        self, 
        title: str, 
        description: str = "", 
        due_date: Optional[str] = None,
        priority: str = "medium"
    ) -> Dict:
        """
        Create a new reminder
        
        Args:
            title: Title/summary of the reminder
            description: Detailed description
            due_date: Due date in ISO format or natural language
            priority: Priority level (low, medium, high)
            
        Returns:
            Created reminder dict
        """
        reminders = self._load_reminders()
        
        # Parse due date if provided (supports natural language)
        parsed_due_date = None
        if due_date:
            parsed_due_date = parse_natural_date(due_date)
        
        reminder = {
            "id": self._generate_id(),
            "title": title,
            "description": description,
            "due_date": parsed_due_date,
            "created_at": datetime.now().isoformat(),
            "completed": False,
            "priority": priority.lower() if priority else "medium"
        }
        
        reminders.append(reminder)
        self._save_reminders(reminders)
        
        return reminder
    
    def get_reminders(self, include_completed: bool = False) -> List[Dict]:
        """
        Get all reminders
        
        Args:
            include_completed: Whether to include completed reminders
            
        Returns:
            List of reminders
        """
        reminders = self._load_reminders()
        
        if not include_completed:
            reminders = [r for r in reminders if not r.get("completed", False)]
        
        # Sort by created date (newest first)
        reminders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return reminders
    
    def get_reminder(self, reminder_id: str) -> Optional[Dict]:
        """Get a specific reminder by ID"""
        reminders = self._load_reminders()
        
        for reminder in reminders:
            if reminder.get("id") == reminder_id:
                return reminder
        
        return None
    
    def update_reminder(
        self, 
        reminder_id: str, 
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None
    ) -> Optional[Dict]:
        """Update a reminder"""
        reminders = self._load_reminders()
        
        for i, reminder in enumerate(reminders):
            if reminder.get("id") == reminder_id:
                if title is not None:
                    reminder["title"] = title
                if description is not None:
                    reminder["description"] = description
                if due_date is not None:
                    reminder["due_date"] = due_date
                if completed is not None:
                    reminder["completed"] = completed
                if priority is not None:
                    reminder["priority"] = priority.lower()
                
                reminders[i] = reminder
                self._save_reminders(reminders)
                return reminder
        
        return None
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        reminders = self._load_reminders()
        
        original_length = len(reminders)
        reminders = [r for r in reminders if r.get("id") != reminder_id]
        
        if len(reminders) < original_length:
            self._save_reminders(reminders)
            return True
        
        return False
    
    def mark_completed(self, reminder_id: str) -> Optional[Dict]:
        """Mark a reminder as completed"""
        return self.update_reminder(reminder_id, completed=True)
    
    def get_due_reminders(self) -> List[Dict]:
        """
        Get reminders that are due now and haven't been notified yet
        
        Returns:
            List of due reminders
        """
        reminders = self._load_reminders()
        due_reminders = []
        now = datetime.now()
        
        for reminder in reminders:
            # Skip completed reminders
            if reminder.get("completed", False):
                continue
            
            # Skip already notified reminders
            if reminder.get("notified", False):
                continue
            
            # Check if due date exists and is valid
            due_date_str = reminder.get("due_date")
            if not due_date_str:
                continue
            
            try:
                # Try to parse as ISO format datetime
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                
                # Check if due (current time >= due time)
                if now >= due_date:
                    due_reminders.append(reminder)
            except (ValueError, AttributeError):
                # If parsing fails, skip this reminder
                continue
        
        return due_reminders
    
    def mark_notified(self, reminder_id: str) -> Optional[Dict]:
        """Mark a reminder as notified"""
        reminders = self._load_reminders()
        
        for i, reminder in enumerate(reminders):
            if reminder.get("id") == reminder_id:
                reminder["notified"] = True
                reminder["last_notified_at"] = datetime.now().isoformat()
                reminders[i] = reminder
                self._save_reminders(reminders)
                return reminder
        
        return None


# Global instance
_reminder_service: Optional[ReminderService] = None


def get_reminder_service() -> ReminderService:
    """Get or create reminder service instance"""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service
