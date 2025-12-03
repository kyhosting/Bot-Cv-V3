import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner

logger = logging.getLogger(__name__)

ASK_MANAJEMEN_ACTION = 0
ASK_GROUP_ID = 1
ASK_SETTING_VALUE = 2

db_available = False
try:
    from database.models import GroupSettingsModel, ActivityLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_manajemen_grup_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Daftar Grup 🜲"), KeyboardButton("🜲 Anti-Link 🜲")],
        [KeyboardButton("🜲 Anti-Spam 🜲"), KeyboardButton("🜲 Anti-Virtex 🜲")],
        [KeyboardButton("🜲 Auto Welcome 🜲"), KeyboardButton("🜲 Slowmode 🜲")],
        [KeyboardButton("🜲 Banned Words 🜲"), KeyboardButton("🜲 Auto Kick 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_toggle_keyboard():
    keyboard = [
        [KeyboardButton("✅ AKTIFKAN"), KeyboardButton("❌ NONAKTIFKAN")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_cancel_keyboard():
    keyboard = [[KeyboardButton("🔙 KEMBALI 🔙")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def manajemen_grup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ Akses Ditolak\nAnda tidak memiliki akses ke menu Manajemen Grup.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    text = """```
👥 MANAJEMEN GRUP
───────────────────────────────────────

Kelola pengaturan grup bot dari sini.

───────────────────────────────────────
FITUR TERSEDIA
───────────────────────────────────────
🜲 Daftar Grup   — Lihat semua grup
🜲 Anti-Link     — Hapus link otomatis
🜲 Anti-Spam     — Proteksi spam
🜲 Anti-Virtex   — Proteksi virus teks
🜲 Auto Welcome  — Sambutan otomatis
🜲 Slowmode      — Atur delay pesan
🜲 Banned Words  — Kata terlarang
🜲 Auto Kick     — Kick otomatis

───────────────────────────────────────
Catatan:
Bot harus menjadi admin di grup untuk
menggunakan fitur-fitur ini.
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_manajemen_grup_keyboard()
    )
    return ASK_MANAJEMEN_ACTION


async def manajemen_grup_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if text == "🜲 Daftar Grup 🜲":
        return await show_all_groups(update, context)
    
    elif text == "🜲 Anti-Link 🜲":
        context.user_data['setting_type'] = 'anti_link'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Anti-Link:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    elif text == "🜲 Anti-Spam 🜲":
        context.user_data['setting_type'] = 'anti_spam'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Anti-Spam:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    elif text == "🜲 Anti-Virtex 🜲":
        context.user_data['setting_type'] = 'anti_virtex'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Anti-Virtex:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    elif text == "🜲 Auto Welcome 🜲":
        context.user_data['setting_type'] = 'auto_welcome'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Auto Welcome:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    elif text == "🜲 Slowmode 🜲":
        context.user_data['setting_type'] = 'slowmode'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Slowmode:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    elif text == "🜲 Banned Words 🜲":
        context.user_data['setting_type'] = 'banned_words'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Banned Words:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    elif text == "🜲 Auto Kick 🜲":
        context.user_data['setting_type'] = 'auto_kick'
        await update.message.reply_text(
            "Masukkan Group ID untuk mengatur Auto Kick:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    return ASK_MANAJEMEN_ACTION


async def manajemen_grup_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Manajemen Grup.",
            parse_mode="Markdown",
            reply_markup=get_manajemen_grup_keyboard()
        )
        return ASK_MANAJEMEN_ACTION
    
    try:
        group_id = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Group ID tidak valid. Masukkan angka saja.",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_GROUP_ID
    
    context.user_data['target_group_id'] = group_id
    setting_type = context.user_data.get('setting_type')
    
    if setting_type == 'slowmode':
        await update.message.reply_text(
            "Masukkan durasi slowmode dalam detik (0 untuk nonaktifkan):",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_SETTING_VALUE
    
    elif setting_type == 'banned_words':
        await update.message.reply_text(
            "Masukkan kata yang ingin di-banned (pisahkan dengan koma):\n\nContoh: spam,judi,promosi",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_SETTING_VALUE
    
    else:
        await update.message.reply_text(
            f"Pilih aksi untuk {setting_type.replace('_', ' ').title()}:",
            parse_mode="Markdown",
            reply_markup=get_toggle_keyboard()
        )
        return ASK_SETTING_VALUE


async def manajemen_grup_setting_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Manajemen Grup.",
            parse_mode="Markdown",
            reply_markup=get_manajemen_grup_keyboard()
        )
        return ASK_MANAJEMEN_ACTION
    
    group_id = context.user_data.get('target_group_id')
    setting_type = context.user_data.get('setting_type')
    
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_manajemen_grup_keyboard()
        )
        return ASK_MANAJEMEN_ACTION
    
    try:
        db = get_db()
        if not db.is_connected:
            await update.message.reply_text(
                "❌ Database tidak terhubung.",
                parse_mode="Markdown",
                reply_markup=get_manajemen_grup_keyboard()
            )
            return ASK_MANAJEMEN_ACTION
        
        await GroupSettingsModel.get_or_create(group_id)
        
        if setting_type == 'slowmode':
            try:
                seconds = int(text.strip())
                await GroupSettingsModel.update_setting(group_id, 'slowmode_seconds', seconds)
                await update.message.reply_text(
                    f"✅ Slowmode berhasil diatur ke {seconds} detik untuk grup {group_id}",
                    parse_mode="Markdown",
                    reply_markup=get_manajemen_grup_keyboard()
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Masukkan angka yang valid.",
                    parse_mode="Markdown",
                    reply_markup=get_cancel_keyboard()
                )
                return ASK_SETTING_VALUE
        
        elif setting_type == 'banned_words':
            words = [w.strip().lower() for w in text.split(',') if w.strip()]
            for word in words:
                await GroupSettingsModel.add_banned_word(group_id, word)
            await update.message.reply_text(
                f"✅ {len(words)} kata berhasil ditambahkan ke daftar banned untuk grup {group_id}",
                parse_mode="Markdown",
                reply_markup=get_manajemen_grup_keyboard()
            )
        
        else:
            if text == "✅ AKTIFKAN":
                value = True
            elif text == "❌ NONAKTIFKAN":
                value = False
            else:
                await update.message.reply_text(
                    "❌ Pilih AKTIFKAN atau NONAKTIFKAN.",
                    parse_mode="Markdown",
                    reply_markup=get_toggle_keyboard()
                )
                return ASK_SETTING_VALUE
            
            await GroupSettingsModel.update_setting(group_id, setting_type, value)
            status = "diaktifkan" if value else "dinonaktifkan"
            await update.message.reply_text(
                f"✅ {setting_type.replace('_', ' ').title()} berhasil {status} untuk grup {group_id}",
                parse_mode="Markdown",
                reply_markup=get_manajemen_grup_keyboard()
            )
        
        await ActivityLogModel.log(
            user_id=update.effective_user.id,
            action=f"update_group_setting",
            group_id=group_id,
            details={"setting": setting_type, "value": text}
        )
        
    except Exception as e:
        logger.error(f"Error updating group setting: {e}")
        await update.message.reply_text(
            "❌ Gagal mengupdate pengaturan grup.",
            parse_mode="Markdown",
            reply_markup=get_manajemen_grup_keyboard()
        )
    
    return ASK_MANAJEMEN_ACTION


async def show_all_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_manajemen_grup_keyboard()
        )
        return ASK_MANAJEMEN_ACTION
    
    try:
        db = get_db()
        if db.is_connected:
            groups = await GroupSettingsModel.get_all_groups()
            
            if not groups:
                await update.message.reply_text(
                    "Belum ada grup terdaftar.",
                    parse_mode="Markdown",
                    reply_markup=get_manajemen_grup_keyboard()
                )
                return ASK_MANAJEMEN_ACTION
            
            group_text = """```
📋 DAFTAR GRUP
───────────────────────────────────────

"""
            
            for i, group in enumerate(groups[:15], 1):
                group_id = group.get('group_id', 'N/A')
                title = group.get('group_title', 'Unknown')[:20]
                anti_link = "✅" if group.get('anti_link') else "❌"
                anti_spam = "✅" if group.get('anti_spam') else "❌"
                
                group_text += f"{i}. {title}\n"
                group_text += f"   ID: {group_id}\n"
                group_text += f"   Anti-Link: {anti_link} | Anti-Spam: {anti_spam}\n\n"
            
            if len(groups) > 15:
                group_text += f"... dan {len(groups) - 15} grup lainnya\n"
            
            group_text += """
───────────────────────────────────────
```"""
            
            await update.message.reply_text(
                group_text,
                parse_mode="Markdown",
                reply_markup=get_manajemen_grup_keyboard()
            )
    except Exception as e:
        logger.error(f"Error fetching groups: {e}")
        await update.message.reply_text(
            "❌ Gagal mengambil data grup.",
            parse_mode="Markdown",
            reply_markup=get_manajemen_grup_keyboard()
        )
    
    return ASK_MANAJEMEN_ACTION
