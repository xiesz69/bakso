import os
import time
import subprocess
import requests
import threading
import select
import sys
import json
from datetime import datetime

# --- KONFIGURASI AWAL ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''

APPS_TO_MONITOR = ['com.termux', 'com.roblox.client'] 
PROCESS_WHITELIST = [
    'com.android.systemui', 'com.android.launcher3', 'com.android12.launcher3',
    'com.google.android.inputmethod', 'com.android.phone', 'com.google.android.gms', 'com.android.settings',
    'com.termux', 'system_server', 'zygote', 'surfaceflinger', 'init', 'su'
]

CHECK_INTERVAL = 30
is_monitoring = False
last_status = {}
last_hourly_report_hour = -1

CURRENT_VERSION = "2.4"
UPDATE_AVAILABLE = False
REMOTE_VERSION = ""

def check_update():
    global UPDATE_AVAILABLE, REMOTE_VERSION
    url = "https://raw.githubusercontent.com/xiesz69/bakso/main/monitor.py"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            for line in response.text.splitlines():
                if 'CURRENT_VERSION =' in line:
                    REMOTE_VERSION = line.split('"')[1]
                    if REMOTE_VERSION != CURRENT_VERSION:
                        UPDATE_AVAILABLE = True
                    break
    except: pass

def load_config():
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, APPS_TO_MONITOR, PROCESS_WHITELIST, is_monitoring
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                TELEGRAM_BOT_TOKEN = config.get('telegram_bot_token', TELEGRAM_BOT_TOKEN)
                TELEGRAM_CHAT_ID = config.get('telegram_chat_id', TELEGRAM_CHAT_ID)
                APPS_TO_MONITOR = config.get('apps_to_monitor', APPS_TO_MONITOR)
                PROCESS_WHITELIST = config.get('process_whitelist', PROCESS_WHITELIST)
                is_monitoring = config.get('is_monitoring', is_monitoring)
        except: pass

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'telegram_bot_token': TELEGRAM_BOT_TOKEN,
                'telegram_chat_id': TELEGRAM_CHAT_ID,
                'apps_to_monitor': APPS_TO_MONITOR,
                'process_whitelist': PROCESS_WHITELIST,
                'is_monitoring': is_monitoring
            }, f, indent=4)
    except: pass

# --- WARNA ---
R = "\033[91m" # Red
G = "\033[92m" # Green
Y = "\033[93m" # Yellow
B = "\033[94m" # Blue
C = "\033[96m" # Cyan
W = "\033[97m" # White
BOLD = "\033[1m"
RESET = "\033[0m"

def get_system_info():
    info = {
        'mem_total': 0, 'mem_avail': 0, 'mem_used': 0,
        'uptime': 0.0, 'cpu_usage': 0, 'cores': 1
    }
    try:
        info['cores'] = os.cpu_count() or 1
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if "MemTotal" in line: info['mem_total'] = int(line.split()[1]) // 1024
                if "MemAvailable" in line: info['mem_avail'] = int(line.split()[1]) // 1024
        info['mem_used'] = info['mem_total'] - info['mem_avail']
        
        with open('/proc/uptime', 'r') as f:
            info['uptime'] = float(f.readline().split()[0]) // 3600
            
        with open('/proc/loadavg', 'r') as f:
            load1 = float(f.read().split()[0])
            # Hitung persentase beban CPU relatif terhadap core, max 100% untuk awam
            usage = int((load1 / info['cores']) * 100)
            info['cpu_usage'] = min(usage, 100)
    except: pass
    return info

def get_app_uptime(package_name):
    try:
        # Mencoba mendapatkan uptime menggunakan ps -o etimes (detik aktif)
        output = subprocess.check_output(['ps', '-A', '-o', 'NAME,ETIMES'], stderr=subprocess.STDOUT).decode('utf-8').splitlines()
        for line in output:
            if package_name in line:
                parts = line.strip().split()
                # Pastikan kolom terakhir adalah angka (detik)
                uptime_sec = int(parts[-1])
                if uptime_sec < 60: return f"{uptime_sec} dtk"
                if uptime_sec < 3600: return f"{int(uptime_sec/60)} mnt"
                return f"{uptime_sec/3600:.1f} jam"
    except: pass
    return "0 mnt"

