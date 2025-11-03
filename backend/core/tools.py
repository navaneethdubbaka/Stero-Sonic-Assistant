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
from pathlib import Path

# Add services to path
sys.path.append(str(Path(__file__).parent.parent))

from services.email_service import EmailService
from services.whatsapp_service import WhatsAppService
from services.camera_service import CameraService
from services.screenshot_service import ScreenshotService
from services.system_service import SystemService
from services.data_service import DataService
from services.lens_service import LensService

# Initialize services
email_service = EmailService()
whatsapp_service = WhatsAppService()
camera_service = CameraService()
screenshot_service = ScreenshotService()
system_service = SystemService()
data_service = DataService()
lens_service = LensService()


# Tool input schemas
class SendEmailInput(BaseModel):
    to: str = Field(description="Email address of the recipient")
    content: str = Field(description="Email content/message")
    attachment_path: Optional[str] = Field(None, description="Path to attachment file (optional)")


class SendWhatsAppInput(BaseModel):
    name: str = Field(description="Name of the contact from contacts file")
    message: str = Field(description="Message to send via WhatsApp")


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

# Tool functions
def send_email(to: str, content: str, attachment_path: Optional[str] = None) -> str:
    """Send an email with optional attachment"""
    result = email_service.send_email(to, content, attachment_path)
    if result.get("success"):
        return f"Email sent successfully to {to}"
    return f"Failed to send email: {result.get('error', 'Unknown error')}"


def send_whatsapp(name: str, message: str) -> str:
    """Send a WhatsApp message to a contact"""
    result = whatsapp_service.send_message(name, message)
    if result.get("success"):
        return f"WhatsApp message sent successfully to {name}"
    return f"Failed to send WhatsApp message: {result.get('error', 'Unknown error')}"


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
            func=send_whatsapp,
            name="send_whatsapp",
            description="Send a WhatsApp message to a contact. Use this when user wants to send a WhatsApp message.",
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
                func=lambda args: (lambda a=_parse_args(args): send_whatsapp(a.get('name', ''), a.get('message', '')))(),
                description="Send a WhatsApp message to a contact. Input should be dict with 'name' and 'message'"
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
        ]
    
    return tools

