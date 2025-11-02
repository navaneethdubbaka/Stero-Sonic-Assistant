import spacy
from typing import Optional, Dict, Callable

class IntentParser:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model 'en_core_web_sm' not found. Please install it using: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def parse_intent(self, command: str) -> Optional[str]:
        """Parse user command and return intent"""
        if not self.nlp:
            return self._simple_intent_mapping(command.lower())
        
        doc = self.nlp(command.lower())
        
        patterns = {
            "wikipedia": [("search", "VERB"), ("wikipedia", "PROPN")],
            "youtube": [("search", "VERB"), ("youtube", "PROPN")],
            "note down": [("note", "NOUN"), ("down", "PART")],
            "stackoverflow": [("search", "VERB"), ("stackoverflow", "PROPN")],
            "music": [("play", "VERB"), ("music", "NOUN")],
            "time": [("time", "NOUN")],
            "mirror": [("open", "VERB"), ("mirror", "NOUN")],
            "store": [("store", "VERB"), ("data", "NOUN")],
            "retrieve": [("retrieve", "VERB"), ("data", "NOUN")],
            "email": [("send", "VERB"), ("email", "NOUN")],
            "selfie": [("take", "VERB"), ("selfie", "NOUN")],
            "google": [("search", "VERB"), ("google", "PROPN")],
            "close windows": [("close", "VERB"), ("windows", "NOUN")],
            "research": [("help", "VERB"), ("research", "NOUN")],
            "who are you": [("who", "PRON"), ("are", "VERB"), ("you", "PRON")],
            "send message": [("send", "VERB"), ("message", "NOUN")],
            "activate chatbot": [("activate", "VERB"), ("chatbot", "NOUN")],
            "switch windows": [("switch", "VERB"), ("windows", "NOUN")],
            "open lens": [("open", "VERB"), ("lens", "NOUN")],
            "scan the screen": [("scan", "VERB"), ("screen", "NOUN")],
            "open": [("open", "VERB")],
            "analyse data": [("analyse", "VERB"), ("data", "NOUN")]
        }
        
        for intent, key_parts in patterns.items():
            if all(keyword in [token.text for token in doc] and
                   any(tag == pos for _, pos in key_parts for token in doc if token.text == keyword)
                   for keyword, tag in key_parts):
                return intent
        
        return None
    
    def _simple_intent_mapping(self, command: str) -> Optional[str]:
        """Fallback simple keyword-based intent mapping"""
        command_lower = command.lower()
        
        intent_keywords = {
            "wikipedia": ["wikipedia", "wiki"],
            "youtube": ["youtube", "yt"],
            "note down": ["note down", "note"],
            "stackoverflow": ["stackoverflow", "stack overflow"],
            "music": ["play music", "music"],
            "time": ["time", "what time"],
            "mirror": ["mirror", "camera"],
            "store": ["store data", "store"],
            "retrieve": ["retrieve", "get data"],
            "email": ["send email", "email"],
            "selfie": ["selfie", "take selfie"],
            "google": ["google", "search google"],
            "close windows": ["close windows", "close"],
            "research": ["research", "help research"],
            "who are you": ["who are you"],
            "send message": ["send message", "message"],
            "activate chatbot": ["activate chatbot", "chatbot"],
            "switch windows": ["switch windows", "switch"],
            "open lens": ["open lens", "lens"],
            "scan the screen": ["scan screen", "scan"],
            "open": ["open"],
            "analyse data": ["analyse data", "analyze data", "data"]
        }
        
        for intent, keywords in intent_keywords.items():
            if any(keyword in command_lower for keyword in keywords):
                return intent
        
        return None

# Global instance
intent_parser = IntentParser()

