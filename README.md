# Ask Gemini Hotkey

A simple Windows utility that allows you to instantly launch the [Google Gemini CLI](https://github.com/google/gemini-cli) in the context of your currently active window by holding **Shift** and **double middle-clicking** anywhere on the screen.

This tool is perfect for developers, writers, and anyone who wants a faster way to interact with Gemini without constantly switching windows or manually navigating `cd` commands in a terminal.

## Features

- **Context-Aware Launching**: Hold **Shift** and **double middle-click** on a window, and the Gemini CLI will start with its working directory set to that application's folder.
  - **File Explorer**: Opens Gemini in the exact folder you are viewing.
  - **Code Editors (VS Code, Cursor, Sublime)**: Intelligently finds the project folder open in the editor.
  - **Other Applications**: Defaults to the application's working directory or your Documents folder.
- **Simple & Lightweight**: Runs quietly in the background with minimal system resources.
- **Easy Installation**: Simple `install.bat` script to get you started in seconds.
- **No Annoying Windows**: The hotkey script runs silently in the background without a persistent console window.

## Prerequisites

- **Operating System**: Windows 10/11
- **Python**: Python 3 must be installed and added to your system's PATH. You can download it from [python.org](https://www.python.org/).
- **Gemini CLI**: The `gemini` or `npx @google/gemini-cli` command must be accessible from your terminal.

## Installation

1.  Make sure you have met all the prerequisites.
2.  Download the latest release from the [Releases](https://github.com/hexcreator/gcli-hotkey/releases) page or clone this repository.
3.  Right-click on `install.bat` and select **"Run as administrator"**.
4.  Follow the on-screen instructions. The installer will copy the necessary files and add the hotkey to your Windows startup programs.

The hotkey will be active the next time you log in. To start it immediately without logging out, you can run the script from the start menu (`Ask Gemini Hotkey`).

## How to Use

- **Hold the Shift key and double-click the middle mouse button** on any window.
- A new terminal window will open with the Gemini CLI, ready for your prompts in the correct directory.

The double-click speed is set to 500ms by default.

## Uninstallation

1.  Right-click on `uninstall.bat` and select **"Run as administrator"**.
2.  The script will remove the startup entry and delete the program files.

## For Developers

This project consists of three main files:
- `hotkey.py`: The core Python script that listens for the Shift + double middle-click combination and launches Gemini.
- `installer.py`: A Python script that handles the logic for installation (copying files, setting registry keys) and uninstallation.
- `install.bat` / `uninstall.bat`: Convenience scripts for easy execution of the installer.

You can customize the behavior by editing `hotkey.py`. To run it manually for testing, you can execute:
```bash
python hotkey.py
```
Make sure you have the required Python packages installed:
```bash
pip install pynput psutil pywin32
```

---

*Disclaimer: This is an unofficial utility and is not affiliated with Google.*