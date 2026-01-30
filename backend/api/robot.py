"""
Robot API Router - Endpoints for controlling the Raspberry Pi robot
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import requests
import os

from services.robot_service import get_robot_service

router = APIRouter()


# =========================
# REQUEST MODELS
# =========================
class MoveCommand(BaseModel):
    direction: str  # "forward", "backward", "left", "right", "stop"
    speed: int = 160


class ServoCommand(BaseModel):
    angle: int  # 0-180


class VoiceCommand(BaseModel):
    text: str  # Voice command text to parse


# =========================
# ROBOT SERVICE
# =========================
robot_service = get_robot_service()


# =========================
# ENDPOINTS
# =========================

@router.get("/status")
async def get_robot_status():
    """Get robot connection status"""
    return robot_service.get_status()


@router.post("/move")
async def move_robot(command: MoveCommand):
    """Send movement command to robot"""
    result = robot_service.move(command.direction, command.speed)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send command"))
    return result


@router.post("/stop")
async def stop_robot():
    """Emergency stop"""
    result = robot_service.stop()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to stop robot"))
    return result


@router.post("/servo")
async def set_servo(command: ServoCommand):
    """Set servo angle"""
    result = robot_service.set_servo(command.angle)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to set servo"))
    return result


@router.post("/look/{direction}")
async def look_direction(direction: str):
    """
    Turn camera/servo to look in a direction
    
    Args:
        direction: "left", "right", or "center"
    """
    direction = direction.lower()
    if direction == "left":
        result = robot_service.look_left()
    elif direction == "right":
        result = robot_service.look_right()
    elif direction == "center":
        result = robot_service.look_center()
    else:
        raise HTTPException(status_code=400, detail="Invalid direction. Use: left, right, center")
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to move servo"))
    return result


@router.get("/camera/capture")
async def capture_image():
    """Capture a single image from robot camera"""
    result = robot_service.capture_image()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to capture image"))
    return result


@router.get("/camera/stream")
async def camera_stream_proxy():
    """
    Proxy the camera MJPEG stream from the Pi.
    This allows the main backend to serve the stream even if CORS is an issue.
    """
    pi_url = robot_service.pi_url
    stream_url = f"{pi_url}/camera/stream"
    
    def generate():
        try:
            with requests.get(stream_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
        except Exception as e:
            print(f"Stream error: {e}")
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/camera/stream-url")
async def get_stream_url():
    """Get the direct URL for camera stream (for embedding in iframe/img)"""
    return {
        "url": robot_service.get_camera_stream_url(),
        "control_page": robot_service.get_control_page_url()
    }


@router.post("/reconnect")
async def reconnect_robot():
    """Attempt to reconnect to the robot"""
    result = robot_service.reconnect()
    return result


@router.post("/voice-command")
async def process_voice_command(command: VoiceCommand):
    """
    Process a voice command text and execute the appropriate robot action
    
    Args:
        command: Voice command text to parse
    
    Returns:
        Result of the action taken
    """
    text = command.text.lower().strip()
    
    # Parse the command
    action = None
    result = None
    
    # Movement commands
    if any(word in text for word in ["forward", "go", "ahead", "move forward"]):
        action = "forward"
        speed = _extract_speed(text)
        result = robot_service.move_forward(speed)
    
    elif any(word in text for word in ["backward", "back", "reverse", "move back"]):
        action = "backward"
        speed = _extract_speed(text)
        result = robot_service.move_backward(speed)
    
    elif "left" in text:
        if "look" in text:
            action = "look left"
            result = robot_service.look_left()
        else:
            action = "turn left"
            speed = _extract_speed(text)
            result = robot_service.turn_left(speed)
    
    elif "right" in text:
        if "look" in text:
            action = "look right"
            result = robot_service.look_right()
        else:
            action = "turn right"
            speed = _extract_speed(text)
            result = robot_service.turn_right(speed)
    
    elif any(word in text for word in ["stop", "halt", "freeze", "brake"]):
        action = "stop"
        result = robot_service.stop()
    
    elif any(word in text for word in ["center", "straight", "look ahead"]):
        action = "look center"
        result = robot_service.look_center()
    
    elif "capture" in text or "photo" in text or "picture" in text or "image" in text:
        action = "capture image"
        result = robot_service.capture_image()
    
    else:
        return {
            "success": False,
            "error": "Command not recognized",
            "text": text,
            "hint": "Try: forward, backward, left, right, stop, look left/right/center, capture"
        }
    
    if result:
        result["action"] = action
        result["original_text"] = text
    
    return result


def _extract_speed(text: str) -> int:
    """Extract speed value from voice command text"""
    import re
    
    # Check for speed keywords
    if "fast" in text or "quick" in text:
        return 200
    elif "slow" in text:
        return 100
    elif "max" in text or "full" in text:
        return 255
    
    # Try to find a number
    numbers = re.findall(r'\d+', text)
    if numbers:
        speed = int(numbers[0])
        return max(0, min(255, speed))
    
    # Default speed
    return 160
