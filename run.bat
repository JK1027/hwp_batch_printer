@echo off
echo [INFO] Checking environment for HWP Batch Printer...

REM Check virtual environment
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat

REM Check dependencies
python -c "import PySide6, win32com" 2>nul
if %errorlevel% equ 0 goto START_APP

echo [WARNING] Missing required libraries (PySide6, pywin32).
echo [INFO] Installing packages from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt

:START_APP
echo [OK] Starting application...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application terminated unexpectedly.
    pause
)
