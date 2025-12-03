import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes
from datetime import datetime

from config import is_owner, REQUIRED_GROUPS, OWNER_IDS

logger = logging.getLogger(__name__)

db_available = False
try:
    from database.models import UserVerificationModel, UserModel, VIPAccessModel, VVIPAccessModel, ActivityLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_verification_keyboard():
    keyboard = []
    
    if len(REQUIRED_GROUPS) >= 1 and REQUIRED_GROUPS[0].get("link"):
        keyboard.append([InlineKeyboardButton("🜲 Join Grup 1 🜲", url=REQUIRED_GROUPS[0]["link"])])
    
    if len(REQUIRED_GROUPS) >= 2 and REQUIRED_GROUPS[1].get("link"):
        keyboard.append([InlineKeyboardButton("🜲 Join Grup 2 🜲", url=REQUIRED_GROUPS[1]["link"])])
    
    keyboard.append([InlineKeyboardButton("🜲 Verifikasi Ulang 🜲", callback_data="verify_recheck")])
    
    return InlineKeyboardMarkup(keyboard)


def get_verification_message(user_name: str):
    return f"""⚠️ *Verifikasi Grup Wajib*

Halo *{user_name}* 👋
Untuk menggunakan *semua fitur premium bot*, pastikan kamu sudah bergabung dengan kedua grup resmi di bawah ini.

Silakan tekan tombol berikut untuk bergabung, lalu klik *Verifikasi Ulang*.

Terima kasih 🙏"""


def get_access_revoked_message():
    return """⚠️ *Akses Dicabut*

Sistem mendeteksi bahwa kamu keluar dari salah satu grup wajib.

Akses bot kamu telah dicabut dan status dikembalikan ke *REGULER* dengan limit *0*.

Silakan bergabung kembali ke kedua grup untuk mengaktifkan fitur bot."""


def get_verification_success_message(user_name: str):
    return f"""✅ *Verifikasi Berhasil!*

Halo *{user_name}* 👋
Selamat! Kamu sudah bergabung ke semua grup wajib.

Sekarang kamu bisa menggunakan seluruh fitur bot ini.

Ketik /start untuk memulai."""


async def check_user_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> tuple:
    joined_group1 = False
    joined_group2 = False
    
    for i, group in enumerate(REQUIRED_GROUPS):
        try:
            chat_id = group.get("chat_id")
            username = group.get("username")
            
            if chat_id:
                try:
                    member = await context.bot.get_chat_member(chat_id, user_id)
                    if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                        if i == 0:
                            joined_group1 = True
                        else:
                            joined_group2 = True
                except Exception as e:
                    logger.warning(f"Could not check membership for chat_id {chat_id}: {e}")
            
            if username and not (joined_group1 if i == 0 else joined_group2):
                try:
                    member = await context.bot.get_chat_member(f"@{username}", user_id)
                    if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                        if i == 0:
                            joined_group1 = True
                        else:
                            joined_group2 = True
                except Exception as e:
                    logger.warning(f"Could not check membership for @{username}: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking group {i+1}: {e}")
            continue
    
    return joined_group1, joined_group2


async def verify_user_access(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                             show_message: bool = True) -> bool:
    user = update.effective_user
    if not user:
        return False
    
    user_id = user.id
    
    if is_owner(user_id):
        return True
    
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
    
    if show_message and update.message:
        user_name = user.first_name or user.username or "User"
        await update.message.reply_text(
            get_verification_message(user_name),
            parse_mode="Markdown",
            reply_markup=get_verification_keyboard()
        )
    
    return False


