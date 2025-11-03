import os
import pywhatkit as kit
import pyautogui
import time
from typing import Optional

class WhatsAppService:
    def __init__(self):
        self.contacts_file = os.getenv("CONTACTS_FILE_PATH", "./data/contacts.txt")
        # Configurable timing for WhatsApp Web load and sending
        try:
            self.whatsapp_wait = int(os.getenv("WHATSAPP_WAIT_SECONDS", "20"))
        except Exception:
            self.whatsapp_wait = 20
        try:
            self.whatsapp_enter_retries = int(os.getenv("WHATSAPP_ENTER_RETRIES", "3"))
        except Exception:
            self.whatsapp_enter_retries = 3
    
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
    
    def send_message(self, name_or_number: str, message: str) -> dict:
        """Send WhatsApp message to a contact name (from contacts file) or a phone number."""
        try:
            raw = (name_or_number or '').strip()
            phone_number = None
            # Heuristic: if it looks like a phone number, use as-is
            if raw.startswith('+') or raw.replace('+', '').replace(' ', '').replace('-', '').isdigit():
                phone_number = raw
            else:
                # Treat as a contact name and resolve from file
                phone_number = self.get_contact_number(raw)
                if not phone_number:
                    return {"success": False, "error": f"Contact '{raw}' not found"}
            
            # Send message instantly - increase wait_time for web to load chat
            # pywhatkit default is 20; we allow env override
            wait_time = max(10, int(self.whatsapp_wait))
            kit.sendwhatmsg_instantly(phone_number, message, wait_time, tab_close=False)

            # Additional buffer for slower loads
            time.sleep(2)

            # Try to ensure focus and send using Enter with retries
            retries = max(1, int(self.whatsapp_enter_retries))
            for i in range(retries):
                # Click near the bottom center to focus input (best effort)
                try:
                    width, height = pyautogui.size()
                    pyautogui.click(width // 2, int(height * 0.9))
                    time.sleep(0.2)
                except Exception:
                    pass
                # Press Enter to send
                pyautogui.press('enter')
                # Short delay between attempts if needed
                time.sleep(1.2)
            
            return {"success": True, "message": "WhatsApp message sent successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

