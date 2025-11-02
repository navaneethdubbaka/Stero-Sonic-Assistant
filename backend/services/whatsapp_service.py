import os
import pywhatkit as kit
import pyautogui
import time
from typing import Optional

class WhatsAppService:
    def __init__(self):
        self.contacts_file = os.getenv("CONTACTS_FILE_PATH", "./data/contacts.txt")
    
    def get_contact_number(self, name: str) -> Optional[str]:
        """Get contact number from contacts file"""
        try:
            if not os.path.exists(self.contacts_file):
                return None
            
            with open(self.contacts_file, 'r') as file:
                contacts = {}
                for line in file:
                    line = line.strip()
                    if ',' in line:
                        k, v = line.split(',', 1)
                        contacts[k.lower()] = v
                return contacts.get(name.lower())
        except Exception as e:
            print(f"Error reading contacts: {e}")
            return None
    
    def send_message(self, name: str, message: str) -> dict:
        """Send WhatsApp message"""
        try:
            phone_number = self.get_contact_number(name)
            if not phone_number:
                return {"success": False, "error": f"Contact '{name}' not found"}
            
            # Send message instantly
            kit.sendwhatmsg_instantly(phone_number, message, 10, tab_close=False)
            
            # Wait for message to be typed
            time.sleep(15)
            
            # Press Enter to send
            pyautogui.press('enter')
            
            return {"success": True, "message": "WhatsApp message sent successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

