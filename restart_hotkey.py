#!/usr/bin/env python3
"""
Kill old hotkey process and start the new one
"""

import psutil
import os
import subprocess
import time

def kill_old_processes():
    """Find and kill all hotkey processes except this one"""
    current_pid = os.getpid()
    killed = 0
    
    print("Looking for running hotkey processes...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue
                
            # Check if it's a Python process
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    # Check if it's running any hotkey script
                    for arg in cmdline:
                        if any(script in str(arg) for script in [
                            'hotkey.py', 'hotkey_double_middle.py', 
                            'gemini_hotkey', 'GeminiHotkey'
                        ]):
                            print(f"Found: PID {proc.info['pid']} - {' '.join(cmdline[:3])}...")
                            try:
                                proc.kill()
                                killed += 1
                                print(f"  ✓ Killed")
                            except:
                                print(f"  ✗ Could not kill")
                            break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return killed

def start_new_version():
    """Start the new hotkey script"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    new_script = os.path.join(script_dir, "hotkey.py")
    
    if not os.path.exists(new_script):
        print(f"\nError: {new_script} not found!")
        print("Make sure hotkey.py is in the same folder")
        return False
    
    print(f"\nStarting new version: {new_script}")
    
    # Start it with pythonw to run in background
    try:
        subprocess.Popen(["pythonw", new_script])
        print("✓ New version started in background")
        return True
    except:
        # Fallback to regular python
        subprocess.Popen(["python", new_script])
        print("✓ New version started")
        return True

def main():
    print("Hotkey Process Restart Tool")
    print("===========================\n")
    
    # Kill old processes
    killed = kill_old_processes()
    
    if killed > 0:
        print(f"\nKilled {killed} old process(es)")
        print("Waiting 2 seconds...")
        time.sleep(2)
    else:
        print("\nNo old processes found")
    
    # Start new version
    if start_new_version():
        print("\n✅ Success! The new Shift + double middle-click version is now running")
        print("\nYou can close this window")
    else:
        print("\n❌ Failed to start new version")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")