from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import speech_recognition as sr
import io
import base64
import asyncio

router = APIRouter()

# Wake word detector state
_wake_word_detected = asyncio.Event()
_wake_word_enabled = False

class AudioInput(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: Optional[str] = "en-in"

class VoiceCommand(BaseModel):
    command: str

class WakeWordStatus(BaseModel):
    enabled: bool
    is_running: bool


def _on_wake_word_detected():
    """Callback when wake word is detected"""
    global _wake_word_detected
    _wake_word_detected.set()
    print("[WAKE] Wake word detected via API callback!")


def start_wake_word_listener():
    """Start the wake word detection service"""
    global _wake_word_enabled
    try:
        from backend.services.wakeword_service import start_wake_word_detection
    except ImportError:
        from services.wakeword_service import start_wake_word_detection
    
    start_wake_word_detection(_on_wake_word_detected)
    _wake_word_enabled = True
    print("[OK] Wake word listener started via API")


def stop_wake_word_listener():
    """Stop the wake word detection service"""
    global _wake_word_enabled
    try:
        from backend.services.wakeword_service import stop_wake_word_detection
    except ImportError:
        from services.wakeword_service import stop_wake_word_detection
    
    stop_wake_word_detection()
    _wake_word_enabled = False
    print("[STOP] Wake word listener stopped via API")


@router.post("/recognize")
async def recognize_speech(audio_input: AudioInput):
    """Recognize speech from audio data"""
    try:
        r = sr.Recognizer()
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_input.audio_data)
        
        # Convert to AudioData
        audio_data = sr.AudioData(audio_bytes, 44100, 2)
        
        # Recognize speech
        text = r.recognize_google(audio_data, language=audio_input.language)
        
        return {"text": text, "confidence": 1.0}
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/check-command")
async def check_command(voice_command: VoiceCommand):
    """Check if the wake word is detected"""
    command = voice_command.command.lower()
    wake_word = "sonic"
    
    if wake_word in command:
        return {"detected": True, "command": command}
    return {"detected": False, "command": command}


@router.post("/wakeword/start")
async def start_wakeword():
    """Start the wake word detection service"""
    try:
        start_wake_word_listener()
        return {"status": "started", "message": "Wake word detection started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start wake word detection: {str(e)}")


@router.post("/wakeword/stop")
async def stop_wakeword():
    """Stop the wake word detection service"""
    try:
        stop_wake_word_listener()
        return {"status": "stopped", "message": "Wake word detection stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop wake word detection: {str(e)}")


@router.get("/wakeword/status")
async def get_wakeword_status():
    """Get the status of the wake word detection service"""
    global _wake_word_enabled
    try:
        try:
            from backend.services.wakeword_service import get_detector
        except ImportError:
            from services.wakeword_service import get_detector
        
        detector = get_detector()
        return WakeWordStatus(enabled=_wake_word_enabled, is_running=detector.is_running())
    except Exception as e:
        return WakeWordStatus(enabled=False, is_running=False)


@router.get("/wakeword/wait")
async def wait_for_wakeword(timeout: Optional[float] = 30.0):
    """
    Wait for the wake word to be detected.
    Returns when wake word is detected or timeout occurs.
    
    Args:
        timeout: Maximum time to wait in seconds (default 30s)
    """
    global _wake_word_detected
    
    # Clear any previous detection
    _wake_word_detected.clear()
    
    try:
        # Wait for wake word with timeout
        await asyncio.wait_for(_wake_word_detected.wait(), timeout=timeout)
        _wake_word_detected.clear()
        return {"detected": True, "message": "Wake word detected!"}
    except asyncio.TimeoutError:
        return {"detected": False, "message": "Timeout waiting for wake word"}

