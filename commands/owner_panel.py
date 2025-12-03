import logging
import random
import string
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import is_owner

logger = logging.getLogger(__name__)

ASK_ACTION = 0
ASK_USER_ID = 1
ASK_DURATION = 2
ASK_CODE_TYPE = 3
ASK_CODE_VALUE = 4
ASK_CODE_DURATION = 5
ASK_CODE_LIMIT = 6
ASK_CODE_EXPIRY = 7
ASK_BROADCAST_TYPE = 8
ASK_BROADCAST_MSG = 9

db_available = False
try:
    from database.models import UserModel, VIPAccessModel, VVIPAccessModel, RedeemCodeModel, ActivityLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


def get_cancel_keyboard():
    keyboard = [[KeyboardButton("🔙 KEMBALI 🔙")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_owner_panel_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Lihat Semua User 🜲")],
        [KeyboardButton("🜲 Ban User 🜲"), KeyboardButton("🜲 Unban User 🜲")],
        [KeyboardButton("🜲 Tambah VIP 🜲"), KeyboardButton("🜲 Tambah VVIP 🜲")],
        [KeyboardButton("🜲 Buat Redeem 🜲"), KeyboardButton("🜲 Lihat Redeem 🜲")],
        [KeyboardButton("🜲 Broadcast 🜲"), KeyboardButton("🜲 Statistik 🜲")],
        [KeyboardButton("🜲 Reset Limit 🜲"), KeyboardButton("🜲 Export Data 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def owner_panel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "⚠️ Akses Ditolak\nAnda tidak memiliki akses ke menu owner.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    text = """```
👑 OWNER PANEL
───────────────────────────────────────

Selamat datang di Panel Owner!
Pilih aksi yang ingin dilakukan:

───────────────────────────────────────
MANAJEMEN USER
───────────────────────────────────────
🜲 Lihat Semua User  — Lihat daftar user
🜲 Ban/Unban User    — Kelola akses user
🜲 Edit VIP/VVIP     — Atur membership
🜲 Reset Limit       — Reset limit harian

───────────────────────────────────────
REDEEM CODE
───────────────────────────────────────
🜲 Buat Redeem       — Generate kode baru
🜲 Lihat Redeem      — Lihat semua kode

───────────────────────────────────────
LAINNYA
───────────────────────────────────────
🜲 Broadcast         — Kirim pesan massal
🜲 Export Data       — Export data user
🜲 Statistik         — Lihat statistik bot

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_owner_panel_keyboard()
    )
    return ASK_ACTION


async def owner_panel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if text == "🜲 Lihat Semua User 🜲":
        return await show_all_users(update, context)
    
    elif text == "🜲 Ban User 🜲":
        context.user_data['owner_action'] = 'ban'
        await update.message.reply_text(
            "Masukkan User ID yang ingin di-ban:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_USER_ID
    
    elif text == "🜲 Unban User 🜲":
        context.user_data['owner_action'] = 'unban'
        await update.message.reply_text(
            "Masukkan User ID yang ingin di-unban:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_USER_ID
    
    elif text == "🜲 Tambah VIP 🜲":
        context.user_data['owner_action'] = 'add_vip'
        await update.message.reply_text(
            "Masukkan User ID yang ingin ditambahkan VIP:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_USER_ID
    
    elif text == "🜲 Tambah VVIP 🜲":
        context.user_data['owner_action'] = 'add_vvip'
        await update.message.reply_text(
            "Masukkan User ID yang ingin ditambahkan VVIP:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_USER_ID
    
    elif text == "🜲 Buat Redeem 🜲":
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("VIP"), KeyboardButton("VVIP")],
            [KeyboardButton("🔙 KEMBALI 🔙")]
        ], resize_keyboard=True)
        await update.message.reply_text(
            "Pilih tipe redeem code:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return ASK_CODE_TYPE
    
    elif text == "🜲 Lihat Redeem 🜲":
        return await show_all_redeem(update, context)
    
    elif text == "🜲 Broadcast 🜲":
        keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("Semua User"), KeyboardButton("VIP Only")],
            [KeyboardButton("VVIP Only")],
            [KeyboardButton("🔙 KEMBALI 🔙")]
        ], resize_keyboard=True)
        await update.message.reply_text(
            "Pilih target broadcast:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return ASK_BROADCAST_TYPE
    
    elif text == "🜲 Statistik 🜲":
        return await show_statistics(update, context)
    
    elif text == "🜲 Reset Limit 🜲":
        context.user_data['owner_action'] = 'reset_limit'
        await update.message.reply_text(
            "Masukkan User ID yang limitnya ingin di-reset:",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_USER_ID
    
    elif text == "🜲 Export Data 🜲":
        return await export_data(update, context)
    
    return ASK_ACTION


async def owner_panel_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        target_user_id = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ User ID tidak valid. Masukkan angka saja.",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_USER_ID
    
    context.user_data['target_user_id'] = target_user_id
    action = context.user_data.get('owner_action')
    
    if action in ['add_vip', 'add_vvip']:
        await update.message.reply_text(
            "Masukkan durasi dalam hari (contoh: 7, 30, 365):",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_DURATION
    
    elif action == 'ban':
        if db_available:
            try:
                db = get_db()
                if db.is_connected:
                    await UserModel.ban_user(target_user_id, True)
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="ban_user",
                        details={"target": target_user_id}
                    )
                    await update.message.reply_text(
                        f"✅ User {target_user_id} berhasil di-ban",
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
            except Exception as e:
                logger.error(f"Ban error: {e}")
                await update.message.reply_text(
                    "❌ Gagal ban user.",
                    parse_mode="Markdown",
                    reply_markup=get_owner_panel_keyboard()
                )
        return ASK_ACTION
    
    elif action == 'unban':
        if db_available:
            try:
                db = get_db()
                if db.is_connected:
                    await UserModel.ban_user(target_user_id, False)
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="unban_user",
                        details={"target": target_user_id}
                    )
                    await update.message.reply_text(
                        f"✅ User {target_user_id} berhasil di-unban",
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
            except Exception as e:
                logger.error(f"Unban error: {e}")
                await update.message.reply_text(
                    "❌ Gagal unban user.",
                    parse_mode="Markdown",
                    reply_markup=get_owner_panel_keyboard()
                )
        return ASK_ACTION
    
    elif action == 'reset_limit':
        if db_available:
            try:
                db = get_db()
                if db.is_connected:
                    await UserModel.reset_daily_limit(target_user_id)
                    await update.message.reply_text(
                        f"✅ Limit user {target_user_id} berhasil di-reset",
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
            except Exception as e:
                logger.error(f"Reset limit error: {e}")
                await update.message.reply_text(
                    "❌ Gagal reset limit.",
                    parse_mode="Markdown",
                    reply_markup=get_owner_panel_keyboard()
                )
        return ASK_ACTION
    
    return ASK_ACTION


async def owner_panel_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        duration = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Durasi tidak valid. Masukkan angka saja.",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return ASK_DURATION
    
    target_user_id = context.user_data.get('target_user_id')
    action = context.user_data.get('owner_action')
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                if action == 'add_vip':
                    await VIPAccessModel.grant_access(target_user_id, duration)
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="add_vip",
                        details={"target": target_user_id, "duration": duration}
                    )
                    await update.message.reply_text(
                        f"✅ VIP berhasil ditambahkan\n\nUser: `{target_user_id}`\nDurasi: {duration} hari",
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
                elif action == 'add_vvip':
                    await VVIPAccessModel.grant_access(target_user_id, duration)
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="add_vvip",
                        details={"target": target_user_id, "duration": duration}
                    )
                    await update.message.reply_text(
                        f"✅ VVIP berhasil ditambahkan\n\nUser: `{target_user_id}`\nDurasi: {duration} hari",
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
        except Exception as e:
            logger.error(f"Add access error: {e}")
            await update.message.reply_text(
                "❌ Gagal menambahkan akses.",
                parse_mode="Markdown",
                reply_markup=get_owner_panel_keyboard()
            )
    
    return ASK_ACTION


async def owner_panel_code_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    if text not in ["VIP", "VVIP"]:
        await update.message.reply_text(
            "❌ Pilih VIP atau VVIP.",
            parse_mode="Markdown"
        )
        return ASK_CODE_TYPE
    
    context.user_data['code_type'] = text.lower()
    await update.message.reply_text(
        "Masukkan kode redeem (atau ketik 'AUTO' untuk generate otomatis):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_CODE_VALUE


async def owner_panel_code_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    if text.upper() == "AUTO":
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    else:
        code = text.strip().upper()
    
    context.user_data['redeem_code'] = code
    await update.message.reply_text(
        "Masukkan durasi VIP/VVIP dalam hari:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_CODE_DURATION


async def owner_panel_code_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        duration = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Durasi tidak valid.",
            parse_mode="Markdown"
        )
        return ASK_CODE_DURATION
    
    context.user_data['code_duration'] = duration
    await update.message.reply_text(
        "Masukkan batas penggunaan (contoh: 1, 5, 10):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_CODE_LIMIT


async def owner_panel_code_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        max_uses = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Batas tidak valid.",
            parse_mode="Markdown"
        )
        return ASK_CODE_LIMIT
    
    context.user_data['code_limit'] = max_uses
    await update.message.reply_text(
        "Masukkan masa expired kode dalam hari (contoh: 30, 60):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_CODE_EXPIRY


async def owner_panel_code_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        expiry_days = int(text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Masa expired tidak valid.",
            parse_mode="Markdown"
        )
        return ASK_CODE_EXPIRY
    
    code = context.user_data.get('redeem_code')
    code_type = context.user_data.get('code_type')
    duration = context.user_data.get('code_duration')
    max_uses = context.user_data.get('code_limit')
    
    if db_available:
        try:
            db = get_db()
            if db.is_connected:
                result = await RedeemCodeModel.create_code(
                    code=code,
                    code_type=code_type,
                    duration_days=duration,
                    max_uses=max_uses,
                    expired_days=expiry_days,
                    issuer_id=update.effective_user.id
                )
                
                if result:
                    await ActivityLogModel.log(
                        user_id=update.effective_user.id,
                        action="create_redeem",
                        details={"code": code, "type": code_type, "duration": duration}
                    )
                    
                    success_text = f"""```
🎉 REDEEM CODE BERHASIL DIBUAT
───────────────────────────────────────

🔑 Kode    : {code}
⭐ Akses   : {code_type.upper()}
📌 Limit   : {max_uses} pengguna
🕒 Durasi  : {duration} hari
📅 Expired : {expiry_days} hari

───────────────────────────────────────
```"""
                    
                    await update.message.reply_text(
                        success_text,
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
                else:
                    await update.message.reply_text(
                        "❌ Gagal membuat kode redeem.",
                        parse_mode="Markdown",
                        reply_markup=get_owner_panel_keyboard()
                    )
        except Exception as e:
            logger.error(f"Create redeem error: {e}")
            await update.message.reply_text(
                "❌ Gagal membuat kode redeem.",
                parse_mode="Markdown",
                reply_markup=get_owner_panel_keyboard()
            )
    
    return ASK_ACTION


async def owner_panel_broadcast_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    context.user_data['broadcast_type'] = text
    await update.message.reply_text(
        "Masukkan pesan broadcast:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    return ASK_BROADCAST_MSG


async def owner_panel_broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🔙 KEMBALI 🔙":
        await update.message.reply_text(
            "Kembali ke Owner Panel.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    broadcast_type = context.user_data.get('broadcast_type')
    
    await update.message.reply_text(
        f"📢 Broadcast Dijadwalkan\n\nTarget: {broadcast_type}\nPesan akan dikirim segera.",
        parse_mode="Markdown",
        reply_markup=get_owner_panel_keyboard()
    )
    return ASK_ACTION


async def show_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        db = get_db()
        if db.is_connected:
            users = await UserModel.get_all_users()
            
            if not users:
                await update.message.reply_text(
                    "Belum ada user terdaftar.",
                    parse_mode="Markdown",
                    reply_markup=get_owner_panel_keyboard()
                )
                return ASK_ACTION
            
            user_list = "📋 Daftar User\n\n"
            for i, user in enumerate(users[:20], 1):
                user_list += f"{i}. `{user.get('user_id')}` - {user.get('username', 'N/A')} ({user.get('role')})\n"
            
            if len(users) > 20:
                user_list += f"\n... dan {len(users) - 20} user lainnya"
            
            await update.message.reply_text(
                user_list,
                parse_mode="Markdown",
                reply_markup=get_owner_panel_keyboard()
            )
    except Exception as e:
        logger.error(f"Show users error: {e}")
        await update.message.reply_text(
            "❌ Gagal mengambil data user.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
    
    return ASK_ACTION


async def show_all_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        db = get_db()
        if db.is_connected:
            codes = await RedeemCodeModel.get_all_codes()
            
            if not codes:
                await update.message.reply_text(
                    "Belum ada kode redeem.",
                    parse_mode="Markdown",
                    reply_markup=get_owner_panel_keyboard()
                )
                return ASK_ACTION
            
            code_list = "📋 Daftar Redeem Code\n\n"
            for i, code in enumerate(codes[:15], 1):
                status_emoji = "✅" if code.get('status') == 'active' else "❌"
                code_list += f"{i}. `{code.get('code')}` {status_emoji} - {code.get('type').upper()} ({code.get('current_uses')}/{code.get('max_uses')})\n"
            
            if len(codes) > 15:
                code_list += f"\n... dan {len(codes) - 15} kode lainnya"
            
            await update.message.reply_text(
                code_list,
                parse_mode="Markdown",
                reply_markup=get_owner_panel_keyboard()
            )
    except Exception as e:
        logger.error(f"Show redeem error: {e}")
        await update.message.reply_text(
            "❌ Gagal mengambil data redeem.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
    
    return ASK_ACTION


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_available:
        await update.message.reply_text(
            "❌ Database tidak tersedia.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
        return ASK_ACTION
    
    try:
        db = get_db()
        if db.is_connected:
            total_users = await UserModel.count_total()
            role_counts = await UserModel.count_by_role()
            vip_count = await VIPAccessModel.count_active()
            vvip_count = await VVIPAccessModel.count_active()
            
            stats_text = f"""```
📊 STATISTIK BOT
───────────────────────────────────────

👥 Total User  : {total_users}
⭐ Reguler     : {role_counts.get('reguler', 0)}
💎 VIP Aktif   : {vip_count}
👑 VVIP Aktif  : {vvip_count}

───────────────────────────────────────
```"""
            
            await update.message.reply_text(
                stats_text,
                parse_mode="Markdown",
                reply_markup=get_owner_panel_keyboard()
            )
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await update.message.reply_text(
            "❌ Gagal mengambil statistik.",
            parse_mode="Markdown",
            reply_markup=get_owner_panel_keyboard()
        )
    
    return ASK_ACTION


async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📤 Export Data\n\nFitur export sedang dalam pengembangan.",
        parse_mode="Markdown",
        reply_markup=get_owner_panel_keyboard()
    )
    return ASK_ACTION
