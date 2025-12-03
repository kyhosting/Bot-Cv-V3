import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import is_owner, BOT_NAME, BOT_CREATOR

logger = logging.getLogger(__name__)

db_available = False
try:
    from database.models import UserModel, VIPAccessModel, VVIPAccessModel
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
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} hari {hours} jam"
    elif hours > 0:
        return f"{hours} jam {minutes} menit"
    else:
        return f"{minutes} menit"


async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    name = user.full_name or "User"
    username = f"@{user.username}" if user.username else "Tidak ada"
    
    role = "⭐ Reguler"
    expired_str = "—"
    remaining = "—"
    limit_remaining = 10
    total_ops = 0
    daily_used = 0
    
    if is_owner(user_id):
        role = "👑 OWNER"
        limit_remaining = "∞"
    elif db_available:
        try:
            db_user = await UserModel.get_by_id(user_id)
            
            if db_user:
                user_role = db_user.get("role", "reguler")
                total_ops = db_user.get("total_requests", 0)
                daily_limit = db_user.get("daily_limit", 10)
                daily_used = db_user.get("daily_used", 0)
                limit_remaining = max(0, daily_limit - daily_used)
                
                if user_role == "vvip":
                    role = "👑 VVIP"
                    vvip_access = await VVIPAccessModel.get_access(user_id)
                    if vvip_access and vvip_access.get("status") == "active":
                        exp = vvip_access.get("expired_at")
                        if exp:
                            expired_str = exp.strftime("%d-%m-%Y %H:%M")
                            remaining = format_remaining_time(exp)
                        limit_remaining = vvip_access.get("daily_limit", 100) - daily_used
                elif user_role == "vip":
                    role = "💎 VIP"
                    vip_access = await VIPAccessModel.get_access(user_id)
                    if vip_access and vip_access.get("status") == "active":
                        exp = vip_access.get("expired_at")
                        if exp:
                            expired_str = exp.strftime("%d-%m-%Y %H:%M")
                            remaining = format_remaining_time(exp)
                        limit_remaining = vip_access.get("daily_limit", 50) - daily_used
        except Exception as e:
            logger.error(f"Error checking status: {e}")
    else:
        from commands.vip_system import get_user_role, get_user_data, update_user_data, OWNER_ID
        from commands.menu import get_main_menu_keyboard
        
        user_data = get_user_data(user_id)
        if not user_data:
            update_user_data(user_id, {
                "name": name,
                "username": username,
                "role": "FREE",
                "expired": None,
                "total_operations": 0
            })
            user_data = get_user_data(user_id)
        
        role_old = get_user_role(user_id)
        total_ops = user_data.get("total_operations", 0)
        
        expired = user_data.get("expired")
        if expired:
            if isinstance(expired, str):
                try:
                    expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
                except:
                    expired = None
        
        if expired and expired > datetime.now():
            expired_str = expired.strftime("%d-%m-%Y %H:%M")
            remaining_days = (expired - datetime.now()).days
            remaining = f"{remaining_days} hari"
        
        if role_old == "OWNER":
            role = "👑 OWNER"
            limit_remaining = "∞"
        elif role_old == "PREMIUM":
            role = "👑 VVIP"
        elif role_old == "VIP":
            role = "💎 VIP"
        else:
            role = "⭐ Reguler"
    
    status_text = f"""```
📊 STATUS AKUN
───────────────────────────────────────

👤 INFORMASI AKUN
───────────────────────────────────────
• Nama         : {name}
• ID           : {user_id}
• Username     : {username}

💎 STATUS MEMBERSHIP
───────────────────────────────────────
• Role         : {role}
• Masa Aktif   : {expired_str}
• Sisa Waktu   : {remaining}

📊 STATISTIK
───────────────────────────────────────
• Total Request  : {total_ops}
• Limit Hari Ini : {limit_remaining}
• Digunakan      : {daily_used}

───────────────────────────────────────
{BOT_NAME} (BY {BOT_CREATOR})
───────────────────────────────────────
```"""
    
    from commands.menu import get_main_menu_keyboard
    keyboard = get_main_menu_keyboard(user_id)
    
    await update.message.reply_text(
        status_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
