@echo off
REM --- Uninstalls the Ask Gemini Hotkey ---

echo ===================================
echo  Uninstalling Ask Gemini Hotkey
echo ===================================
echo.

REM Change to the directory where the script is located
cd /d "%~dp0"

REM Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Python is not found. The script will proceed,
    echo but might not be able to clean up everything if Python is required.
    echo.
)

REM Run the uninstaller
echo Running the Python uninstaller script...
echo.
python installer.py uninstall

echo.
echo ---
echo Uninstallation process finished.
pause
