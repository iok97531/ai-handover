@echo off
REM Build Python backend into a standalone executable using PyInstaller
REM Run this before `npm run build:win`
REM Requirements: Python must be installed and in PATH

setlocal
cd /d "%~dp0\..\backend"

echo [1/3] Installing PyInstaller...
python -m pip install pyinstaller --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install PyInstaller
    exit /b 1
)

echo [2/3] Running PyInstaller...
python -m PyInstaller backend.spec --distpath dist --workpath build\pyinstaller --clean
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller build failed
    exit /b 1
)

echo [3/3] Verifying output...
if not exist "dist\backend\backend.exe" (
    echo [ERROR] backend.exe not found in backend\dist\backend\
    exit /b 1
)

echo.
echo [SUCCESS] Backend built: backend\dist\backend\backend.exe
echo You can now run: npm run build:win
endlocal
