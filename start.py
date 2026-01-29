"""
Quick start script for Stereo Sonic Assistant
Starts backend and optionally frontend
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# Set UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import webview
        print("[OK] Python dependencies OK")
    except ImportError as e:
        print(f"[X] Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    # Check wake word dependencies
    try:
        import openwakeword
        import sounddevice
        print("[OK] Wake word dependencies OK")
    except ImportError as e:
        print(f"[!] Wake word detection unavailable: {e}")
        print("  Install with: pip install openwakeword sounddevice")
        print("  (Application will still work without wake word detection)")
    
    # Check for wake word model
    model_path = Path(__file__).parent / "sonic_india2.onnx"
    if model_path.exists():
        print("[OK] Wake word model found")
    else:
        print("[!] Wake word model not found (sonic_india2.onnx)")
    
    # Check spaCy model
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("[OK] spaCy model OK")
    except OSError:
        print("[X] spaCy model not found")
        print("Please run: pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl")
        return False
    
    # Check .env file
    env_path = Path(".env")
    if not env_path.exists():
        print("[!] .env file not found")
        print("Please create .env file with required variables (see .env.example)")
    
    return True

def start_backend():
    """Start FastAPI backend"""
    print("\nStarting backend server...")
    backend_path = Path(__file__).parent / "backend" / "main.py"
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(backend_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Wait for server to start
        return process
    except Exception as e:
        print(f"Error starting backend: {e}")
        return None

def start_standalone():
    """Start standalone app with pywebview"""
    print("\nStarting standalone application...")
    app_path = Path(__file__).parent / "app.py"
    
    try:
        subprocess.run([sys.executable, str(app_path)])
    except KeyboardInterrupt:
        print("\nApplication stopped")
    except Exception as e:
        print(f"Error starting app: {e}")

def main():
    """Main function"""
    print("=" * 50)
    print("Stereo Sonic Assistant - Quick Start")
    print("=" * 50)
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\nStarting application...")
    print("Press Ctrl+C to stop\n")
    
    # Start backend
    backend_process = start_backend()
    
    if backend_process is None:
        print("Failed to start backend")
        sys.exit(1)
    
    try:
        # Start standalone app
        start_standalone()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if backend_process:
            backend_process.terminate()
            backend_process.wait()

if __name__ == "__main__":
    main()

