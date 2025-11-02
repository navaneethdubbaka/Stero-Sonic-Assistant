import pyautogui
import os
import base64
from PIL import Image
import io
from typing import Optional, Tuple
import tkinter as tk

class ScreenshotService:
    def __init__(self):
        self.screenshot_path = os.getenv("SCREENSHOT_PATH", "./screenshots/screenshot.png")
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> dict:
        """Take screenshot of screen or region"""
        try:
            # Ensure directory exists
            screenshot_dir = os.path.dirname(os.path.abspath(self.screenshot_path))
            if screenshot_dir and not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir, exist_ok=True)
            
            # Take screenshot
            screenshot = pyautogui.screenshot(region=region)
            
            # Ensure absolute path
            abs_path = os.path.abspath(self.screenshot_path)
            screenshot.save(abs_path)
            
            # Convert to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "path": abs_path,
                "image_base64": image_base64
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def capture_region(self) -> dict:
        """Capture a selected region of the screen"""
        try:
            root = tk.Tk()
            root.withdraw()
            
            # Get screen dimensions
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Create fullscreen window
            selection_window = tk.Toplevel(root)
            selection_window.attributes('-fullscreen', True)
            selection_window.attributes('-alpha', 0.3)
            selection_window.configure(bg='gray')
            
            start_x = start_y = end_x = end_y = 0
            region = None
            
            def on_button_press(event):
                nonlocal start_x, start_y
                start_x, start_y = event.x, event.y
                canvas.coords(rect, start_x, start_y, start_x, start_y)
            
            def on_mouse_move(event):
                nonlocal end_x, end_y
                end_x, end_y = event.x, event.y
                canvas.coords(rect, start_x, start_y, end_x, end_y)
            
            def on_button_release(event):
                nonlocal region
                nonlocal start_x, start_y, end_x, end_y
                region = (start_x, start_y, end_x - start_x, end_y - start_y)
                root.quit()
                root.destroy()
            
            canvas = tk.Canvas(selection_window, cursor="cross", bg='gray')
            canvas.pack(fill=tk.BOTH, expand=True)
            rect = canvas.create_rectangle(0, 0, 0, 0, outline='red', width=2)
            
            canvas.bind("<ButtonPress-1>", on_button_press)
            canvas.bind("<B1-Motion>", on_mouse_move)
            canvas.bind("<ButtonRelease-1>", on_button_release)
            
            root.mainloop()
            
            if region:
                return self.take_screenshot(region)
            else:
                return {"success": False, "error": "No region selected"}
        except Exception as e:
            return {"success": False, "error": str(e)}

