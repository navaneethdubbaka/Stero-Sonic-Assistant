"""
Stereo Sonic Assistant - Standalone Application
Uses pywebview to create a standalone app with FastAPI backend and React frontend
"""

import webview
import threading
import uvicorn
import os
from pathlib import Path
import sys

# Set UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.main import app

# Configuration
BACKEND_PORT = 8000
FRONTEND_BUILD_PATH = Path(__file__).parent / "frontend" / "build"
FRONTEND_INDEX = FRONTEND_BUILD_PATH / "index.html"

# Wake word detector instance
_wake_word_detector = None

def start_server():
    """Start FastAPI server in a separate thread"""
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="info")

def start_wake_word_detection():
    """Start wake word detection in background"""
    global _wake_word_detector
    try:
        from backend.services.wakeword_service import start_wake_word_detection as start_detector
        
        def on_wake_word():
            print("[WAKE] Wake word 'Sonic' detected! Ready for command...")
            # The voice API will handle the detection event
        
        _wake_word_detector = start_detector(on_wake_word)
        print("[OK] Wake word detection initialized")
    except ImportError as e:
        print(f"[!] Wake word detection not available: {e}")
        print("   Install with: pip install openwakeword sounddevice")
    except Exception as e:
        print(f"[!] Failed to start wake word detection: {e}")

def main():
    """Main function to start the application"""
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    import time
    time.sleep(2)
    
    # Start wake word detection
    start_wake_word_detection()
    
    # Check if frontend build exists
    if FRONTEND_INDEX.exists():
        # Serve frontend build - create a simple HTTP server
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import os
        
        class CustomHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(FRONTEND_BUILD_PATH), **kwargs)
            
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                super().end_headers()
        
        # Start frontend server on different port
        frontend_port = 3000
        frontend_server = HTTPServer(('127.0.0.1', frontend_port), CustomHandler)
        frontend_thread = threading.Thread(target=frontend_server.serve_forever, daemon=True)
        frontend_thread.start()
        
        url = f'http://127.0.0.1:{frontend_port}'
    else:
        print(f"Warning: Frontend build not found at {FRONTEND_INDEX}")
        print("Please build the React app first: cd frontend && npm run build")
        print("Starting with API endpoint...")
        url = f'http://127.0.0.1:{BACKEND_PORT}/docs'
    
    # Create webview window
    webview.create_window(
        'Stereo Sonic Assistant',
        url=url,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True
    )
    
    # Start webview
    webview.start(debug=False)

if __name__ == '__main__':
    main()

