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
# ใช้ URL แบบเต็ม
curl -L -o /sdcard/Download/my_rejoin_tool.py \
  "https://raw.githubusercontent.com/nickprm1-ship-it/MyRejoinTool/refs/heads/main/MyRejoinTool.py"

# ตรวจสอบว่าไฟล์ที่ดาวน์โหลดมาเป็นสคริปต์ Python จริงหรือไม่
if ! head -n1 /sdcard/Download/my_rejoin_tool.py | grep -q "python"; then
    echo "❌ ไฟล์ที่ดาวน์โหลดมาไม่ถูกต้อง (อาจเป็น 404 page)"
    echo "🔍 ตรวจสอบลิงก์: https://raw.githubusercontent.com/nickprm1-ship-it/MyRejoinTool/refs/heads/main/MyRejoinTool.py"
    exit 1
fi

echo "[5/5] Launching tool..."
python /sdcard/Download/my_rejoin_tool.py