async def send_verification_required(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    
    user_name = user.first_name or user.username or "User"
    
    if update.message:
        await update.message.reply_text(
            get_verification_message(user_name),
            parse_mode="Markdown",
            reply_markup=get_verification_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            get_verification_message(user_name),
            parse_mode="Markdown",
            reply_markup=get_verification_keyboard()
        )


async def handle_verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    user = query.from_user
    user_id = user.id
    callback_data = query.data
    
    if is_owner(user_id):
        await query.edit_message_text(
            "👑 *OWNER Terdeteksi*\n\nAnda adalah OWNER bot, verifikasi tidak diperlukan.\n\nKetik /start untuk memulai.",
            parse_mode="Markdown"
        )
        return
    
    if callback_data == "verify_recheck":
        joined_group1, joined_group2 = await check_user_membership(context, user_id)
        
        if db_available:
            try:
                await UserVerificationModel.create_or_update(
                    user_id=user_id,
                    joined_group1=joined_group1,
                    joined_group2=joined_group2
                )
                
                await ActivityLogModel.log(
                    user_id=user_id,
                    action="verification_check",
                    username=user.username,
                    details={
                        "joined_group1": joined_group1,
                        "joined_group2": joined_group2,
                        "result": "success" if (joined_group1 and joined_group2) else "failed"
                    }
                )
            except Exception as e:
                logger.error(f"Error in verification: {e}")
        
        if joined_group1 and joined_group2:
            user_name = user.first_name or user.username or "User"
            
            if db_available:
                try:
                    db_user = await UserModel.get_by_id(user_id)
                    if db_user and db_user.get("daily_limit", 0) == 0:
                        await UserModel.set_daily_limit(user_id, 10)
                except Exception as e:
                    logger.error(f"Error restoring limit: {e}")
            
            await query.edit_message_text(
                get_verification_success_message(user_name),
                parse_mode="Markdown"
            )
        else:
            status_g1 = "✅" if joined_group1 else "❌"
            status_g2 = "✅" if joined_group2 else "❌"
            
            user_name = user.first_name or user.username or "User"
            
            group1_name = REQUIRED_GROUPS[0].get("name", "Grup Wajib 1") if len(REQUIRED_GROUPS) >= 1 else "Grup Wajib 1"
            group2_name = REQUIRED_GROUPS[1].get("name", "Grup Wajib 2") if len(REQUIRED_GROUPS) >= 2 else "Grup Wajib 2"
            
            message = f"""⚠️ *Verifikasi Belum Selesai*

Halo *{user_name}* 👋

Status keanggotaan grup:
{status_g1} Grup 1: {group1_name}
{status_g2} Grup 2: {group2_name}

Pastikan kamu sudah bergabung ke *kedua grup* tersebut, lalu tekan *Verifikasi Ulang* kembali."""
            
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=get_verification_keyboard()
            )
    
    elif callback_data == "verify_join":
        joined_group1, joined_group2 = await check_user_membership(context, user_id)
        
        if joined_group1 and joined_group2:
            if db_available:
                await UserVerificationModel.create_or_update(
                    user_id=user_id,
                    joined_group1=True,
                    joined_group2=True
                )
            
            user_name = user.first_name or user.username or "User"
            await query.edit_message_text(
                get_verification_success_message(user_name),
                parse_mode="Markdown"
            )
        else:
            user_name = user.first_name or user.username or "User"
            await query.edit_message_text(
                get_verification_message(user_name),
                parse_mode="Markdown",
                reply_markup=get_verification_keyboard()
            )


async def handle_member_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member_update = update.my_chat_member
    if not chat_member_update:
        return
    
    if chat_member_update.new_chat_member.status == ChatMember.MEMBER:
        user = chat_member_update.from_user
        if not user:
            return
        
        user_id = user.id
        
        if is_owner(user_id):
            return
        
        user_name = user.first_name or user.username or "User"
        
        text = f"""🎉 *SELAMAT BERGABUNG!*

Halo *{user_name}* 👋
Terima kasih sudah bergabung!

Untuk menggunakan bot, pastikan kamu juga bergabung ke grup wajib lainnya."""
        
        try:
            await user.send_message(
                text,
                parse_mode="Markdown",
                reply_markup=get_verification_keyboard()
            )
        except Exception as e:
            logger.warning(f"Could not send welcome DM: {e}")


async def handle_member_left(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    if is_owner(user_id):
        return
    
    if db_available:
        try:
            await UserVerificationModel.revoke_access(user_id)
            
            await ActivityLogModel.log(
                user_id=user_id,
                action="access_revoked",
                details={"reason": "left_required_group"}
            )
            
            logger.info(f"Access revoked for user {user_id} - left required group")
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=get_access_revoked_message(),
                    parse_mode="Markdown",
                    reply_markup=get_verification_keyboard()
                )
            except Exception as e:
                logger.warning(f"Could not send revoke notification to {user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Error revoking access for {user_id}: {e}")


async def check_verification_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_user:
        return True
    
    user_id = update.effective_user.id
    
    if is_owner(user_id):
        return True
    
    if update.message and update.message.text:
        text = update.message.text
        if text == "/start" or text.startswith("/start "):
            return True
    
    is_verified = await verify_user_access(update, context, show_message=True)
    return is_verified


def is_private_chat(update: Update) -> bool:
    if update.effective_chat:
        return update.effective_chat.type == "private"
    return False


def is_group_chat(update: Update) -> bool:
    if update.effective_chat:
        return update.effective_chat.type in ["group", "supergroup"]
    return False


async def check_group_mode(context: ContextTypes.DEFAULT_TYPE, group_id: int) -> bool:
    if not db_available:
        return False
    
    try:
        from database.models import GuildModeModel
        return await GuildModeModel.is_group_enabled(group_id)
    except Exception as e:
        logger.error(f"Error checking group mode: {e}")
        return False
