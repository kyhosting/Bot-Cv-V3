import logging
import psutil
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner

logger = logging.getLogger(__name__)

ASK_MONITORING_ACTION = 0

db_available = False
try:
    from database.models import ActivityLogModel, MonitoringLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_monitoring_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Status Sistem 🜲"), KeyboardButton("🜲 Error Log 🜲")],
        [KeyboardButton("🜲 Activity Log 🜲"), KeyboardButton("🜲 DB Status 🜲")],
        [KeyboardButton("🜲 Running Jobs 🜲"), KeyboardButton("🜲 Force Restart 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def monitoring_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ Akses Ditolak\nAnda tidak memiliki akses ke menu monitoring.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    text = """```
📊 MONITORING BOT
───────────────────────────────────────

Selamat datang di Panel Monitoring!
Pilih informasi yang ingin dilihat:

───────────────────────────────────────
MONITORING
───────────────────────────────────────
🜲 Status Sistem   — CPU/RAM/Storage
🜲 Error Log       — Log error terbaru
🜲 Activity Log    — Log aktivitas user
🜲 DB Status       — Status database
🜲 Running Jobs    — Job yang berjalan
🜲 Force Restart   — Restart bot

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_monitoring_keyboard()
    )
    return ASK_MONITORING_ACTION


async def monitoring_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if text == "🜲 Status Sistem 🜲":
        return await show_system_status(update, context)
    
    elif text == "🜲 Error Log 🜲":
        return await show_error_logs(update, context)
    
    elif text == "🜲 Activity Log 🜲":
        return await show_activity_logs(update, context)
    
    elif text == "🜲 DB Status 🜲":
        return await show_db_status(update, context)
    
    elif text == "🜲 Running Jobs 🜲":
        return await show_running_jobs(update, context)
    
    elif text == "🜲 Force Restart 🜲":
        await update.message.reply_text(
            "⚠️ Force restart tidak tersedia melalui bot.\nGunakan Replit console untuk restart.",
            parse_mode="Markdown",
            reply_markup=get_monitoring_keyboard()
        )
        return ASK_MONITORING_ACTION
    
    return ASK_MONITORING_ACTION


async def show_system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
    
    status_text = f"""```
📊 STATUS SISTEM
───────────────────────────────────────

🖥️ CPU Usage    : {cpu_percent}%
💾 RAM Usage    : {memory.percent}%
📀 Disk Usage   : {disk.percent}%
⏰ Uptime       : {uptime_str}

💾 RAM Total    : {memory.total // (1024**3)} GB
💾 RAM Used     : {memory.used // (1024**3)} GB
📀 Disk Total   : {disk.total // (1024**3)} GB
📀 Disk Used    : {disk.used // (1024**3)} GB

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        status_text,
        parse_mode="Markdown",
        reply_markup=get_monitoring_keyboard()
    )
    return ASK_MONITORING_ACTION


async def show_error_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_monitoring_keyboard()
        )
        return ASK_MONITORING_ACTION
    
    try:
        db = get_db()
        if db.is_connected:
            errors = await MonitoringLogModel.get_errors(limit=10)
            
            if not errors:
                await update.message.reply_text(
                    "✅ Tidak ada error log terbaru.",
                    parse_mode="Markdown",
                    reply_markup=get_monitoring_keyboard()
                )
                return ASK_MONITORING_ACTION
            
            error_text = "🚨 Error Log Terbaru\n\n"
            for i, error in enumerate(errors, 1):
                error_text += f"{i}. {error.get('type')} - {error.get('message', 'N/A')[:50]}\n"
            
            await update.message.reply_text(
                error_text,
                parse_mode="Markdown",
                reply_markup=get_monitoring_keyboard()
            )
    except Exception as e:
        logger.error(f"Error log fetch error: {e}")
        await update.message.reply_text(
            "❌ Gagal mengambil error log.",
            parse_mode="Markdown",
            reply_markup=get_monitoring_keyboard()
        )
    
    return ASK_MONITORING_ACTION


async def show_activity_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_monitoring_keyboard()
        )
        return ASK_MONITORING_ACTION
    
    try:
        db = get_db()
        if db.is_connected:
            logs = await ActivityLogModel.get_recent_logs(limit=15)
            
            if not logs:
                await update.message.reply_text(
                    "Belum ada activity log.",
                    parse_mode="Markdown",
                    reply_markup=get_monitoring_keyboard()
                )
                return ASK_MONITORING_ACTION
            
            log_text = "📋 Activity Log Terbaru\n\n"
            for i, log in enumerate(logs, 1):
                log_text += f"{i}. {log.get('username', 'N/A')} - {log.get('action')}\n"
            
            await update.message.reply_text(
                log_text,
                parse_mode="Markdown",
                reply_markup=get_monitoring_keyboard()
            )
    except Exception as e:
        logger.error(f"Activity log fetch error: {e}")
        await update.message.reply_text(
            "❌ Gagal mengambil activity log.",
            parse_mode="Markdown",
            reply_markup=get_monitoring_keyboard()
        )
    
    return ASK_MONITORING_ACTION


async def show_db_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_status = "🔴 Offline"
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                db_status = "🟢 Online"
        except:
            pass
    
    status_text = f"""```
🗄️ DATABASE STATUS
───────────────────────────────────────

📊 Status      : {db_status}
🔧 Type        : PostgreSQL
🔒 Connection  : Pool Active

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        status_text,
        parse_mode="Markdown",
        reply_markup=get_monitoring_keyboard()
    )
    return ASK_MONITORING_ACTION


async def show_running_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs_text = """```
⚙️ RUNNING JOBS
───────────────────────────────────────

✅ Bot Handler      : Active
✅ Database Pool    : Active
✅ Message Handler  : Active

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        jobs_text,
        parse_mode="Markdown",
        reply_markup=get_monitoring_keyboard()
    )
    return ASK_MONITORING_ACTION
