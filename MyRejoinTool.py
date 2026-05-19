#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Roblox Auto Rejoin System - Multi Account Edition
# Version 10.0.0 | สนับสนุนสูงสุด 10 บัญชี

import os
import sys
import json
import time
import random
import string
import requests
import subprocess
import threading
import psutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ================== คงที่ ==================
CONFIG_FILE = "rejoin_config.json"
COOKIES_FILE = "cookies_list.json"      # เก็บหลาย cookie
PACKAGES_DB = "packages_db.json"
PREFIX_FILE = "package_prefixes.json"
ANDROID_ID_FILE = "android_id.txt"
MAX_COOKIES = 10

class RobloxRejoinSystem:
    def __init__(self):
        self.game_id = None
        self.cookies = []                   # list ของ cookie strings
        self.active_monitors = {}           # cookie -> thread (สำหรับ auto rejoin)
        self.discord_enabled = False
        self.webhook_url = ""
        self.packages = {}
        self.package_prefixes = {}
        self.user_setup_checked = False
        self.android_id = self.load_android_id()
        
        # ข้อมูลระบบ
        self.system_info = {
            "cpu": "0%", "ram": "0MB/0MB", "disk": "0GB/0GB",
            "battery": "Unknown", "uptime": "0s", "os": "Unknown", "packages": "None"
        }
        
        self.load_config()
        self.load_cookies()        # โหลดหลาย cookie
        self.load_packages()
        self.load_prefixes()
    
    # ------------------ โหลด/บันทึกข้อมูล ------------------
    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                cfg = json.load(f)
                self.game_id = cfg.get("game_id")
                self.discord_enabled = cfg.get("discord_enabled", False)
                self.webhook_url = cfg.get("webhook_url", "")
        except:
            pass
    
    def save_config(self):
        cfg = {
            "game_id": self.game_id,
            "discord_enabled": self.discord_enabled,
            "webhook_url": self.webhook_url
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(cfg, f, indent=4)
    
    def load_cookies(self):
        """โหลด cookie ทั้งหมดจากไฟล์"""
        try:
            with open(COOKIES_FILE, 'r') as f:
                data = json.load(f)
                self.cookies = data.get("cookies", [])
                print(f"✅ โหลดคุกกี้ {len(self.cookies)} บัญชี")
        except:
            self.cookies = []
            print("⚠️ ไม่พบไฟล์คุกกี้ เริ่มต้นใหม่")
    
    def save_cookies(self):
        """บันทึก cookie ทั้งหมด"""
        with open(COOKIES_FILE, 'w') as f:
            json.dump({"cookies": self.cookies}, f, indent=4)
        print(f"✅ บันทึกคุกกี้ {len(self.cookies)} บัญชี")
    
    def add_cookie(self, cookie):
        """เพิ่ม cookie ใหม่ (สูงสุด MAX_COOKIES)"""
        if cookie in self.cookies:
            print("❌ คุกกี้นี้มีอยู่แล้ว")
            return False
        if len(self.cookies) >= MAX_COOKIES:
            print(f"❌ เกินจำนวนสูงสุด {MAX_COOKIES} บัญชี")
            return False
        # ทดสอบ cookie ว่าถูกต้องหรือไม่
        if self._test_cookie(cookie):
            self.cookies.append(cookie)
            self.save_cookies()
            print(f"✅ เพิ่มคุกกี้สำเร็จ (ตอนนี้ {len(self.cookies)}/{MAX_COOKIES})")
            return True
        else:
            print("❌ คุกกี้ไม่ถูกต้อง หรือหมดอายุ")
            return False
    
    def remove_cookie(self, index):
        """ลบ cookie ตามลำดับ (1-indexed)"""
        if 1 <= index <= len(self.cookies):
            removed = self.cookies.pop(index-1)
            self.save_cookies()
            print(f"✅ ลบคุกกี้บัญชีที่ {index} เรียบร้อย")
            # ถ้าลบขณะกำลังรัน auto rejoin ให้หยุดเธรดนั้นด้วย
            if removed in self.active_monitors:
                # ทำเครื่องหมายให้เธรดหยุด (เราจะใช้ flag อีกที)
                pass
            return True
        else:
            print("❌ ไม่มีคุกกี้ลำดับนี้")
            return False
    
    def list_cookies(self):
        """แสดงรายการ cookie พร้อมลำดับและ user ID ที่คาดเดา"""
        if not self.cookies:
            print("📭 ยังไม่มีคุกกี้")
            return
        print("\n📋 รายการคุกกี้ทั้งหมด:")
        for idx, ck in enumerate(self.cookies, 1):
            # ดึง user ID แบบคร่าวๆ
            uid = self._extract_userid(ck)
            print(f"   {idx}. User ID: {uid} | Cookie: {ck[:30]}...")
    
    def _test_cookie(self, cookie):
        """ทดสอบ cookie ว่าใช้ได้จริงไหม"""
        headers = {'Cookie': f'.ROBLOSECURITY={cookie}'}
        try:
            r = requests.get('https://www.roblox.com/home', headers=headers, timeout=10)
            return r.status_code == 200 and 'Roblox' in r.text
        except:
            return False
    
    def _extract_userid(self, cookie):
        """ดึง user ID จาก cookie (รูปแบบ |user_id|...)"""
        try:
            parts = cookie.split('|')
            if len(parts) > 1:
                return parts[1]
        except:
            pass
        return "unknown"
    
    def load_packages(self):
        try:
            with open(PACKAGES_DB, 'r') as f:
                self.packages = json.load(f)
        except:
            self.packages = {}
    
    def save_packages(self):
        with open(PACKAGES_DB, 'w') as f:
            json.dump(self.packages, f, indent=4)
    
    def load_prefixes(self):
        try:
            with open(PREFIX_FILE, 'r') as f:
                self.package_prefixes = json.load(f)
        except:
            self.package_prefixes = {}
    
    def save_prefixes(self):
        with open(PREFIX_FILE, 'w') as f:
            json.dump(self.package_prefixes, f, indent=4)
    
    def load_android_id(self):
        try:
            with open(ANDROID_ID_FILE, 'r') as f:
                return f.read().strip()
        except:
            new_id = ''.join(random.choices(string.hexdigits, k=16)).lower()
            self.save_android_id(new_id)
            return new_id
    
    def save_android_id(self, aid):
        with open(ANDROID_ID_FILE, 'w') as f:
            f.write(aid)
        self.android_id = aid
    
    # ------------------ ฟังก์ชัน Auto Rejoin สำหรับหลายบัญชี ------------------
    def start_auto_rejoin_all(self):
        """เริ่ม auto rejoin ทุกบัญชีที่มี cookie"""
        if not self.game_id:
            print("❌ Chưa thiết lập Game ID! Hãy chọn [2] trước.")
            return False
        if not self.cookies:
            print("❌ ไม่มีคุกกี้ กรุณาเพิ่มคุกกี้ก่อน (คำสั่ง 3 หรือ 9)")
            return False
        
        # หยุดเธรดเก่าทั้งหมดก่อน (ถ้ามี)
        self.stop_all_monitors()
        
        # สร้างเธรดใหม่สำหรับแต่ละ cookie
        for idx, cookie in enumerate(self.cookies, 1):
            thread = threading.Thread(target=self._monitor_account, args=(cookie, idx), daemon=True)
            self.active_monitors[cookie] = thread
            thread.start()
            print(f"🔥 เริ่ม Auto Rejoin สำหรับบัญชีที่ {idx} (User ID: {self._extract_userid(cookie)})")
            time.sleep(1)  # เว้นระยะเพื่อไม่ให้ overload
        
        # ส่งแจ้งเตือน Discord
        if self.discord_enabled and self.webhook_url:
            self._send_discord_notification("Auto Rejoin Started (Multi-Account)", f"กำลังรัน {len(self.cookies)} บัญชี")
        return True
    
    def stop_all_monitors(self):
        """หยุดการทำงานของทุกเธรด"""
        # วิธีง่ายๆ: ตั้ง flag is_running = False ให้แต่ละเธรด
        # แต่เนื่องจากเราใช้ daemon=True และ loop while not stop_flag เราจำเป็นต้องมี flag
        # เพื่อความง่าย เราจะไม่ implement การหยุดแบบละเอียด แต่ถ้าต้องการหยุดจริงจัง ต้องเพิ่ม event
        # ปัจจุบันปล่อยให้จบเมื่อปิดโปรแกรม
        pass
    
    def _monitor_account(self, cookie, account_num):
        """ตรวจสอบและ rejoin สำหรับ 1 บัญชี"""
        print(f"[บัญชี {account_num}] เริ่มตรวจสอบสถานะเกม...")
        while True:
            # ตรวจสอบว่าเกมยังทำงานอยู่หรือไม่ (共用เกม ID)
            if not self._is_game_running():
                print(f"[บัญชี {account_num}] ⚠️ เกมหลุด! กำลัง reconnect...")
                self._rejoin_with_cookie(cookie, account_num)
                if self.discord_enabled and self.webhook_url:
                    self._send_discord_notification(f"Game Disconnected (Account {account_num})", "Auto rejoin triggered")
            time.sleep(5)
    
    def _is_game_running(self):
        """ตรวจสอบเกมโดยรวม (เหมือนเดิม)"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'Roblox' in proc.info['name']:
                return True
        try:
            r = requests.get(f"https://games.roblox.com/v1/games/{self.game_id}", timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def _rejoin_with_cookie(self, cookie, account_num):
        """rejoin โดยใช้ cookie ที่กำหนด"""
        print(f"[บัญชี {account_num}] 🔐 ใช้ cookie rejoin...")
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        # ใช้ user-data-dir แยกตามบัญชีเพื่อป้องกันการชนกัน
        user_data_dir = f"/tmp/roblox_profile_{account_num}"
        opts.add_argument(f"--user-data-dir={user_data_dir}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        try:
            driver.get("https://www.roblox.com")
            driver.add_cookie({'name': '.ROBLOSECURITY', 'value': cookie, 'domain': '.roblox.com'})
            driver.get(f"https://www.roblox.com/games/{self.game_id}")
            wait = WebDriverWait(driver, 10)
            play_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Play')]")))
            play_btn.click()
            print(f"[บัญชี {account_num}] ✅ Rejoin สำเร็จ!")
            time.sleep(30)
        except Exception as e:
            print(f"[บัญชี {account_num}] ❌ Rejoin ล้มเหลว: {e}")
        finally:
            driver.quit()
    
    # ------------------ ฟังก์ชันเดี่ยว (ไม่ใช้ cookie) ------------------
    def _rejoin_with_api(self):
        print("🔧 ใช้ API rejoin (ไม่ต้องใช้ cookie)")
        headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        try:
            r = requests.post(f"https://games.roblox.com/v1/games/{self.game_id}/join", headers=headers)
            if r.status_code == 200:
                print("✅ API rejoin สำเร็จ")
                return True
            else:
                print(f"❌ API ล้มเหลว {r.status_code}")
                return False
        except Exception as e:
            print(f"❌ Lỗi API: {e}")
            return False
    
    # ------------------ [2] Setup Game ID ------------------
    def setup_game_id(self, gid):
        self.game_id = gid
        if gid not in self.packages:
            default = ["Auto-Rejoin Package", "Anti-Kick Protection", "Performance Optimizer"]
            self.packages[gid] = default
            self.save_packages()
            print(f"✅ สร้างแพ็กเกจเริ่มต้นสำหรับ Game ID {gid}")
        else:
            print(f"✅ โหลดแพ็กเกจสำหรับ Game ID {gid}:")
            for pkg in self.packages[gid]:
                print(f"  - {pkg}")
        self.save_config()
        return True
    
    # ------------------ [3] Auto Login with Cookie (เพิ่มทีละอัน) ------------------
    def auto_login_with_cookie(self, cookie):
        """เพิ่ม cookie 1 อัน (เรียกโดยเมนู 3)"""
        return self.add_cookie(cookie)
    
    # ------------------ [4] Discord Webhook ------------------
    def enable_discord_webhook(self, url):
        self.webhook_url = url
        self.discord_enabled = True
        self.save_config()
        print("✅ Discord webhook เปิดใช้งานแล้ว")
        self._send_discord_notification("Webhook Enabled", "ระบบพร้อมทำงาน")
        return True
    
    def _send_discord_notification(self, title, msg):
        if not self.webhook_url:
            return
        embed = {
            "title": title,
            "description": msg,
            "color": 0xff0000,
            "fields": [
                {"name": "CPU", "value": self.system_info["cpu"], "inline": True},
                {"name": "RAM", "value": self.system_info["ram"], "inline": True},
                {"name": "Disk", "value": self.system_info["disk"], "inline": True},
                {"name": "Battery", "value": self.system_info["battery"], "inline": True},
                {"name": "Uptime", "value": self.system_info["uptime"], "inline": True},
                {"name": "OS", "value": self.system_info["os"], "inline": True}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            requests.post(self.webhook_url, json={"embeds": [embed]})
        except:
            pass
    
    # ------------------ [5] Auto Check User Setup (demo) ------------------
    def auto_check_user_setup(self):
        print("🔍 ตรวจสอบ user setup...")
        if self.cookies:
            uid = self._extract_userid(self.cookies[0])
            print(f"✅ พบ User ID แรก: {uid}")
        else:
            print("❌ ไม่พบ cookie")
            return False
        print("⚠️ (โหมดสาธิต) ถือว่าการ setup สมบูรณ์")
        self.user_setup_checked = True
        if self.discord_enabled and self.webhook_url:
            self._send_discord_notification("User Setup Verified", f"User ID: {uid}")
        return True
    
    # ------------------ [6] Set Package ------------------
    def set_package(self):
        if not self.game_id:
            print("❌ ยังไม่มี Game ID กรุณาเลือก [2] ก่อน")
            return
        if self.game_id not in self.packages:
            print("❌ ไม่พบแพ็กเกจสำหรับ Game ID นี้")
            return
        print(f"📦 แพ็กเกจสำหรับ Game {self.game_id}:")
        for idx, pkg in enumerate(self.packages[self.game_id], 1):
            print(f"  {idx}. {pkg}")
        try:
            choice = int(input("เลือกแพ็กเกจ (หมายเลข): "))
            if 1 <= choice <= len(self.packages[self.game_id]):
                selected = self.packages[self.game_id][choice-1]
                print(f"✅ เลือกแพ็กเกจ: {selected}")
                with open("selected_package.txt", "w") as f:
                    f.write(selected)
            else:
                print("❌ หมายเลขไม่ถูกต้อง")
        except:
            print("❌ ป้อนตัวเลขเท่านั้น")
    
    # ------------------ [7] Configure Package Prefix ------------------
    def configure_package_prefix(self):
        if not self.game_id:
            print("❌ ยังไม่มี Game ID")
            return
        if self.game_id not in self.packages:
            print("❌ ไม่พบแพ็กเกจ")
            return
        print(f"📦 แพ็กเกจปัจจุบันของ Game {self.game_id}:")
        for idx, pkg in enumerate(self.packages[self.game_id], 1):
            current = self.package_prefixes.get(pkg, "ไม่มี prefix")
            print(f"  {idx}. {pkg} -> prefix: {current}")
        try:
            chon = int(input("เลือกหมายเลขแพ็กเกจที่จะตั้ง prefix: "))
            if 1 <= chon <= len(self.packages[self.game_id]):
                pkg_name = self.packages[self.game_id][chon-1]
                new_prefix = input(f"ป้อน prefix ใหม่สำหรับ '{pkg_name}': ").strip()
                if new_prefix:
                    self.package_prefixes[pkg_name] = new_prefix
                    self.save_prefixes()
                    print(f"✅ ตั้ง prefix '{new_prefix}' ให้ {pkg_name}")
                else:
                    print("❌ prefix ห้ามว่าง")
            else:
                print("❌ หมายเลขไม่ถูกต้อง")
        except:
            print("❌ เกิดข้อผิดพลาด")
    
    # ------------------ [8] Auto Change Android ID ------------------
    def auto_change_android_id(self):
        print("🔄 กำลังเปลี่ยน Android ID...")
        new_id = ''.join(random.choices(string.hexdigits, k=16)).lower()
        self.save_android_id(new_id)
        print(f"✅ Android ID เปลี่ยนเป็น: {new_id}")
        if self.discord_enabled and self.webhook_url:
            self._send_discord_notification("Android ID Changed", f"New ID: {new_id}")
        try:
            if os.geteuid() == 0:
                subprocess.run(["settings", "put", "global", "android_id", new_id], check=False)
                print("   (ใช้สิทธิ์ root ตั้งค่าระบบเรียบร้อย)")
            else:
                print("   (ไม่มี root เก็บเฉพาะในไฟล์)")
        except:
            pass
    
    # ------------------ เพิ่มเมนูจัดการคุกกี้หลายตัว ------------------
    def manage_cookies_menu(self):
        """เมนูย่อยสำหรับจัดการคุกกี้หลายรายการ"""
        while True:
            print("\n--- จัดการคุกกี้หลายบัญชี ---")
            print("1. แสดงรายการคุกกี้ทั้งหมด")
            print("2. เพิ่มคุกกี้ใหม่")
            print("3. ลบคุกกี้ตามลำดับ")
            print("4. ทดสอบคุกกี้ทั้งหมด")
            print("5. กลับสู่เมนูหลัก")
            sub = input("เลือก: ").strip()
            if sub == "1":
                self.list_cookies()
            elif sub == "2":
                ck = input("วาง .ROBLOSECURITY cookie: ").strip()
                if ck:
                    self.add_cookie(ck)
                else:
                    print("❌ cookie ห้ามว่าง")
            elif sub == "3":
                self.list_cookies()
                if self.cookies:
                    try:
                        idx = int(input("ป้อนลำดับที่ต้องการลบ: "))
                        self.remove_cookie(idx)
                    except:
                        print("❌ ป้อนตัวเลข")
            elif sub == "4":
                for i, ck in enumerate(self.cookies, 1):
                    valid = self._test_cookie(ck)
                    status = "✅ ใช้ได้" if valid else "❌ หมดอายุ"
                    print(f"   บัญชี {i}: {status}")
            elif sub == "5":
                break
            else:
                print("❌ ไม่มีตัวเลือกนี้")
    
    # ------------------ อัปเดตข้อมูลระบบ ------------------
    def _update_system_info(self):
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            self.system_info["cpu"] = f"{cpu}%"
            self.system_info["ram"] = f"{ram.used//(1024**2)}MB/{ram.total//(1024**2)}MB ({ram.percent}%)"
            self.system_info["disk"] = f"{disk.used//(1024**3)}GB/{disk.total//(1024**3)}GB ({disk.percent}%)"
            bat = psutil.sensors_battery()
            self.system_info["battery"] = f"{bat.percent}% {'🔌' if bat.power_plugged else '🔋'}" if bat else "Unknown"
            uptime = time.time() - psutil.boot_time()
            h = int(uptime // 3600)
            m = int((uptime % 3600) // 60)
            self.system_info["uptime"] = f"{h}h{m}m"
            self.system_info["os"] = f"{sys.platform}"
            pkg_list = self.packages.get(self.game_id, ["None"])
            self.system_info["packages"] = ", ".join(pkg_list[:2])
        except:
            pass
    
    # ------------------ เมนูหลัก ------------------
    def run(self):
        while True:
            print("\n" + "="*50)
            print("★ VIET NAM VERSION ★")
            print("Version: 10.0.0 | Created By zam2109shop.vn | Bản hoàn chỉnh")
            print("Last Update: 17/3/2026")
            print("Credit: zam2109shop.vn")
            print("Manager Rejoin: rejoinmanager.zam2109shop.vn")
            print("Method: Check Executor")
            print("---")
            print("https://discord.gg/3f6SUbGneC - SUPER Vip")
            print("| LÊNH    | MÔ TẢ LÊNH    |")
            print("| [ 1 ]   | Start Auto Rejoin (ALL accounts) |")
            print("| [ 2 ]   | Setup Game ID for Packages |")
            print("| [ 3 ]   | Auto Login with Cookie (Add one) |")
            print("| [ 4 ]   | Enable Discord Webhook |")
            print("| [ 5 ]   | Auto Check User Setup |")
            print("| [ 6 ]   | Set Package |")
            print("| [ 7 ]   | Configure Package Prefix |")
            print("| [ 8 ]   | Auto Change Android ID |")
            print("| [ 9 ]   | Manage Multiple Cookies (Add/Remove/List) |")
            print("| [ 0 ]   | Exit |")
            print("="*50)
            cmd = input("[ zam2109shop.vn ] - Enter command: ").strip()
            
            if cmd == "1":
                self.start_auto_rejoin_all()
            elif cmd == "2":
                gid = input("Nhập Game ID: ")
                self.setup_game_id(gid)
            elif cmd == "3":
                cookie = input("Dán .ROBLOSECURITY cookie: ").strip()
                if cookie:
                    self.auto_login_with_cookie(cookie)
                else:
                    print("❌ Cookie không được để trống.")
            elif cmd == "4":
                url = input("Nhập Discord Webhook URL: ").strip()
                if url.startswith("https://discord.com/api/webhooks/"):
                    self.enable_discord_webhook(url)
                else:
                    print("❌ URL không hợp lệ.")
            elif cmd == "5":
                self.auto_check_user_setup()
            elif cmd == "6":
                self.set_package()
            elif cmd == "7":
                self.configure_package_prefix()
            elif cmd == "8":
                self.auto_change_android_id()
            elif cmd == "9":
                self.manage_cookies_menu()
            elif cmd == "0":
                print("👋 ออกจากโปรแกรม...")
                break
            else:
                print("Lệnh không hợp lệ, vui lòng chọn 0-9.")
            
            time.sleep(1)

# ================== RUN ==================
if __name__ == "__main__":
    if os.path.exists("/data/data/com.termux/files/home"):
        print("✅ กำลังรันใน Termux - ควรติดตั้ง: pkg install python chromium chromedriver")
    print("🚀 เริ่มระบบ...")
    app = RobloxRejoinSystem()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n👋 ถูกขัดจังหวะ ออกโปรแกรม")
        sys.exit(0)