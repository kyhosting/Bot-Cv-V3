import logging
import re
import json
from datetime import datetime, timedelta
from telegram import Update, ChatMemberUpdated
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus

from config import is_owner

logger = logging.getLogger(__name__)

db_available = False
try:
    from database.models import GroupSettingsModel, ActivityLogModel, SystemSecurityModel, GroupMemberModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass

LINK_PATTERN = re.compile(
    r'(https?://|www\.|t\.me/|telegram\.me/|@)[^\s]+',
    re.IGNORECASE
)

VIRTEX_PATTERN = re.compile(
    r'(.)\1{50,}|[\u2060-\u206F]{20,}|[\u200B-\u200F]{20,}',
    re.UNICODE
)

spam_tracker = {}


async def get_group_settings(group_id: int):
    if not db_available:
        return None
    
    try:
        db = get_db()
        if db.is_connected:
            return await GroupSettingsModel.get_or_create(group_id)
    except Exception as e:
        logger.error(f"Error getting group settings: {e}")
    return None


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    message = update.message
    chat = message.chat
    user = message.from_user
    
    if chat.type not in ['group', 'supergroup']:
        return
    
    if is_owner(user.id):
        return
    
    try:
        member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except:
        return
    
    settings = await get_group_settings(chat.id)
    if not settings:
        return
    
    text = message.text or message.caption or ""
    
    if settings.get('anti_link', False):
        if await check_anti_link(update, context, settings, text):
            return
    
    if settings.get('anti_virtex', False):
        if await check_anti_virtex(update, context, text):
            return
    
    if settings.get('anti_spam', False):
        if await check_anti_spam(update, context, user.id, chat.id):
            return
    
    banned_words = json.loads(settings.get('banned_words', '[]'))
    if banned_words:
        if await check_banned_words(update, context, text, banned_words):
            return


async def check_anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE, settings: dict, text: str) -> bool:
    if not text:
        return False
    
    matches = LINK_PATTERN.findall(text)
    if not matches:
        return False
    
    whitelist = json.loads(settings.get('link_whitelist', '[]'))
    
    for match in matches:
        is_whitelisted = False
        for allowed in whitelist:
            if allowed.lower() in text.lower():
                is_whitelisted = True
                break
        
        if not is_whitelisted:
            try:
                await update.message.delete()
                
                warning_text = f"""```
⚠️ LINK TERDETEKSI
───────────────────────────────────────

Link tidak diizinkan di grup ini.
Pesan Anda telah dihapus.

User: {update.effective_user.first_name}

───────────────────────────────────────
```"""
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=warning_text,
                    parse_mode="Markdown"
                )
                
                if db_available:
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="anti_link_triggered",
                        group_id=update.effective_chat.id,
                        details={"link_detected": match}
                    )
                
                return True
            except Exception as e:
                logger.error(f"Error in anti-link: {e}")
    
    return False


async def check_anti_virtex(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    if not text:
        return False
    
    if len(text) > 4000:
        try:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Pesan terlalu panjang telah dihapus.",
                parse_mode="Markdown"
            )
            return True
        except:
            pass
    
    if VIRTEX_PATTERN.search(text):
        try:
            await update.message.delete()
            
            warning_text = f"""```
⚠️ VIRTEX TERDETEKSI
───────────────────────────────────────

Pesan berbahaya telah dihapus.

User: {update.effective_user.first_name}

───────────────────────────────────────
```"""
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=warning_text,
                parse_mode="Markdown"
            )
            
            if db_available:
                await ActivityLogModel.log(
                    user_id=update.effective_user.id,
                    action="anti_virtex_triggered",
                    group_id=update.effective_chat.id,
                    details={}
                )
            
            return True
        except Exception as e:
            logger.error(f"Error in anti-virtex: {e}")
    
    return False


