"""
Reminders API Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.reminder_service import get_reminder_service

router = APIRouter()
reminder_service = get_reminder_service()


class ReminderCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = None
    priority: Optional[str] = "medium"


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None


@router.get("/")
async def get_reminders(include_completed: bool = False):
    """Get all reminders"""
    try:
        reminders = reminder_service.get_reminders(include_completed=include_completed)
        return {
            "success": True,
            "reminders": reminders,
            "count": len(reminders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{reminder_id}")
async def get_reminder(reminder_id: str):
    """Get a specific reminder"""
    try:
        reminder = reminder_service.get_reminder(reminder_id)
        if reminder:
            return {"success": True, "reminder": reminder}
        raise HTTPException(status_code=404, detail="Reminder not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_reminder(reminder: ReminderCreate):
    """Create a new reminder"""
    try:
        created_reminder = reminder_service.create_reminder(
            title=reminder.title,
            description=reminder.description or "",
            due_date=reminder.due_date,
            priority=reminder.priority or "medium"
        )
        return {
            "success": True,
            "reminder": created_reminder,
            "message": "Reminder created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{reminder_id}")
async def update_reminder(reminder_id: str, reminder: ReminderUpdate):
    """Update a reminder"""
    try:
        updated_reminder = reminder_service.update_reminder(
            reminder_id=reminder_id,
            title=reminder.title,
            description=reminder.description,
            due_date=reminder.due_date,
            completed=reminder.completed,
            priority=reminder.priority
        )
        if updated_reminder:
            return {
                "success": True,
                "reminder": updated_reminder,
                "message": "Reminder updated successfully"
            }
        raise HTTPException(status_code=404, detail="Reminder not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{reminder_id}/complete")
async def mark_complete(reminder_id: str):
    """Mark a reminder as completed"""
    try:
        updated_reminder = reminder_service.mark_completed(reminder_id)
        if updated_reminder:
            return {
                "success": True,
                "reminder": updated_reminder,
                "message": "Reminder marked as completed"
            }
        raise HTTPException(status_code=404, detail="Reminder not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """Delete a reminder"""
    try:
        success = reminder_service.delete_reminder(reminder_id)
        if success:
            return {
                "success": True,
                "message": "Reminder deleted successfully"
            }
        raise HTTPException(status_code=404, detail="Reminder not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
