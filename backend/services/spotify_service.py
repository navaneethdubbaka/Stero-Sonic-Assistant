"""
Spotify Service - Search and play songs on Spotify
"""

import os
import webbrowser
import urllib.parse
import subprocess
import time
from typing import Optional, Dict
from pathlib import Path

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[SPOTIFY] pyautogui not available - auto-play may not work")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[SPOTIFY] OpenCV not available - will use fallback method")


class SpotifyService:
    """Service to interact with Spotify"""
    
    def __init__(self, play_button_image_path: Optional[str] = None):
        self.spotify_app_paths = [
            r"C:\Users\{}\AppData\Roaming\Spotify\Spotify.exe",
            r"C:\Program Files\Spotify\Spotify.exe",
            r"C:\Program Files (x86)\Spotify\Spotify.exe"
        ]
        # Path to play button template image for template matching
        self.play_button_image_path = play_button_image_path
        if play_button_image_path:
            # Default path in assets folder
            default_path = Path(__file__).parent.parent.parent / "assets" / "spotify_play_button.png"
            if not Path(play_button_image_path).exists() and default_path.exists():
                self.play_button_image_path = str(default_path)
    
    def _find_spotify_app(self) -> Optional[str]:
        """Find Spotify application path"""
        username = os.getenv("USERNAME")
        
        # Try common paths
        for path_template in self.spotify_app_paths:
            path = path_template.format(username) if "{}" in path_template else path_template
            if os.path.exists(path):
                return path
        
        return None
    
    def open_spotify(self) -> Dict:
        """
        Open Spotify application
        
        Returns:
            Result dictionary
        """
        try:
            spotify_path = self._find_spotify_app()
            
            if spotify_path:
                # Open Spotify desktop app
                subprocess.Popen([spotify_path], shell=False)
                print("[SPOTIFY] Opening Spotify desktop app")
                time.sleep(2)  # Wait for Spotify to open
                return {
                    "success": True,
                    "message": "Spotify opened successfully"
                }
            else:
                # Fallback: Open Spotify web player
                webbrowser.open("https://open.spotify.com")
                print("[SPOTIFY] Opening Spotify web player")
                return {
                    "success": True,
                    "message": "Spotify web player opened"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_play_button_by_template(self, screenshot_array, template_path: str):
        """
        Find the play button using OpenCV template matching
        
        Args:
            screenshot_array: Screenshot as numpy array (BGR format)
            template_path: Path to the template image of play button
            
        Returns:
            Tuple of (x, y) coordinates or None if not found
        """
        try:
            # Load the template image
            template = cv2.imread(template_path)
            if template is None:
                print(f"[SPOTIFY] Failed to load template image: {template_path}")
                return None
            
            # Convert template to grayscale for better matching
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            screenshot_gray = cv2.cvtColor(screenshot_array, cv2.COLOR_BGR2GRAY)
            
            # Get template dimensions
            h, w = template_gray.shape
            
            # Perform template matching with multiple scales for robustness
            best_match = None
            best_val = 0
            best_scale = 1.0
            
            # Try multiple scales (50% to 150% of original size)
            for scale in [0.5, 0.75, 1.0, 1.25, 1.5]:
                # Resize template
                scaled_template = cv2.resize(template_gray, None, fx=scale, fy=scale)
                scaled_h, scaled_w = scaled_template.shape
                
                # Skip if template is larger than screenshot
                if scaled_h > screenshot_gray.shape[0] or scaled_w > screenshot_gray.shape[1]:
                    continue
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # Keep track of best match
                if max_val > best_val:
                    best_val = max_val
                    best_match = max_loc
                    best_scale = scale
            
            # Check if match is good enough (threshold)
            if best_match and best_val > 0.6:  # 60% confidence threshold
                # Calculate center of matched region
                scaled_h = int(h * best_scale)
                scaled_w = int(w * best_scale)
                center_x = best_match[0] + scaled_w // 2
                center_y = best_match[1] + scaled_h // 2
                
                print(f"[SPOTIFY] Found play button at ({center_x}, {center_y}) with confidence {best_val:.2%} at scale {best_scale}")
                return (center_x, center_y)
            else:
                print(f"[SPOTIFY] Play button match too weak (confidence: {best_val:.2%})")
                return None
                
        except Exception as e:
            print(f"[SPOTIFY] Error in template matching: {e}")
            return None
    
    def _find_play_button_by_color(self, screenshot_array):
        """
        Find the play button using OpenCV color detection (fallback method)
        
        Args:
            screenshot_array: Screenshot as numpy array (BGR format)
            
        Returns:
            Tuple of (x, y) coordinates or None if not found
        """
        try:
            # Convert BGR to HSV for better color detection
            hsv = cv2.cvtColor(screenshot_array, cv2.COLOR_BGR2HSV)
            
            # Define range for green color (Spotify's green play button)
            lower_green = np.array([35, 100, 100])  # Lower bound for green
            upper_green = np.array([85, 255, 255])  # Upper bound for green
            
            # Create mask for green color
            mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Find contours (shapes) in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours to find circular play buttons
            play_buttons = []
            for contour in contours:
                # Get the bounding circle
                (x, y), radius = cv2.minEnclosingCircle(contour)
                
                # Filter by size (play button should be reasonably sized)
                if 15 < radius < 100:  # Adjust based on typical button size
                    area = cv2.contourArea(contour)
                    circularity = (4 * np.pi * area) / (cv2.arcLength(contour, True) ** 2) if cv2.arcLength(contour, True) > 0 else 0
                    
                    # Check if it's roughly circular (play button)
                    if circularity > 0.5:  # Reasonably circular
                        play_buttons.append((int(x), int(y), radius))
            
            if play_buttons:
                # Sort by y-coordinate (top to bottom) and return the first one
                play_buttons.sort(key=lambda b: b[1])
                x, y, radius = play_buttons[0]
                print(f"[SPOTIFY] Found green play button at ({x}, {y}) with radius {radius}")
                return (x, y)
            else:
                print("[SPOTIFY] No green play button found")
                return None
                
        except Exception as e:
            print(f"[SPOTIFY] Error detecting play button: {e}")
            return None
    
    def _auto_play_first_result(self, delay: float = 4.0, method: str = "opencv"):
        """
        Automatically play the first search result after a delay
        
        Args:
            delay: Seconds to wait before playing (default 4.0)
            method: Method to use - "opencv", "keyboard", or "click" (default "opencv")
        """
        try:
            if not PYAUTOGUI_AVAILABLE:
                print("[SPOTIFY] Auto-play not available - pyautogui not installed")
                return
            
            # Wait for search results to load
            print(f"[SPOTIFY] Waiting {delay} seconds for search results...")
            time.sleep(delay)
            
            if method == "opencv" and CV2_AVAILABLE:
                # Method 1: OpenCV-based visual detection (BEST - most reliable)
                print("[SPOTIFY] Using OpenCV to find and click play button...")
                
                # Press Tab once to focus on Spotify window
                pyautogui.press('tab')
                time.sleep(0.5)
                
                # Take a screenshot
                screenshot = pyautogui.screenshot()
                # Convert PIL image to OpenCV format (numpy array)
                screenshot_array = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Try template matching first if template image is available
                play_button_pos = None
                if self.play_button_image_path and Path(self.play_button_image_path).exists():
                    print(f"[SPOTIFY] Using template matching with image: {self.play_button_image_path}")
                    play_button_pos = self._find_play_button_by_template(screenshot_array, self.play_button_image_path)
                
                # Fallback to color detection if template matching failed
                if not play_button_pos:
                    print("[SPOTIFY] Template matching failed or not available, using color detection")
                    play_button_pos = self._find_play_button_by_color(screenshot_array)
                
                if play_button_pos:
                    x, y = play_button_pos
                    # Click on the play button
                    pyautogui.moveTo(x, y, duration=0.3)
                    time.sleep(0.2)
                    pyautogui.click()
                    print(f"[SPOTIFY] Clicked play button at ({x}, {y})")
                else:
                    print("[SPOTIFY] Play button not found, falling back to keyboard method")
                    # Fallback to keyboard method
                    pyautogui.press('enter')
                    time.sleep(0.5)
                    pyautogui.press('space')
            
            elif method == "keyboard":
                # Method 2: Keyboard navigation
                print("[SPOTIFY] Using keyboard to play first result...")
                
                for _ in range(3):
                    pyautogui.press('tab')
                    time.sleep(0.2)
                
                pyautogui.press('down')
                time.sleep(0.3)
                pyautogui.press('enter')
                print("[SPOTIFY] Pressed Enter to play")
                
                time.sleep(1)
                pyautogui.press('space')
                print("[SPOTIFY] Pressed Space as backup")
                
            elif method == "click":
                # Method 3: Mouse click (least reliable)
                print("[SPOTIFY] Using mouse click to play first result...")
                
                screen_width, screen_height = pyautogui.size()
                click_x = int(screen_width * 0.15)
                click_y = int(screen_height * 0.35)
                
                pyautogui.moveTo(click_x, click_y, duration=0.5)
                time.sleep(0.3)
                pyautogui.click()
                print(f"[SPOTIFY] Clicked at position ({click_x}, {click_y})")
            
            print("[SPOTIFY] Auto-play command sent!")
            
        except Exception as e:
            print(f"[SPOTIFY] Auto-play failed: {e}")
    
    def search_and_play(self, query: str, platform: str = "spotify", auto_play: bool = True) -> Dict:
        """
        Search for a song and play it on Spotify
        
        Args:
            query: Song name, artist, or search query
            platform: Music platform (currently only 'spotify' supported)
            auto_play: Whether to automatically play the first result (default True)
            
        Returns:
            Result dictionary
        """
        try:
            if platform.lower() != "spotify":
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not supported yet. Only Spotify is supported."
                }
            
            # Clean the query
            clean_query = query.strip()
            
            # Encode for URL
            encoded_query = urllib.parse.quote(clean_query)
            
            # Method 1: Try Spotify URI (desktop app)
            spotify_uri = f"spotify:search:{encoded_query}"
            
            try:
                # Try to open with Spotify desktop app
                os.startfile(spotify_uri)
                print(f"[SPOTIFY] Searching for: {clean_query} (desktop)")
                
                # Auto-play first result after delay
                if auto_play:
                    import threading
                    play_thread = threading.Thread(
                        target=self._auto_play_first_result,
                        args=(5.0, "opencv"),  # 5 second delay, OpenCV method
                        daemon=True
                    )
                    play_thread.start()
                
                return {
                    "success": True,
                    "message": f"Searching and playing '{clean_query}' on Spotify",
                    "query": clean_query,
                    "method": "desktop"
                }
            except Exception:
                # Fallback: Open in web player
                web_url = f"https://open.spotify.com/search/{encoded_query}"
                webbrowser.open(web_url)
                print(f"[SPOTIFY] Searching for: {clean_query} (web)")
                
                # Auto-play first result after longer delay (web is slower)
                if auto_play:
                    import threading
                    play_thread = threading.Thread(
                        target=self._auto_play_first_result,
                        args=(7.0, "opencv"),  # 7 second delay for web, OpenCV method
                        daemon=True
                    )
                    play_thread.start()
                
                return {
                    "success": True,
                    "message": f"Searching and playing '{clean_query}' on Spotify web player",
                    "query": clean_query,
                    "method": "web"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def play_song_directly(self, song_name: str, artist: Optional[str] = None) -> Dict:
        """
        Play a song directly on Spotify
        
        Args:
            song_name: Name of the song
            artist: Optional artist name for better search results
            
        Returns:
            Result dictionary
        """
        try:
            # Build search query
            if artist:
                query = f"{song_name} {artist}"
            else:
                query = song_name
            
            # Use search_and_play
            result = self.search_and_play(query, platform="spotify")
            
            if result.get("success"):
                result["message"] = f"Playing '{song_name}'" + (f" by {artist}" if artist else "") + " on Spotify"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global instance
_spotify_service: Optional[SpotifyService] = None


def get_spotify_service(play_button_image_path: Optional[str] = None) -> SpotifyService:
    """
    Get or create Spotify service instance
    
    Args:
        play_button_image_path: Optional path to play button template image for matching
                                Example: "E:/Stero Sonic Assistant/assets/spotify_play_button.png"
    
    Returns:
        SpotifyService instance
    """
    global _spotify_service
    if _spotify_service is None:
        _spotify_service = SpotifyService(play_button_image_path=play_button_image_path)
    return _spotify_service
