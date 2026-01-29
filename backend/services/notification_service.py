"""
Notification Service for Windows
Fetches and monitors Windows notifications from the Action Center
Uses Windows Runtime APIs to access notification content
"""

import os
import json
import subprocess
import threading
import time
import asyncio
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

# Try to import winrt for Windows Runtime APIs
# Note: winrt package only supports Python 3.7-3.9, not Python 3.10+
# If you're using Python 3.10+, the PowerShell fallback method will be used
try:
    from winrt.windows.ui.notifications.management import UserNotificationListener, UserNotificationListenerAccessStatus
    from winrt.windows.data.xml.dom import XmlDocument
    WINRT_AVAILABLE = True
except ImportError:
    WINRT_AVAILABLE = False
    import sys
    if sys.version_info >= (3, 10):
        print("Note: winrt package requires Python 3.7-3.9. Using PowerShell fallback method for notifications.")
    else:
        print("Warning: winrt package not available. Install with: pip install winrt (requires Python 3.7-3.9)")


class NotificationService:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "..", "data", "notifications.db")
        self.capture_file = os.path.join(os.path.dirname(__file__), "notification_capture.json")
        self.last_check_time = datetime.now()
        self.monitoring = False
        self.monitor_thread = None
        self.last_event_id = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for storing notifications"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    app_name TEXT,
                    title TEXT,
                    body TEXT,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON notifications(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_app_name ON notifications(app_name)
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing notification database: {e}")
    
    def _get_notifications_winrt(self) -> List[Dict]:
        """Get notifications using Windows Runtime APIs (if available)
        
        Uses UserNotificationListener to read notification content from XML Toast format.
        This method extracts the actual title and body text from notifications.
        """
        if not WINRT_AVAILABLE:
            return []
        
        try:
            # Run async function in sync context
            return asyncio.run(self._read_notifications_async())
        except Exception as e:
            print(f"Error reading notifications via WinRT: {e}")
            return []
    
    async def _read_notifications_async(self) -> List[Dict]:
        """Async method to read notifications using WinRT UserNotificationListener"""
        notifications = []
        
        try:
            listener = UserNotificationListener.get_default()
            
            # Request access to notifications
            access = await listener.request_access_async()
            if access != UserNotificationListenerAccessStatus.ALLOWED:
                print("WinRT: Access NOT allowed. Go to Windows Settings → Notifications → Allow.")
                return []
            
            # Get all current notifications
            user_notifications = await listener.get_notifications_async()
            
            for notif in user_notifications:
                try:
                    app_name = notif.app_info.display_info.display_name
                    
                    # Get the notification visual binding
                    try:
                        binding = notif.notification.visual.get_binding("ToastGeneric")
                        xml_content = binding.get_xml()
                    except:
                        # Try alternative method if ToastGeneric binding doesn't exist
                        try:
                            xml_content = notif.notification.visual.get_binding("")
                        except:
                            xml_content = None
                    
                    if not xml_content:
                        continue
                    
                    # Parse XML content
                    doc = XmlDocument()
                    doc.load_xml(xml_content)
                    
                    # Extract text nodes
                    text_nodes = doc.get_elements_by_tag_name("text")
                    texts = [node.inner_text for node in text_nodes if node.inner_text]
                    
                    title = texts[0] if len(texts) > 0 else ""
                    body = " ".join(texts[1:]) if len(texts) > 1 else ""
                    
                    # Get timestamp - try to get from notification, otherwise use current time
                    try:
                        # Try to get creation time from notification
                        timestamp = datetime.now().isoformat()
                        # Note: UserNotification doesn't expose creation time directly
                        # We use current time as approximation
                    except:
                        timestamp = datetime.now().isoformat()
                    
                    notification_data = {
                        'timestamp': timestamp,
                        'app_name': app_name,
                        'title': title,
                        'body': body
                    }
                    
                    notifications.append(notification_data)
                    
                except Exception as e:
                    # Skip notifications that can't be parsed
                    continue
            
        except Exception as e:
            print(f"Error in async notification reading: {e}")
        
        return notifications
    
    def _get_notifications_powershell(self) -> List[Dict]:
        """Get notifications using PowerShell with better content extraction"""
        try:
            # PowerShell script to get notification history with better content extraction
            # Note: Windows doesn't provide direct API access to notification history
            # We'll parse event logs more carefully to extract notification content
            ps_script = '''
            $notifications = @()
            
            # Try to get notifications from event logs with detailed parsing
            try {
                # Get events from UserNotificationsPlatform log
                $events = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-UserNotificationsPlatform/Operational'} -MaxEvents 100 -ErrorAction SilentlyContinue | Sort-Object TimeCreated -Descending
                
                foreach ($event in $events) {
                    $message = $event.Message
                    $xml = $event.ToXml()
                    
                    # Extract ApplicationId from XML
                    $appId = "System"
                    if ($xml -match '<Data Name="ApplicationId">([^<]+)</Data>') {
                        $appId = $matches[1]
                    } elseif ($message -match "ApplicationId[:\s]+([^\s\n]+)") {
                        $appId = $matches[1]
                    }
                    
                    # Extract Title from XML - try multiple fields
                    $title = "Notification"
                    if ($xml -match '<Data Name="Title">([^<]+)</Data>') {
                        $title = [System.Web.HttpUtility]::HtmlDecode($matches[1])
                    } elseif ($xml -match '<Data Name="HeaderText">([^<]+)</Data>') {
                        $title = [System.Web.HttpUtility]::HtmlDecode($matches[1])
                    } elseif ($xml -match '<Data Name="ToastHeader">([^<]+)</Data>') {
                        $title = [System.Web.HttpUtility]::HtmlDecode($matches[1])
                    } elseif ($message -match "Title[:\s]+([^\n]+)") {
                        $title = $matches[1].Trim()
                    }
                    
                    # Extract Body/Content from XML - try multiple fields
                    $body = ""
                    if ($xml -match '<Data Name="Body">([^<]+)</Data>') {
                        $body = [System.Web.HttpUtility]::HtmlDecode($matches[1])
                    } elseif ($xml -match '<Data Name="Content">([^<]+)</Data>') {
                        $body = [System.Web.HttpUtility]::HtmlDecode($matches[1])
                    } elseif ($xml -match '<Data Name="BodyText">([^<]+)</Data>') {
                        $body = [System.Web.HttpUtility]::HtmlDecode($matches[1])
                    } elseif ($xml -match '<Data Name="ToastXml">(.+?)</Data>') {
                        # Try to parse Toast XML
                        $toastXml = $matches[1]
                        try {
                            $toastDoc = New-Object System.Xml.XmlDocument
                            $toastXmlDecoded = [System.Web.HttpUtility]::HtmlDecode($toastXml)
                            $toastDoc.LoadXml($toastXmlDecoded)
                            
                            $ns = New-Object System.Xml.XmlNamespaceManager($toastDoc.NameTable)
                            $ns.AddNamespace("t", "http://schemas.microsoft.com/notifications/2016/toast.xsd")
                            
                            $bodyNodes = $toastDoc.SelectNodes("//t:text[position()>1]", $ns)
                            if ($bodyNodes) {
                                $body = ($bodyNodes | ForEach-Object { $_.InnerText }) -join " "
                            }
                        } catch {}
                    } elseif ($message -match "Body[:\s]+([^\n]+)") {
                        $body = $matches[1].Trim()
                    } elseif ($message -match "Content[:\s]+([^\n]+)") {
                        $body = $matches[1].Trim()
                    }
                    
                    # Always add notification, even if content is minimal
                    # This ensures we capture all notifications for future reference
                    $props = @{
                        Timestamp = $event.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                        AppName = $appId
                        Title = $title
                        Body = $body
                    }
                    $notifications += New-Object PSObject -Property $props
                }
            } catch {
                Write-Error $_.Exception.Message
            }
            
            # If still no notifications, try Action Center log
            if ($notifications.Count -eq 0) {
                try {
                    $events = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-ActionCenter/Operational'} -MaxEvents 50 -ErrorAction SilentlyContinue | Sort-Object TimeCreated -Descending
                    foreach ($event in $events) {
                        $message = $event.Message
                        $xml = $event.ToXml()
                        
                        if ($xml -match '<Data Name="AppId">([^<]+)</Data>') {
                            $appId = $matches[1]
                        } else {
                            $appId = "Action Center"
                        }
                        
                        $title = "Action Center Notification"
                        if ($xml -match '<Data Name="Title">([^<]+)</Data>') {
                            $title = $matches[1]
                        }
                        
                        $body = $message
                        
                        $props = @{
                            Timestamp = $event.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                            AppName = $appId
                            Title = $title
                            Body = $body
                        }
                        $notifications += New-Object PSObject -Property $props
                    }
                } catch {}
            }
            
            if ($notifications.Count -eq 0) {
                return "[]"
            }
            
            $notifications | ConvertTo-Json -Compress
            '''
            
            # Execute PowerShell script
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout and result.stdout.strip():
                try:
                    output = result.stdout.strip()
                    # Remove any error messages that might be in the output
                    if output.startswith('[') or output.startswith('{'):
                        notifications = json.loads(output)
                        if isinstance(notifications, list):
                            return notifications
                        elif isinstance(notifications, dict):
                            return [notifications]
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}, output: {result.stdout[:200]}")
            
            return []
            
        except Exception as e:
            print(f"Error getting notifications via PowerShell: {e}")
            return []
    
    def _get_notifications_alternative(self) -> List[Dict]:
        """Alternative method to get notifications using Windows API"""
        try:
            # Use a Python-based approach with win32api or registry access
            # For now, return empty list - we'll store notifications as they come in
            return []
        except Exception as e:
            print(f"Error in alternative notification method: {e}")
            return []
    
    def _store_notification(self, notification: Dict):
        """Store notification in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (timestamp, app_name, title, body, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                notification.get('timestamp', datetime.now().isoformat()),
                notification.get('app_name', 'Unknown'),
                notification.get('title', ''),
                notification.get('body', ''),
                json.dumps(notification)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error storing notification: {e}")
    
    def get_recent_notifications(self, limit: int = 10) -> Dict:
        """Get recent notifications from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, app_name, title, body, raw_data
                FROM notifications
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            notifications = []
            for row in rows:
                notifications.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'app_name': row[2],
                    'title': row[3],
                    'body': row[4],
                    'raw_data': json.loads(row[5]) if row[5] else {}
                })
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "notifications": []
            }
    
    def get_notifications_by_app(self, app_name: str, limit: int = 10) -> Dict:
        """Get notifications filtered by app name
        
        Note: Windows Event Logs don't store notification content for privacy/security reasons.
        Only metadata (app name, timestamp) is typically available. Content is only captured
        if notifications are intercepted in real-time as they arrive.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, app_name, title, body, raw_data
                FROM notifications
                WHERE app_name LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f'%{app_name}%', limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            notifications = []
            for row in rows:
                notifications.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'app_name': row[2],
                    'title': row[3] if row[3] else f"Notification from {row[2]}",
                    'body': row[4] if row[4] else "Content not available (Windows privacy restriction)",
                    'raw_data': json.loads(row[5]) if row[5] else {}
                })
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications),
                "app_name": app_name,
                "note": "Notification content may be limited due to Windows privacy restrictions. Content is only available for notifications captured in real-time."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "notifications": []
            }
    
    def get_new_notifications(self, since_minutes: int = 5) -> Dict:
        """Get notifications from the last N minutes"""
        try:
            since_time = (datetime.now() - timedelta(minutes=since_minutes)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, app_name, title, body, raw_data
                FROM notifications
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (since_time,))
            
            rows = cursor.fetchall()
            conn.close()
            
            notifications = []
            for row in rows:
                notifications.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'app_name': row[2],
                    'title': row[3],
                    'body': row[4],
                    'raw_data': json.loads(row[5]) if row[5] else {}
                })
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications),
                "since_minutes": since_minutes
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "notifications": []
            }
    
    def _intercept_notification_powershell(self) -> Optional[Dict]:
        """Intercept a notification in real-time using PowerShell COM interface"""
        try:
            # PowerShell script to hook into notification events
            ps_script = '''
            # Register for notification events using COM
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            
            [ComImport]
            [Guid("4E14FB9F-2E6B-4F1C-8F5F-7B5B8C6D4E2A")]
            [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            public interface INotificationActivationCallback {
                void Activate([MarshalAs(UnmanagedType.LPWStr)] string appUserModelId,
                             [MarshalAs(UnmanagedType.LPWStr)] string invokedArgs,
                             [MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 3)] ushort[] data,
                             uint dataCount);
            }
"@
            
            # Try to get notification from event log with XML parsing
            $events = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-UserNotificationsPlatform/Operational'} -MaxEvents 1 -ErrorAction SilentlyContinue | Sort-Object TimeCreated -Descending
            
            if ($events) {
                $event = $events[0]
                $xml = $event.ToXml()
                $timestamp = $event.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                
                # Extract full notification XML content
                $appId = "Unknown"
                $title = "Notification"
                $body = ""
                
                # Try to extract from XML
                if ($xml -match '<Data Name="ApplicationId">([^<]+)</Data>') {
                    $appId = $matches[1]
                }
                
                # Try to get toast XML content - check multiple possible field names
                $toastXml = ""
                if ($xml -match '<Data Name="ToastXml">(.+?)</Data>') {
                    $toastXml = $matches[1]
                } elseif ($xml -match '<Data Name="ToastXML">(.+?)</Data>') {
                    $toastXml = $matches[1]
                } elseif ($xml -match '<Data Name="NotificationXml">(.+?)</Data>') {
                    $toastXml = $matches[1]
                } elseif ($xml -match '<Data Name="ContentXml">(.+?)</Data>') {
                    $toastXml = $matches[1]
                }
                
                if ($toastXml) {
                    try {
                        # Decode HTML entities
                        $toastXmlDecoded = $toastXml
                        try {
                            Add-Type -AssemblyName System.Web
                            $toastXmlDecoded = [System.Web.HttpUtility]::HtmlDecode($toastXml)
                        } catch {
                            # Fallback if System.Web not available
                            $toastXmlDecoded = $toastXml -replace '&lt;', '<' -replace '&gt;', '>' -replace '&amp;', '&' -replace '&quot;', '"'
                        }
                        
                        $toastDoc = New-Object System.Xml.XmlDocument
                        $toastDoc.LoadXml($toastXmlDecoded)
                        $ns = New-Object System.Xml.XmlNamespaceManager($toastDoc.NameTable)
                        $ns.AddNamespace("t", "http://schemas.microsoft.com/notifications/2016/toast.xsd")
                        $ns.AddNamespace("action", "http://schemas.microsoft.com/notifications/2016/action.xsd")
                        
                        # Try to get title from multiple possible locations
                        $titleNode = $toastDoc.SelectSingleNode("//t:text[1]", $ns)
                        if ($titleNode -and $titleNode.InnerText) {
                            $title = $titleNode.InnerText
                        } else {
                            $headerNode = $toastDoc.SelectSingleNode("//t:header", $ns)
                            if ($headerNode) {
                                $titleAttr = $headerNode.GetAttribute("title")
                                if ($titleAttr) { $title = $titleAttr }
                            }
                        }
                        
                        # Try to get body from multiple possible locations
                        $bodyNodes = $toastDoc.SelectNodes("//t:text[position()>1]", $ns)
                        if ($bodyNodes -and $bodyNodes.Count -gt 0) {
                            $body = ($bodyNodes | ForEach-Object { $_.InnerText }) -join " "
                        } else {
                            # Try alternative locations
                            $bodyNode = $toastDoc.SelectSingleNode("//t:body", $ns)
                            if ($bodyNode) {
                                $body = $bodyNode.InnerText
                            }
                        }
                    } catch {
                        # If XML parsing fails, try to extract text directly
                        if ($toastXml -match '<text[^>]*>([^<]+)</text>') {
                            $title = $matches[1]
                        }
                        if ($toastXml -match '<text[^>]*>([^<]+)</text>') {
                            $allMatches = [regex]::Matches($toastXml, '<text[^>]*>([^<]+)</text>')
                            if ($allMatches.Count -gt 1) {
                                $body = ($allMatches | Select-Object -Skip 1 | ForEach-Object { $_.Groups[1].Value }) -join " "
                            }
                        }
                    }
                }
                
                # If no title/body from XML, try message parsing
                if ($title -eq "Notification" -and $body -eq "") {
                    $message = $event.Message
                    if ($message -match "Title[:\s]+([^\n]+)") {
                        $title = $matches[1].Trim()
                    }
                    if ($message -match "Body[:\s]+([^\n]+)") {
                        $body = $matches[1].Trim()
                    }
                }
                
                $props = @{
                    Timestamp = $timestamp
                    AppName = $appId
                    Title = $title
                    Body = $body
                }
                
                return (New-Object PSObject -Property $props) | ConvertTo-Json -Compress
            }
            
            return $null
            '''
            
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout and result.stdout.strip():
                try:
                    notification = json.loads(result.stdout.strip())
                    return notification
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            print(f"Error intercepting notification: {e}")
            return None
    
    def _read_captured_notifications(self) -> List[Dict]:
        """Read notifications captured by PowerShell hook"""
        notifications = []
        try:
            if os.path.exists(self.capture_file):
                with open(self.capture_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                notif = json.loads(line.strip())
                                notifications.append(notif)
                            except json.JSONDecodeError:
                                continue
                # Clear the file after reading
                with open(self.capture_file, 'w', encoding='utf-8') as f:
                    pass
        except Exception as e:
            print(f"Error reading captured notifications: {e}")
        return notifications
    
    def _monitor_notifications_loop(self, callback: Optional[Callable] = None):
        """Background thread to monitor for new notifications"""
        last_check = datetime.now()
        seen_notification_ids = set()  # Track seen notifications to avoid duplicates
        
        while self.monitoring:
            try:
                # Check for new notifications every 2 seconds (more frequent for real-time)
                current_time = datetime.now()
                
                # Read captured notifications from PowerShell hook
                captured_notifications = self._read_captured_notifications()
                
                for notif in captured_notifications:
                    timestamp = notif.get('timestamp', datetime.now().isoformat())
                    app_name = notif.get('app_name', 'Unknown')
                    title = notif.get('title', '')
                    body = notif.get('body', '')
                    
                    notif_id = f"{app_name}_{title}_{body}_{timestamp}"
                    
                    if notif_id not in seen_notification_ids:
                        seen_notification_ids.add(notif_id)
                        # Store notification
                        self._store_notification(notif)
                        if callback:
                            callback(notif)
                
                # Also try to intercept the latest notification from event log
                latest_notification = self._intercept_notification_powershell()
                
                if latest_notification:
                    timestamp = latest_notification.get('timestamp', datetime.now().isoformat())
                    app_name = latest_notification.get('app_name', 'Unknown')
                    title = latest_notification.get('title', '')
                    body = latest_notification.get('body', '')
                    
                    notif_id = f"{app_name}_{title}_{body}_{timestamp}"
                    
                    if notif_id not in seen_notification_ids:
                        seen_notification_ids.add(notif_id)
                        self._store_notification(latest_notification)
                        if callback:
                            callback(latest_notification)
                
                # Try WinRT first (better content extraction), fallback to PowerShell
                new_notifications = []
                if WINRT_AVAILABLE:
                    try:
                        new_notifications = self._get_notifications_winrt()
                    except Exception as e:
                        print(f"WinRT failed, falling back to PowerShell: {e}")
                        new_notifications = self._get_notifications_powershell()
                else:
                    new_notifications = self._get_notifications_powershell()
                
                for notif in new_notifications:
                    # Create a unique ID for this notification
                    timestamp = notif.get('timestamp', datetime.now().isoformat())
                    app_name = notif.get('app_name', 'Unknown')
                    title = notif.get('title', '')
                    body = notif.get('body', '')
                    
                    # Create unique ID
                    notif_id = f"{app_name}_{title}_{body}_{timestamp}"
                    
                    # Check if we've seen this notification before
                    if notif_id not in seen_notification_ids:
                        seen_notification_ids.add(notif_id)
                        
                        # Check if notification is recent (last 60 seconds)
                        try:
                            # Try parsing different timestamp formats
                            try:
                                notif_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                            except:
                                try:
                                    notif_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                except:
                                    notif_time = datetime.now()
                            
                            time_diff = (current_time - notif_time).total_seconds()
                            
                            # If notification is within last 60 seconds, consider it new
                            if abs(time_diff) < 60:
                                # Store new notification
                                self._store_notification(notif)
                                
                                # Call callback if provided
                                if callback:
                                    callback(notif)
                        except Exception as e:
                            # If parsing fails, still store it (might be a new notification)
                            self._store_notification(notif)
                            if callback:
                                callback(notif)
                
                # Clean up old seen IDs (keep only last 100)
                if len(seen_notification_ids) > 100:
                    seen_notification_ids.clear()
                
                time.sleep(2)  # Check every 2 seconds for real-time monitoring
                
            except Exception as e:
                print(f"Error in notification monitoring loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start monitoring for new notifications in real-time"""
        if self.monitoring:
            return {"success": False, "error": "Monitoring already started"}
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_notifications_loop,
            args=(callback,),
            daemon=True
        )
        self.monitor_thread.start()
        
        return {"success": True, "message": "Notification monitoring started"}
    
    def stop_monitoring(self):
        """Stop monitoring for new notifications"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return {"success": True, "message": "Notification monitoring stopped"}
    
    def get_notification_history(self, days: int = 7) -> Dict:
        """Get notification history from the last N days"""
        try:
            since_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, timestamp, app_name, title, body, raw_data
                FROM notifications
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (since_time,))
            
            rows = cursor.fetchall()
            conn.close()
            
            notifications = []
            for row in rows:
                notifications.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'app_name': row[2],
                    'title': row[3],
                    'body': row[4],
                    'raw_data': json.loads(row[5]) if row[5] else {}
                })
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications),
                "days": days
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "notifications": []
            }
    
    def get_notifications_winrt(self) -> Dict:
        """Get notifications directly using WinRT UserNotificationListener
        
        This method reads notifications from Windows Action Center using WinRT APIs
        and extracts the title and body text from each notification.
        
        Note: winrt package only supports Python 3.7-3.9. For Python 3.10+, 
        use the PowerShell fallback method (get_recent_notifications).
        """
        if not WINRT_AVAILABLE:
            import sys
            if sys.version_info >= (3, 10):
                error_msg = "WinRT not available. The winrt package only supports Python 3.7-3.9. You are using Python {}.{}. Use the PowerShell fallback method instead.".format(
                    sys.version_info.major, sys.version_info.minor
                )
            else:
                error_msg = "WinRT not available. Install with: pip install winrt (requires Python 3.7-3.9)"
            return {
                "success": False,
                "error": error_msg,
                "notifications": []
            }
        
        try:
            notifications = self._get_notifications_winrt()
            
            # Store notifications in database
            for notif in notifications:
                self._store_notification(notif)
            
            return {
                "success": True,
                "notifications": notifications,
                "count": len(notifications),
                "method": "WinRT"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "notifications": []
            }
    
    def add_test_notification(self, app_name: str, title: str, body: str):
        """Add a test notification to the database (for testing)"""
        notification = {
            'timestamp': datetime.now().isoformat(),
            'app_name': app_name,
            'title': title,
            'body': body
        }
        self._store_notification(notification)
        return {"success": True, "message": "Test notification added"}

