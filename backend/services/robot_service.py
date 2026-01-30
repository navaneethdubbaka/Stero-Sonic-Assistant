"""
Robot Service - Communicates with Raspberry Pi robot controller over HTTP
"""

import os
import requests
from typing import Optional, Dict, Any
import base64


class RobotService:
    """Service for controlling the Raspberry Pi robot via HTTP"""
    
    def __init__(self, pi_url: Optional[str] = None):
        self.pi_url = pi_url or os.getenv("ROBOT_PI_URL", "http://192.168.1.100:8080")
        self.timeout = int(os.getenv("ROBOT_TIMEOUT", "5"))
        self._connected = False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the Pi"""
        url = f"{self.pi_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                return {"success": False, "error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            self._connected = False
            return {"success": False, "error": f"Cannot connect to robot at {self.pi_url}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get robot connection status"""
        result = self._make_request("GET", "/status")
        if "arduino_connected" in result:
            self._connected = result.get("arduino_connected", False)
            result["success"] = True
        return result
    
    def is_connected(self) -> bool:
        """Check if robot is reachable and Arduino is connected"""
        status = self.get_status()
        return status.get("success", False) and status.get("arduino_connected", False)
    
    def move(self, direction: str, speed: int = 160) -> Dict[str, Any]:
        """
        Send movement command to robot
        
        Args:
            direction: One of "forward", "backward", "left", "right", "stop"
            speed: Motor speed (0-255)
        
        Returns:
            Result dict with success status
        """
        print(f"[DEBUG robot_service.move] Received - direction: {direction!r} (type: {type(direction).__name__}), speed: {speed!r}")
        
        valid_directions = ["forward", "backward", "left", "right", "stop"]
        
        # Ensure direction is a string before calling .lower()
        if not isinstance(direction, str):
            direction = str(direction)
        
        direction_lower = direction.lower().strip()
        print(f"[DEBUG robot_service.move] Normalized direction: {direction_lower!r}")
        
        if direction_lower not in valid_directions:
            print(f"[DEBUG robot_service.move] INVALID! {direction_lower!r} not in {valid_directions}")
            return {"success": False, "error": f"Invalid direction. Must be one of: {valid_directions}"}
        
        speed = max(0, min(255, int(speed) if speed else 160))
        print(f"[DEBUG robot_service.move] Making request with direction={direction_lower}, speed={speed}")
        
        return self._make_request("POST", "/robot/move", {
            "direction": direction_lower,
            "speed": speed
        })
    
    def move_forward(self, speed: int = 160) -> Dict[str, Any]:
        """Move robot forward"""
        return self.move("forward", speed)
    
    def move_backward(self, speed: int = 160) -> Dict[str, Any]:
        """Move robot backward"""
        return self.move("backward", speed)
    
    def turn_left(self, speed: int = 160) -> Dict[str, Any]:
        """Turn robot left"""
        return self.move("left", speed)
    
    def turn_right(self, speed: int = 160) -> Dict[str, Any]:
        """Turn robot right"""
        return self.move("right", speed)
    
    def stop(self) -> Dict[str, Any]:
        """Stop robot immediately"""
        return self._make_request("POST", "/robot/stop", {})
    
    def set_servo(self, angle: int) -> Dict[str, Any]:
        """
        Set servo/pan angle
        
        Args:
            angle: Angle in degrees (0-180, 90 is center)
        
        Returns:
            Result dict with success status
        """
        angle = max(0, min(180, angle))
        return self._make_request("POST", "/robot/servo", {"angle": angle})
    
    def look_left(self) -> Dict[str, Any]:
        """Turn camera/servo to look left (45 degrees)"""
        return self.set_servo(45)
    
    def look_right(self) -> Dict[str, Any]:
        """Turn camera/servo to look right (135 degrees)"""
        return self.set_servo(135)
    
    def look_center(self) -> Dict[str, Any]:
        """Turn camera/servo to center (90 degrees)"""
        return self.set_servo(90)
    
    def capture_image(self) -> Dict[str, Any]:
        """
        Capture a single image from robot camera
        
        Returns:
            Result dict with base64 encoded image if successful
        """
        result = self._make_request("GET", "/camera/capture")
        if result.get("success") and result.get("image_base64"):
            return {
                "success": True,
                "image_base64": result["image_base64"],
                "content_type": result.get("content_type", "image/jpeg")
            }
        return result
    
    def get_camera_stream_url(self) -> str:
        """Get URL for camera MJPEG stream"""
        return f"{self.pi_url}/camera/stream"
    
    def get_control_page_url(self) -> str:
        """Get URL for web control interface"""
        return f"{self.pi_url}/control"
    
    def reconnect(self) -> Dict[str, Any]:
        """Attempt to reconnect Arduino on the Pi"""
        return self._make_request("POST", "/robot/reconnect", {})


# Singleton instance
_robot_service: Optional[RobotService] = None


def get_robot_service(pi_url: Optional[str] = None) -> RobotService:
    """Get or create the robot service singleton"""
    global _robot_service
    if _robot_service is None:
        _robot_service = RobotService(pi_url)
    return _robot_service
