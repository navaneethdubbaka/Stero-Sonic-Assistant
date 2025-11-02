from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.email_service import EmailService
from services.whatsapp_service import WhatsAppService
from services.camera_service import CameraService
from services.screenshot_service import ScreenshotService
from services.system_service import SystemService
from services.data_service import DataService
from services.lens_service import LensService
from core.intent_parser import intent_parser
from core.speech import tts

router = APIRouter()

# Initialize services
email_service = EmailService()
whatsapp_service = WhatsAppService()
camera_service = CameraService()
screenshot_service = ScreenshotService()
system_service = SystemService()
data_service = DataService()
lens_service = LensService()

class CommandInput(BaseModel):
    command: str

class EmailInput(BaseModel):
    to: str
    content: str
    attachment_path: Optional[str] = None

class WhatsAppInput(BaseModel):
    name: str
    message: str

class StoreDataInput(BaseModel):
    key: str
    value: str

class RetrieveDataInput(BaseModel):
    key: str

class NoteInput(BaseModel):
    text: str

class AnalyzeDataInput(BaseModel):
    dataframe_path: str
    task: str

class SearchInput(BaseModel):
    query: str

class OpenAppInput(BaseModel):
    app_name: str

@router.post("/execute")
async def execute_command(cmd: CommandInput):
    """Execute command based on intent"""
    try:
        intent = intent_parser.parse_intent(cmd.command)
        
        if not intent:
            return {"success": False, "error": "Command not recognized"}
        
        # Route to appropriate handler
        handlers = {
            "wikipedia": lambda: system_service.search_wikipedia(cmd.command),
            "youtube": lambda: system_service.open_youtube(cmd.command),
            "google": lambda: system_service.open_google(cmd.command),
            "stackoverflow": lambda: system_service.open_stackoverflow(),
            "music": lambda: system_service.play_music(),
            "time": lambda: system_service.get_time(),
            "mirror": lambda: {"success": True, "message": "Mirror mode activated"},
            "selfie": lambda: camera_service.capture_image(),
            "close windows": lambda: system_service.close_processes(['notepad.exe', 'chrome.exe', 'WhatsApp.exe']),
            "switch windows": lambda: system_service.switch_windows(),
            "open": lambda: system_service.open_windows_search(cmd.command),
            "who are you": lambda: {"success": True, "message": "I am Stereo Sonic, created by Navaneeth. I can help you with daily tasks."}
        }
        
        if intent in handlers:
            result = handlers[intent]()
            if result.get("success"):
                message = result.get("message", "Command executed successfully")
                tts.speak(message)
            return result
        else:
            return {"success": False, "error": f"Handler not implemented for intent: {intent}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/email/send")
async def send_email(email_input: EmailInput):
    """Send email"""
    result = email_service.send_email(email_input.to, email_input.content, email_input.attachment_path)
    return result

@router.post("/whatsapp/send")
async def send_whatsapp(whatsapp_input: WhatsAppInput):
    """Send WhatsApp message"""
    result = whatsapp_service.send_message(whatsapp_input.name, whatsapp_input.message)
    return result

@router.post("/data/store")
async def store_data(data_input: StoreDataInput):
    """Store data"""
    result = data_service.store_data(data_input.key, data_input.value)
    return result

@router.post("/data/retrieve")
async def retrieve_data(data_input: RetrieveDataInput):
    """Retrieve data"""
    result = data_service.retrieve_data(data_input.key)
    return result

@router.post("/note/save")
async def save_note(note_input: NoteInput):
    """Save note"""
    result = data_service.save_note(note_input.text)
    return result

@router.get("/camera/capture")
async def capture_image():
    """Capture image from camera"""
    result = camera_service.capture_image()
    return result

@router.get("/camera/feed")
async def get_camera_feed():
    """Get camera feed (for mirror mode)"""
    from fastapi.responses import StreamingResponse
    try:
        return StreamingResponse(
            camera_service.get_video_feed(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/screenshot/capture")
async def capture_screenshot():
    """Take screenshot"""
    result = screenshot_service.take_screenshot()
    return result

@router.post("/screenshot/region")
async def capture_screenshot_region():
    """Capture screenshot region"""
    result = screenshot_service.capture_region()
    return result

@router.post("/lens/upload")
async def upload_to_lens(image_path: str):
    """Upload image to Google Lens"""
    result = lens_service.upload_image_to_lens(image_path)
    return result

@router.post("/lens/camera")
async def use_lens_camera():
    """Use lens with camera image"""
    camera_result = camera_service.capture_image()
    if camera_result.get("success"):
        path = camera_result.get("path")
        return lens_service.upload_image_to_lens(path)
    return camera_result

@router.post("/lens/screen")
async def scan_screen():
    """Scan screen with lens"""
    screenshot_result = screenshot_service.capture_region()
    if screenshot_result.get("success"):
        path = screenshot_result.get("path")
        return lens_service.upload_image_to_lens(path)
    return screenshot_result

