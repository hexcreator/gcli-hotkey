#!/usr/bin/env python3
"""
Gemini CLI Launcher - Shift + Double Middle-Click Version
Hold Shift and double middle-click any window to launch Gemini in that context
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
from pynput import mouse, keyboard

class GeminiHotkey:
    def __init__(self):
        self.running = True
        self.last_middle_click_time = 0
        self.double_click_threshold = 0.5  # 500ms
        self.shift_pressed = False
        
    def get_path_from_window(self, x, y):
        """Get path from window at coordinates"""
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
                try:
                    pythoncom.CoInitialize()
                    shell = win32com.client.Dispatch("Shell.Application")
                    for window in shell.Windows():
                        if window.HWND == hwnd:
                            path = window.Document.Folder.Self.Path
                            pythoncom.CoUninitialize()
                            return path
                    pythoncom.CoUninitialize()
                except:
                    pythoncom.CoUninitialize()
            
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
            
            # Method 3: Get process working directory (not exe location)
            try:
                cwd = process.cwd()
                # Only use if it's not a system directory
                if cwd and os.path.exists(cwd) and not any(sys in cwd.lower() for sys in ['system32', 'windows', 'program files', 'appdata']):
                    print(f"Using working directory: {cwd}")
                    return cwd
            except:
                pass
            
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
            
            # Method 4: Extract from window title (last resort)
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
    
    def launch_gemini(self, path):
        """Launch Gemini in the specified path"""
        print(f"Launching Gemini in: {path}")
        
        try:
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
        if button == mouse.Button.middle and pressed:
            if not self.shift_pressed:
                return

            current_time = time.time()
            
            # Check if it's a double-click
            if current_time - self.last_middle_click_time < self.double_click_threshold:
                # Double-click detected!
                print(f"\n🖱️ Shift + Double middle-click at ({x}, {y})")
                
                # Get path and launch in separate thread
                path = self.get_path_from_window(x, y)
                threading.Thread(
                    target=self.launch_gemini,
                    args=(path,),
                    daemon=True
                ).start()
                
                # Reset timer
                self.last_middle_click_time = 0
            else:
                # First click
                self.last_middle_click_time = current_time
    
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
    
    launcher = GeminiHotkey()
    launcher.run()

if __name__ == "__main__":
    main()