import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner

logger = logging.getLogger(__name__)

ASK_MAINTENANCE_ACTION = 0

maintenance_mode = False

db_available = False
try:
    from database.models import BotStatusModel, ActivityLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


async def is_maintenance_mode():
    global maintenance_mode
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                status = await BotStatusModel.get("maintenance_mode")
                return status == "true"
        except:
            pass
    
    return maintenance_mode


async def set_maintenance_mode(enabled: bool):
    global maintenance_mode
    maintenance_mode = enabled
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                await BotStatusModel.set("maintenance_mode", "true" if enabled else "false")
        except:
            pass


async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if is_owner(update.effective_user.id):
        return False
    
    if await is_maintenance_mode():
        text = """```
⚙️ MAINTENANCE
───────────────────────────────────────

Bot sedang dalam perawatan. 
Mohon tunggu sebentar.

Silakan coba lagi dalam beberapa menit.

───────────────────────────────────────
```"""
        
        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )
        return True
    
    return False


def get_maintenance_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Maintenance ON 🜲"), KeyboardButton("🜲 Maintenance OFF 🜲")],
        [KeyboardButton("🜲 Status 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def maintenance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ Akses Ditolak\nAnda tidak memiliki akses ke menu maintenance.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    current_status = await is_maintenance_mode()
    status_str = "🔴 ON" if current_status else "🟢 OFF"
    
    text = f"""```
⚙️ MAINTENANCE MODE
───────────────────────────────────────

Status saat ini: {status_str}

Pilih aksi:

───────────────────────────────────────
PENGATURAN
───────────────────────────────────────
🜲 Maintenance ON   — Aktifkan mode maintenance
🜲 Maintenance OFF  — Nonaktifkan maintenance
🜲 Status           — Lihat status saat ini

───────────────────────────────────────
Catatan:
Saat maintenance ON, hanya owner yang 
bisa menggunakan bot.
User lain akan mendapat pesan maintenance.
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_maintenance_keyboard()
    )
    return ASK_MAINTENANCE_ACTION


async def maintenance_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if text == "🜲 Maintenance ON 🜲":
        await set_maintenance_mode(True)
        
        if db_available:
            try:
                db = get_db()
                if db.is_connected:
                    await ActivityLogModel.log(
                        user_id=user_id,
                        action="maintenance_on",
                        details={"enabled": True}
                    )
            except:
                pass
        
        await update.message.reply_text(
            "✅ Maintenance Mode AKTIF\n\nSemua user (kecuali owner) tidak bisa menggunakan bot.\nMereka akan melihat pesan maintenance.",
            parse_mode="Markdown",
            reply_markup=get_maintenance_keyboard()
        )
        return ASK_MAINTENANCE_ACTION
    
    elif text == "🜲 Maintenance OFF 🜲":
        await set_maintenance_mode(False)
        
        if db_available:
            try:
                db = get_db()
                if db.is_connected:
                    await ActivityLogModel.log(
                        user_id=user_id,
                        action="maintenance_off",
                        details={"enabled": False}
                    )
            except:
                pass
        
        await update.message.reply_text(
            "✅ Maintenance Mode NONAKTIF\n\nSemua user bisa menggunakan bot kembali.",
            parse_mode="Markdown",
            reply_markup=get_maintenance_keyboard()
        )
        return ASK_MAINTENANCE_ACTION
    
    elif text == "🜲 Status 🜲":
        current_status = await is_maintenance_mode()
        status_str = "🔴 ON" if current_status else "🟢 OFF"
        
        await update.message.reply_text(
            f"📊 Status Maintenance: {status_str}",
            parse_mode="Markdown",
            reply_markup=get_maintenance_keyboard()
        )
        return ASK_MAINTENANCE_ACTION
    
    return ASK_MAINTENANCE_ACTION
