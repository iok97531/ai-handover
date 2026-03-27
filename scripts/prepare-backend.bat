@echo off
REM Prepare Python backend for distribution
REM Run this before `npm run build:win`

echo Installing Python dependencies for backend...

cd /d "%~dp0\..\backend"

python -m pip install -r requirements.txt --target .\vendor --upgrade --quiet

echo Backend preparation complete.
echo You can now run: npm run build:win