def send_telegram_msg(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try: requests.post(url, data=payload, timeout=10)
    except: pass

def is_app_running(package_name):
    try:
        output = subprocess.check_output(['ps', '-A']).decode('utf-8')
        return package_name in output
    except: return False

def clear_ram_smart():
    try:
        os.system("sync")
        os.system("su -c 'echo 3 > /proc/sys/vm/drop_caches' > /dev/null 2>&1")
        output = subprocess.check_output(['ps', '-A']).decode('utf-8').splitlines()
        for line in output:
            parts = line.split()
            if len(parts) < 9: continue
            proc = parts[8]
            if '.' in proc:
                if not any(safe in proc for safe in PROCESS_WHITELIST + APPS_TO_MONITOR):
                    os.system(f"am force-stop {proc} > /dev/null 2>&1")
    except: pass

def monitor_loop():
    global is_monitoring, last_status, last_hourly_report_hour
    try:
        while True:
            if is_monitoring:
                now = datetime.now()
                curr_hour = now.hour
                curr_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

                # Laporan Rutin Setiap Jam
                if last_hourly_report_hour != curr_hour:
                    if last_hourly_report_hour != -1: # Jangan kirim saat baru start pertama kali (opsional)
                        stats = get_system_info()
                        live_apps = [(app, get_app_uptime(app)) for app in APPS_TO_MONITOR if is_app_running(app)]
                        
                        msg = (
                            "📊 *LAPORAN STATUS BERKALA*\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"⏰ *Waktu:* `{curr_time_str}`\n"
                            f"💾 *RAM:* `{stats['mem_used']}MB / {stats['mem_total']}MB`\n"
                            f"⚡ *Beban CPU:* `{stats['cpu_usage']}%`\n"
                            f"⏳ *Uptime Sistem:* `{stats['uptime']:.1f} jam`\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                            "📱 *Aplikasi Aktif:*\n"
                        )
                        if live_apps:
                            for app, uptime in live_apps:
                                msg += f"✅ `{app}` ({uptime})\n"
                        else:
                            msg += "❌ Tidak ada aplikasi target aktif\n"
                        msg += "━━━━━━━━━━━━━━━━━━━━━━"
                        
                        send_telegram_msg(msg)
                    last_hourly_report_hour = curr_hour

                # Cek Aplikasi Mati (Alert)
                for app in APPS_TO_MONITOR:
                    running = is_app_running(app)
                    if not running and last_status.get(app, True):
                        stats = get_system_info()
                        msg = (
                            "🔴 *PERINGATAN: APLIKASI MATI*\n"
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"📦 *Paket:* `{app}`\n"
                            f"⏰ *Waktu:* `{curr_time_str}`\n"
                            f"💾 *RAM:* `{stats['mem_used']}MB / {stats['mem_total']}MB`\n"
                            f"⏳ *Uptime Sistem:* `{stats['uptime']:.1f} jam`\n"
                            "━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        send_telegram_msg(msg)
                    last_status[app] = running
                
                clear_ram_smart()
            time.sleep(CHECK_INTERVAL)
    except: pass

def perform_update():
    os.system('clear')
    print(f"\n  {BOLD}{B}🔄 PROSES UPDATE{RESET}")
    print(f"  {C}==========================================={RESET}")
    try:
        print(f"  {W}Menarik data terbaru dari GitHub...{RESET}")
        repo_path = os.path.dirname(os.path.abspath(__file__))
        output = subprocess.check_output(['git', '-C', repo_path, 'pull'], stderr=subprocess.STDOUT).decode('utf-8')
        
        print(f"\n  {G}HASIL:{RESET}\n  {W}{output}{RESET}")
        print(f"  {G}Update selesai! Silakan jalankan ulang script.{RESET}")
        os.system("termux-wake-unlock")
        input("\n  Tekan Enter untuk keluar...")
        sys.exit(0)
    except Exception as e:
        print(f"\n  {R}Gagal memperbarui: {e}{RESET}")
        input("\n  Tekan Enter...")

def get_ram_color(percent):
    if percent < 60: return G
    if percent < 85: return Y
    return R

def show_menu():
    global is_monitoring, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, last_status
    
    while True:
        os.system('clear')
        stats = get_system_info()
        ram_p = (stats['mem_used'] / stats['mem_total'] * 100) if stats['mem_total'] > 0 else 0
        
        live_apps = [app for app in APPS_TO_MONITOR if is_app_running(app)]
        dead_apps = [app for app in APPS_TO_MONITOR if app not in live_apps]
        
        status_tag = f"{G}{BOLD}ACTIVE{RESET}" if is_monitoring else f"{R}{BOLD}INACTIVE{RESET}"
        
        LINE = f"{C}==========================================={RESET}"
        print(LINE)
        print(f"  {BOLD}{W}🚀 ANDROID SYSTEM MONITOR PRO v{CURRENT_VERSION}{RESET}")
        if UPDATE_AVAILABLE:
            print(f"  {R}{BOLD}✨ UPDATE TERSEDIA: v{REMOTE_VERSION}{RESET}")
            print(f"  {Y}Gunakan 'git pull' untuk memperbarui{RESET}")
        print(LINE)
        print(f"  {BOLD}STATUS:{RESET} {status_tag} | {BOLD}CPU:{RESET} {stats['cpu_usage']}%")
        print(f"  {BOLD}UPTIME SYSTEM:{RESET} {stats['uptime']:.1f} Hours")
        print(LINE)
        print(f"  {BOLD}DASHBOARD RAM{RESET}")
        
        # RAM Progress Bar
        bar_len = 20
        filled = int(bar_len * ram_p / 100)
        bar = (f"{get_ram_color(ram_p)}█" * filled) + (f"{W}░" * (bar_len - filled))
        print(f"  [{bar}{RESET}] {get_ram_color(ram_p)}{ram_p:.1f}%{RESET}")
        print(f"  {W}Used:{RESET} {stats['mem_used']}MB  {W}Free:{RESET} {stats['mem_avail']}MB  {W}Total:{RESET} {stats['mem_total']}MB")
        
        print(LINE)
        print(f"  {BOLD}MONITORING APPS{RESET} ({len(APPS_TO_MONITOR)})")
        print(f"  {G}● {RESET}{len(live_apps)} Online   {R}● {RESET}{len(dead_apps)} Offline")
        print(LINE)
        
        print(f"\n{BOLD}{B}  [ MENU UTAMA ]{RESET} (Refresh 10s)")
        print(f"  {C}1.{RESET} {W}Toggle Monitor (On/Off){RESET}")
        print(f"  {C}2.{RESET} {W}Manajemen Aplikasi{RESET}")
        print(f"  {C}3.{RESET} {W}Manajemen Whitelist{RESET}")
        print(f"  {C}4.{RESET} {W}Konfigurasi Telegram{RESET}")
        print(f"  {C}5.{RESET} {W}Lihat Status Detail{RESET}")
        print(f"  {C}6.{RESET} {W}Update Script{RESET}")
        print(f"  {R}0. Keluar{RESET}")
        
        print(f"\n{B}  >> Pilih opsi: {RESET}", end="", flush=True)

        ready, _, _ = select.select([sys.stdin], [], [], 10)
        
        if ready:
            choice = sys.stdin.readline().strip()
            
            if choice == '1':
                is_monitoring = not is_monitoring
                save_config()
            elif choice == '2':
                print(f"\n  {B}[1]{RESET} Tambah  {B}[2]{RESET} Hapus")
                sub = input("  >> ")
                if sub == '1':
                    pkg = input("  Masukkan Nama Paket: ").strip()
                    if pkg: 
                        APPS_TO_MONITOR.append(pkg)
                        last_status[pkg] = True
                        save_config()
                elif sub == '2':
                    for i, a in enumerate(APPS_TO_MONITOR): print(f"  {i+1}. {a}")
                    try:
                        idx = int(input("  Hapus No: ")) - 1
                        if 0 <= idx < len(APPS_TO_MONITOR): 
                            app = APPS_TO_MONITOR.pop(idx)
                            last_status.pop(app, None)
                            save_config()
                    except: pass
            elif choice == '3':
                print(f"\n  {B}[1]{RESET} Tambah  {B}[2]{RESET} Hapus")
                sub = input("  >> ")
                if sub == '1':
                    pkg = input("  Masukkan Nama Paket: ").strip()
                    if pkg: 
                        PROCESS_WHITELIST.append(pkg)
                        save_config()
                elif sub == '2':
                    for i, a in enumerate(PROCESS_WHITELIST): print(f"  {i+1}. {a}")
                    try:
                        idx = int(input("  Hapus No: ")) - 1
                        if 0 <= idx < len(PROCESS_WHITELIST): 
                            PROCESS_WHITELIST.pop(idx)
                            save_config()
                    except: pass
            elif choice == '4':
                print(f"\n  {BOLD}KONFIGURASI TELEGRAM{RESET}")
                print(f"  Current Token: {TELEGRAM_BOT_TOKEN if TELEGRAM_BOT_TOKEN else '(Belum diatur)'}")
                print(f"  Current Chat ID: {TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID else '(Belum diatur)'}")
                
                t = input(f"\n  Input Token baru (Enter skip): ").strip()
                c = input(f"  Input Chat ID baru (Enter skip): ").strip()
                if t: TELEGRAM_BOT_TOKEN = t
                if c: TELEGRAM_CHAT_ID = c
                if t or c: save_config()
            elif choice == '5':
                print(f"\n{BOLD}Daftar Pantau:{RESET}"); print(", ".join(APPS_TO_MONITOR))
                print(f"\n{BOLD}Daftar Whitelist:{RESET}"); print(", ".join(PROCESS_WHITELIST))
                input("\nTekan Enter...")
            elif choice == '6':
                perform_update()
            elif choice == '0':
                os.system("termux-wake-unlock")
                print(f"\n{G}Terima kasih telah menggunakan Monitor Pro!{RESET}")
                break
        else:
            continue

if __name__ == "__main__":
    load_config()
    last_status = {app: True for app in APPS_TO_MONITOR}
    
    threading.Thread(target=check_update, daemon=True).start()
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

    os.system("termux-wake-lock")
    show_menu()