async def check_anti_spam(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> bool:
    global spam_tracker
    
    key = f"{user_id}_{chat_id}"
    now = datetime.now()
    
    if key not in spam_tracker:
        spam_tracker[key] = {"count": 1, "first_msg": now, "warned": False}
        return False
    
    tracker = spam_tracker[key]
    time_diff = (now - tracker["first_msg"]).total_seconds()
    
    if time_diff > 10:
        spam_tracker[key] = {"count": 1, "first_msg": now, "warned": False}
        return False
    
    tracker["count"] += 1
    
    if tracker["count"] > 5:
        if not tracker["warned"]:
            try:
                await update.message.delete()
                
                warning_text = f"""```
⚠️ SPAM TERDETEKSI
───────────────────────────────────────

Anda mengirim pesan terlalu cepat.
Mohon tunggu beberapa detik.

User: {update.effective_user.first_name}

───────────────────────────────────────
```"""
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=warning_text,
                    parse_mode="Markdown"
                )
                
                tracker["warned"] = True
                
                if db_available:
                    await ActivityLogModel.log(
                        user_id=user_id,
                        action="anti_spam_triggered",
                        group_id=chat_id,
                        details={"message_count": tracker["count"]}
                    )
                
                return True
            except Exception as e:
                logger.error(f"Error in anti-spam: {e}")
        else:
            try:
                await update.message.delete()
                return True
            except:
                pass
    
    return False


async def check_banned_words(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, banned_words: list) -> bool:
    if not text or not banned_words:
        return False
    
    text_lower = text.lower()
    
    for word in banned_words:
        if word.lower() in text_lower:
            try:
                await update.message.delete()
                
                warning_text = f"""```
⚠️ KATA TERLARANG
───────────────────────────────────────

Pesan mengandung kata terlarang.
Pesan Anda telah dihapus.

User: {update.effective_user.first_name}

───────────────────────────────────────
```"""
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=warning_text,
                    parse_mode="Markdown"
                )
                
                if db_available:
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="banned_word_triggered",
                        group_id=update.effective_chat.id,
                        details={"word": word}
                    )
                
                return True
            except Exception as e:
                logger.error(f"Error in banned words: {e}")
    
    return False


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    
    chat = update.message.chat
    
    if chat.type not in ['group', 'supergroup']:
        return
    
    settings = await get_group_settings(chat.id)
    if not settings:
        return
    
    if not settings.get('auto_welcome', False):
        return
    
    welcome_template = settings.get('welcome_message', 'Selamat datang di grup!')
    
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue
        
        welcome_msg = welcome_template.replace('{name}', new_member.first_name or 'Member')
        welcome_msg = welcome_msg.replace('{group}', chat.title or 'grup')
        
        welcome_text = f"""```
👋 SELAMAT DATANG
───────────────────────────────────────

{welcome_msg}

───────────────────────────────────────
```"""
        
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_text,
                parse_mode="Markdown"
            )
            
            if db_available:
                await GroupMemberModel.add_member(
                    group_id=chat.id,
                    user_id=new_member.id,
                    username=new_member.username,
                    first_name=new_member.first_name
                )
                
                await ActivityLogModel.log(
                    user_id=new_member.id,
                    action="member_joined",
                    group_id=chat.id,
                    username=new_member.username,
                    details={"first_name": new_member.first_name}
                )
        except Exception as e:
            logger.error(f"Error sending welcome: {e}")


