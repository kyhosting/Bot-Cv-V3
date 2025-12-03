import logging
import os
import sys
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner, BOT_NAME, BOT_CREATOR

logger = logging.getLogger(__name__)

ASK_SISTEM_ACTION = 0

db_available = False
try:
    from database.models import BotStatusModel, ActivityLogModel, MonitoringLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_sistem_bot_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Status Bot 🜲"), KeyboardButton("🜲 Integrity Check 🜲")],
        [KeyboardButton("🜲 Debug Mode 🜲"), KeyboardButton("🜲 Reload Modules 🜲")],
        [KeyboardButton("🜲 Clear Cache 🜲"), KeyboardButton("🜲 System Info 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def sistem_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ Akses Ditolak\nAnda tidak memiliki akses ke menu Sistem Bot.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    text = """```
⚙️ SISTEM BOT
───────────────────────────────────────

Selamat datang di Panel Sistem Bot!
Kelola sistem bot dari sini.

───────────────────────────────────────
MENU SISTEM
───────────────────────────────────────
🜲 Status Bot      — Status keseluruhan bot
🜲 Integrity Check — Verifikasi integritas
🜲 Debug Mode      — Mode debugging
🜲 Reload Modules  — Reload module bot
🜲 Clear Cache     — Bersihkan cache
🜲 System Info     — Info sistem detail

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION


async def sistem_bot_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        return ConversationHandler.END
    
    if text == "🔙 KEMBALI 🔙":
        from commands.start import get_start_keyboard
        await update.message.reply_text(
            "Kembali ke menu utama.",
            parse_mode="Markdown",
            reply_markup=get_start_keyboard(user_id)
        )
        return ConversationHandler.END
    
    if text == "🜲 Status Bot 🜲":
        return await show_bot_status(update, context)
    
    elif text == "🜲 Integrity Check 🜲":
        return await integrity_check(update, context)
    
    elif text == "🜲 Debug Mode 🜲":
        return await toggle_debug_mode(update, context)
    
    elif text == "🜲 Reload Modules 🜲":
        return await reload_modules(update, context)
    
    elif text == "🜲 Clear Cache 🜲":
        return await clear_cache(update, context)
    
    elif text == "🜲 System Info 🜲":
        return await show_system_info(update, context)
    
    return ASK_SISTEM_ACTION


async def show_bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_status = "🔴 Offline"
    total_users = 0
    total_vip = 0
    total_vvip = 0
    total_groups = 0
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                db_status = "🟢 Online"
                from database.models import UserModel, VIPAccessModel, VVIPAccessModel, GroupSettingsModel
                total_users = await UserModel.count_total()
                total_vip = await VIPAccessModel.count_active()
                total_vvip = await VVIPAccessModel.count_active()
                total_groups = await GroupSettingsModel.count_groups()
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
    
    status_text = f"""```
🤖 STATUS BOT
───────────────────────────────────────

📛 Nama Bot    : {BOT_NAME}
👨‍💻 Creator     : {BOT_CREATOR}
🗄️ Database    : {db_status}

───────────────────────────────────────
📊 STATISTIK
───────────────────────────────────────
👥 Total User  : {total_users}
⭐ VIP Aktif   : {total_vip}
💎 VVIP Aktif  : {total_vvip}
👥 Total Grup  : {total_groups}

───────────────────────────────────────
✅ Bot Status  : Running
✅ Handler     : Active
✅ Polling     : Active

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        status_text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION


async def integrity_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Memulai integrity check...",
        parse_mode="Markdown"
    )
    
    checks = []
    all_passed = True
    
    required_files = [
        "main.py",
        "config.py",
        "commands/start.py",
        "commands/menu.py",
        "database/connection.py",
        "database/models.py"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            checks.append(f"✅ {file}")
        else:
            checks.append(f"❌ {file} - MISSING")
            all_passed = False
    
    creator_verified = False
    try:
        with open("commands/start.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "(BY @KIFZLDEV)" in content:
                creator_verified = True
                checks.append("✅ Creator verification")
            else:
                checks.append("❌ Creator verification - FAILED")
                all_passed = False
    except:
        checks.append("❌ Creator verification - ERROR")
        all_passed = False
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                checks.append("✅ Database connection")
            else:
                checks.append("❌ Database connection - FAILED")
                all_passed = False
        except:
            checks.append("❌ Database connection - ERROR")
            all_passed = False
    else:
        checks.append("⚠️ Database module not loaded")
    
    status_icon = "✅" if all_passed else "❌"
    status_text = "PASSED" if all_passed else "FAILED"
    
    result_text = f"""```
🔍 INTEGRITY CHECK
───────────────────────────────────────

{status_icon} Status: {status_text}

───────────────────────────────────────
HASIL PENGECEKAN
───────────────────────────────────────
"""
    
    for check in checks:
        result_text += f"{check}\n"
    
    result_text += """
───────────────────────────────────────
```"""
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                await ActivityLogModel.log(
                    user_id=update.effective_user.id,
                    action="integrity_check",
                    details={"passed": all_passed}
                )
        except:
            pass
    
    await update.message.reply_text(
        result_text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION


async def toggle_debug_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_level = logging.getLogger().level
    
    if current_level == logging.DEBUG:
        logging.getLogger().setLevel(logging.INFO)
        new_status = "OFF"
        new_level = "INFO"
    else:
        logging.getLogger().setLevel(logging.DEBUG)
        new_status = "ON"
        new_level = "DEBUG"
    
    text = f"""```
🔧 DEBUG MODE
───────────────────────────────────────

Status Debug : {new_status}
Log Level    : {new_level}

Debug mode telah di-toggle.
Log akan menampilkan lebih banyak detail.

───────────────────────────────────────
```"""
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                await BotStatusModel.set("debug_mode", new_status.lower())
                await ActivityLogModel.log(
                    user_id=update.effective_user.id,
                    action="debug_mode_toggle",
                    details={"status": new_status}
                )
        except:
            pass
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION


async def reload_modules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """```
🔄 RELOAD MODULES
───────────────────────────────────────

⚠️ Reload modules tidak tersedia secara 
   langsung melalui bot.

Untuk reload modules:
1. Gunakan Replit console
2. Restart workflow bot

Atau gunakan fitur Auto-Restart di Replit.

───────────────────────────────────────
```"""
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                await ActivityLogModel.log(
                    user_id=update.effective_user.id,
                    action="reload_modules_attempted",
                    details={}
                )
        except:
            pass
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION


async def clear_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import gc
    gc.collect()
    
    context.user_data.clear()
    context.bot_data.clear()
    
    text = """```
🧹 CLEAR CACHE
───────────────────────────────────────

✅ Python garbage collector executed
✅ User data cache cleared
✅ Bot data cache cleared

Cache berhasil dibersihkan!

───────────────────────────────────────
```"""
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                await ActivityLogModel.log(
                    user_id=update.effective_user.id,
                    action="clear_cache",
                    details={"success": True}
                )
        except:
            pass
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION


async def show_system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import platform
    import psutil
    
    python_version = platform.python_version()
    os_info = platform.system()
    
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
    
    text = f"""```
💻 SYSTEM INFO
───────────────────────────────────────

🐍 Python      : {python_version}
🖥️ OS          : {os_info}
⏰ Uptime      : {uptime_str}

───────────────────────────────────────
RESOURCE USAGE
───────────────────────────────────────
🖥️ CPU         : {cpu_percent}%
💾 RAM         : {memory.percent}%
📀 Disk        : {disk.percent}%

💾 RAM Used    : {memory.used // (1024**2)} MB
💾 RAM Total   : {memory.total // (1024**2)} MB
📀 Disk Used   : {disk.used // (1024**3)} GB
📀 Disk Total  : {disk.total // (1024**3)} GB

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_sistem_bot_keyboard()
    )
    return ASK_SISTEM_ACTION
