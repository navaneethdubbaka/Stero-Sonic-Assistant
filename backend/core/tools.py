"""
Langchain tools for Stereo Sonic Assistant
These tools allow the LLM to interact with all services
"""

from langchain.tools import Tool
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    from langchain.tools import StructuredTool
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List
import json
import sys
import os
from pathlib import Path
from langchain_core.messages import HumanMessage

from core.llm_factory import create_vision_llm

# Add services to path
sys.path.append(str(Path(__file__).parent.parent))

from services.email_service import EmailService
from services.whatsapp_service import WhatsAppService
from services.camera_service import CameraService
from services.screenshot_service import ScreenshotService
from services.system_service import SystemService
from services.data_service import DataService
from services.lens_service import LensService
from services.notification_service import NotificationService
from services.reminder_service import get_reminder_service
from services.spotify_service import get_spotify_service
from services.robot_service import get_robot_service

# Initialize services
email_service = EmailService()
whatsapp_service = WhatsAppService()
camera_service = CameraService()
screenshot_service = ScreenshotService()
system_service = SystemService()
data_service = DataService()
lens_service = LensService()
notification_service = NotificationService()
reminder_service = get_reminder_service()

# Initialize Spotify service with play button template image
spotify_service = get_spotify_service(play_button_image_path=r"E:\Stero Sonic Assistant\spotify_play.png")

# Initialize Robot service for Pi robot control
robot_service = get_robot_service()

# Start notification monitoring on initialization
notification_service.start_monitoring()


# Tool input schemas
class SendEmailInput(BaseModel):
    to: str = Field(description="Email address of the recipient")
    content: str = Field(description="Email content/message")
    attachment_path: Optional[str] = Field(None, description="Path to attachment file (optional)")


class SendWhatsAppInput(BaseModel):
    name: Optional[str] = Field(None, description="Contact name from contacts file (optional)")
    phone_number: Optional[str] = Field(None, description="Recipient phone number with country code (e.g., +15551234567)")
    message: str = Field(description="Message to send via WhatsApp")

    @root_validator(pre=True)
    def _require_name_or_number(cls, values):
        if not values.get('name') and not values.get('phone_number'):
            # Allow some agents that put recipient under 'to'
            if values.get('to'):
                values['name'] = values.get('to')
        return values


class StoreDataInput(BaseModel):
    key: str = Field(description="Key to store the data under")
    value: str = Field(description="Value to store")


class RetrieveDataInput(BaseModel):
    key: str = Field(description="Key to retrieve data for")


class SaveNoteInput(BaseModel):
    text: str = Field(description="Text content to save as note")
    file_path: Optional[str] = Field(None, description="Path where to save the note (optional)")


class UploadImageToLensInput(BaseModel):
    image_path: str = Field(description="Path to the image file to upload to Google Lens")


class SearchWikipediaInput(BaseModel):
    query: str = Field(description="Search query for Wikipedia")


class SearchYouTubeInput(BaseModel):
    query: str = Field(description="Search query for YouTube")


class SearchGoogleInput(BaseModel):
    query: str = Field(description="Search query for Google")


class OpenAppInput(BaseModel):
    app_name: str = Field(description="Name of the application to open via Windows search")


class CloseProcessesInput(BaseModel):
    exe_list: List[str] = Field(description="List of executable names to close (e.g., ['chrome.exe', 'notepad.exe'])")


class CloseAppsByNamesInput(BaseModel):
    names: Optional[List[str]] = Field(None, description="List of application names (e.g., ['chrome','spotify','notepad.exe']) to close")
    app_names: Optional[List[str]] = Field(None, description="Alias for names; some agents send 'app_names'")

    @root_validator(pre=True)
    def _coalesce_names(cls, values):
        # Accept either 'names' or 'app_names'
        if (not values.get('names')) and values.get('app_names'):
            values['names'] = values.get('app_names')
        return values


class ListRunningAppsInput(BaseModel):
    include_system: Optional[bool] = Field(False, description="Include system/background processes as well")


class GetNotificationsInput(BaseModel):
    limit: Optional[int] = Field(10, description="Number of recent notifications to retrieve (default: 10)")


class GetNotificationsByAppInput(BaseModel):
    app_name: str = Field(description="Name of the application to filter notifications by")
    limit: Optional[int] = Field(10, description="Number of notifications to retrieve (default: 10)")


# Robot tool input schemas
class RobotMoveInput(BaseModel):
    direction: str = Field(description="Direction to move: 'forward', 'backward', 'left', 'right', or 'stop'")
    speed: Optional[int] = Field(160, description="Movement speed (0-255, default 160)")


class RobotServoInput(BaseModel):
    angle: int = Field(description="Servo angle in degrees (0-180, 90 is center)")


class RobotLookInput(BaseModel):
    direction: str = Field(description="Direction to look: 'left', 'right', or 'center'")


# Tool functions
def send_email(to: str, content: str, attachment_path: Optional[str] = None) -> str:
    """Send an email with optional attachment"""
    result = email_service.send_email(to, content, attachment_path)
    if result.get("success"):
        return f"Email sent successfully to {to}"
    return f"Failed to send email: {result.get('error', 'Unknown error')}"


def send_whatsapp(recipient: str, message: str) -> str:
    """Send a WhatsApp message to a contact name or direct phone number"""
    result = whatsapp_service.send_message(recipient, message)
    if result.get("success"):
        return f"WhatsApp message sent successfully"
    return f"Failed to send WhatsApp message: {result.get('error', 'Unknown error')}"


def send_whatsapp_tool(name: Optional[str] = None, phone_number: Optional[str] = None, message: str = "", to: Optional[str] = None, **kwargs) -> str:
    """Wrapper that accepts name or phone_number (or 'to' alias) and sends via WhatsApp.

    Agents may supply inputs with different keys; this consolidates into one recipient string.
    """
    recipient = phone_number or name or to or ""
    # Also check common alternate nesting
    if not recipient and isinstance(kwargs.get('recipient'), str):
        recipient = kwargs.get('recipient')
    raw_arg = kwargs.get('__arg')
    if not recipient and isinstance(raw_arg, str):
        recipient = raw_arg

    # If recipient is a dict-like string, try to parse and extract fields
    def _try_parse_dict_string(s: str):
        try:
            j = s
            if s.strip().startswith("'") or s.strip().startswith('{'):
                j = s.replace("'", '"')
            data = json.loads(j)
            if isinstance(data, dict):
                return data
        except Exception:
            return None
        return None

    if isinstance(recipient, str) and recipient.strip().startswith('{'):
        parsed = _try_parse_dict_string(recipient)
        if parsed:
            # Prefer explicit phone_number, fallback to name/to
            pn = parsed.get('phone_number') or parsed.get('to')
            nm = parsed.get('name')
            msg = parsed.get('message', message)
            recipient = pn or nm or recipient
            message = msg

    # Also allow full payload in __arg/input
    payload = None
    if isinstance(raw_arg, str) and raw_arg.strip().startswith('{'):
        payload = _try_parse_dict_string(raw_arg)
    if payload is None and isinstance(kwargs.get('input'), str) and kwargs.get('input').strip().startswith('{'):
        payload = _try_parse_dict_string(kwargs.get('input'))
    if isinstance(payload, dict):
        recipient = payload.get('phone_number') or payload.get('name') or recipient
        if not message:
            message = payload.get('message', message)

    if not recipient:
        return "Failed to send WhatsApp message: No recipient provided"
    return send_whatsapp(str(recipient), message)