async def handle_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member:
        return
    
    chat = update.message.chat
    left_member = update.message.left_chat_member
    
    if chat.type not in ['group', 'supergroup']:
        return
    
    if is_owner(left_member.id):
        return
    
    if db_available:
        try:
            await GroupMemberModel.remove_member(chat.id, left_member.id)
            
            await ActivityLogModel.log(
                user_id=left_member.id,
                action="member_left",
                group_id=chat.id,
                username=left_member.username,
                details={"first_name": left_member.first_name}
            )
        except Exception as e:
            logger.error(f"Error handling left member: {e}")
    
    try:
        from config import REQUIRED_GROUPS
        
        is_required_group = False
        for group in REQUIRED_GROUPS:
            group_chat_id = group.get("chat_id")
            group_username = group.get("username")
            
            if group_chat_id and group_chat_id == chat.id:
                is_required_group = True
                break
            
            if group_username:
                try:
                    if chat.username and chat.username.lower() == group_username.lower():
                        is_required_group = True
                        break
                except:
                    pass
        
        if is_required_group:
            try:
                from database.models import UserVerificationModel
                from commands.verify import get_access_revoked_message, get_verification_keyboard
                
                await UserVerificationModel.revoke_access(left_member.id)
                
                await ActivityLogModel.log(
                    user_id=left_member.id,
                    action="access_revoked",
                    group_id=chat.id,
                    username=left_member.username,
                    details={"reason": "left_required_group", "group_name": chat.title}
                )
                
                logger.info(f"Access revoked for user {left_member.id} - left required group {chat.title}")
                
                try:
                    revoke_text = """⚠️ *Akses Dicabut*

Sistem mendeteksi bahwa kamu keluar dari salah satu grup wajib.

Akses bot kamu telah dicabut dan status dikembalikan ke *REGULER* dengan limit *0*.

Silakan bergabung kembali ke kedua grup untuk mengaktifkan fitur bot."""
                    
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = []
                    
                    if len(REQUIRED_GROUPS) >= 1 and REQUIRED_GROUPS[0].get("link"):
                        keyboard.append([InlineKeyboardButton("🜲 Join Grup 1 🜲", url=REQUIRED_GROUPS[0]["link"])])
                    
                    if len(REQUIRED_GROUPS) >= 2 and REQUIRED_GROUPS[1].get("link"):
                        keyboard.append([InlineKeyboardButton("🜲 Join Grup 2 🜲", url=REQUIRED_GROUPS[1]["link"])])
                    
                    keyboard.append([InlineKeyboardButton("🜲 Verifikasi Ulang 🜲", callback_data="verify_recheck")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=left_member.id,
                        text=revoke_text,
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.warning(f"Could not send revoke notification to {left_member.id}: {e}")
                    
            except Exception as e:
                logger.error(f"Error revoking access for {left_member.id}: {e}")
                
    except Exception as e:
        logger.error(f"Error checking required group: {e}")


class GroupMemberModel:
    @classmethod
    async def add_member(cls, group_id: int, user_id: int, username: str = None, first_name: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        try:
            await db.execute("""
                INSERT INTO group_members (group_id, user_id, username, first_name, joined_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5, $5)
                ON CONFLICT (group_id, user_id) DO UPDATE SET 
                username = COALESCE($3, group_members.username),
                first_name = COALESCE($4, group_members.first_name),
                is_active = TRUE,
                updated_at = $5
            """, group_id, user_id, username, first_name, now)
            return True
        except Exception as e:
            logger.error(f"Error adding member: {e}")
            return None
    
    @classmethod
    async def remove_member(cls, group_id: int, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        try:
            await db.execute("""
                UPDATE group_members SET is_active = FALSE, updated_at = $3 
                WHERE group_id = $1 AND user_id = $2
            """, group_id, user_id, datetime.utcnow())
            return True
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            return False
    
    @classmethod
    async def get_member(cls, group_id: int, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        
        row = await db.fetchrow("""
            SELECT * FROM group_members WHERE group_id = $1 AND user_id = $2
        """, group_id, user_id)
        return dict(row) if row else None
    
    @classmethod
    async def warn_member(cls, group_id: int, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        await db.execute("""
            UPDATE group_members SET warnings = warnings + 1, updated_at = $3 
            WHERE group_id = $1 AND user_id = $2
        """, group_id, user_id, datetime.utcnow())
        return True


class SystemSecurityModel:
    @classmethod
    async def log_security(cls, user_id: int, security_type: str, action: str, details: dict = None, is_blocked: bool = False):
        db = get_db()
        if not db.is_connected:
            return None
        
        try:
            await db.execute("""
                INSERT INTO system_security (user_id, type, action, details, is_blocked, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user_id, security_type, action, json.dumps(details or {}), is_blocked, datetime.utcnow())
            return True
        except Exception as e:
            logger.error(f"Error logging security: {e}")
            return None
