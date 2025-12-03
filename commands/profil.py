import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import is_owner, BOT_NAME, BOT_CREATOR
from utils.helpers import get_user_display_name

logger = logging.getLogger(__name__)

db_available = False
try:
    from database.models import UserModel, VIPAccessModel, VVIPAccessModel, ActivityLogModel
    db_available = True
except ImportError:
    pass


def format_remaining_time(expired_at):
    if expired_at is None:
        return "—"
    
    now = datetime.utcnow()
    if expired_at < now:
        return "Expired"
    
    diff = expired_at - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    
    if days > 0:
        return f"{days} hari {hours} jam"
    elif hours > 0:
        return f"{hours} jam"
    else:
        return "< 1 jam"


async def show_profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "Tidak ada"
    display_name = get_user_display_name(user)
    
    role = "⭐ Reguler"
    expired_str = "—"
    remaining = "—"
    total_requests = 0
    daily_limit = 10
    daily_used = 0
    join_date = "—"
    
    if is_owner(user_id):
        role = "👑 OWNER"
        daily_limit = "∞"
    elif db_available:
        try:
            db_user = await UserModel.get_by_id(user_id)
            
            if db_user:
                user_role = db_user.get("role", "reguler")
                total_requests = db_user.get("total_requests", 0)
                daily_limit = db_user.get("daily_limit", 10)
                daily_used = db_user.get("daily_used", 0)
                
                created = db_user.get("created_at")
                if created:
                    join_date = created.strftime("%d-%m-%Y")
                
                if user_role == "vvip":
                    role = "👑 VVIP"
                    vvip_access = await VVIPAccessModel.get_access(user_id)
                    if vvip_access and vvip_access.get("status") == "active":
                        exp = vvip_access.get("expired_at")
                        if exp:
                            expired_str = exp.strftime("%d-%m-%Y %H:%M")
                            remaining = format_remaining_time(exp)
                        daily_limit = vvip_access.get("daily_limit", 100)
                elif user_role == "vip":
                    role = "💎 VIP"
                    vip_access = await VIPAccessModel.get_access(user_id)
                    if vip_access and vip_access.get("status") == "active":
                        exp = vip_access.get("expired_at")
                        if exp:
                            expired_str = exp.strftime("%d-%m-%Y %H:%M")
                            remaining = format_remaining_time(exp)
                        daily_limit = vip_access.get("daily_limit", 50)
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
    
    limit_remaining = daily_limit if daily_limit == "∞" else max(0, daily_limit - daily_used)
    
    profil_text = f"""```
👤 PROFIL SAYA
───────────────────────────────────────

📍 INFORMASI PRIBADI
───────────────────────────────────────
• Nama       : {display_name}
• ID         : {user_id}
• Username   : {username}
• Bergabung  : {join_date}

💎 STATUS MEMBERSHIP
───────────────────────────────────────
• Status     : {role}
• Masa Aktif : {expired_str}
• Sisa Waktu : {remaining}

📊 STATISTIK PENGGUNAAN
───────────────────────────────────────
• Total Request : {total_requests}
• Limit Harian  : {daily_limit}
• Digunakan     : {daily_used}
• Tersisa       : {limit_remaining}

───────────────────────────────────────
{BOT_NAME} (BY {BOT_CREATOR})
───────────────────────────────────────
```"""
    
    from commands.start import get_start_keyboard
    keyboard = get_start_keyboard(user_id)
    
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos and photos.total_count > 0:
            await update.message.reply_photo(
                photo=photos.photos[0][0].file_id,
                caption=profil_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                profil_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error sending profile: {e}")
        await update.message.reply_text(
            profil_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
