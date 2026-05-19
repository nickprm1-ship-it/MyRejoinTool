#!/bin/bash
# Auto Installer for My Rejoin Tool - Multi Account
# Created by YOUR_NAME

echo "========================================="
echo "  MY REJOIN TOOL - INSTALLER"
echo "  รองรับสูงสุด 10 บัญชี"
echo "========================================="

# ขออนุญาต Storage (เฉพาะ Termux)
if [ -e "/data/data/com.termux/files/home/storage" ]; then
    rm -rf /data/data/com.termux/files/home/storage
fi
termux-setup-storage

# อัปเดตระบบและติดตั้งแพ็กเกจที่จำเป็น
echo "[1/5] อัปเดตระบบ..."
yes | pkg update
yes | pkg upgrade

echo "[2/5] ติดตั้ง Python และ Chromium..."
yes | pkg install python
yes | pkg install python-pip
yes | pkg install chromium

echo "[3/5] ติดตั้ง Python libraries..."
pip install requests psutil selenium webdriver-manager

echo "[4/5] ดาวน์โหลดโปรแกรมหลัก..."
curl -Ls "https://raw.githubusercontent.com/YOUR_USERNAME/MyRejoinTool/main/my_rejoin_tool.py" -o /sdcard/Download/my_rejoin_tool.py

echo "[5/5] เสร็จสิ้น! กำลังเปิดโปรแกรม..."
python /sdcard/Download/my_rejoin_tool.py