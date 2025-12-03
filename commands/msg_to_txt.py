import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_MESSAGE, ASK_FILENAME = range(2)

async def msg_to_txt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
📨 MSG TO TXT
───────────────────────────────────────

Silakan kirim pesan/teks yang ingin 
Anda ubah menjadi file .txt

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_MESSAGE

async def msg_to_txt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    context.user_data['msg_content'] = update.message.text
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
📝 NAMA FILE
───────────────────────────────────────

Masukkan nama file untuk output
(tanpa ekstensi .txt)

Contoh: kontak_saya

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILENAME

async def msg_to_txt_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    filename = update.message.text.strip()
    msg_content = context.user_data.get('msg_content', '')
    
    filepath = f"temp_{update.effective_user.id}_{filename}.txt"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(msg_content)
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        await update.message.reply_document(
            document=open(filepath, 'rb'),
            filename=f"{filename}.txt",
            caption="✅ Berhasil convert MSG to TXT!",
            reply_markup=keyboard
        )
        
        user_data = get_user_data(update.effective_user.id)
        total_ops = user_data.get("total_operations", 0) + 1
        update_user_data(update.effective_user.id, {"total_operations": total_ops})
        
    except Exception as e:
        await update.message.reply_text(f"```\n❌ Error: {str(e)}\n```",
                parse_mode="Markdown", reply_markup=keyboard)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
    
    return ConversationHandler.END
