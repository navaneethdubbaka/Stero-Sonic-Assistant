"""
Wake Word Detection Service using OpenWakeWord
Uses the sonic_india2.onnx model for detecting "Sonic" wake word
"""

import numpy as np
import sounddevice as sd
import time
import threading
from pathlib import Path
from typing import Callable, Optional
import queue

# Model path - relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "sonic_india2.onnx"

# Audio settings
SAMPLE_RATE = 16000
FRAME_SIZE = 1280
THRESHOLD = 0.80
COOLDOWN_SECONDS = 1.5


class WakeWordDetector:
    """
    Wake word detector using OpenWakeWord library.
    Listens for the "Sonic" wake word and triggers callbacks.
    """
    
    def __init__(self, model_path: Optional[str] = None, threshold: float = THRESHOLD):
        self.model_path = model_path or str(MODEL_PATH)
        self.threshold = threshold
        self.model = None
        self.is_listening = False
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callbacks: list[Callable[[], None]] = []
        self._last_trigger_time = 0.0
        self._prev_score = 0.0
        self._audio_stream = None
        self._detection_queue = queue.Queue()
        
    def _load_model(self):
        """Load the OpenWakeWord model"""
        if self.model is None:
            try:
                from openwakeword.model import Model
                print(f"Loading wake word model from: {self.model_path}")
                self.model = Model(wakeword_models=[self.model_path])
                print("Wake word model loaded successfully")
            except ImportError:
                raise ImportError(
                    "openwakeword is not installed. "
                    "Please install it with: pip install openwakeword"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load wake word model: {e}")
    
    def add_callback(self, callback: Callable[[], None]):
        """Add a callback function to be called when wake word is detected"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[], None]):
        """Remove a callback function"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _trigger_callbacks(self):
        """Trigger all registered callbacks"""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in wake word callback: {e}")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for audio stream processing"""
        if status:
            print(f"Audio status: {status}")
        
        # Convert audio data to int16
        audio = np.frombuffer(indata, dtype=np.int16)
        
        # Get prediction scores from model
        scores = self.model.predict(audio)
        
        for model_name, score in scores.items():
            now = time.time()
            
            # Rising-edge detection with cooldown
            # Only trigger when score crosses threshold from below
            if (
                self._prev_score < self.threshold
                and score >= self.threshold
                and (now - self._last_trigger_time) > COOLDOWN_SECONDS
            ):
                self._last_trigger_time = now
                self._detection_queue.put(score)
                print(f"[WAKE] WAKE WORD DETECTED! score={score:.2f}")
            
            self._prev_score = score
    
    def _listener_loop(self):
        """Main listener loop running in separate thread"""
        self._load_model()
        
        print("[LISTEN] Wake word listener started")
        print("[MIC] Say: Sonic")
        
        try:
            self._audio_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                blocksize=FRAME_SIZE,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            )
            self._audio_stream.start()
            
            while not self._stop_event.is_set():
                # Check for detections
                try:
                    score = self._detection_queue.get(timeout=0.1)
                    self._trigger_callbacks()
                except queue.Empty:
                    pass
                    
        except Exception as e:
            print(f"Wake word listener error: {e}")
        finally:
            if self._audio_stream:
                self._audio_stream.stop()
                self._audio_stream.close()
                self._audio_stream = None
            print("[STOP] Wake word listener stopped")
    
    def start(self):
        """Start listening for wake word in background thread"""
        if self.is_listening:
            print("Wake word detector is already running")
            return
        
        self._stop_event.clear()
        self._listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._listener_thread.start()
        self.is_listening = True
    
    def stop(self):
        """Stop listening for wake word"""
        if not self.is_listening:
            return
        
        self._stop_event.set()
        if self._listener_thread:
            self._listener_thread.join(timeout=2.0)
            self._listener_thread = None
        self.is_listening = False
    
    def is_running(self) -> bool:
        """Check if the detector is currently running"""
        return self.is_listening and self._listener_thread is not None and self._listener_thread.is_alive()


# Global instance for easy access
_detector_instance: Optional[WakeWordDetector] = None


def get_detector() -> WakeWordDetector:
    """Get or create the global wake word detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = WakeWordDetector()
    return _detector_instance


def start_wake_word_detection(callback: Optional[Callable[[], None]] = None) -> WakeWordDetector:
    """
    Start wake word detection with optional callback.
    
    Args:
        callback: Optional function to call when wake word is detected
        
    Returns:
        The WakeWordDetector instance
    """
    detector = get_detector()
    if callback:
        detector.add_callback(callback)
    detector.start()
    return detector


def stop_wake_word_detection():
    """Stop wake word detection"""
    global _detector_instance
    if _detector_instance:
        _detector_instance.stop()


# For testing/standalone usage
if __name__ == "__main__":
    def on_wake_word():
        print(">>> Wake word callback triggered! <<<")
    
    detector = start_wake_word_detection(on_wake_word)
    
    try:
        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_wake_word_detection()
