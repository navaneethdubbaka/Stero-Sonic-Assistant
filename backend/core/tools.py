"""
Langchain tools for Stereo Sonic Assistant
These tools allow the LLM to interact with all services
"""

from langchain.tools import Tool
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional, List
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
            func=close_processes,
            name="close_processes",
            description="Close specific executable processes. Use this when user wants to close applications or processes. Provide a list of executable names like ['chrome.exe', 'notepad.exe'].",
            args_schema=CloseProcessesInput
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
                func=lambda args: send_email(args.get('to', ''), args.get('content', ''), args.get('attachment_path')),
                description="Send an email to a recipient with optional attachment. Input should be dict with 'to', 'content', and optional 'attachment_path'"
            ),
            Tool(
                name="send_whatsapp",
                func=lambda args: send_whatsapp(args.get('name', ''), args.get('message', '')),
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
                func=search_wikipedia,
                description="Search Wikipedia for information about a topic"
            ),
            Tool(
                name="search_youtube",
                func=search_youtube,
                description="Search YouTube for videos"
            ),
            Tool(
                name="search_google",
                func=search_google,
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
                func=open_app,
                description="Open an application using Windows search"
            ),
            Tool(
                name="switch_windows",
                func=switch_windows,
                description="Switch between open windows"
            ),
            Tool(
                name="close_processes",
                func=close_processes,
                description="Close specific executable processes"
            ),
            Tool(
                name="store_data",
                func=store_data,
                description="Store key-value data for later retrieval"
            ),
            Tool(
                name="retrieve_data",
                func=retrieve_data,
                description="Retrieve stored data by key"
            ),
            Tool(
                name="save_note",
                func=save_note,
                description="Save a note or text to a file"
            ),
            Tool(
                name="upload_image_to_lens",
                func=upload_image_to_lens,
                description="Upload an image to Google Lens for visual search"
            ),
            Tool(
                name="scan_screen_with_lens",
                func=scan_screen_with_lens,
                description="Take a screenshot and upload it to Google Lens"
            ),
        ]
    
    return tools

