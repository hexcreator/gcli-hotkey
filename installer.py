import os
import sys
import shutil
import subprocess
import winreg
import time

# --- Configuration ---
APP_NAME = "Ask Gemini Hotkey"
INSTALL_DIR_NAME = "AskGeminiHotkey"
SCRIPT_NAME = "hotkey.py"
STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REQUIRED_PACKAGES = ['pynput', 'psutil', 'pywin32']

# --- Helper Functions ---

def get_install_path():
    """Gets the full installation path in AppData."""
    try:
        appdata_path = os.environ['APPDATA']
        return os.path.join(appdata_path, INSTALL_DIR_NAME)
    except KeyError:
        print("ERROR: APPDATA environment variable not found.")
        sys.exit(1)

def is_installed():
    """Checks if the application is installed."""
    install_path = get_install_path()
    script_path = os.path.join(install_path, SCRIPT_NAME)
    
    # Check for registry key
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        registry_exists = True
    except FileNotFoundError:
        registry_exists = False
        
    # Check for script file
    file_exists = os.path.exists(script_path)

    return registry_exists and file_exists

def get_pythonw_path():
    """Finds the path to pythonw.exe."""
    python_exe = sys.executable
    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        print("ERROR: pythonw.exe not found. Make sure you are running this with a standard Python installation.")
        return None
    return pythonw_exe

def check_and_install_dependencies():
    """Checks for required packages and installs them if missing."""
    print("Checking for required packages...")
    installed_packages = subprocess.check_output([sys.executable, '-m', 'pip', 'list']).decode('utf-8')
    
    missing_packages = [pkg for pkg in REQUIRED_PACKAGES if pkg.lower() not in installed_packages.lower()]
    
    if not missing_packages:
        print("✓ All required packages are already installed.")
        return True
        
    print(f"Missing packages: {', '.join(missing_packages)}")
    print("Attempting to install...")
    
    try:
        for package in missing_packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("✓ All packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ ERROR: Failed to install packages: {e}")
        print("Please install them manually using: pip install pynput psutil pywin32")
        return False

# --- Core Functions ---

def install():
    """Installs the hotkey script and adds it to startup."""
    print(f"--- Installing {APP_NAME} ---")

    if is_installed():
        print("✓ Already installed. To reinstall, please uninstall first.")
        return

    # 1. Check dependencies
    if not check_and_install_dependencies():
        sys.exit(1)

    # 2. Get paths
    install_dir = get_install_path()
    source_script_path = os.path.join(os.path.dirname(__file__), SCRIPT_NAME)
    dest_script_path = os.path.join(install_dir, SCRIPT_NAME)
    pythonw_path = get_pythonw_path()

    if not os.path.exists(source_script_path):
        print(f"✗ ERROR: '{SCRIPT_NAME}' not found in the current directory.")
        sys.exit(1)
        
    if not pythonw_path:
        sys.exit(1)

    # 3. Create directory and copy script
    print(f"Creating directory: {install_dir}")
    os.makedirs(install_dir, exist_ok=True)
    print(f"Copying '{SCRIPT_NAME}' to '{install_dir}'")
    shutil.copy(source_script_path, dest_script_path)

    # 4. Add to startup registry
    command = f'"{pythonw_path}" "{dest_script_path}"'
    print("Adding to Windows startup...")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        print("✓ Registry key added successfully.")
    except Exception as e:
        print(f"✗ ERROR: Could not set registry key: {e}")
        print("  -> Try running the installer as an administrator.")
        # Clean up
        shutil.rmtree(install_dir)
        sys.exit(1)
        
    print(f"\n✓ {APP_NAME} installation complete!")
    print("The hotkey will be active after the next time you log in.")
    print("To start it immediately, run the script from the Start Menu or run this command:")
    print(f'  start "" {command}')


def uninstall():
    """Removes the hotkey script and its startup entry."""
    print(f"--- Uninstalling {APP_NAME} ---")
    
    if not is_installed():
        print("✓ Application is not installed.")
        return

    # 1. Remove registry key
    print("Removing startup registry key...")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, APP_NAME)
        print("✓ Registry key removed.")
    except FileNotFoundError:
        print("✓ Registry key already removed.")
    except Exception as e:
        print(f"✗ WARNING: Could not remove registry key: {e}")
        print("  -> You may need to remove it manually using 'regedit'.")

    # 2. Remove installation directory
    install_dir = get_install_path()
    if os.path.exists(install_dir):
        print(f"Removing directory: {install_dir}")
        # Add a small delay to ensure the process is not running
        time.sleep(1)
        try:
            shutil.rmtree(install_dir)
            print("✓ Directory removed.")
        except Exception as e:
            print(f"✗ WARNING: Could not remove directory: {e}")
            print("  -> You may need to delete it manually.")
            print(f"  -> Path: {install_dir}")

    print(f"\n✓ {APP_NAME} uninstallation complete.")
    print("If the script was running, the process may still be active until you log out or kill it manually.")

def main():
    """Main function to handle command-line arguments."""
    if len(sys.argv) == 1 or sys.argv[1].lower() not in ['install', 'uninstall']:
        print(f"Usage: python {os.path.basename(__file__)} [install|uninstall]")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    
    if action == 'install':
        install()
    elif action == 'uninstall':
        uninstall()

if __name__ == "__main__":
    main()
