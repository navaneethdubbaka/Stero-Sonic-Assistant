import os
from typing import Optional

class DataService:
    def __init__(self):
        self.stored_data_path = os.getenv("STORED_DATA_PATH", "./data/stored_data.txt")
        os.makedirs(os.path.dirname(self.stored_data_path), exist_ok=True)
    
    def store_data(self, key: str, value: str) -> dict:
        """Store key-value data"""
        try:
            with open(self.stored_data_path, 'a+') as file:
                file.seek(0)
                existing_data = file.read()
                file.seek(0, 2)
                if existing_data:
                    file.write("\n")
                file.write(f"{key},{value}")
            
            return {"success": True, "message": "Data stored successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def retrieve_data(self, key: str) -> dict:
        """Retrieve value by key"""
        try:
            if not os.path.exists(self.stored_data_path):
                return {"success": False, "error": "Data file does not exist"}
            
            with open(self.stored_data_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if ',' in line:
                        k, v = line.split(',', 1)
                        if k == key:
                            return {"success": True, "value": v}
            
            return {"success": False, "error": "Key not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_note(self, text: str, file_path: Optional[str] = None) -> dict:
        """Save a note/voice transcription"""
        try:
            if not file_path:
                file_path = os.path.join(os.path.dirname(self.stored_data_path), "noted_data.txt")
            
            with open(file_path, "w") as file:
                file.write(text)
            
            return {"success": True, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

