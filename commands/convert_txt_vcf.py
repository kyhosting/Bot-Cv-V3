import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_FILE, ASK_FILENAME, ASK_CONTACTNAME = range(3)

def create_vcf_file(phone_numbers, contact_name, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for i, phone in enumerate(phone_numbers, start=1):
            phone_str = str(phone).strip()
            if not phone_str.startswith('+') and not phone_str.startswith('0'):
                phone_str = '+' + phone_str
            
            vcf_entry = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name} {str(i).zfill(4)}
TEL;TYPE=CELL:{phone_str}
END:VCARD

"""
            f.write(vcf_entry)

async def txt_to_vcf_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
🏷️ TXT TO VCF
───────────────────────────────────────

Kirim file .txt yang berisi nomor telepon
untuk dikonversi menjadi file .vcf

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE

async def txt_to_vcf_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    numbers = re.findall(r'\d+', content)
    
    if not numbers:
        os.remove(filepath)
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Tidak ada nomor ditemukan!\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    context.user_data['phone_numbers'] = numbers
    context.user_data['txt_filepath'] = filepath
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = f"""```
📝 NAMA FILE VCF
───────────────────────────────────────

Total nomor ditemukan: {len(numbers)}

Masukkan nama file output
(tanpa ekstensi .vcf)

Contoh: kontak

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILENAME

async def txt_to_vcf_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'txt_filepath' in context.user_data and os.path.exists(context.user_data['txt_filepath']):
            os.remove(context.user_data['txt_filepath'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    context.user_data['vcf_filename'] = update.message.text.strip()
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
👤 NAMA KONTAK
───────────────────────────────────────

Masukkan format nama kontak
(akan ditambah nomor urut otomatis)

Contoh: kontak
Hasil: kontak 0001, kontak 0002, ...

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_CONTACTNAME

async def txt_to_vcf_contactname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'txt_filepath' in context.user_data and os.path.exists(context.user_data['txt_filepath']):
            os.remove(context.user_data['txt_filepath'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    contact_name = update.message.text.strip()
    phone_numbers = context.user_data.get('phone_numbers', [])
    vcf_filename = context.user_data.get('vcf_filename', 'output')
    
    vcf_filepath = f"temp_{update.effective_user.id}_{vcf_filename}.vcf"
    
    create_vcf_file(phone_numbers, contact_name, vcf_filepath)
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        await update.message.reply_document(
            document=open(vcf_filepath, 'rb'),
            filename=f"{vcf_filename}.vcf",
            caption=f"✅ Berhasil convert TXT to VCF!\n📂 Total: {len(phone_numbers)} kontak",
            reply_markup=keyboard
        )
        
        user_data = get_user_data(update.effective_user.id)
        total_ops = user_data.get("total_operations", 0) + 1
        update_user_data(update.effective_user.id, {"total_operations": total_ops})
        
    except Exception as e:
        await update.message.reply_text(f"```\n❌ Error: {str(e)}\n```",
                parse_mode="Markdown", reply_markup=keyboard)
    finally:
        if 'txt_filepath' in context.user_data and os.path.exists(context.user_data['txt_filepath']):
            os.remove(context.user_data['txt_filepath'])
        if os.path.exists(vcf_filepath):
            os.remove(vcf_filepath)
    
    return ConversationHandler.END
