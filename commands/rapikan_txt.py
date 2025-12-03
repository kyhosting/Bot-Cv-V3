import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_FILE = range(1)

def clean_text_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    for line in lines:
        cleaned = ''.join(line.split())
        cleaned = cleaned.replace('-', '')
        cleaned = cleaned.replace('(', '')
        cleaned = cleaned.replace(')', '')
        cleaned = cleaned.replace('/', '')
        cleaned = cleaned.replace('+', '')
        if cleaned:
            cleaned_lines.append(cleaned + '\n')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

async def rapikan_txt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
🚧 RAPIKAN TXT
───────────────────────────────────────

Kirim file .txt yang ingin dibersihkan
dari spasi, tanda - ( ) / dan karakter
lainnya.

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE

async def rapikan_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    if not update.message.document:
        await update.message.reply_text("```\n❌ Kirim file .txt!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    if not update.message.document.file_name.endswith('.txt'):
        await update.message.reply_text("```\n❌ File harus berformat .txt!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    file = await update.message.document.get_file()
    filepath = f"temp_{update.effective_user.id}_{update.message.document.file_name}"
    await file.download_to_drive(filepath)
    
    clean_text_file(filepath)
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        await update.message.reply_document(
            document=open(filepath, 'rb'),
            filename=f"cleaned_{update.message.document.file_name}",
            caption="```\n✅ Berhasil merapikan TXT!\n\nKetik 'menu' untuk kembali.\n```",
            parse_mode="Markdown",
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
