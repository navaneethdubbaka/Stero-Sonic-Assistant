import pyttsx3
import threading
import re

class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        # Set female voice (usually index 1)
        if len(self.voices) > 1:
            self.engine.setProperty('voice', self.voices[1].id)
        
        # Set speech rate and volume
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)
    
    def clean_text_for_speech(self, text: str) -> str:
        """
        Clean text by removing/replacing special characters for better TTS
        Keeps: letters, numbers, basic punctuation (. , ! ? - ')
        Removes: markdown formatting, emojis, special symbols
        """
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold **text**
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic *text*
        text = re.sub(r'__(.+?)__', r'\1', text)      # Bold __text__
        text = re.sub(r'_(.+?)_', r'\1', text)        # Italic _text_
        text = re.sub(r'`(.+?)`', r'\1', text)        # Inline code
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove emojis and special unicode characters
        text = re.sub(r'[^\w\s.,!?\'-]', ' ', text, flags=re.UNICODE)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
        
    def speak(self, text: str):
        """Speak text in a separate thread to avoid blocking"""
        # Clean the text before speaking
        clean_text = self.clean_text_for_speech(text)
        
        def _speak():
            self.engine.say(clean_text)
            self.engine.runAndWait()
        
        thread = threading.Thread(target=_speak)
        thread.start()
        return thread
    
    def speak_sync(self, text: str):
        """Speak text synchronously (blocking)"""
        # Clean the text before speaking
        clean_text = self.clean_text_for_speech(text)
        self.engine.say(clean_text)
        self.engine.runAndWait()

# Global instance
tts = TextToSpeech()

