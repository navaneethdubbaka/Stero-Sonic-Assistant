import pyttsx3
import threading

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
        
    def speak(self, text: str):
        """Speak text in a separate thread to avoid blocking"""
        def _speak():
            self.engine.say(text)
            self.engine.runAndWait()
        
        thread = threading.Thread(target=_speak)
        thread.start()
        return thread
    
    def speak_sync(self, text: str):
        """Speak text synchronously (blocking)"""
        self.engine.say(text)
        self.engine.runAndWait()

# Global instance
tts = TextToSpeech()

