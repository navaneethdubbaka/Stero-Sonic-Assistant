import cv2
import os
from typing import Optional
import base64
from PIL import Image
import io

class CameraService:
    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        self.camera_image_path = os.getenv("CAMERA_IMAGE_PATH", "./screenshots/camera_image.png")
    
    def capture_image(self) -> dict:
        """Capture image from camera"""
        try:
            if not self.camera.isOpened():
                self.camera = cv2.VideoCapture(0)
            
            ret, frame = self.camera.read()
            if not ret:
                return {"success": False, "error": "Could not capture image"}
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.camera_image_path), exist_ok=True)
            
            # Save image
            cv2.imwrite(self.camera_image_path, frame)
            
            # Convert to base64 for API response
            _, buffer = cv2.imencode('.png', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "success": True,
                "path": self.camera_image_path,
                "image_base64": image_base64
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_video_feed(self):
        """Get video feed generator for mirror mode"""
        while True:
            ret, frame = self.camera.read()
            if not ret:
                break
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def release(self):
        """Release camera resource"""
        if self.camera:
            self.camera.release()
            cv2.destroyAllWindows()

