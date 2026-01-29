"""
Reminder Scheduler - Background service to check and notify due reminders
"""

import threading
import time
from datetime import datetime
from typing import Optional, Callable
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.reminder_service import get_reminder_service


class ReminderScheduler:
    """Background scheduler for reminder notifications"""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize the scheduler
        
        Args:
            check_interval: How often to check for due reminders (in seconds)
        """
        self.check_interval = check_interval
        self.reminder_service = get_reminder_service()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks: list[Callable] = []
        
    def register_callback(self, callback: Callable):
        """
        Register a callback to be called when a reminder is due
        
        Args:
            callback: Function that takes a reminder dict as argument
        """
        self._callbacks.append(callback)
    
    def _check_reminders(self):
        """Check for due reminders and trigger callbacks"""
        try:
            due_reminders = self.reminder_service.get_due_reminders()
            
            if due_reminders:
                print(f"[REMINDER] Found {len(due_reminders)} due reminder(s)")
                
                for reminder in due_reminders:
                    # Trigger all registered callbacks
                    for callback in self._callbacks:
                        try:
                            callback(reminder)
                        except Exception as e:
                            print(f"[REMINDER] Error in callback: {e}")
                    
                    # Mark as notified
                    self.reminder_service.mark_notified(reminder["id"])
                    print(f"[REMINDER] Notified: {reminder.get('title', 'Untitled')}")
        
        except Exception as e:
            print(f"[REMINDER] Error checking reminders: {e}")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        print(f"[REMINDER] Scheduler started (checking every {self.check_interval}s)")
        
        while not self._stop_event.is_set():
            self._check_reminders()
            
            # Sleep in small intervals to allow quick shutdown
            for _ in range(self.check_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
        
        print("[REMINDER] Scheduler stopped")
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            print("[REMINDER] Scheduler is already running")
            return
        
        self._stop_event.clear()
        self.is_running = True
        
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        
        print("[OK] Reminder scheduler initialized")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        print("[REMINDER] Stopping scheduler...")
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5)
        
        self.is_running = False
        print("[REMINDER] Scheduler stopped")


# Global instance
_scheduler: Optional[ReminderScheduler] = None


def get_scheduler() -> ReminderScheduler:
    """Get or create scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ReminderScheduler(check_interval=30)  # Check every 30 seconds
    return _scheduler


def start_reminder_scheduler(check_interval: int = 30) -> ReminderScheduler:
    """
    Start the reminder scheduler
    
    Args:
        check_interval: How often to check for due reminders (in seconds)
        
    Returns:
        ReminderScheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = ReminderScheduler(check_interval=check_interval)
    
    _scheduler.start()
    return _scheduler


def stop_reminder_scheduler():
    """Stop the reminder scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
