import logging
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner

logger = logging.getLogger(__name__)

ASK_PENGATURAN_ACTION = 0
ASK_PENGATURAN_GROUP_ID = 1
ASK_WELCOME_MSG = 2
ASK_WHITELIST_LINK = 3

db_available = False
try:
    from database.models import GroupSettingsModel, ActivityLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_pengaturan_grup_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Lihat Setting Grup 🜲")],
        [KeyboardButton("🜲 Set Welcome Message 🜲")],
        [KeyboardButton("🜲 Whitelist Link 🜲"), KeyboardButton("🜲 Reset Setting 🜲")],
        [KeyboardButton("🜲 Toggle Features 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_cancel_keyboard():
    keyboard = [[KeyboardButton("🔙 KEMBALI 🔙")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def pengaturan_grup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ Akses Ditolak\nAnda tidak memiliki akses ke menu Pengaturan Grup.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    text = """```
⚙️ PENGATURAN GRUP
───────────────────────────────────────

Konfigurasi detail untuk setiap grup.

───────────────────────────────────────
MENU PENGATURAN
───────────────────────────────────────
🜲 Lihat Setting Grup  — Lihat config grup
🜲 Set Welcome Message — Atur pesan sambutan
🜲 Whitelist Link      — Link yang diizinkan
🜲 Reset Setting       — Reset ke default
🜲 Toggle Features     — On/Off fitur

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_pengaturan_grup_keyboard()
    )
    return ASK_PENGATURAN_ACTION


async def pengaturan_grup_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if text == "🜲 Lihat Setting Grup 🜲":
        context.user_data['pengaturan_action'] = 'view'
        await update.message.reply_text(
            "Masukkan Group ID untuk melihat pengaturan:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PENGATURAN_GROUP_ID
    
    elif text == "🜲 Set Welcome Message 🜲":
        context.user_data['pengaturan_action'] = 'welcome'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Welcome Message:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PENGATURAN_GROUP_ID
    
    elif text == "🜲 Whitelist Link 🜲":
        context.user_data['pengaturan_action'] = 'whitelist'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Whitelist Link:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PENGATURAN_GROUP_ID
    
    elif text == "🜲 Reset Setting 🜲":
        context.user_data['pengaturan_action'] = 'reset'
        await update.message.reply_text(
            "Masukkan Group ID untuk reset pengaturan:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PENGATURAN_GROUP_ID
    
    elif text == "🜲 Toggle Features 🜲":
        context.user_data['pengaturan_action'] = 'toggle'
        await update.message.reply_text(
            "Masukkan Group ID untuk toggle fitur:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PENGATURAN_GROUP_ID
    
    return ASK_PENGATURAN_ACTION


async def pengaturan_grup_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Pengaturan Grup.",
            parse_mode="Markdown",
            reply_markup=get_pengaturan_grup_keyboard()
        )
        return ASK_PENGATURAN_ACTION
    
    try:
        group_id = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Group ID tidak valid. Masukkan angka saja.",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_PENGATURAN_GROUP_ID
    
    context.user_data['target_group_id'] = group_id
    action = context.user_data.get('pengaturan_action')
    
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_pengaturan_grup_keyboard()
        )
        return ASK_PENGATURAN_ACTION
    
    try:
        db = get_db()
        if not db.is_connected:
            await update.message.reply_text(
                "❌ Database tidak terhubung.",
                parse_mode="Markdown",
                reply_markup=get_pengaturan_grup_keyboard()
            )
            return ASK_PENGATURAN_ACTION
        
        settings = await GroupSettingsModel.get_or_create(group_id)
        
        if action == 'view':
            anti_link = "✅ Aktif" if settings.get('anti_link') else "❌ Nonaktif"
            anti_spam = "✅ Aktif" if settings.get('anti_spam') else "❌ Nonaktif"
            anti_virtex = "✅ Aktif" if settings.get('anti_virtex') else "❌ Nonaktif"
            auto_welcome = "✅ Aktif" if settings.get('auto_welcome') else "❌ Nonaktif"
            slowmode = settings.get('slowmode_seconds', 0)
            
            banned_words = json.loads(settings.get('banned_words', '[]'))
            banned_count = len(banned_words) if isinstance(banned_words, list) else 0
            
            whitelist = json.loads(settings.get('link_whitelist', '[]'))
            whitelist_count = len(whitelist) if isinstance(whitelist, list) else 0
            
            welcome_msg = settings.get('welcome_message', 'Default')[:50]
            
            view_text = f"""```
⚙️ PENGATURAN GRUP
───────────────────────────────────────

📋 Group ID    : {group_id}
📛 Nama        : {settings.get('group_title', 'Unknown')}

───────────────────────────────────────
STATUS FITUR
───────────────────────────────────────
🔗 Anti-Link   : {anti_link}
🚫 Anti-Spam   : {anti_spam}
📝 Anti-Virtex : {anti_virtex}
👋 Auto Welcome: {auto_welcome}
⏱️ Slowmode    : {slowmode} detik

───────────────────────────────────────
DATA LAINNYA
───────────────────────────────────────
🚫 Banned Words  : {banned_count} kata
✅ Whitelist Link: {whitelist_count} link
💬 Welcome Msg   : {welcome_msg}...

───────────────────────────────────────
```"""
            
            await update.message.reply_text(
                view_text,
                parse_mode="Markdown",
                reply_markup=get_pengaturan_grup_keyboard()
            )
            return ASK_PENGATURAN_ACTION
        
        elif action == 'welcome':
            await update.message.reply_text(
                "Masukkan pesan welcome baru:\n\nGunakan {name} untuk nama user dan {group} untuk nama grup.",
                parse_mode="Markdown",
                reply_markup=get_cancel_keyboard()
            )
            return ASK_WELCOME_MSG
        
        elif action == 'whitelist':
            await update.message.reply_text(
                "Masukkan link yang ingin di-whitelist (pisahkan dengan koma):\n\nContoh: t.me/grupkita,youtube.com",
                parse_mode="Markdown",
                reply_markup=get_cancel_keyboard()
            )
            return ASK_WHITELIST_LINK
        
        elif action == 'reset':
            await GroupSettingsModel.update_setting(group_id, 'anti_link', False)
            await GroupSettingsModel.update_setting(group_id, 'anti_spam', False)
            await GroupSettingsModel.update_setting(group_id, 'anti_virtex', False)
            await GroupSettingsModel.update_setting(group_id, 'auto_welcome', False)
            await GroupSettingsModel.update_setting(group_id, 'slowmode_seconds', 0)
            await GroupSettingsModel.update_setting(group_id, 'banned_words', '[]')
            await GroupSettingsModel.update_setting(group_id, 'link_whitelist', '[]')
            await GroupSettingsModel.update_setting(group_id, 'welcome_message', 'Selamat datang di grup!')
            
            await ActivityLogModel.log(
                user_id=update.effective_user.id,
                action="reset_group_settings",
                group_id=group_id,
                details={}
            )
            
            await update.message.reply_text(
                f"✅ Pengaturan grup {group_id} berhasil di-reset ke default.",
                parse_mode="Markdown",
                reply_markup=get_pengaturan_grup_keyboard()
            )
            return ASK_PENGATURAN_ACTION
        
        elif action == 'toggle':
            keyboard = ReplyKeyboardMarkup([
                [KeyboardButton("🔗 Toggle Anti-Link"), KeyboardButton("🚫 Toggle Anti-Spam")],
                [KeyboardButton("📝 Toggle Anti-Virtex"), KeyboardButton("👋 Toggle Auto Welcome")],
                [KeyboardButton("🔙 KEMBALI 🔙")]
            ], resize_keyboard=True)
            
            await update.message.reply_text(
                "Pilih fitur yang ingin di-toggle:",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            return ASK_WELCOME_MSG
        
    except Exception as e:
        logger.error(f"Error in pengaturan grup: {e}")
        await update.message.reply_text(
            "❌ Terjadi error.",
            parse_mode="Markdown",
            reply_markup=get_pengaturan_grup_keyboard()
        )
    
    return ASK_PENGATURAN_ACTION


async def pengaturan_grup_welcome_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Pengaturan Grup.",
            parse_mode="Markdown",
            reply_markup=get_pengaturan_grup_keyboard()
        )
        return ASK_PENGATURAN_ACTION
    
    group_id = context.user_data.get('target_group_id')
    action = context.user_data.get('pengaturan_action')
    
    if action == 'toggle':
        try:
            db = get_db()
            if db.is_connected:
                settings = await GroupSettingsModel.get_or_create(group_id)
                
                if "Anti-Link" in text:
                    new_value = not settings.get('anti_link', False)
                    await GroupSettingsModel.update_setting(group_id, 'anti_link', new_value)
                    status = "diaktifkan" if new_value else "dinonaktifkan"
                    await update.message.reply_text(f"✅ Anti-Link berhasil {status}.", parse_mode="Markdown", reply_markup=get_pengaturan_grup_keyboard())
                
                elif "Anti-Spam" in text:
                    new_value = not settings.get('anti_spam', False)
                    await GroupSettingsModel.update_setting(group_id, 'anti_spam', new_value)
                    status = "diaktifkan" if new_value else "dinonaktifkan"
                    await update.message.reply_text(f"✅ Anti-Spam berhasil {status}.", parse_mode="Markdown", reply_markup=get_pengaturan_grup_keyboard())
                
                elif "Anti-Virtex" in text:
                    new_value = not settings.get('anti_virtex', False)
                    await GroupSettingsModel.update_setting(group_id, 'anti_virtex', new_value)
                    status = "diaktifkan" if new_value else "dinonaktifkan"
                    await update.message.reply_text(f"✅ Anti-Virtex berhasil {status}.", parse_mode="Markdown", reply_markup=get_pengaturan_grup_keyboard())
                
                elif "Auto Welcome" in text:
                    new_value = not settings.get('auto_welcome', False)
                    await GroupSettingsModel.update_setting(group_id, 'auto_welcome', new_value)
                    status = "diaktifkan" if new_value else "dinonaktifkan"
                    await update.message.reply_text(f"✅ Auto Welcome berhasil {status}.", parse_mode="Markdown", reply_markup=get_pengaturan_grup_keyboard())
                
                return ASK_PENGATURAN_ACTION
        except Exception as e:
            logger.error(f"Toggle error: {e}")
    
    else:
        try:
            db = get_db()
            if db.is_connected:
                await GroupSettingsModel.update_setting(group_id, 'welcome_message', text)
                await ActivityLogModel.log(
                    user_id=update.effective_user.id,
                    action="set_welcome_message",
                    group_id=group_id,
                    details={"message": text[:100]}
                )
                
                await update.message.reply_text(
                    f"✅ Welcome message berhasil diatur untuk grup {group_id}",
                    parse_mode="Markdown",
                    reply_markup=get_pengaturan_grup_keyboard()
                )
        except Exception as e:
            logger.error(f"Set welcome error: {e}")
            await update.message.reply_text(
                "❌ Gagal mengatur welcome message.",
                parse_mode="Markdown",
                reply_markup=get_pengaturan_grup_keyboard()
            )
    
    return ASK_PENGATURAN_ACTION


async def pengaturan_grup_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Pengaturan Grup.",
            parse_mode="Markdown",
            reply_markup=get_pengaturan_grup_keyboard()
        )
        return ASK_PENGATURAN_ACTION
    
    group_id = context.user_data.get('target_group_id')
    
    try:
        db = get_db()
        if db.is_connected:
            settings = await GroupSettingsModel.get_or_create(group_id)
            whitelist = json.loads(settings.get('link_whitelist', '[]'))
            
            links = [l.strip().lower() for l in text.split(',') if l.strip()]
            for link in links:
                if link not in whitelist:
                    whitelist.append(link)
            
            await GroupSettingsModel.update_setting(group_id, 'link_whitelist', json.dumps(whitelist))
            
            await ActivityLogModel.log(
                user_id=update.effective_user.id,
                action="add_whitelist_links",
                group_id=group_id,
                details={"links": links}
            )
            
            await update.message.reply_text(
                f"✅ {len(links)} link berhasil ditambahkan ke whitelist untuk grup {group_id}",
                parse_mode="Markdown",
                reply_markup=get_pengaturan_grup_keyboard()
            )
    except Exception as e:
        logger.error(f"Whitelist error: {e}")
        await update.message.reply_text(
            "❌ Gagal menambahkan whitelist.",
            parse_mode="Markdown",
            reply_markup=get_pengaturan_grup_keyboard()
        )
    
    return ASK_PENGATURAN_ACTION
