@echo off
REM --- Installs the Ask Gemini Hotkey ---

echo =================================
echo  Installing Ask Gemini Hotkey
echo =================================
echo.

REM Change to the directory where the script is located
cd /d "%~dp0"

REM Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not found in your PATH.
    echo Please install Python and add it to your PATH to continue.
    echo.
    pause
    exit /b 1
)

REM Run the installer
echo Running the Python installer script...
echo.
python installer.py install

echo.
echo ---
echo Installation process finished.
pause
