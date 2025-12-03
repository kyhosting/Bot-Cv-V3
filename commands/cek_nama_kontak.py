import os
import vobject
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role
from commands.menu import get_main_menu_keyboard

ASK_FILE = range(1)

async def cek_nama_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "FREE"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "FREE")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
🔍 CEK NAMA KONTAK
───────────────────────────────────────

Kirim file .vcf untuk melihat
daftar nama kontak

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE

async def cek_nama_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    filepath = f"temp_{update.effective_user.id}_{update.message.document.file_name}"
    await file.download_to_drive(filepath)
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            vcf_content = f.read()
        
        vcard_list = list(vobject.readComponents(vcf_content))
        
        names = []
        for i, vcard in enumerate(vcard_list[:10], 1):
            if hasattr(vcard, 'fn'):
                names.append(f"{i}. {vcard.fn.value}")
            else:
                names.append(f"{i}. (Tanpa nama)")
        
        if len(vcard_list) > 10:
            names.append(f"\n... dan {len(vcard_list) - 10} kontak lainnya")
        
        names_text = '\n'.join(names)
        
        text = f"""```
✅ DAFTAR NAMA KONTAK
───────────────────────────────────────

Total: {len(vcard_list)} kontak

{names_text}

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
