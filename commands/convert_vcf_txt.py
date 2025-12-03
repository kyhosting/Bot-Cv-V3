import os
import vobject
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_FILE = range(1)

def extract_phone_numbers(vcf_filepath, txt_filepath):
    with open(vcf_filepath, 'r', encoding='utf-8') as f:
        vcf_content = f.read()
    
    vcard_list = vobject.readComponents(vcf_content)
    
    with open(txt_filepath, 'w', encoding='utf-8') as f:
        for vcard in vcard_list:
            if hasattr(vcard, 'tel'):
                for tel in vcard.tel_list:
                    f.write(tel.value + '\n')

async def vcf_to_txt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
♻️ VCF TO TXT
───────────────────────────────────────

Kirim file .vcf untuk mengekstrak
nomor telepon menjadi file .txt

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE

async def vcf_to_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    if not update.message.document:
        await update.message.reply_text("```\n❌ Kirim file .vcf!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    if not update.message.document.file_name.endswith('.vcf'):
        await update.message.reply_text("```\n❌ File harus berformat .vcf!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    file = await update.message.document.get_file()
    vcf_filepath = f"temp_{update.effective_user.id}_{update.message.document.file_name}"
    await file.download_to_drive(vcf_filepath)
    
    txt_filename = update.message.document.file_name.replace('.vcf', '.txt')
    txt_filepath = f"temp_{update.effective_user.id}_{txt_filename}"
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        extract_phone_numbers(vcf_filepath, txt_filepath)
        
        with open(txt_filepath, 'r') as f:
            total_numbers = len(f.readlines())
        
        await update.message.reply_document(
            document=open(txt_filepath, 'rb'),
            filename=txt_filename,
            caption=f"✅ Berhasil extract VCF to TXT!\n📂 Total: {total_numbers} nomor",
            reply_markup=keyboard
        )
        
        user_data = get_user_data(update.effective_user.id)
        total_ops = user_data.get("total_operations", 0) + 1
        update_user_data(update.effective_user.id, {"total_operations": total_ops})
        
    except Exception as e:
        await update.message.reply_text(f"```\n❌ Error: {str(e)}\n```",
                parse_mode="Markdown", reply_markup=keyboard)
    finally:
        if os.path.exists(vcf_filepath):
            os.remove(vcf_filepath)
        if os.path.exists(txt_filepath):
            os.remove(txt_filepath)
    
    return ConversationHandler.END
