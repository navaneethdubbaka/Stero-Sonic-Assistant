import os
import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional

class LensService:
    def __init__(self):
        self.button_image_path = os.getenv("LENS_BUTTON_IMAGE", "./assets/lens_button.png")
    
    def find_and_click_image(self, image_path: str, confidence: float = 0.8, timeout: int = 10) -> bool:
        """Find and click an image on screen"""
        start_time = time.time()
        
        while True:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            
            if location is not None:
                center = pyautogui.center(location)
                pyautogui.click(center)
                return True
            
            if time.time() - start_time > timeout:
                return False
            
            time.sleep(0.5)
    
    def upload_image_to_lens(self, image_path: str) -> dict:
        """Upload image to Google Lens"""
        try:
            # Ensure absolute path
            abs_image_path = os.path.abspath(image_path)
            if not os.path.exists(abs_image_path):
                return {"success": False, "error": f"Image file not found: {abs_image_path}"}
            
            chrome_options = Options()
            chrome_options.add_experimental_option("detach", True)
            # Try to find Chrome in common locations
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                return {"success": False, "error": f"Failed to initialize Chrome driver: {str(e)}"}
            
            try:
                driver.get("https://lens.google.com/")
                time.sleep(3)
                
                # Try to find and click the upload button using Selenium
                try:
                    # Look for file input element
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    # Wait for page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Try multiple methods to upload
                    # Method 1: Find file input directly
                    try:
                        file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
                        file_input.send_keys(abs_image_path)
                        time.sleep(5)
                        return {"success": True, "message": f"Image uploaded to Google Lens successfully. Path: {abs_image_path}"}
                    except:
                        pass
                    
                    # Method 2: Try clicking upload area and using pyautogui
                    try:
                        # Click on the upload area
                        upload_area = driver.find_element(By.CSS_SELECTOR, '[data-testid="upload-area"], button, .upload-area')
                        driver.execute_script("arguments[0].click();", upload_area)
                        time.sleep(2)
                        
                        # Use pyautogui to type file path
                        pyautogui.write(abs_image_path)
                        time.sleep(1)
                        pyautogui.press('enter')
                        time.sleep(5)
                        return {"success": True, "message": f"Image uploaded to Google Lens successfully. Path: {abs_image_path}"}
                    except:
                        pass
                    
                    # Method 3: Fallback to image recognition if button image exists
                    if os.path.exists(self.button_image_path):
                        if self.find_and_click_image(self.button_image_path):
                            time.sleep(2)
                            pyautogui.write(abs_image_path)
                            time.sleep(1)
                            pyautogui.press('enter')
                            time.sleep(5)
                            return {"success": True, "message": f"Image uploaded to Google Lens successfully. Path: {abs_image_path}"}
                    
                    return {"success": False, "error": "Could not find upload button on Google Lens page"}
                    
                except Exception as e:
                    return {"success": False, "error": f"Failed to upload image: {str(e)}"}
                    
            finally:
                # Don't close the browser immediately - let user see results
                # driver.quit()  # Commented out to keep browser open
                pass
                
        except Exception as e:
            return {"success": False, "error": str(e)}

