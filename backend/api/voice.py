from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import speech_recognition as sr
import io
import base64

router = APIRouter()

class AudioInput(BaseModel):
    audio_data: str  # Base64 encoded audio
    language: Optional[str] = "en-in"

class VoiceCommand(BaseModel):
    command: str

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

