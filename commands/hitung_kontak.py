import os
import re
import vobject
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role
from commands.menu import get_main_menu_keyboard

ASK_FILE = range(1)

async def hitung_kontak_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "FREE"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "FREE")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
🔢 HITUNG KONTAK
───────────────────────────────────────

Kirim file .txt atau .vcf untuk 
menghitung jumlah kontak/nomor

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE

async def hitung_kontak_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    if not update.message.document:
        await update.message.reply_text("```\n❌ Kirim file .txt atau .vcf!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    filename = update.message.document.file_name
    
    if not (filename.endswith('.txt') or filename.endswith('.vcf')):
        await update.message.reply_text("```\n❌ File harus berformat .txt atau .vcf!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    file = await update.message.document.get_file()
    filepath = f"temp_{update.effective_user.id}_{filename}"
    await file.download_to_drive(filepath)
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        if filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            numbers = re.findall(r'\d+', content)
            total = len(numbers)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                vcf_content = f.read()
            vcard_list = list(vobject.readComponents(vcf_content))
            total = len(vcard_list)
        
        text = f"""```
✅ HASIL PERHITUNGAN
───────────────────────────────────────

Nama File  : {filename}
Total Kontak: {total}

───────────────────────────────────────
```"""
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
        
    except Exception as e:
        await update.message.reply_text(f"```\n❌ Error: {str(e)}\n```",
                parse_mode="Markdown", reply_markup=keyboard)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
    
    return ConversationHandler.END
