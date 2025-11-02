import psutil
import pyautogui
import os
import webbrowser
import wikipedia
import datetime
import time
import subprocess
from typing import List

class SystemService:
    def __init__(self):
        self.music_dir = os.getenv("MUSIC_DIR", "E:\\Music")
        self.last_play_time = 0
        self.play_cooldown = 5  # Seconds - prevent rapid toggling
    
    def open_windows_search(self, app_name: str) -> dict:
        """Open Windows search and search for app"""
        try:
            words = app_name.split()
            if len(words) > 1:
                app_name = ' '.join(words[1:])
            
            pyautogui.press('winleft')
            time.sleep(1)
            pyautogui.typewrite(app_name)
            time.sleep(1)
            pyautogui.press('enter')
            
            return {"success": True, "message": f"Searching for {app_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close_processes(self, exe_list: List[str]) -> dict:
        """Close specific executable processes"""
        try:
            closed = []
            for process in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if process.info['exe'] and any(process.info['exe'].endswith(exe) for exe in exe_list):
                        pid = process.info['pid']
                        process_name = process.info['name']
                        psutil.Process(pid).terminate()
                        closed.append({"name": process_name, "pid": pid})
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            return {"success": True, "closed_processes": closed}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def switch_windows(self) -> dict:
        """Switch between windows"""
        try:
            pyautogui.keyDown('alt')
            pyautogui.press('tab')
            time.sleep(1)
            pyautogui.keyUp('alt')
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_time(self) -> dict:
        """Get current time"""
        str_time = datetime.datetime.now().strftime("%H:%M:%S")
        return {"success": True, "time": str_time}
    
    def search_wikipedia(self, query: str) -> dict:
        """Search Wikipedia"""
        try:
            query = query.replace("wikipedia", "").strip()
            results = wikipedia.summary(query, sentences=2)
            return {"success": True, "summary": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_youtube(self, query: str) -> dict:
        """Open YouTube search"""
        try:
            url = f"https://www.youtube.com/search?q={query}"
            webbrowser.open(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_google(self, query: str) -> dict:
        """Open Google search"""
        try:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def open_stackoverflow(self) -> dict:
        """Open StackOverflow"""
        try:
            webbrowser.open("https://stackoverflow.com")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def play_music(self) -> dict:
        """Open Spotify and start playing music"""
        try:
            # Prevent rapid toggling - if we just played music recently, don't toggle again
            current_time = time.time()
            if current_time - self.last_play_time < self.play_cooldown:
                return {"success": True, "song": "Spotify - Already handling music playback"}
            
            # Check if Spotify is already running
            spotify_running = False
            for process in psutil.process_iter(['name']):
                try:
                    if 'spotify' in process.info['name'].lower():
                        spotify_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            spotify_opened = False
            
            if not spotify_running:
                # Try to open Spotify desktop app first
                spotify_paths = [
                    os.path.join(os.environ.get('APPDATA', ''), 'Spotify', 'Spotify.exe'),
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WindowsApps', 'Spotify.exe'),
                    'C:\\Program Files\\Spotify\\Spotify.exe',
                    'C:\\Users\\{}\\AppData\\Roaming\\Spotify\\Spotify.exe'.format(os.environ.get('USERNAME', '')),
                ]
                
                for path in spotify_paths:
                    if os.path.exists(path):
                        try:
                            subprocess.Popen([path])
                            spotify_opened = True
                            time.sleep(3)  # Wait for Spotify to launch
                            break
                        except:
                            continue
                
                # If desktop app not found, try using Windows search
                if not spotify_opened:
                    try:
                        pyautogui.press('winleft')
                        time.sleep(0.5)
                        pyautogui.typewrite('spotify')
                        time.sleep(1)
                        pyautogui.press('enter')
                        time.sleep(3)  # Wait for Spotify to launch
                        spotify_opened = True
                    except:
                        pass
                
                # Last resort: try opening Spotify web player
                if not spotify_opened:
                    try:
                        webbrowser.open("https://open.spotify.com")
                        time.sleep(3)  # Wait for browser to open
                    except:
                        pass
            
            # Try to play/resume music
            # Wait for Spotify to be ready
            if spotify_opened:
                time.sleep(6)  # Wait longer for Spotify to fully load and initialize
                
                # Try to find and activate Spotify window using Windows API
                try:
                    import win32gui
                    import win32con
                    
                    def enum_windows_callback(hwnd, windows):
                        window_text = win32gui.GetWindowText(hwnd)
                        if 'spotify' in window_text.lower():
                            windows.append((hwnd, window_text))
                    
                    spotify_windows = []
                    win32gui.EnumWindows(enum_windows_callback, spotify_windows)
                    
                    if spotify_windows:
                        # Get the first Spotify window
                        hwnd, _ = spotify_windows[0]
                        # Bring window to foreground
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(1)  # Wait for window to activate
                except ImportError:
                    # win32gui not available, use Alt+Tab method
                    try:
                        # Press Alt+Tab multiple times to find Spotify
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(0.5)
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(1)  # Wait for window switch
                    except:
                        pass
                except:
                    # Fallback to Alt+Tab method
                    try:
                        pyautogui.hotkey('alt', 'tab')
                        time.sleep(1)
                    except:
                        pass
                
                # Now try multiple methods to start playback
                try:
                    # Method 1: Spacebar (works when Spotify is focused)
                    pyautogui.press('space')
                    time.sleep(0.8)
                except:
                    pass
                
                try:
                    # Method 2: Media play key (works system-wide)
                    pyautogui.press('playpause')
                    time.sleep(0.5)
                except:
                    pass
                
                # Try once more with spacebar if media key didn't work
                try:
                    pyautogui.press('space')
                except:
                    pass
            elif not spotify_running:
                # Spotify web player was opened - try to play
                time.sleep(4)  # Wait for browser to fully load Spotify
                try:
                    # Focus on browser window first
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(0.5)
                    # Press spacebar to play
                    pyautogui.press('space')
                    time.sleep(0.5)
                    # Also try media play key
                    pyautogui.press('playpause')
                except:
                    try:
                        pyautogui.press('playpause')
                    except:
                        pass
            else:
                # Spotify was already running - try to resume if paused
                time.sleep(1)
                try:
                    # Try to activate Spotify window
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(0.5)
                    # Press spacebar to play/resume
                    pyautogui.press('space')
                except:
                    # Fallback to media play key
                    try:
                        pyautogui.press('playpause')
                    except:
                        pass
            
            # Update last play time to prevent rapid toggling
            self.last_play_time = current_time
            
            return {"success": True, "song": "Spotify - Playing music"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

