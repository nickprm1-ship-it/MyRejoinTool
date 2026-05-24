#!/bin/bash
# ===========================================
#  MyRejoinTool v2.0 - ติดตั้งอัตโนมัติ Termux
#  รองรับ 10 บัญชี, ใช้ .ROBLOSECURITY cookie
#  ติดตั้ง selenium + chromedriver จริง
# ===========================================

set -e

echo "========================================="
echo "  MY REJOIN TOOL v2.0"
echo "  กำลังติดตั้ง dependencies..."
echo "========================================="

# อัปเดตแพ็กเกจ
pkg update -y && pkg upgrade -y

# ติดตั้ง python และ pip
pkg install python -y

# ติดตั้ง selenium, requests, psutil
pip install selenium requests psutil

# ติดตั้ง chromium สำหรับ Termux
pkg install chromium -y

# ตรวจสอบ chromedriver
CHROME_VERSION=$(chromium --version | grep -oP '\d+\.\d+\.\d+' | head -1)
echo "Chromium version: $CHROME_VERSION"

# สร้างไฟล์ main.py
cat > main.py << 'PYEOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyRejoinTool v2.0 - ควบคุม 10 บัญชี Roblox
ใช้ .ROBLOSECURITY cookie, selenium คลิกเกมจริง
"""

import os
import sys
import time
import json
import threading
import logging
import random
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import psutil

# ===================== การตั้งค่า =====================
ACCOUNTS_FILE = "accounts.json"
JOIN_URL = "https://www.roblox.com/games/123456789/example"
CHECK_INTERVAL = 10  # วินาที
MAX_RETRIES = 5
USE_PROCESS_DETECT = True
USE_API_CHECK = True

# ===================== ตั้งค่า Logging =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("rejoin_tool.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MyRejoinTool")

# ===================== อ่านข้อมูลบัญชี =====================
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        logger.error(f"ไม่พบไฟล์ {ACCOUNTS_FILE}")
        sys.exit(1)
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

# ===================== ฟังก์ชัน Selenium =====================
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.binary_location = "/data/data/com.termux/files/usr/bin/chromium"
    driver = webdriver.Chrome(options=options)
    return driver

def inject_cookie(driver, cookie_str):
    try:
        driver.get("https://www.roblox.com/login")
        time.sleep(2)
        driver.delete_all_cookies()
        cookie = {
            'name': '.ROBLOSECURITY',
            'value': cookie_str,
            'domain': '.roblox.com',
            'path': '/',
            'secure': True,
            'httpOnly': True
        }
        driver.add_cookie(cookie)
        driver.get("https://www.roblox.com/home")
        time.sleep(2)
        return True
    except Exception as e:
        logger.error(f"Inject cookie error: {e}")
        return False

def try_join_game(driver, join_url):
    try:
        driver.get(join_url)
        time.sleep(3)
        try:
            join_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'เล่น')]"))
            )
            join_btn.click()
            logger.info("คลิกปุ่มเล่นสำเร็จ")
            return True
        except:
            try:
                join_link = driver.find_element(By.CSS_SELECTOR, "a[data-testid='play-button']")
                join_link.click()
                logger.info("คลิก join link สำเร็จ")
                return True
            except:
                logger.warning("ไม่พบปุ่มเล่น อาจอยู่ในเกมแล้ว")
                return True
    except Exception as e:
        logger.error(f"Join game error: {e}")
        return False

# ===================== ตรวจจับหลุด =====================
def detect_kicked(driver, join_url):
    # ตรวจสอบว่า driver ยังทำงานอยู่
    try:
        driver.current_url
    except:
        return True  # driver ตาย
    # ตรวจสอบว่า redirect ไปหน้า lobby หรือยัง
    try:
        current = driver.current_url.lower()
        if "games" in current and "private" not in current:
            return True
    except:
        pass
    return False

def detect_kicked_process(roblox_process_name="RobloxPlayerBeta"):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if roblox_process_name.lower() in proc.info['name'].lower():
                return False  # ยังมี process
        except:
            continue
    return True  # process ไม่มี = หลุด

def detect_kicked_api(user_id):
    try:
        url = f"https://economy.roblox.com/v1/users/{user_id}/currency"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code == 200:
            return True  # ยังอยู่ในเกม (API ใช้งานได้)
    except:
        pass
    return False

# ===================== ตรวจสอบสถานะบัญชี =====================
def check_online(account):
    cookie = account['cookie']
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Cookie": f".ROBLOSECURITY={cookie}"}
        resp = requests.get("https://users.roblox.com/v1/users/authenticated", headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

# ===================== กระบวนการหลัก =====================
def run_account(account):
    name = account['name']
    cookie = account['cookie']
    join_url = account.get('join_url', JOIN_URL)
    
    driver = None
    monitor_thread = None
    stop_event = threading.Event()
    
    def monitor():
        while not stop_event.is_set():
            time.sleep(CHECK_INTERVAL)
            try:
                if driver:
                    if detect_kicked(driver, join_url):
                        logger.info(f"{name}: ตรวจจับว่าหลุด (URL เปลี่ยน)")
                        stop_event.set()
                        break
            except:
                pass
            if USE_PROCESS_DETECT:
                if detect_kicked_process():
                    logger.info(f"{name}: ตรวจจับว่าหลุด (process หาย)")
                    stop_event.set()
                    break
            if USE_API_CHECK:
                user_data = check_online(account)
                if not user_data:
                    logger.info(f"{name}: ตรวจจับว่าหลุด (API ไม่ตอบ)")
                    stop_event.set()
                    break
    
    def login_and_join():
        nonlocal driver
        for attempt in range(MAX_RETRIES):
            logger.info(f"{name}: พยายามเชื่อมต่อครั้งที่ {attempt+1}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            try:
                driver = create_driver()
                if not inject_cookie(driver, cookie):
                    logger.error(f"{name}: inject cookie ล้มเหลว")
                    continue
                time.sleep(2)
                if try_join_game(driver, join_url):
                    logger.info(f"{name}: เข้าเกมสำเร็จ")
                    return True
            except Exception as e:
                logger.error(f"{name}: error {e}")
                time.sleep(5)
        return False
    
    if login_and_join():
        stop_event.clear()
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        # รอจนกว่าจะหลุด
        stop_event.wait()
        logger.info(f"{name}: กำลังรีเชื่อมต่อ...")
        time.sleep(3)
        # ปิด driver เก่า
        if driver:
            try:
                driver.quit()
            except:
                pass
        # รีเชื่อมต่อ
        run_account(account)
    else:
        logger.error(f"{name}: เชื่อมต่อล้มเหลวหลังจาก {MAX_RETRIES} ครั้ง")

# ===================== ฟังก์ชันหลัก =====================
def main():
    logger.info("เริ่มต้น MyRejoinTool v2.0")
    
    accounts = load_accounts()
    logger.info(f"โหลด {len(accounts)} บัญชี")
    
    threads = []
    for acc in accounts:
        t = threading.Thread(target=run_account, args=(acc,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(2)  # เว้นระหว่างบัญชี
    
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("ผู้ใช้กด Ctrl+C หยุดการทำงาน")
        sys.exit(0)

if __name__ == "__main__":
    main()
PYEOF

chmod +x main.py

# สร้างไฟล์ accounts.json ตัวอย่าง
if [ ! -f accounts.json ]; then
    cat > accounts.json << 'JSONEOF'
[
    {
        "name": "บัญชี1",
        "cookie": "ใส่_._ROBLOSECURITY_ตรงนี้",
        "join_url": "https://www.roblox.com/games/123456789/example-game"
    },
    {
        "name": "บัญชี2",
        "cookie": "ใส่_._ROBLOSECURITY_ตรงนี้",
        "join_url": "https://www.roblox.com/games/123456789/example-game"
    }
]
JSONEOF
    echo "สร้างไฟล์ accounts.json แล้ว กรุณาใส่คุกกี้ให้ถูกต้อง"
fi

echo ""
echo "========================================="
echo "  ติดตั้งเสร็จสมบูรณ์!"
echo "  วิธีใช้งาน:"
echo "  1. แก้ไข accounts.json ใส่คุกกี้ .ROBLOSECURITY"
echo "  2. เปลี่ยน join_url เป็นเกมที่ต้องการ"
echo "  3. รัน: python main.py"
echo "========================================="
