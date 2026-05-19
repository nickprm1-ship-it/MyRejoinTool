#!/bin/bash
# Auto Installer for My Rejoin Tool - Multi Account
# Created by nickprm1-ship-it

echo "========================================="
echo "  MY REJOIN TOOL - INSTALLER"
echo "  รองรับสูงสุด 10 บัญชี"
echo "========================================="

# ขออนุญาต Storage (Termux)
termux-setup-storage

# อัปเดตระบบ
echo "[1/5] อัปเดตระบบ..."
pkg update -y && pkg upgrade -y

# ติดตั้ง Python และ Chromium
echo "[2/5] ติดตั้ง Python และ Chromium..."
pkg install python -y
pkg install chromium -y

# ติดตั้ง Python libraries (ใช้ pkg สำหรับ psutil แทน pip)
echo "[3/5] ติดตั้ง Python libraries..."
pkg install python-psutil -y   # สำคัญ: ใช้ package ของ Termux
pip install requests selenium webdriver-manager

# ดาวน์โหลดไฟล์หลัก
echo "[4/5] ดาวน์โหลดโปรแกรมหลัก..."
curl -Ls -o /sdcard/Download/my_rejoin_tool.py \
  "https://raw.githubusercontent.com/nickprm1-ship-it/MyRejoinTool/main/my_rejoin_tool.py"

# ตรวจสอบว่าดาวน์โหลดสำเร็จ
if [ ! -f /sdcard/Download/my_rejoin_tool.py ]; then
    echo "❌ ดาวน์โหลดไม่สำเร็จ (ไฟล์ไม่พบ)"
    exit 1
fi

echo "[5/5] เสร็จสิ้น! กำลังเปิดโปรแกรม..."
python /sdcard/Download/my_rejoin_tool.py
