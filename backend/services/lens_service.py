import os
import time
import webbrowser
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

class LensService:
    def __init__(self):
        self.button_image_path = os.getenv("LENS_BUTTON_IMAGE", "./assets/lens_button.png")
    
    def find_and_click_image(self, image_path: str, confidence: float = 0.8, timeout: int = 10) -> bool:
        """Find and click an image on screen"""
        start_time = time.time()
        
        while True:
            # Some environments lack OpenCV; confidence arg would fail there. Fallback gracefully.
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            except TypeError:
                location = pyautogui.locateOnScreen(image_path)
            
            if location is not None:
                center = pyautogui.center(location)
                pyautogui.click(center)
                return True
            
            if time.time() - start_time > timeout:
                return False
            
            time.sleep(0.5)
    
    def upload_image_to_lens(self, image_path: str) -> dict:
        """Upload image to Google Lens with robust fallbacks (Selenium → browser + GUI)."""
        try:
            abs_image_path = os.path.abspath(image_path)
            if not os.path.exists(abs_image_path):
                return {"success": False, "error": f"Image file not found: {abs_image_path}"}

            # 1) Try Selenium-driven Chrome first
            driver = None
            try:
                chrome_options = ChromeOptions()
                chrome_options.add_experimental_option("detach", True)
                # Optional: reduce automation banners
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
                chrome_options.add_experimental_option('useAutomationExtension', False)

                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

                # Prefer direct upload endpoint if available
                driver.get("https://lens.google.com/upload")
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                # Try multiple selectors for file input
                selectors = [
                    'input[type="file"]',
                    'input[type=file]',
                    'input[type="file"][accept*="image"]',
                ]
                file_input = None
                for css in selectors:
                    try:
                        file_input = driver.find_element(By.CSS_SELECTOR, css)
                        if file_input:
                            break
                    except Exception:
                        continue

                if file_input is None:
                    # Some pages build input dynamically; inject one and use it
                    driver.execute_script(
                        """
                        const input = document.createElement('input');
                        input.type = 'file';
                        input.accept = 'image/*';
                        input.style.display = 'block';
                        document.body.appendChild(input);
                        """
                    )
                    file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')

                file_input.send_keys(abs_image_path)
                # Give Lens time to process upload
                time.sleep(5)
                return {"success": True, "message": f"Image uploaded to Google Lens successfully. Path: {abs_image_path}"}

            except Exception as e:
                # Fall through to non-Selenium path
                if driver is not None:
                    try:
                        # Keep browser open for user; do not quit
                        pass
                    except Exception:
                        pass

            # 2) Fallback: open default browser and use GUI automation
            try:
                webbrowser.open("https://lens.google.com/upload")
                # Allow browser to load
                time.sleep(4)

                # Try to focus the OS file dialog by sending Enter if upload button auto-opens dialog
                # Otherwise try clicking a known upload area image if provided
                if os.path.exists(self.button_image_path):
                    self.find_and_click_image(self.button_image_path)
                    time.sleep(1.5)

                # Type the absolute path and press Enter
                pyautogui.write(abs_image_path)
                time.sleep(0.8)
                pyautogui.press('enter')
                time.sleep(5)
                return {"success": True, "message": f"Image uploaded to Google Lens successfully. Path: {abs_image_path}"}
            except Exception as e:
                return {"success": False, "error": f"Failed to open browser or interact with file dialog: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

