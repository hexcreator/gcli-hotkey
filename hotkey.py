#!/usr/bin/env python3
"""
Gemini CLI Launcher - Double Middle-Click Version
Double middle-click any window to launch Gemini in that context
"""

import os
import subprocess
import win32gui
import win32process
import win32com.client
import psutil
import pythoncom
import time
import threading
import sys
import pyperclip
from PIL import ImageGrab
from pynput import mouse, keyboard

class GeminiDoubleMiddleClick:
    def __init__(self):
        self.running = True
        self.last_middle_click_time = 0
        self.last_click_pos = (0, 0)
        self.double_click_threshold = 0.5  # 500ms
        self.shift_pressed = False  # Track if Shift key is held
        self.last_screenshot = None  # Track last screenshot path
        
    def capture_window_to_file(self, hwnd, save_dir):
        """Capture a window screenshot to a file"""
        print(f"Attempting to capture screenshot...")
        try:
            # Get window rectangle
            rect = win32gui.GetWindowRect(hwnd)
            x, y, right, bottom = rect
            print(f"Window rect: {x}, {y}, {right}, {bottom}")
            
            # Capture the window
            screenshot = ImageGrab.grab(bbox=(x, y, right, bottom))
            
            # Save to file with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"browser_screenshot_{timestamp}.png"
            filepath = os.path.join(save_dir, filename)
            
            screenshot.save(filepath, "PNG")
            
            print(f"✓ Screenshot saved: {filename}")
            print(f"  Full path: {filepath}")
            return filepath
        except Exception as e:
            print(f"Screenshot error: {e}")
            import traceback
            traceback.print_exc()
            return None
        """Get Explorer path using COM in a thread-safe way"""
        result = [None]  # Use list to store result from thread
        
        def get_path():
            try:
                pythoncom.CoInitialize()
                shell = win32com.client.Dispatch("Shell.Application")
                for window in shell.Windows():
                    try:
                        if window.HWND == hwnd:
                            result[0] = window.Document.Folder.Self.Path
                            break
                    except:
                        continue
                pythoncom.CoUninitialize()
            except Exception as e:
                print(f"COM Error details: {e}")
                pythoncom.CoUninitialize()
        
        # Run in thread to ensure proper COM initialization
        thread = threading.Thread(target=get_path)
        thread.start()
        thread.join(timeout=2.0)  # Wait max 2 seconds
        
        return result[0]
    
    def get_path_from_window(self, x, y):
        """Get path from window at coordinates"""
        # Reset screenshot path
        self.last_screenshot = None
        
        try:
            # Get window at point
            hwnd = win32gui.WindowFromPoint((x, y))
            if not hwnd:
                return os.path.expanduser("~\\Documents")
            
            # Get top-level window
            while hwnd:
                parent = win32gui.GetParent(hwnd)
                if not parent or parent == hwnd:
                    break
                hwnd = parent
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()
            
            # Get window info
            window_title = win32gui.GetWindowText(hwnd)
            window_class = win32gui.GetClassName(hwnd)
            
            print(f"\n--- Double middle-click detected ---")
            print(f"Window: {window_title}")
            print(f"Process: {process_name}")
            print(f"Class: {window_class}")
            
            # Method 1: File Explorer - get actual folder being viewed
            if process_name == 'explorer.exe' and window_class == 'CabinetWClass':
                print("Detected File Explorer window")
                
                # Try COM approach
                path = self.get_explorer_path_com(hwnd)
                if path:
                    print(f"Explorer path found via COM: {path}")
                    return path
                
                # Fallback: Try to extract from window title
                # File Explorer format: "FolderName - File Explorer" or just "FolderName"
                if window_title:
                    # Remove " - File Explorer" suffix if present
                    folder_part = window_title.replace(" - File Explorer", "").strip()
                    
                    # Check if it's a full path
                    if os.path.exists(folder_part):
                        print(f"Found full path in title: {folder_part}")
                        return folder_part
                    
                    # Try to find in common locations
                    common_paths = [
                        os.path.expanduser(f"~\\{folder_part}"),
                        os.path.expanduser(f"~\\Desktop\\{folder_part}"),
                        os.path.expanduser(f"~\\Documents\\{folder_part}"),
                        os.path.expanduser(f"~\\Downloads\\{folder_part}"),
                        f"C:\\{folder_part}",
                        f"D:\\{folder_part}",
                    ]
                    
                    for test_path in common_paths:
                        if os.path.exists(test_path) and os.path.isdir(test_path):
                            print(f"Found folder from title: {test_path}")
                            return test_path
                    
                    # Special case for 'Desktop' which might just show as "Desktop"
                    if folder_part.lower() == "desktop":
                        desktop = os.path.expanduser("~\\Desktop")
                        print(f"Desktop folder detected: {desktop}")
                        return desktop
            
            # Method 2: For editors, check command line for opened folders
            if any(editor in process_name for editor in ['code.exe', 'cursor.exe', 'sublime_text.exe']):
                try:
                    cmdline = process.cmdline()
                    # Look for --folder-uri argument (Cursor/VS Code specific)
                    for i, arg in enumerate(cmdline):
                        if arg == '--folder-uri' and i + 1 < len(cmdline):
                            folder_uri = cmdline[i + 1]
                            if folder_uri.startswith('file:///'):
                                import urllib.parse
                                path = urllib.parse.unquote(folder_uri[8:])
                                path = path.replace('/', '\\')
                                if len(path) > 1 and path[1] == ':':
                                    path = path[0].upper() + path[1:]
                                if os.path.exists(path):
                                    print(f"Found folder from --folder-uri: {path}")
                                    return path
                    
                    # Look for regular folder paths in arguments
                    for arg in cmdline[1:]:  # Skip exe path
                        if os.path.exists(arg) and os.path.isdir(arg):
                            print(f"Found folder in args: {arg}")
                            return arg
                except:
                    pass
                
                # For Cursor/VS Code, parse the window title
                # Format: "filename - foldername - Cursor/VS Code"
                if ' - Cursor' in window_title or ' - Visual Studio Code' in window_title:
                    parts = window_title.split(' - ')
                    if len(parts) >= 3:
                        # The folder name is usually the second-to-last part
                        folder_name = parts[-2].strip()
                        # Check if it's a full path
                        if os.path.exists(folder_name) and os.path.isdir(folder_name):
                            print(f"Found full path in title: {folder_name}")
                            return folder_name
                        # Otherwise, try to find it in common locations
                        else:
                            # Get the file path from the first part if possible
                            file_part = parts[0].strip()
                            # Common project locations to check
                            search_paths = [
                                os.path.dirname(os.path.abspath(__file__)),  # Script directory
                                os.getcwd(),  # Current working directory
                                os.path.expanduser("~\\Documents"),
                                os.path.expanduser("~\\Desktop"),
                                os.path.expanduser("~\\source\\repos"),
                                "C:\\projects",
                                "D:\\projects"
                            ]
                            
                            # Also check parent directories of the script
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            parent = os.path.dirname(script_dir)
                            while parent and parent != os.path.dirname(parent):
                                search_paths.append(parent)
                                parent = os.path.dirname(parent)
                            
                            for search_path in search_paths:
                                test_path = os.path.join(search_path, folder_name)
                                if os.path.exists(test_path) and os.path.isdir(test_path):
                                    print(f"Found folder in {search_path}: {test_path}")
                                    return test_path
            
            # Method 3: Browsers - take screenshot and use Downloads folder
            if any(browser in process_name for browser in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe', 'vivaldi.exe']):
                print(f"Detected browser: {process_name}")
                
                # Use Downloads folder as default for browsers
                downloads = os.path.expanduser("~\\Downloads")
                if not os.path.exists(downloads):
                    downloads = os.path.expanduser("~\\Documents")
                
                # Take screenshot of browser window and save to the folder
                screenshot_path = self.capture_window_to_file(hwnd, downloads)
                if screenshot_path:
                    # Store the screenshot path to reference it later
                    self.last_screenshot = screenshot_path
                    print(f"Screenshot saved: {screenshot_path}")
                else:
                    self.last_screenshot = None
                    print("Failed to capture screenshot")
                
                print(f"Using Downloads folder for browser context: {downloads}")
                return downloads
            
            # Method 4: Get process working directory (not exe location)
            try:
                cwd = process.cwd()
                # Only use if it's not a system directory
                if cwd and os.path.exists(cwd) and not any(sys in cwd.lower() for sys in ['system32', 'windows', 'program files', 'appdata']):
                    print(f"Using working directory: {cwd}")
                    return cwd
            except:
                pass
            
            # Method 4: Browsers - take screenshot and use Downloads folder
            if any(browser in process_name for browser in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe', 'vivaldi.exe']):
                print(f"Detected browser: {process_name}")
                
                # Use Downloads folder as default for browsers
                downloads = os.path.expanduser("~\\Downloads")
                if not os.path.exists(downloads):
                    downloads = os.path.expanduser("~\\Documents")
                
                # Take screenshot of browser window and save to the folder
                screenshot_path = self.capture_window_to_file(hwnd, downloads)
                if screenshot_path:
                    # Store the screenshot path to reference it later
                    self.last_screenshot = screenshot_path
                    print(f"Screenshot saved: {screenshot_path}")
                else:
                    self.last_screenshot = None
                    print("Failed to capture screenshot")
                
                print(f"Using Downloads folder for browser context: {downloads}")
                return downloads
            
            # Method 3: For editors, check command line for opened folders
            if any(editor in process_name for editor in ['code.exe', 'cursor.exe', 'sublime_text.exe']):
                try:
                    cmdline = process.cmdline()
                    # Look for folder paths in arguments
                    for arg in cmdline[1:]:  # Skip exe path
                        if os.path.exists(arg) and os.path.isdir(arg):
                            print(f"Found folder in args: {arg}")
                            return arg
                except:
                    pass
            
            # Method 4: For browsers - try to get Downloads or Desktop folder
            if any(browser in process_name for browser in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe']):
                print(f"Detected browser: {process_name}")
                
                # For browsers, we can't get the current page's context easily
                # But we can make smart defaults:
                
                # If the title contains common code-related terms, use a project folder
                title_lower = window_title.lower()
                if any(term in title_lower for term in ['github', 'gitlab', 'bitbucket', 'localhost:', '127.0.0.1', 'codepen', 'jsfiddle', 'stackoverflow']):
                    # Try to extract project name from title
                    if 'github.com' in title_lower:
                        # GitHub URLs often have format: "repo-name · owner/repo-name"
                        import re
                        match = re.search(r'([^/\s]+/[^/\s]+)', window_title)
                        if match:
                            repo_name = match.group(1).split('/')[-1]
                            print(f"Detected GitHub repo: {repo_name}")
                            # Look for this repo in common locations
                            search_paths = [
                                os.path.dirname(os.path.abspath(__file__)),
                                os.getcwd(),
                                os.path.expanduser("~\\source\\repos"),
                                os.path.expanduser("~\\Documents\\GitHub"),
                                os.path.expanduser("~\\Documents"),
                                os.path.expanduser("~\\Desktop"),
                                "C:\\projects",
                                "D:\\projects"
                            ]
                            for search_path in search_paths:
                                test_path = os.path.join(search_path, repo_name)
                                if os.path.exists(test_path) and os.path.isdir(test_path):
                                    print(f"Found matching repo folder: {test_path}")
                                    return test_path
                    
                # Also check clipboard for URLs that might give context
                try:
                    clipboard = pyperclip.paste()
                    if clipboard and 'github.com' in clipboard.lower():
                        # Extract repo name from GitHub URL
                        import re
                        match = re.search(r'github\.com/([^/]+)/([^/\s\?]+)', clipboard)
                        if match:
                            repo_name = match.group(2).replace('.git', '')
                            print(f"Found GitHub URL in clipboard: {repo_name}")
                            # Search for this repo
                            for search_path in search_paths:
                                test_path = os.path.join(search_path, repo_name)
                                if os.path.exists(test_path) and os.path.isdir(test_path):
                                    print(f"Found repo from clipboard: {test_path}")
                                    return test_path
                except:
                    pass
                    dev_folders = [
                        os.path.expanduser("~\\source\\repos"),
                        os.path.expanduser("~\\Documents\\GitHub"),
                        os.path.expanduser("~\\projects"),
                        "C:\\projects"
                    ]
                    for folder in dev_folders:
                        if os.path.exists(folder):
                            print(f"Using development folder: {folder}")
                            return folder
                
                # For general browsing, use Downloads (likely downloading files)
                downloads = os.path.expanduser("~\\Downloads")
                if os.path.exists(downloads):
                    print(f"Browser detected, using Downloads: {downloads}")
                    return downloads
            
            # Method 5: Extract from window title (last resort)
            if window_title:
                import re
                match = re.search(r'([A-Z]:\\[^<>:"|*?\[\]]+?)(?:\s|$|"|\'|-)', window_title)
                if match:
                    path = match.group(1).strip()
                    if os.path.exists(path):
                        if os.path.isfile(path):
                            path = os.path.dirname(path)
                        print(f"Found in title: {path}")
                        return path
            
        except Exception as e:
            print(f"Error getting path: {e}")
        
        # Default
        default = os.path.expanduser("~\\Documents")
        print(f"Using default: {default}")
        return default
    
    def launch_gemini(self, path, is_browser=False):
        """Launch Gemini in the specified path"""
        print(f"Launching Gemini in: {path}")
        
        if is_browser and self.last_screenshot:
            screenshot_name = os.path.basename(self.last_screenshot)
            # Copy the @filename to clipboard for easy pasting
            reference = f"@{screenshot_name}"
            try:
                pyperclip.copy(reference)
                print(f"\n💡 Browser screenshot saved as: {screenshot_name}")
                print(f"   '{reference}' copied to clipboard - just paste it!")
                print(f"   Example prompt: 'Explain what's shown in {reference}'")
            except:
                print(f"\n💡 Browser screenshot saved as: {screenshot_name}")
                print(f"   Type '@{screenshot_name}' in Gemini to reference it")
        
        try:
            # Just launch Gemini normally - files are referenced within prompts
            subprocess.Popen(
                f'start "Gemini CLI" cmd /k "cd /d "{path}" && gemini"',
                shell=True
            )
            print("✓ Launched successfully")
        except:
            try:
                subprocess.Popen(
                    f'start "Gemini CLI" cmd /k "cd /d "{path}" && npx @google/gemini-cli"',
                    shell=True
                )
                print("✓ Launched with npx")
            except Exception as e:
                print(f"✗ Launch failed: {e}")
    
    def on_press(self, key):
        """Handle key press"""
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = True
    
    def on_release(self, key):
        """Handle key release"""
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = False
    
    def on_click(self, x, y, button, pressed):
        """Handle mouse clicks"""
        # Only process if Shift is held down
        if not self.shift_pressed:
            return
            
        if button == mouse.Button.middle and pressed:
            current_time = time.time()
            
            # Check if it's a double-click
            if current_time - self.last_middle_click_time < self.double_click_threshold:
                # Double-click detected!
                print(f"\n🖱️ Shift + Double middle-click at ({x}, {y})")
                
                # Get path and check if browser
                path = self.get_path_from_window(x, y)
                
                # Check if we captured a screenshot (indicates browser)
                is_browser = self.last_screenshot is not None
                
                # Launch in separate thread
                threading.Thread(
                    target=self.launch_gemini,
                    args=(path, is_browser),
                    daemon=True
                ).start()
                
                # Reset timer
                self.last_middle_click_time = 0
            else:
                # First click
                self.last_middle_click_time = current_time
                self.last_click_pos = (x, y)
    
    def run(self):
        """Run the mouse and keyboard listeners"""
        print("Gemini Shift + Double Middle-Click Launcher")
        print("===========================================")
        print("✓ Running! Hold 'Shift' and double middle-click any window")
        print("✓ The double-click must be within 500ms")
        print("✓ Press Ctrl+C in this console window to exit")
        print("  (Note: Ctrl+C only works when this console window is focused)\n")
        
        # Create and start listeners
        mouse_listener = mouse.Listener(on_click=self.on_click)
        keyboard_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        
        mouse_listener.start()
        keyboard_listener.start()
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.running = False
            mouse_listener.stop()
            keyboard_listener.stop()
            return

def main():
    # First, install pynput if needed
    try:
        import pynput
    except ImportError:
        print("Installing required package: pynput")
        subprocess.check_call(["pip", "install", "pynput"])
        print("Please restart the script")
        return
    
    launcher = GeminiDoubleMiddleClick()
    launcher.run()

if __name__ == "__main__":
    main()