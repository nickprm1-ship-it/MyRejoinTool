#!/bin/bash
echo "========================================="
echo "  MY REJOIN TOOL - INSTALLER"
echo "========================================="

termux-setup-storage

echo "[1/5] Updating packages..."
pkg update -y && pkg upgrade -y

echo "[2/5] Installing Python & Chromium..."
pkg install python -y
pkg install chromium -y

echo "[3/5] Installing Python libraries..."
pkg install python-psutil -y
pip install requests selenium webdriver-manager

echo "[4/5] Downloading main tool..."
URL="https://raw.githubusercontent.com/nickprm1-ship-it/MyRejoinTool/main/my_rejoin_tool.py"
OUTPUT="/sdcard/Download/my_rejoin_tool.py"

# ดาวน์โหลดและตรวจสอบสถานะ
if curl -fsSL -o "$OUTPUT" "$URL"; then
    echo "✅ Download successful"
else
    echo "❌ Download failed (HTTP 404 or connection error)"
    echo "   Please check if the file exists at: $URL"
    exit 1
fi

# ตรวจสอบว่าไฟล์ที่โหลดมาขึ้นต้นด้วย #! (ไม่ใช่ 404)
if ! head -n1 "$OUTPUT" | grep -q "^#!"; then
    echo "❌ Downloaded file is not a valid Python script (might be 404 page)"
    echo "   First line: $(head -n1 "$OUTPUT")"
    exit 1
fi

echo "[5/5] Launching tool..."
python "$OUTPUT"
