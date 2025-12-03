import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_MODE, ASK_ADMIN_NUM, ASK_NAVY_NUM, ASK_FILENAME, ASK_CONTACTNAME, ASK_BLOCK_INPUT = range(6)

def create_vcf_entry(phone_number, contact_name):
    phone_str = str(phone_number).strip()
    if not phone_str.startswith('+') and not phone_str.startswith('0'):
        phone_str = '+' + phone_str
    
    vcf_entry = f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
TEL;TYPE=CELL:{phone_str}
END:VCARD

"""
    return vcf_entry

async def create_admin_navy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    mode_keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("MODE A - GUIDED")],
        [KeyboardButton("MODE B - AUTO PARSE")],
        [KeyboardButton("MODE C - MINIMAL")],
        [KeyboardButton("❌ BATAL ❌")]
    ], resize_keyboard=True)
    
    text = """```
📨 CREATE ADMIN & NAVY
───────────────────────────────────────

Pilih mode yang ingin digunakan:

MODE A - GUIDED
Input bertahap (satu per satu)

MODE B - AUTO PARSE
Input block teks otomatis

MODE C - MINIMAL
Input satu nomor minimal

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=mode_keyboard)
    return ASK_MODE

async def create_admin_navy_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    mode = update.message.text
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    if mode == "MODE A - GUIDED":
        context.user_data['admin_navy_mode'] = 'A'
        
        text = """```
📞 NOMOR ADMIN
───────────────────────────────────────

MODE A - GUIDED

Kirimkan nomor Admin
(format +62... atau 0...)

Bisa kirim beberapa nomor dengan enter

───────────────────────────────────────
```"""
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
        return ASK_ADMIN_NUM
        
    elif mode == "MODE B - AUTO PARSE":
        context.user_data['admin_navy_mode'] = 'B'
        
        text = """```
📋 INPUT BLOCK
───────────────────────────────────────

MODE B - AUTO PARSE

Kirim block teks dengan format:
ADMIN
+628123456789
NAVY
+628987654321

Bot akan parse otomatis!

───────────────────────────────────────
```"""
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
        return ASK_BLOCK_INPUT
        
    elif mode == "MODE C - MINIMAL":
        context.user_data['admin_navy_mode'] = 'C'
        
        text = """```
📞 NOMOR TELEPON
───────────────────────────────────────

MODE C - MINIMAL

Kirim 1 nomor telepon
(format +62... atau 0...)

───────────────────────────────────────
```"""
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
        return ASK_ADMIN_NUM
    
    else:
        await update.message.reply_text("```\n❌ Pilih mode yang valid!\n```", parse_mode="Markdown")
        return ASK_MODE

async def create_admin_navy_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    admin_numbers = update.message.text.strip().split('\n')
    admin_numbers = [num.strip() for num in admin_numbers if num.strip()]
    context.user_data['admin_numbers'] = admin_numbers
    
    mode = context.user_data.get('admin_navy_mode')
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    if mode == 'C':
        text = """```
📝 NAMA FILE
───────────────────────────────────────

Masukkan nama file output
(tanpa ekstensi .vcf)

Contoh: ADMIN DAN NAVY

───────────────────────────────────────
```"""
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
        context.user_data['navy_numbers'] = []
        return ASK_FILENAME
    
    text = """```
🚢 NOMOR NAVY
───────────────────────────────────────

Kirimkan nomor Navy
(format +62... atau 0...)

Bisa kirim beberapa nomor dengan enter

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_NAVY_NUM

async def create_admin_navy_navy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    navy_numbers = update.message.text.strip().split('\n')
    navy_numbers = [num.strip() for num in navy_numbers if num.strip()]
    context.user_data['navy_numbers'] = navy_numbers
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
📝 NAMA FILE
───────────────────────────────────────

Masukkan nama file output
(tanpa ekstensi .vcf)

Contoh: ADMIN DAN NAVY

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILENAME

async def create_admin_navy_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    context.user_data['vcf_filename'] = update.message.text.strip()
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
👤 FORMAT NAMA KONTAK
───────────────────────────────────────

Masukkan format nama kontak

Contoh: admin
Hasil: admin 01, navy 01

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_CONTACTNAME

async def create_admin_navy_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    contact_format = update.message.text.strip()
    admin_numbers = context.user_data.get('admin_numbers', [])
    navy_numbers = context.user_data.get('navy_numbers', [])
    vcf_filename = context.user_data.get('vcf_filename', 'output')
    
    vcf_filepath = f"temp_{update.effective_user.id}_{vcf_filename}.vcf"
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        with open(vcf_filepath, 'w', encoding='utf-8') as f:
            index = 1
            for phone in admin_numbers:
                vcf_entry = create_vcf_entry(phone, f"{contact_format} {str(index).zfill(2)}")
                f.write(vcf_entry)
                index += 1
            
            for phone in navy_numbers:
                vcf_entry = create_vcf_entry(phone, f"navy {str(index).zfill(2)}")
                f.write(vcf_entry)
                index += 1
        
        total_contacts = len(admin_numbers) + len(navy_numbers)
        
        await update.message.reply_document(
            document=open(vcf_filepath, 'rb'),
            filename=f"{vcf_filename}.vcf",
            caption=f"✅ Berhasil create ADMIN & NAVY!\n📂 Total: {total_contacts} kontak\n   Admin: {len(admin_numbers)} | Navy: {len(navy_numbers)}",
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
    
    return ConversationHandler.END

async def create_admin_navy_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    block_text = update.message.text.strip()
    lines = block_text.split('\n')
    
    admin_numbers = []
    navy_numbers = []
    current_category = None
    
    for line in lines:
        line = line.strip()
        if line.upper() == 'ADMIN':
            current_category = 'ADMIN'
        elif line.upper() == 'NAVY':
            current_category = 'NAVY'
        elif line and (line.startswith('+') or line.startswith('0') or line.isdigit()):
            if current_category == 'ADMIN':
                admin_numbers.append(line)
            elif current_category == 'NAVY':
                navy_numbers.append(line)
    
    if not admin_numbers and not navy_numbers:
        await update.message.reply_text("```\n❌ Tidak ada nomor valid ditemukan!\n```", parse_mode="Markdown")
        return ASK_BLOCK_INPUT
    
    context.user_data['admin_numbers'] = admin_numbers
    context.user_data['navy_numbers'] = navy_numbers
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = f"""```
📝 NAMA FILE
───────────────────────────────────────

Total parsed:
Admin: {len(admin_numbers)}
Navy: {len(navy_numbers)}

Masukkan nama file output
(tanpa ekstensi .vcf)

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILENAME
