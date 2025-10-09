@echo off
echo ============================================================
echo Building Order of the Stone for Windows
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

echo Python found!
echo.

REM Install PyInstaller
echo Installing PyInstaller...
python -m pip install --quiet pyinstaller

REM Install game dependencies
echo Installing game dependencies...
python -m pip install --quiet pygame pillow

echo.
echo Building executable...
python build_simple.py windows

echo.
echo ============================================================
echo Build complete!
echo.
echo Your Windows executable is at:
echo releases\windows\Order_of_the_Stone.exe
echo.
echo You can now copy this file back to your Mac!
echo ============================================================
pause