def capture_camera_image(*args, **kwargs) -> str:
    """Capture an image from the camera"""
    result = camera_service.capture_image()
    if result.get("success"):
        return f"Image captured successfully and saved to {result.get('path')}"
    return f"Failed to capture image: {result.get('error', 'Unknown error')}"


def take_screenshot(*args, **kwargs) -> str:
    """Take a screenshot of the screen"""
    result = screenshot_service.take_screenshot()
    if result.get("success"):
        return f"Screenshot taken successfully and saved to {result.get('path')}"
    return f"Failed to take screenshot: {result.get('error', 'Unknown error')}"


def get_current_time(*args, **kwargs) -> str:
    """Get the current time"""
    result = system_service.get_time()
    if result.get("success"):
        return f"The current time is {result.get('time')}"
    return f"Failed to get time: {result.get('error', 'Unknown error')}"


def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information about a topic"""
    result = system_service.search_wikipedia(query)
    if result.get("success"):
        return result.get("summary", "No summary found")
    return f"Failed to search Wikipedia: {result.get('error', 'Unknown error')}"


def search_youtube(query: str) -> str:
    """Search YouTube for videos"""
    result = system_service.open_youtube(query)
    if result.get("success"):
        return f"YouTube search opened for: {query}"
    return f"Failed to search YouTube: {result.get('error', 'Unknown error')}"


def search_google(query: str) -> str:
    """Search Google for information"""
    result = system_service.open_google(query)
    if result.get("success"):
        return f"Google search opened for: {query}"
    return f"Failed to search Google: {result.get('error', 'Unknown error')}"


def open_stackoverflow(*args, **kwargs) -> str:
    """Open StackOverflow website"""
    result = system_service.open_stackoverflow()
    if result.get("success"):
        return "StackOverflow opened successfully"
    return f"Failed to open StackOverflow: {result.get('error', 'Unknown error')}"


def play_music(song_name: str = "", artist: str = "", platform: str = "spotify") -> str:
    """
    Play music - either search on Spotify or play from local directory
    
    Args:
        song_name: Name of song to search and play (optional). If not provided, plays local music.
        artist: Artist name for better search results (optional)
        platform: Music platform to use (default: "spotify", can also be "local")
    
    Returns:
        Status message
    
    Examples:
        - "play Apna Bana Le" → song_name="Apna Bana Le", platform="spotify"
        - "play Shape of You by Ed Sheeran" → song_name="Shape of You", artist="Ed Sheeran"
        - "play music" → Uses local music directory
    """
    # If song name is provided, search and play on specified platform
    if song_name and song_name.strip():
        if platform.lower() == "local":
            # Play from local directory
            result = system_service.play_music()
            if result.get("success"):
                return f"Playing music: {result.get('song', 'Unknown song')}"
            return f"Failed to play music: {result.get('error', 'Unknown error')}"
        else:
            # Search and play on Spotify (default)
            try:
                if artist and artist.strip():
                    result = spotify_service.play_song_directly(song_name, artist=artist)
                else:
                    result = spotify_service.search_and_play(song_name)
                
                if result.get("success"):
                    return result.get("message", f"Playing '{song_name}' on Spotify")
                else:
                    return f"Failed to play song: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"Error playing song: {str(e)}"
    else:
        # No song specified, play local music
        result = system_service.play_music()
        if result.get("success"):
            return f"Playing music: {result.get('song', 'Unknown song')}"
        return f"Failed to play music: {result.get('error', 'Unknown error')}"


def open_app(app_name: str) -> str:
    """Open an application using Windows search"""
    result = system_service.open_windows_search(app_name)
    if result.get("success"):
        return result.get("message", f"Application {app_name} opened")
    return f"Failed to open application: {result.get('error', 'Unknown error')}"


def switch_windows(*args, **kwargs) -> str:
    """Switch between open windows"""
    result = system_service.switch_windows()
    if result.get("success"):
        return "Switched windows successfully"
    return f"Failed to switch windows: {result.get('error', 'Unknown error')}"


def close_processes(exe_list: List[str]) -> str:
    """Close specific executable processes"""
    result = system_service.close_processes(exe_list)
    if result.get("success"):
        closed = result.get("closed_processes", [])
        if closed:
            names = [p.get("name", "Unknown") for p in closed]
            return f"Closed processes: {', '.join(names)}"
        return "No matching processes found to close"
    return f"Failed to close processes: {result.get('error', 'Unknown error')}"


def list_running_apps(include_system: Optional[bool] = False) -> str:
    """List running user-facing applications with pid, name, exe, and optional window title"""
    result = system_service.get_running_apps(include_system=bool(include_system))
    if not result.get("success"):
        return f"Failed to list running apps: {result.get('error', 'Unknown error')}"
    apps = result.get("apps", [])
    if not apps:
        return "No running applications found"
    # Produce a concise, LLM-parsable listing
    lines = [f"{a.get('name','Unknown')} (pid {a.get('pid')}): {a.get('window_title') or ''}".strip() for a in apps]
    return "\n".join(lines)


def close_apps_by_names(names: List[str]) -> str:
    """Close applications by friendly names or executable names"""
    result = system_service.close_apps_by_names(names)
    if result.get("success"):
        closed = result.get("closed", [])
        if closed:
            names_str = ", ".join(f"{c.get('name','Unknown')} (pid {c.get('pid')})" for c in closed)
            return f"Closed: {names_str}"
        return "No matching applications found to close"
    return f"Failed to close apps: {result.get('error','Unknown error')}"


def close_apps_by_names_tool(names: Optional[List[str]] = None, app_names: Optional[List[str]] = None, **kwargs) -> str:
    """Wrapper accepting either 'names' or 'app_names' (from dict/JSON/kwargs) and delegating.

    Accepts inputs in multiple shapes to be resilient to agent formatting.
    """
    merged = names or app_names
    # Try kwargs
    if not merged and kwargs:
        if isinstance(kwargs.get('names'), list):
            merged = kwargs.get('names')
        elif isinstance(kwargs.get('app_names'), list):
            merged = kwargs.get('app_names')
        elif 'input' in kwargs:
            raw = kwargs.get('input')
            try:
                if isinstance(raw, str):
                    parsed = json.loads(raw)
                else:
                    parsed = raw
                if isinstance(parsed, dict):
                    merged = parsed.get('names') or parsed.get('app_names')
                elif isinstance(parsed, list):
                    merged = parsed
                elif isinstance(parsed, str):
                    merged = [s.strip() for s in parsed.split(',') if s.strip()]
            except Exception:
                if isinstance(raw, str):
                    merged = [s.strip() for s in raw.split(',') if s.strip()]
        elif '__arg' in kwargs:
            raw = kwargs.get('__arg')
            # Try JSON first (after converting single quotes to double quotes)
            if isinstance(raw, str):
                try:
                    j = raw.replace("'", '"')
                    parsed = json.loads(j)
                    if isinstance(parsed, dict):
                        merged = parsed.get('names') or parsed.get('app_names')
                    elif isinstance(parsed, list):
                        merged = parsed
                except Exception:
                    # Fallback: naive bracket extraction of a list inside the string
                    try:
                        start = raw.find('[')
                        end = raw.rfind(']')
                        if start != -1 and end != -1 and end > start:
                            inner = raw[start+1:end]
                            parts = [p.strip().strip('"').strip("'") for p in inner.split(',')]
                            merged = [p for p in parts if p]
                    except Exception:
                        pass
    # Final normalization
    if not merged:
        return "Failed to close apps: No application names provided"
    if isinstance(merged, str):
        merged = [merged]
    merged = [str(x).strip() for x in merged if str(x).strip()]
    return close_apps_by_names(merged)


def store_data(key: str, value: str) -> str:
    """Store key-value data for later retrieval"""
    result = data_service.store_data(key, value)
    if result.get("success"):
        return f"Data stored successfully with key: {key}"
    return f"Failed to store data: {result.get('error', 'Unknown error')}"


def retrieve_data(key: str) -> str:
    """Retrieve stored data by key"""
    result = data_service.retrieve_data(key)
    if result.get("success"):
        return f"Retrieved data for key '{key}': {result.get('value')}"
    return f"Failed to retrieve data: {result.get('error', 'Unknown error')}"


def save_note(text: str, file_path: Optional[str] = None) -> str:
    """Save a note or text to a file"""
    result = data_service.save_note(text, file_path)
    if result.get("success"):
        return f"Note saved successfully to {result.get('path')}"
    return f"Failed to save note: {result.get('error', 'Unknown error')}"


def upload_image_to_lens(image_path: str) -> str:
    """Upload an image to Google Lens for visual search"""
    result = lens_service.upload_image_to_lens(image_path)
    if result.get("success"):
        return result.get("message", "Image uploaded to Google Lens successfully")
    return f"Failed to upload image to Lens: {result.get('error', 'Unknown error')}"


def scan_screen_with_lens(*args, **kwargs) -> str:
    """Take a screenshot and upload it to Google Lens"""
    # Take full screenshot instead of region selection (more reliable)
    screenshot_result = screenshot_service.take_screenshot()
    if screenshot_result.get("success"):
        path = screenshot_result.get("path")
        lens_result = lens_service.upload_image_to_lens(path)
        if lens_result.get("success"):
            return f"Screenshot captured and uploaded to Google Lens successfully. Path: {path}"
        return f"Screenshot captured at {path}, but failed to upload to Lens: {lens_result.get('error', 'Unknown error')}"
    return f"Failed to capture screenshot: {screenshot_result.get('error', 'Unknown error')}"


def scan_camera_with_lens(*args, **kwargs) -> str:
    """Capture an image from the camera and upload it to Google Lens for visual search"""
    # Capture image from camera
    camera_result = camera_service.capture_image()
    if camera_result.get("success"):
        path = camera_result.get("path")
        lens_result = lens_service.upload_image_to_lens(path)
        if lens_result.get("success"):
            return f"Camera image captured and uploaded to Google Lens successfully. Path: {path}"
        return f"Camera image captured at {path}, but failed to upload to Lens: {lens_result.get('error', 'Unknown error')}"
    return f"Failed to capture camera image: {camera_result.get('error', 'Unknown error')}"


def analyze_image_with_vision(image_path: str, user_prompt: Optional[str] = None) -> str:
    """Analyze an image using vision LLM (Ollama when LOCAL_LLM=True, else Gemini)."""
    try:
        abs_image_path = os.path.abspath(image_path)
        if not os.path.exists(abs_image_path):
            return f"Error: Image file not found at {abs_image_path}"
        
        llm = create_vision_llm()
        prompt_text = user_prompt or "Please analyze this image and describe what you see. Provide a detailed explanation of the contents, objects, text, and any other relevant information."
        
        import base64
        with open(abs_image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        _, ext = os.path.splitext(abs_image_path)
        mime_type = "image/png" if ext.lower() == ".png" else "image/jpeg"
        image_url = f"data:{mime_type};base64,{image_data}"
        
        # Message format supported by both Gemini and Ollama (LangChain multimodal)
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": image_url},
            ]
        )
        response = llm.invoke([message])
        return response.content
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error analyzing image with vision: {str(e)}"


def analyze_screen_with_vision(*args, **kwargs) -> str:
    """Take a screenshot and analyze it using Gemini vision"""
    # Take screenshot
    screenshot_result = screenshot_service.take_screenshot()
    if screenshot_result.get("success"):
        path = screenshot_result.get("path")
        # Analyze with Gemini vision
        analysis_result = analyze_image_with_vision(path)
        return f"Screenshot captured and analyzed. Path: {path}\n\nAnalysis:\n{analysis_result}"
    return f"Failed to capture screenshot: {screenshot_result.get('error', 'Unknown error')}"


def analyze_camera_with_vision(*args, **kwargs) -> str:
    """Capture an image from the camera and analyze it using Gemini vision"""
    # Capture image from camera
    camera_result = camera_service.capture_image()
    if camera_result.get("success"):
        path = camera_result.get("path")
        # Analyze with Gemini vision
        analysis_result = analyze_image_with_vision(path)
        return f"Camera image captured and analyzed. Path: {path}\n\nAnalysis:\n{analysis_result}"
    return f"Failed to capture camera image: {camera_result.get('error', 'Unknown error')}"


def get_recent_notifications(limit: Optional[int] = 10) -> str:
    """Get recent notifications from notification history"""
    result = notification_service.get_recent_notifications(limit=limit or 10)
    if result.get("success"):
        notifications = result.get("notifications", [])
        if not notifications:
            return "No recent notifications found"
        
        # Format notifications nicely
        lines = []
        for notif in notifications:
            timestamp = notif.get('timestamp', 'Unknown time')
            app_name = notif.get('app_name', 'Unknown app')
            title = notif.get('title', 'No title')
            body = notif.get('body', '')
            
            line = f"[{timestamp}] {app_name}: {title}"
            if body:
                line += f" - {body}"
            lines.append(line)
        
        return f"Found {len(notifications)} recent notification(s):\n" + "\n".join(lines)
    return f"Failed to get notifications: {result.get('error', 'Unknown error')}"


def get_new_notifications(*args, **kwargs) -> str:
    """Get new notifications from the last few minutes"""
    result = notification_service.get_new_notifications(since_minutes=5)
    if result.get("success"):
        notifications = result.get("notifications", [])
        if not notifications:
            return "No new notifications found in the last 5 minutes"
        
        # Format notifications nicely
        lines = []
        for notif in notifications:
            timestamp = notif.get('timestamp', 'Unknown time')
            app_name = notif.get('app_name', 'Unknown app')
            title = notif.get('title', 'No title')
            body = notif.get('body', '')
            
            line = f"[{timestamp}] {app_name}: {title}"
            if body:
                line += f" - {body}"
            lines.append(line)
        
        return f"Found {len(notifications)} new notification(s):\n" + "\n".join(lines)
    return f"Failed to get new notifications: {result.get('error', 'Unknown error')}"


def get_notifications_by_app(app_name: str, limit: Optional[int] = 10) -> str:
    """Get notifications filtered by application name"""
    result = notification_service.get_notifications_by_app(app_name=app_name, limit=limit or 10)
    if result.get("success"):
        notifications = result.get("notifications", [])
        if not notifications:
            return f"No notifications found from {app_name}"
        
        # Format notifications nicely
        lines = []
        content_available = False
        for notif in notifications:
            timestamp = notif.get('timestamp', 'Unknown time')
            title = notif.get('title', 'No title')
            body = notif.get('body', '')
            
            # Check if this is the privacy restriction message
            if body and "Content not available" not in body and body.strip():
                content_available = True
            
            line = f"[{timestamp}] {title}"
            if body and body.strip():
                line += f" - {body}"
            lines.append(line)
        
        response = f"Found {len(notifications)} notification(s) from {app_name}:\n" + "\n".join(lines)
        
        # Add note if content is not available
        if not content_available:
            response += "\n\nNote: Windows privacy restrictions prevent accessing notification content from history. Content is only available for notifications captured in real-time as they arrive."
        
        return response
    return f"Failed to get notifications from {app_name}: {result.get('error', 'Unknown error')}"


# Reminder tool functions
def create_reminder(title: str, description: str = "", due_date: str = "", priority: str = "medium") -> str:
    """
    Create a new reminder/task with optional due date
    
    Args:
        title: Title or summary of the reminder (e.g., "call mom", "buy groceries")
        description: Detailed description (optional)
        due_date: REQUIRED if user mentions time! Due date/time in natural language like:
                  "in 5 minutes", "in 2 hours", "tomorrow at 3pm", "today at 5pm", 
                  "next Monday", "at 8pm". Leave empty only if no time is mentioned.
        priority: Priority level - low, medium, or high (default: medium)
    
    Returns:
        Confirmation message
    
    IMPORTANT: When user says "remind me to X in Y time" or "remind me to X at Y time",
    you MUST extract and pass the time part (e.g., "in 5 minutes", "at 3pm") to the due_date parameter!
    
    Examples:
    - "remind me to call mom in 5 minutes" → title="call mom", due_date="in 5 minutes"
    - "remind me to take medicine at 8pm" → title="take medicine", due_date="at 8pm"
    - "remind me tomorrow to buy milk" → title="buy milk", due_date="tomorrow"
    - "add reminder to exercise" → title="exercise", due_date="" (no time mentioned)
    """
    try:
        # If no due_date provided, try to extract from title
        if not due_date and title:
            import re
            # Look for time expressions in the title
            time_patterns = [
                r'in\s+\d+\s+(minute|minutes|min|hour|hours|hr|day|days)',
                r'at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?',
                r'tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?',
                r'today(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?',
                r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, title.lower())
                if match:
                    due_date = match.group(0)
                    # Remove the time part from title
                    title = re.sub(r'\s*' + re.escape(match.group(0)) + r'\s*', ' ', title, flags=re.IGNORECASE).strip()
                    break
        
        reminder = reminder_service.create_reminder(
            title=title,
            description=description or "",
            due_date=due_date or None,
            priority=priority or "medium"
        )
        
        msg = f"Reminder created: '{title}'"
        if due_date:
            msg += f" (Due: {due_date})"
        if priority and priority.lower() != "medium":
            msg += f" [Priority: {priority.upper()}]"
        
        return msg
    except Exception as e:
        return f"Failed to create reminder: {str(e)}"


def get_reminders_list(include_completed: bool = False) -> str:
    """Get all reminders/tasks"""
    try:
        reminders = reminder_service.get_reminders(include_completed=include_completed)
        
        if not reminders:
            return "No reminders found"
        
        lines = [f"Found {len(reminders)} reminder(s):"]
        for r in reminders:
            status = "✓" if r.get("completed") else "○"
            title = r.get("title", "No title")
            priority = r.get("priority", "medium")
            priority_mark = {"high": "!", "medium": "", "low": "-"}.get(priority, "")
            
            line = f"{status} {title}{priority_mark}"
            
            if r.get("due_date"):
                line += f" (Due: {r.get('due_date')})"
            
            if r.get("description"):
                line += f" - {r.get('description')}"
            
            lines.append(line)
        
        return "\n".join(lines)
    except Exception as e:
        return f"Failed to get reminders: {str(e)}"


def mark_reminder_done(reminder_id: str) -> str:
    """Mark a reminder as completed"""
    try:
        reminder = reminder_service.mark_completed(reminder_id)
        if reminder:
            return f"Marked reminder '{reminder.get('title')}' as completed"
        return "Reminder not found"
    except Exception as e:
        return f"Failed to mark reminder as done: {str(e)}"


# Spotify tool functions
def play_song_on_spotify(song_query: str, artist: str = "") -> str:
    """
    Search and play a song on Spotify
    
    Args:
        song_query: Song name or search query (e.g., "Apna Bana Le", "Shape of You")
        artist: Optional artist name for better results (e.g., "Ed Sheeran")
    
    Returns:
        Status message
    
    Examples:
        - "play Apna Bana Le on Spotify" → song_query="Apna Bana Le"
        - "play Shape of You by Ed Sheeran" → song_query="Shape of You", artist="Ed Sheeran"
        - "search for Coldplay songs on Spotify" → song_query="Coldplay"
    """
    try:
        if artist and artist.strip():
            result = spotify_service.play_song_directly(song_query, artist=artist)
        else:
            result = spotify_service.search_and_play(song_query)
        
        if result.get("success"):
            return result.get("message", f"Playing '{song_query}' on Spotify")
        else:
            return f"Failed to play song: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error playing song on Spotify: {str(e)}"


def search_music(query: str, platform: str = "spotify") -> str:
    """
    Search for music on a streaming platform
    
    Args:
        query: Search query (song name, artist, album, etc.)
        platform: Music platform (default: spotify)
    
    Returns:
        Status message
    """
    try:
        result = spotify_service.search_and_play(query, platform=platform)
        
        if result.get("success"):
            return result.get("message", f"Searching for '{query}' on {platform}")
        else:
            return f"Failed to search: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error searching music: {str(e)}"


# Robot control tool functions
def robot_move(direction: str = "stop", speed: int = 160, **kwargs) -> str:
    """
    Move the robot in a direction
    
    Args:
        direction: One of 'forward', 'backward', 'left', 'right', 'stop'
        speed: Movement speed (0-255, default 160)
    
    Returns:
        Status message
    
    Examples:
        - "move the robot forward" -> direction="forward"
        - "turn the robot left" -> direction="left"
        - "stop the robot" -> direction="stop"
        - "go back" -> direction="backward"
    """
    try:
        # Debug: Print what we received
        print(f"[DEBUG robot_move] Raw input - direction: {direction!r} (type: {type(direction).__name__}), speed: {speed!r} (type: {type(speed).__name__}), kwargs: {kwargs}")
        
        # Handle if direction is actually the RobotMoveInput model or a dict
        if hasattr(direction, 'direction'):
            # It's a Pydantic model
            speed = getattr(direction, 'speed', speed) or 160
            direction = getattr(direction, 'direction', 'stop')
        elif isinstance(direction, dict):
            # If direction is a dict (e.g., the whole input was passed)
            speed = direction.get('speed', speed) or 160
            direction = direction.get('direction', 'stop')
        elif isinstance(direction, str) and (direction.startswith('{') or direction.startswith("'{")):
            # The entire input was passed as a JSON/dict string - parse it
            try:
                # Replace single quotes with double quotes for JSON parsing
                import json
                json_str = direction.replace("'", '"')
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    speed = parsed.get('speed', speed) or 160
                    direction = parsed.get('direction', 'stop')
                    print(f"[DEBUG robot_move] Parsed from JSON string - direction: {direction!r}, speed: {speed}")
            except json.JSONDecodeError:
                # Try ast.literal_eval as fallback
                try:
                    import ast
                    parsed = ast.literal_eval(direction)
                    if isinstance(parsed, dict):
                        speed = parsed.get('speed', speed) or 160
                        direction = parsed.get('direction', 'stop')
                        print(f"[DEBUG robot_move] Parsed with ast - direction: {direction!r}, speed: {speed}")
                except (ValueError, SyntaxError):
                    pass
        
        # Ensure direction is a string
        direction = str(direction).lower().strip()
        
        # Ensure speed is an int
        if isinstance(speed, str):
            try:
                speed = int(speed)
            except ValueError:
                speed = 160
        speed = int(speed) if speed else 160
        
        print(f"[DEBUG robot_move] Processed - direction: {direction!r}, speed: {speed}")
        
        result = robot_service.move(direction, speed)
        print(f"[DEBUG robot_move] Service result: {result}")
        
        if result.get("success"):
            if direction == "stop":
                return "Robot stopped"
            return f"Robot moving {direction} at speed {speed}"
        return f"Failed to move robot: {result.get('error', 'Unknown error')}"
    except Exception as e:
        import traceback
        print(f"[DEBUG robot_move] Exception: {e}\n{traceback.format_exc()}")
        return f"Error controlling robot: {str(e)}"


def robot_move_forward(speed: int = 160) -> str:
    """Move the robot forward"""
    return robot_move("forward", speed)


def robot_move_backward(speed: int = 160) -> str:
    """Move the robot backward"""
    return robot_move("backward", speed)


def robot_turn_left(speed: int = 160) -> str:
    """Turn the robot left"""
    return robot_move("left", speed)


def robot_turn_right(speed: int = 160) -> str:
    """Turn the robot right"""
    return robot_move("right", speed)


def robot_stop(*args, **kwargs) -> str:
    """Stop the robot immediately"""
    try:
        result = robot_service.stop()
        if result.get("success"):
            return "Robot stopped"
        return f"Failed to stop robot: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error stopping robot: {str(e)}"


def robot_set_servo(angle: int = 90, **kwargs) -> str:
    """
    Set the robot camera servo angle
    
    Args:
        angle: Servo angle in degrees (0-180, 90 is center)
    
    Returns:
        Status message
    """
    try:
        # Handle various input formats from LLM
        if isinstance(angle, dict):
            angle = angle.get('angle', 90)
        elif isinstance(angle, str) and (angle.startswith('{') or angle.startswith("'{")):
            # The entire input was passed as a JSON/dict string - parse it
            try:
                import json
                json_str = angle.replace("'", '"')
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    angle = parsed.get('angle', 90)
            except:
                try:
                    import ast
                    parsed = ast.literal_eval(angle)
                    if isinstance(parsed, dict):
                        angle = parsed.get('angle', 90)
                except:
                    pass
        
        # Ensure angle is an int
        if isinstance(angle, str):
            try:
                angle = int(angle)
            except ValueError:
                angle = 90
        angle = int(angle) if angle is not None else 90
        angle = max(0, min(180, angle))  # Clamp to valid range
        
        result = robot_service.set_servo(angle)
        if result.get("success"):
            return f"Robot camera set to {angle} degrees"
        return f"Failed to set servo: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error setting servo: {str(e)}"


def robot_look(direction: str = "center", **kwargs) -> str:
    """
    Make the robot look in a direction (controls camera servo)
    
    Args:
        direction: 'left', 'right', or 'center'
    
    Returns:
        Status message
    
    Examples:
        - "make the robot look left" -> direction="left"
        - "robot look right" -> direction="right"
        - "center the robot camera" -> direction="center"
    """
    try:
        # Handle various input formats from LLM
        if isinstance(direction, dict):
            direction = direction.get('direction', 'center')
        elif isinstance(direction, str) and (direction.startswith('{') or direction.startswith("'{")):
            # The entire input was passed as a JSON/dict string - parse it
            try:
                import json
                json_str = direction.replace("'", '"')
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    direction = parsed.get('direction', 'center')
            except:
                try:
                    import ast
                    parsed = ast.literal_eval(direction)
                    if isinstance(parsed, dict):
                        direction = parsed.get('direction', 'center')
                except:
                    pass
        
        direction = str(direction).lower().strip()
        
        if direction == "left":
            result = robot_service.look_left()
        elif direction == "right":
            result = robot_service.look_right()
        elif direction == "center":
            result = robot_service.look_center()
        else:
            return f"Invalid direction: {direction}. Use 'left', 'right', or 'center'"
        
        if result.get("success"):
            return f"Robot looking {direction}"
        return f"Failed to move camera: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error moving robot camera: {str(e)}"


def robot_capture_image(*args, **kwargs) -> str:
    """
    Capture an image from the robot's camera
    
    Returns:
        Status message with image info
    
    Examples:
        - "take a picture with the robot"
        - "capture image from robot camera"
        - "robot take a photo"
    """
    try:
        result = robot_service.capture_image()
        if result.get("success"):
            return f"Image captured from robot camera successfully"
        return f"Failed to capture image: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error capturing image from robot: {str(e)}"


def robot_get_status(*args, **kwargs) -> str:
    """Get the robot connection status"""
    try:
        result = robot_service.get_status()
        if result.get("success"):
            connected = result.get("arduino_connected", False)
            camera = result.get("camera_available", False)
            status = "connected" if connected else "disconnected"
            cam_status = "available" if camera else "unavailable"
            return f"Robot status: Arduino {status}, Camera {cam_status}"
        return f"Failed to get robot status: {result.get('error', 'Unable to reach robot')}"
    except Exception as e:
        return f"Error getting robot status: {str(e)}"


def open_robot_camera_stream(*args, **kwargs) -> str:
    """
    Open the robot's camera stream in the default web browser.
    Use this when the user wants to see the robot's view, camera feed, or live stream.
    
    Returns:
        Status message
    
    Examples:
        - "show me the robot camera"
        - "open the robot's view"
        - "let me see what the robot sees"
        - "open camera stream"
        - "show robot camera feed"
    """
    import webbrowser
    
    try:
        camera_url = "http://10.51.203.182:8080/camera/stream"
        webbrowser.open(camera_url)
        return f"Opened robot camera stream in browser: {camera_url}"
    except Exception as e:
        return f"Failed to open camera stream: {str(e)}"


# Create Langchain tools
def get_all_tools():
    """Get all available tools for the agent"""
    tools = []
    
    # Fallback parsing helper: accept dict or JSON string
    def _parse_args(args):
        if isinstance(args, dict):
            return args
        if isinstance(args, str):
            try:
                parsed = json.loads(args)
                return parsed if isinstance(parsed, dict) else {"__arg": parsed}
            except Exception:
                return {"__arg": args}
        return {}
    
    # Try to create structured tools, fallback to regular tools if needed
    try:
        tools = [
        StructuredTool.from_function(
            func=send_email,
            name="send_email",
            description="Send an email to a recipient with optional attachment. Use this when user wants to send an email.",
            args_schema=SendEmailInput
        ),
        StructuredTool.from_function(
            func=send_whatsapp_tool,
            name="send_whatsapp",
            description="Send a WhatsApp message to a contact NAME or PHONE NUMBER (with country code). Prefer phone_number if provided.",
            args_schema=SendWhatsAppInput
        ),
        StructuredTool.from_function(
            func=capture_camera_image,
            name="capture_camera_image",
            description="Capture an image from the camera. Use this when user wants to take a selfie or capture from camera.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=take_screenshot,
            name="take_screenshot",
            description="Take a screenshot of the screen. Use this when user wants to capture the screen.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=get_current_time,
            name="get_current_time",
            description="Get the current time. Use this when user asks for the time.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=search_wikipedia,
            name="search_wikipedia",
            description="Search Wikipedia for information about a topic. Use this when user wants to search Wikipedia or learn about something.",
            args_schema=SearchWikipediaInput
        ),
        StructuredTool.from_function(
            func=search_youtube,
            name="search_youtube",
            description="Search YouTube for videos. Use this when user wants to search or watch videos on YouTube.",
            args_schema=SearchYouTubeInput
        ),
        StructuredTool.from_function(
            func=search_google,
            name="search_google",
            description="Search Google for information. Use this when user wants to search the web or Google.",
            args_schema=SearchGoogleInput
        ),
        StructuredTool.from_function(
            func=open_stackoverflow,
            name="open_stackoverflow",
            description="Open StackOverflow website. Use this when user wants to access StackOverflow.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=play_music,
            name="play_music",
            description="Open Spotify and start playing music. Use this ONCE when user wants to play music. Do not call this tool multiple times as it will toggle playback on/off.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=open_app,
            name="open_app",
            description="Open or launch an application on Windows (e.g. 'Google Chrome', 'chrome', 'Notepad', 'Spotify', 'Calculator'). Use this whenever the user asks to open, launch, or start an application. Input: app_name (the application name as the user said it).",
            args_schema=OpenAppInput
        ),
        StructuredTool.from_function(
            func=switch_windows,
            name="switch_windows",
            description="Switch between open windows. Use this when user wants to switch windows or alt-tab.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=list_running_apps,
            name="list_running_apps",
            description="List currently running user-facing applications. Use this BEFORE closing apps to decide what to close.",
            args_schema=ListRunningAppsInput
        ),
        StructuredTool.from_function(
            func=close_processes,
            name="close_processes",
            description="Close specific executable processes. Use this when user wants to close applications or processes. Provide a list of executable names like ['chrome.exe', 'notepad.exe'].",
            args_schema=CloseProcessesInput
        ),
        StructuredTool.from_function(
            func=close_apps_by_names_tool,
            name="close_apps_by_names",
            description="Close apps by names (e.g., 'chrome', 'spotify'). Prefer this after listing running apps.",
            args_schema=CloseAppsByNamesInput
        ),
        StructuredTool.from_function(
            func=store_data,
            name="store_data",
            description="Store key-value data for later retrieval. Use this when user wants to save or store information.",
            args_schema=StoreDataInput
        ),
        StructuredTool.from_function(
            func=retrieve_data,
            name="retrieve_data",
            description="Retrieve stored data by key. Use this when user wants to get previously stored information.",
            args_schema=RetrieveDataInput
        ),
        StructuredTool.from_function(
            func=save_note,
            name="save_note",
            description="Save a note or text to a file. Use this when user wants to note down or save text.",
            args_schema=SaveNoteInput
        ),
        StructuredTool.from_function(
            func=upload_image_to_lens,
            name="upload_image_to_lens",
            description="Upload an image to Google Lens for visual search. Use this when user wants to search an image or use Google Lens. Provide the image file path.",
            args_schema=UploadImageToLensInput
        ),
        StructuredTool.from_function(
            func=scan_screen_with_lens,
            name="scan_screen_with_lens",
            description="Take a screenshot and upload it to Google Lens. Use this when user wants to scan the screen with Google Lens.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=scan_camera_with_lens,
            name="scan_camera_with_lens",
            description="Capture an image from the camera and upload it to Google Lens for visual search. Use this when user wants to take a photo with the camera and search it with Google Lens.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=analyze_screen_with_vision,
            name="analyze_screen_with_vision",
            description="Take a screenshot and analyze it using Gemini vision AI. Use this when user wants to understand or analyze what's on their screen using AI vision.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=analyze_camera_with_vision,
            name="analyze_camera_with_vision",
            description="Capture an image from the camera and analyze it using Gemini vision AI. Use this when user wants to take a photo and understand or analyze it using AI vision.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=get_recent_notifications,
            name="get_recent_notifications",
            description="Get recent notifications from notification history. Use this when user asks about notifications, recent notifications, or any new notifications.",
            args_schema=GetNotificationsInput
        ),
        StructuredTool.from_function(
            func=get_new_notifications,
            name="get_new_notifications",
            description="Get new notifications from the last few minutes. Use this when user asks about new notifications or any new notifications.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=get_notifications_by_app,
            name="get_notifications_by_app",
            description="Get notifications filtered by application name. Use this when user asks about notifications from a specific app (e.g., 'notifications from WhatsApp', 'notifications from Outlook').",
            args_schema=GetNotificationsByAppInput
        ),
        # Robot control tools
        StructuredTool.from_function(
            func=robot_move,
            name="robot_move",
            description="Move the robot in a direction. Use this when user wants to control robot movement. Directions: 'forward', 'backward', 'left', 'right', 'stop'. Speed: 0-255 (default 160).",
            args_schema=RobotMoveInput
        ),
        StructuredTool.from_function(
            func=robot_stop,
            name="robot_stop",
            description="Stop the robot immediately. Use this when user says 'stop the robot', 'robot stop', 'halt', etc.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=robot_look,
            name="robot_look",
            description="Make the robot camera look in a direction. Use for 'robot look left/right/center', 'turn the robot camera'. Directions: 'left', 'right', 'center'.",
            args_schema=RobotLookInput
        ),
        StructuredTool.from_function(
            func=robot_set_servo,
            name="robot_set_servo",
            description="Set robot camera servo to specific angle (0-180 degrees, 90 is center). Use when user specifies exact angle.",
            args_schema=RobotServoInput
        ),
        StructuredTool.from_function(
            func=robot_capture_image,
            name="robot_capture_image",
            description="Capture an image from the robot's camera. Use when user wants to take a photo with the robot camera.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=robot_get_status,
            name="robot_get_status",
            description="Get the robot connection status. Use when user asks about robot status or if robot is connected.",
            args_schema=None
        ),
        StructuredTool.from_function(
            func=open_robot_camera_stream,
            name="open_robot_camera_stream",
            description="Open the robot's camera stream in the browser. Use when user wants to see robot's view, camera feed, live stream, or what the robot sees.",
            args_schema=None
        ),
        ]
    except Exception as e:
        print(f"Warning: Could not create StructuredTools, using regular Tools: {e}")
        # Fallback to regular Tool class
        tools = [
            Tool(
                name="send_email",
                func=lambda args: (lambda a=_parse_args(args): send_email(a.get('to', ''), a.get('content', ''), a.get('attachment_path')))(),
                description="Send an email to a recipient with optional attachment. Input should be dict with 'to', 'content', and optional 'attachment_path'"
            ),
            Tool(
                name="send_whatsapp",
                func=lambda args: (lambda a=_parse_args(args): send_whatsapp_tool(**a))(),
                description="Send a WhatsApp message to NAME or PHONE NUMBER (with country code). Input should include 'phone_number' (preferred) or 'name', and 'message'"
            ),
            Tool(
                name="capture_camera_image",
                func=capture_camera_image,
                description="Capture an image from the camera"
            ),
            Tool(
                name="take_screenshot",
                func=take_screenshot,
                description="Take a screenshot of the screen"
            ),
            Tool(
                name="get_current_time",
                func=get_current_time,
                description="Get the current time"
            ),
            Tool(
                name="search_wikipedia",
                func=lambda args: (lambda a=_parse_args(args): search_wikipedia(a.get('query', a.get('__arg', ''))))(),
                description="Search Wikipedia for information about a topic"
            ),
            Tool(
                name="search_youtube",
                func=lambda args: (lambda a=_parse_args(args): search_youtube(a.get('query', a.get('__arg', ''))))(),
                description="Search YouTube for videos"
            ),
            Tool(
                name="search_google",
                func=lambda args: (lambda a=_parse_args(args): search_google(a.get('query', a.get('__arg', ''))))(),
                description="Search Google for information"
            ),
            Tool(
                name="open_stackoverflow",
                func=open_stackoverflow,
                description="Open StackOverflow website"
            ),
            Tool(
                name="play_music",
                func=lambda args: (lambda a=_parse_args(args): play_music(
                    a.get('song_name', a.get('__arg', '')),
                    a.get('artist', ''),
                    a.get('platform', 'spotify')
                ))(),
                description="Play music on Spotify or locally. IMPORTANT: Extract song name and artist from user's request! Examples: 'play Apna Bana Le' → song_name='Apna Bana Le'; 'play Shape of You by Ed Sheeran' → song_name='Shape of You', artist='Ed Sheeran'. If no song specified, plays local music."
            ),
            Tool(
                name="open_app",
                func=lambda args: (lambda a=_parse_args(args): open_app(a.get('app_name', a.get('__arg', ''))))(),
                description="Open an application using Windows search"
            ),
            Tool(
                name="switch_windows",
                func=switch_windows,
                description="Switch between open windows"
            ),
            Tool(
                name="list_running_apps",
                func=lambda args: (lambda a=_parse_args(args): list_running_apps(a.get('include_system', False)))(),
                description="List currently running user-facing applications"
            ),
            Tool(
                name="close_processes",
                func=lambda args: (lambda a=_parse_args(args): close_processes(a.get('exe_list', [])))(),
                description="Close specific executable processes"
            ),
            Tool(
                name="close_apps_by_names",
                func=lambda args: (lambda a=_parse_args(args): close_apps_by_names_tool(**a))(),
                description="Close apps by friendly names or executable names. Accepts 'names' or 'app_names' as a list."
            ),
            Tool(
                name="store_data",
                func=lambda args: (lambda a=_parse_args(args): store_data(a.get('key', a.get('__arg', '')), a.get('value', '')))(),
                description="Store key-value data for later retrieval"
            ),
            Tool(
                name="retrieve_data",
                func=lambda args: (lambda a=_parse_args(args): retrieve_data(a.get('key', a.get('__arg', ''))))(),
                description="Retrieve stored data by key"
            ),
            Tool(
                name="save_note",
                func=lambda args: (lambda a=_parse_args(args): save_note(a.get('text', a.get('__arg', '')), a.get('file_path')))(),
                description="Save a note or text to a file"
            ),
            Tool(
                name="upload_image_to_lens",
                func=lambda args: (lambda a=_parse_args(args): upload_image_to_lens(a.get('image_path', a.get('__arg', ''))))(),
                description="Upload an image to Google Lens for visual search"
            ),
            Tool(
                name="scan_screen_with_lens",
                func=scan_screen_with_lens,
                description="Take a screenshot and upload it to Google Lens"
            ),
            Tool(
                name="scan_camera_with_lens",
                func=scan_camera_with_lens,
                description="Capture an image from the camera and upload it to Google Lens for visual search"
            ),
            Tool(
                name="analyze_screen_with_vision",
                func=analyze_screen_with_vision,
                description="Take a screenshot and analyze it using Gemini vision AI"
            ),
            Tool(
                name="analyze_camera_with_vision",
                func=analyze_camera_with_vision,
                description="Capture an image from the camera and analyze it using Gemini vision AI"
            ),
            Tool(
                name="get_recent_notifications",
                func=lambda args: (lambda a=_parse_args(args): get_recent_notifications(a.get('limit', 10)))(),
                description="Get recent notifications from notification history"
            ),
            Tool(
                name="get_new_notifications",
                func=get_new_notifications,
                description="Get new notifications from the last few minutes"
            ),
            Tool(
                name="get_notifications_by_app",
                func=lambda args: (lambda a=_parse_args(args): get_notifications_by_app(a.get('app_name', ''), a.get('limit', 10)))(),
                description="Get notifications filtered by application name"
            ),
            Tool(
                name="create_reminder",
                func=lambda args: (lambda a=_parse_args(args): create_reminder(
                    a.get('title', a.get('__arg', '')),
                    a.get('description', ''),
                    a.get('due_date', ''),
                    a.get('priority', 'medium')
                ))(),
                description="Create a new reminder or task with optional due time. IMPORTANT: When user mentions time (like 'in 5 minutes', 'at 3pm', 'tomorrow'), pass it to 'due_date' parameter! Examples: 'remind me to call in 5 minutes' → title='call', due_date='in 5 minutes'. Use for: 'remind me to...', 'add reminder', 'create task', etc."
            ),
            Tool(
                name="get_reminders",
                func=lambda args: (lambda a=_parse_args(args): get_reminders_list(a.get('include_completed', False)))(),
                description="Get all reminders/tasks. Use for: 'show my reminders', 'what are my tasks', 'list reminders', etc."
            ),
            Tool(
                name="mark_reminder_done",
                func=lambda args: (lambda a=_parse_args(args): mark_reminder_done(a.get('reminder_id', a.get('__arg', ''))))(),
                description="Mark a reminder as completed"
            ),
            Tool(
                name="play_song_on_spotify",
                func=lambda args: (lambda a=_parse_args(args): play_song_on_spotify(
                    a.get('song_query', a.get('__arg', '')),
                    a.get('artist', '')
                ))(),
                description="Search and play a specific song on Spotify. Extract song name and optionally artist. Examples: 'play Apna Bana Le on Spotify' → song_query='Apna Bana Le'; 'play Levitating by Dua Lipa' → song_query='Levitating', artist='Dua Lipa'"
            ),
            Tool(
                name="search_music",
                func=lambda args: (lambda a=_parse_args(args): search_music(
                    a.get('query', a.get('__arg', '')),
                    a.get('platform', 'spotify')
                ))(),
                description="Search for music on Spotify. Use for queries like 'search for Coldplay', 'find songs by Taylor Swift'"
            ),
            # Robot control tools
            Tool(
                name="robot_move",
                func=lambda args: (lambda a=_parse_args(args): robot_move(
                    a.get('direction', a.get('__arg', 'stop')),
                    a.get('speed', 160)
                ))(),
                description="Move the robot in a direction. Directions: 'forward', 'backward', 'left', 'right', 'stop'. Speed: 0-255 (default 160)."
            ),
            Tool(
                name="robot_stop",
                func=robot_stop,
                description="Stop the robot immediately"
            ),
            Tool(
                name="robot_look",
                func=lambda args: (lambda a=_parse_args(args): robot_look(a.get('direction', a.get('__arg', 'center'))))(),
                description="Make the robot camera look in a direction: 'left', 'right', 'center'"
            ),
            Tool(
                name="robot_set_servo",
                func=lambda args: (lambda a=_parse_args(args): robot_set_servo(int(a.get('angle', a.get('__arg', 90)))))(),
                description="Set robot camera servo to specific angle (0-180 degrees)"
            ),
            Tool(
                name="robot_capture_image",
                func=robot_capture_image,
                description="Capture an image from the robot's camera"
            ),
            Tool(
                name="robot_get_status",
                func=robot_get_status,
                description="Get the robot connection status"
            ),
            Tool(
                name="open_robot_camera_stream",
                func=open_robot_camera_stream,
                description="Open the robot's camera stream in the browser. Use for: 'show robot camera', 'robot's view', 'camera feed', 'what does the robot see'"
            ),
        ]
    
    return tools

