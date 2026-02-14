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
            words = app_name.strip().split()
            # Only drop first word if it's a verb like "open", "launch", "start"
            if words and words[0].lower() in ("open", "launch", "start"):
                words = words[1:]
            if words:
                app_name = " ".join(words)
            
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


    def get_running_apps(self, include_system: bool = False) -> dict:
        """Return a list of running user-facing applications with pid, name, exe, and window title when available.

        include_system: if False, filters out obvious Windows/system/background processes.
        """
        try:
            user_visible = []
            system_names = {
                'system', 'system idle process', 'idle', 'svchost.exe', 'conhost.exe', 'smss.exe', 'csrss.exe',
                'wininit.exe', 'services.exe', 'lsass.exe', 'winlogon.exe', 'dllhost.exe', 'ctfmon.exe',
                'fontdrvhost.exe', 'explorer.exe', 'searchui.exe', 'searchapp.exe', 'runtimebroker.exe',
                'sihost.exe', 'taskhostw.exe', 'backgroundtaskhost.exe', 'audiodg.exe'
            }

            # Try to import win32 APIs for window titles
            win32_available = False
            try:
                import win32process
                import win32gui
                win32_available = True
            except Exception:
                win32_available = False

            pid_to_title = {}
            if win32_available:
                try:
                    def enum_window_callback(hwnd, acc):
                        if not win32gui.IsWindowVisible(hwnd):
                            return
                        title = win32gui.GetWindowText(hwnd)
                        if not title:
                            return
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            acc[pid] = title
                        except Exception:
                            pass
                    win32gui.EnumWindows(enum_window_callback, pid_to_title)
                except Exception:
                    pid_to_title = {}

            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    name = (proc.info.get('name') or '').lower()
                    exe = (proc.info.get('exe') or '')
                    pid = proc.info.get('pid')
                    if not include_system and (not name or name in system_names):
                        continue
                    title = pid_to_title.get(pid)
                    # Heuristic: consider user-facing if has a window title or known app names
                    likely_user_app = bool(title) or any(k in name for k in [
                        'chrome', 'edge', 'firefox', 'spotify', 'code', 'studio', 'word', 'excel', 'powerpnt',
                        'notepad', 'whatsapp', 'discord', 'slack', 'outlook', 'zoom', 'teams', 'vlc'
                    ])
                    if include_system or likely_user_app:
                        user_visible.append({
                            'pid': pid,
                            'name': proc.info.get('name'),
                            'exe': exe,
                            'window_title': title
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            return {"success": True, "apps": user_visible}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_apps_by_names(self, names: List[str]) -> dict:
        """Close applications whose process name or executable matches any of the provided names (case-insensitive).

        Names can be friendly like "spotify" or executable like "Spotify.exe".
        Skips critical system processes.
        """
        try:
            if not names:
                return {"success": False, "error": "No application names provided"}
            names_lower = [n.lower() for n in names]
            protected = {
                'system', 'system idle process', 'explorer.exe', 'csrss.exe', 'lsass.exe', 'wininit.exe',
                'services.exe', 'smss.exe', 'winlogon.exe', 'svchost.exe'
            }
            closed = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    name = (proc.info.get('name') or '')
                    exe = (proc.info.get('exe') or '')
                    lname = name.lower()
                    if lname in protected:
                        continue
                    match = any(
                        key in lname or (exe and exe.lower().endswith(key))
                        for key in names_lower
                    )
                    if match:
                        p = psutil.Process(proc.info['pid'])
                        p.terminate()
                        closed.append({"name": name, "pid": proc.info['pid']})
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return {"success": True, "closed": closed}
        except Exception as e:
            return {"success": False, "error": str(e)}

