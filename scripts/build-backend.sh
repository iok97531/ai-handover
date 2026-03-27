#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../backend"

echo "[1/3] Installing PyInstaller..."
python3 -m pip install pyinstaller --quiet

echo "[2/3] Running PyInstaller..."
python3 -m PyInstaller backend.spec --distpath dist --workpath build/pyinstaller --clean

echo "[3/3] Verifying output..."
if [ ! -f "dist/backend/backend" ]; then
    echo "[ERROR] backend executable not found in backend/dist/backend/"
    exit 1
fi

echo ""
echo "[SUCCESS] Backend built: backend/dist/backend/backend"
echo "You can now run: npm run build:win"
