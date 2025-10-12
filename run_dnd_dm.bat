@echo off
REM =================================================================
REM AI Dungeon Master - Automated Startup Script
REM =================================================================

echo.
echo ============================================================
echo    AI DUNGEON MASTER - STARTING UP
echo ============================================================
echo.

REM Navigate to project directory
cd /d %~dp0

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [1/5] Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist "5thsrd-py3.8\Scripts\activate.bat" (
    echo [1/5] Activating virtual environment...
    call 5thsrd-py3.8\Scripts\activate.bat
) else (
    echo [1/5] No virtual environment found, using system Python...
)

echo.
echo [2/5] Deleting old templates for fresh regeneration...
if exist "templates" (
    rmdir /s /q templates
    timeout /t 1 /nobreak >nul
    echo    - Templates folder deleted
) else (
    echo    - No templates folder found
)

REM Force delete any remaining template files
if exist "templates" (
    echo    - Force removing stubborn files...
    del /f /s /q templates\* >nul 2>&1
    rmdir /s /q templates >nul 2>&1
)

echo    - Templates will be regenerated on startup

echo.
echo [3/5] Checking required files...
set MISSING_FILES=0

if not exist "flask_campaign_ui.py" (
    echo    ERROR: flask_campaign_ui.py not found!
    set MISSING_FILES=1
)
if not exist "campaign_manager.py" (
    echo    ERROR: campaign_manager.py not found!
    set MISSING_FILES=1
)
if not exist "ai_dm_query_router.py" (
    echo    ERROR: ai_dm_query_router.py not found!
    set MISSING_FILES=1
)
if not exist "ai_dm_free.py" (
    echo    ERROR: ai_dm_free.py not found!
    set MISSING_FILES=1
)

if %MISSING_FILES%==1 (
    echo.
    echo    ERROR: Missing required files!
    echo    Make sure you're in the correct directory.
    pause
    exit /b 1
)

echo    - All required files found!

echo.
echo [4/5] Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL%==0 (
    echo    - Ollama is running
) else (
    echo    WARNING: Ollama not detected!
    echo    Start Ollama with: ollama serve
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b
)

echo.
echo [5/5] Starting Flask Campaign Manager...
echo.
echo ============================================================
echo    SERVER STARTING
echo ============================================================
echo.
echo    DM Interface: http://localhost:5000
echo    Player View:  http://localhost:5000/player
echo.
echo    Press Ctrl+C to stop the server
echo ============================================================
echo.

python flask_campaign_ui.py

pause