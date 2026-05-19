#!/bin/bash
# Auto Installer for My Rejoin Tool - Termux Edition

echo "========================================="
echo "  MY REJOIN TOOL - INSTALLER"
echo "  รองรับสูงสุด 10 บัญชี"
echo "========================================="

termux-setup-storage

echo "[1/6] Updating packages..."
pkg update -y && pkg upgrade -y

echo "[2/6] Installing Python & Chromium..."
pkg install python -y
pkg install chromium -y

echo "[3/6] Installing chromedriver (สำคัญสำหรับ Selenium)..."
pkg install chromedriver -y

echo "[4/6] Installing Python libraries..."
pkg install python-psutil -y
pip install requests selenium

echo "[5/6] Downloading main tool..."
curl -L -o /sdcard/Download/my_rejoin_tool.py \
  "https://raw.githubusercontent.com/nickprm1-ship-it/MyRejoinTool/main/my_rejoin_tool.py"

if ! head -n1 /sdcard/Download/my_rejoin_tool.py | grep -q "python"; then
    echo "❌ ไฟล์ที่ดาวน์โหลดมาไม่ถูกต้อง (อาจเป็น 404 page)"
    exit 1
fi

echo "[6/6] Launching tool..."
python /sdcard/Download/my_rejoin_tool.py
