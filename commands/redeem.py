import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner

logger = logging.getLogger(__name__)

ASK_CODE = 0

db_available = False
try:
    from database.models import RedeemCodeModel, VIPAccessModel, VVIPAccessModel, ActivityLogModel, UserModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_cancel_keyboard():
    keyboard = [[KeyboardButton("❌ BATAL ❌")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def redeem_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """```
🎁 REDEEM CODE
───────────────────────────────────────

Masukkan kode redeem Anda untuk 
mengaktifkan VIP/VVIP.

───────────────────────────────────────
📌 Cara mendapatkan kode:
───────────────────────────────────────
• Hubungi admin/owner
• Ikuti event/promo
• Gabung grup VIP

Silakan masukkan kode:
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_CODE


async def redeem_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if text == "❌ BATAL ❌":
        from commands.start import get_start_keyboard
        await update.message.reply_text(
            "Redeem dibatalkan.",
            parse_mode="Markdown",
            reply_markup=get_start_keyboard(user_id)
        )
        return ConversationHandler.END
    
    code = text.strip().upper()
    
    from commands.menu import get_main_menu_keyboard
    keyboard = get_main_menu_keyboard(user_id)
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                result = await RedeemCodeModel.redeem(code, user_id)
                
                if result.get("success"):
                    await ActivityLogModel.log(
                        user_id=user_id,
                        action="redeem",
                        username=username,
                        details={"code": code, "type": result.get("type"), "duration": result.get("duration")}
                    )
                    
                    success_text = f"""```
🎉 REDEEM BERHASIL!
───────────────────────────────────────

🔑 Kode    : {code}
⭐ Akses   : {result.get('type', 'VIP').upper()}
🕒 Durasi  : {result.get('duration', 7)} hari

───────────────────────────────────────
Selamat menikmati fitur premium!
───────────────────────────────────────
```"""
                    
                    await update.message.reply_text(
                        success_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                else:
                    error_text = f"""```
❌ REDEEM GAGAL
───────────────────────────────────────

{result.get('message', 'Kode tidak valid')}

───────────────────────────────────────
```"""
                    
                    await update.message.reply_text(
                        error_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Redeem error: {e}")
    
    await update.message.reply_text(
        "❌ Database tidak tersedia. Silakan coba lagi nanti.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return ConversationHandler.END
