"""
Reminder Notifier - Handles notifications for due reminders
"""

import sys
import re
from pathlib import Path
from typing import Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))

from core.speech import TextToSpeech
from services.notification_service import NotificationService


class ReminderNotifier:
    """Handles notifications for due reminders"""
    
    def __init__(self):
        self.tts = TextToSpeech()
        self.notification_service = NotificationService()
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for speaking - remove special characters, quotes, etc.
        
        Args:
            text: Raw text that may contain special characters
            
        Returns:
            Cleaned text suitable for TTS
        """
        if not text:
            return ""
        
        # Remove surrounding quotes (single or double)
        text = text.strip("'\"")
        
        # Remove JSON-like syntax
        text = re.sub(r"['\"]?\w+['\"]?\s*:\s*['\"]?", "", text)
        
        # Remove markdown formatting
        text = re.sub(r'[*_`~#]+', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove emojis and special unicode characters
        text = re.sub(r'[^\x00-\x7F\s]+', '', text)
        
        # Remove extra special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\'-]', '', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def notify_reminder(self, reminder: Dict):
        """
        Notify user about a due reminder
        
        Args:
            reminder: Reminder dictionary with title, description, priority, etc.
        """
        # Clean the title and description
        title = self._clean_text(reminder.get("title", "Reminder"))
        description = self._clean_text(reminder.get("description", ""))
        priority = reminder.get("priority", "medium")
        
        # Build notification message
        message = f"Reminder: {title}"
        if description:
            message += f". {description}"
        
        # Add priority indicator for high priority
        if priority == "high":
            message = f"Important {message}"
        
        print(f"[REMINDER ALERT] {message}")
        
        # Speak the reminder
        try:
            speech_text = message
            if priority == "high":
                speech_text = f"This is an important reminder. {title}"
            else:
                speech_text = f"Reminder. {title}"
            
            if description:
                speech_text += f". {description}"
            
            self.tts.speak(speech_text)
        except Exception as e:
            print(f"[REMINDER] Error speaking reminder: {e}")
        
        # Show desktop notification
        try:
            notification_title = "⏰ Reminder" if priority != "high" else "🔴 Important Reminder"
            notification_body = title
            if description:
                notification_body += f"\n{description}"
            
            self.notification_service.send_notification(
                title=notification_title,
                message=notification_body,
                app_name="Stereo Sonic Assistant"
            )
        except Exception as e:
            print(f"[REMINDER] Error sending desktop notification: {e}")


# Global instance
_notifier: Optional[ReminderNotifier] = None


def get_reminder_notifier() -> ReminderNotifier:
    """Get or create reminder notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = ReminderNotifier()
    return _notifier
