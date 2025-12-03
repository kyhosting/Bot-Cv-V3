import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import is_owner, BOT_NAME, BOT_CREATOR, OWNER_IDS, REQUIRED_GROUPS

logger = logging.getLogger(__name__)

db_available = False
try:
    from database.models import UserModel, VIPAccessModel, VVIPAccessModel, ActivityLogModel, UserVerificationModel, GuildModeModel
    from database.connection import get_db
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


def get_start_keyboard(user_id, is_private: bool = True):
    from telegram import ReplyKeyboardMarkup, KeyboardButton
    
    if is_owner(user_id):
        keyboard = [
            [KeyboardButton("🜲 Menu Utama 🜲")],
            [KeyboardButton("🜲 Monitoring Bot 🜲"), KeyboardButton("🜲 Maintenance 🜲")],
            [KeyboardButton("🜲 Manajemen Grup 🜲"), KeyboardButton("🜲 Owner Panel 🜲")],
            [KeyboardButton("🜲 Pengaturan Grup 🜲"), KeyboardButton("🜲 Sistem Bot 🜲")]
        ]
    else:
        if is_private:
            keyboard = [
                [KeyboardButton("🜲 Menu Utama 🜲")],
                [KeyboardButton("🜲 VIP 🜲"), KeyboardButton("🜲 VVIP 🜲")],
                [KeyboardButton("🜲 Redeem 🜲"), KeyboardButton("🜲 Profil 🜲")]
            ]
        else:
            keyboard = [
                [KeyboardButton("🜲 Menu Utama 🜲")],
                [KeyboardButton("🜲 VIP 🜲"), KeyboardButton("🜲 VVIP 🜲")],
                [KeyboardButton("🜲 Redeem 🜲")]
            ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_verification_keyboard():
    keyboard = []
    
    if len(REQUIRED_GROUPS) >= 1 and REQUIRED_GROUPS[0].get("link"):
        keyboard.append([InlineKeyboardButton("🜲 Join Grup 1 🜲", url=REQUIRED_GROUPS[0]["link"])])
    
    if len(REQUIRED_GROUPS) >= 2 and REQUIRED_GROUPS[1].get("link"):
        keyboard.append([InlineKeyboardButton("🜲 Join Grup 2 🜲", url=REQUIRED_GROUPS[1]["link"])])
    
    keyboard.append([InlineKeyboardButton("🜲 Verifikasi Ulang 🜲", callback_data="verify_recheck")])
    
    return InlineKeyboardMarkup(keyboard)


async def check_forced_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    user = update.effective_user
    
    if is_owner(user_id):
        return True
    
    try:
        from commands.verify import check_user_membership, get_verification_message
        joined_group1, joined_group2 = await check_user_membership(context, user_id)
        
        if db_available:
            try:
                await UserVerificationModel.create_or_update(
                    user_id=user_id,
                    joined_group1=joined_group1,
                    joined_group2=joined_group2
                )
            except Exception as e:
                logger.error(f"Error updating verification: {e}")
        
        if joined_group1 and joined_group2:
            return True
        
        user_name = user.first_name or user.username or "User"
        
        await update.message.reply_text(
            get_verification_message(user_name),
            parse_mode="Markdown",
            reply_markup=get_verification_keyboard()
        )
        return False
        
    except Exception as e:
        logger.error(f"Error in check_forced_join: {e}")
        return True


async def show_access_revoked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """⚠️ *Akses Dicabut*

Sistem mendeteksi bahwa kamu keluar dari salah satu grup wajib.

Akses bot kamu telah dicabut dan status dikembalikan ke *REGULER* dengan limit *0*.

Silakan bergabung kembali ke kedua grup untuk mengaktifkan fitur bot."""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_verification_keyboard()
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    
    is_private = update.effective_chat.type == "private" if update.effective_chat else True
    is_group = update.effective_chat.type in ["group", "supergroup"] if update.effective_chat else False
    
    if is_group and not is_owner(user_id):
        try:
            group_id = update.effective_chat.id
            if db_available:
                group_mode_enabled = await GuildModeModel.is_group_enabled(group_id)
                if not group_mode_enabled:
                    return
        except Exception as e:
            logger.error(f"Error checking group mode: {e}")
    
    if is_private and not is_owner(user_id):
        is_verified = await check_forced_join(update, context)
        if not is_verified:
            return
    
    from utils.helpers import get_user_display_name
    display_name = get_user_display_name(user)
    
    role = "Reguler"
    expired_at = "—"
    limit_remaining = 10
    total_requests = 0
    verification_status = "Belum Terverifikasi"
    
    if is_owner(user_id):
        role = "OWNER"
        limit_remaining = "∞"
        verification_status = "BYPASS (Owner)"
    elif db_available:
        try:
            db = get_db()
            if db.is_connected:
                db_user = await UserModel.create_or_update(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                
                await ActivityLogModel.log(
                    user_id=user_id,
                    action="start",
                    username=username,
                    details={"first_name": first_name}
                )
                
                if db_user:
                    user_role = db_user.get("role", "reguler")
                    total_requests = db_user.get("total_requests", 0)
                    daily_limit = db_user.get("daily_limit", 10)
                    daily_used = db_user.get("daily_used", 0)
                    limit_remaining = max(0, daily_limit - daily_used)
                    
                    if user_role == "vvip":
                        role = "VVIP"
                        vvip_access = await VVIPAccessModel.get_access(user_id)
                        if vvip_access and vvip_access.get("status") == "active":
                            expired_at = format_remaining_time(vvip_access.get("expired_at"))
                            limit_remaining = vvip_access.get("daily_limit", 100) - daily_used
                    elif user_role == "vip":
                        role = "VIP"
                        vip_access = await VIPAccessModel.get_access(user_id)
                        if vip_access and vip_access.get("status") == "active":
                            expired_at = format_remaining_time(vip_access.get("expired_at"))
                            limit_remaining = vip_access.get("daily_limit", 50) - daily_used
                    
                    verification = await UserVerificationModel.get_verification(user_id)
                    if verification:
                        if verification.get("status") == "verified":
                            verification_status = "Terverifikasi ✅"
                        else:
                            verification_status = "Belum Terverifikasi ❌"
        except Exception as e:
            logger.error(f"Database error in start: {e}")
    
    welcome_text = f"""```
🎌  KIFZL DEV BOT  
(BY @KIFZLDEV)
───────────────────────────────────────

"KONNICHIWA, WATASHI WA KIFZL_BOT DESU"
Saya siap bantu convert file & management kontak.
✦ Created by: @KIFZLDEV

───────────────────────────────────────
📍 STATUS AKUN
───────────────────────────────────────
• NAMA          : {display_name}
• ID            : {user_id}
• ROLE          : {role}
• VERIFIKASI    : {verification_status}
• MASA AKTIF    : {expired_at}
• LIMIT HARIAN  : {limit_remaining}
• TOTAL OPERASI : {total_requests}

───────────────────────────────────────
⚡ FITUR UTAMA
───────────────────────────────────────
🜲 STATUS               — Cek akses  
🜲 MSG → TXT            — Convert  
🜲 TXT → VCF            — Convert  
🜲 VCF → TXT            — Ekstrak  
🜲 CREATE ADM & NAVY    — Buat kontak admin/navy  
🜲 RAPIKAN TXT          — Bersihkan format  
🜲 XLS → VCF            — Convert XLS  
🜲 GABUNG FILE          — Gabungkan  
🜲 HITUNG KONTAK        — Hitung kontak  
🜲 CEK NAMA KONTAK      — Validasi nama  
🜲 SPLIT FILE           — Bagi file  
🎁 REDEEM CODE          — Aktivasi  

───────────────────────────────────────
```"""
    
    keyboard = get_start_keyboard(user_id, is_private)
    
    if not update.message:
        return
    
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos and photos.total_count > 0:
            await update.message.reply_photo(
                photo=photos.photos[0][0].file_id,
                caption=welcome_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                welcome_text, 
                parse_mode="Markdown", 
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        await update.message.reply_text(
            welcome_text, 
            parse_mode="Markdown", 
            reply_markup=keyboard
        )
