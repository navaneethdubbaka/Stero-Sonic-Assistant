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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

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

# Initialize services
email_service = EmailService()
whatsapp_service = WhatsAppService()
camera_service = CameraService()
screenshot_service = ScreenshotService()
system_service = SystemService()
data_service = DataService()
lens_service = LensService()
notification_service = NotificationService()

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


def play_music(*args, **kwargs) -> str:
    """Play music from the music directory"""
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
    """Analyze an image using Gemini vision capabilities"""
    try:
        # Check if image exists
        abs_image_path = os.path.abspath(image_path)
        if not os.path.exists(abs_image_path):
            return f"Error: Image file not found at {abs_image_path}"
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY not found in environment variables"
        
        # Initialize Gemini vision model
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=api_key
        )
        
        # Create prompt
        prompt_text = user_prompt or "Please analyze this image and describe what you see. Provide a detailed explanation of the contents, objects, text, and any other relevant information."
        
        # Read and encode image as base64
        import base64
        
        # Read and encode image
        with open(abs_image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determine MIME type
        _, ext = os.path.splitext(abs_image_path)
        mime_type = "image/png" if ext.lower() == ".png" else "image/jpeg"
        
        # Create message with image using LangChain's format
        # For ChatGoogleGenerativeAI with vision, we need to use the correct format
        # LangChain Google Generative AI supports images via file paths or base64
        try:
            # Method 1: Use file path directly (simplest approach)
            # LangChain's ChatGoogleGenerativeAI can handle file paths for images
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": abs_image_path
                    }
                ]
            )
            response = llm.invoke([message])
            return response.content
        except Exception as e1:
            # Fallback: try with base64 data URI format
            try:
                message = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:{mime_type};base64,{image_data}"
                        }
                    ]
                )
                response = llm.invoke([message])
                return response.content
            except Exception as e2:
                # Final fallback: use simple content list format
                try:
                    # Some LangChain versions accept simple format
                    message = HumanMessage(content=[prompt_text, abs_image_path])
                    response = llm.invoke([message])
                    return response.content
                except Exception as e3:
                    return f"Error analyzing image with vision. Errors: {str(e1)}, {str(e2)}, {str(e3)}"
                    
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
            description="Open an application using Windows search. Use this when user wants to open or launch an application.",
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
                func=play_music,
                description="Play music from the music directory"
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
        ]
    
    return tools

