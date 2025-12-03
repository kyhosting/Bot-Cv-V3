import os
import re
import vobject
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_FILE, ASK_OUTPUT_NAME, ASK_FILE_PREFIX, ASK_CONTACT_PREFIX, ASK_SPLIT_MODE, ASK_SPLIT_VALUE = range(6)

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def rename_contacts_split(contacts, start_index, contact_prefix):
    renamed_contacts = []
    for index, contact in enumerate(contacts, start=start_index):
        if hasattr(contact, 'fn'):
            clean_name = re.sub(r'\d+', '', contact.fn.value).strip()
            clean_name = remove_emojis(clean_name)
            contact.fn.value = f'{clean_name} {str(index).zfill(2)}'
        renamed_contacts.append(contact)
    return renamed_contacts

async def split_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
✂️ SPLIT FILE
───────────────────────────────────────

Kirim file .txt atau .vcf yang ingin
dipecah menjadi beberapa file

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE

async def split_file_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```", parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    if not update.message.document:
        await update.message.reply_text("```\n❌ Kirim file .txt atau .vcf!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    filename = update.message.document.file_name
    
    if not (filename.endswith('.txt') or filename.endswith('.vcf')):
        await update.message.reply_text("```\n❌ File harus .txt atau .vcf!\n```", parse_mode="Markdown")
        return ASK_FILE
    
    file = await update.message.document.get_file()
    filepath = f"temp_{update.effective_user.id}_{filename}"
    await file.download_to_drive(filepath)
    
    file_type = 'txt' if filename.endswith('.txt') else 'vcf'
    context.user_data['split_file'] = filepath
    context.user_data['split_type'] = file_type
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
📝 NAMA FILE OUTPUT
───────────────────────────────────────

Masukkan nama dasar file output
(tanpa ekstensi)

Contoh: kontak
Hasil: kontak1, kontak2, kontak3...

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_OUTPUT_NAME

async def split_file_output_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'split_file' in context.user_data and os.path.exists(context.user_data['split_file']):
            os.remove(context.user_data['split_file'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```", parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    context.user_data['output_name'] = update.message.text.strip()
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
🔢 AWALAN NOMOR FILE
───────────────────────────────────────

Masukkan awalan nomor file

Contoh: 1
Hasil: kontak1, kontak2, kontak3...

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILE_PREFIX

async def split_file_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'split_file' in context.user_data and os.path.exists(context.user_data['split_file']):
            os.remove(context.user_data['split_file'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```", parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    try:
        file_prefix = int(update.message.text.strip())
        context.user_data['file_prefix'] = file_prefix
    except:
        await update.message.reply_text("```\n❌ Masukkan angka yang valid!\n```", parse_mode="Markdown")
        return ASK_FILE_PREFIX
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    text = """```
👤 AWALAN NOMOR KONTAK
───────────────────────────────────────

Masukkan awalan nomor kontak

Contoh: 01
Hasil: kontak 01, kontak 02, kontak 03...

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_CONTACT_PREFIX

async def split_contact_prefix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'split_file' in context.user_data and os.path.exists(context.user_data['split_file']):
            os.remove(context.user_data['split_file'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```", parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    try:
        contact_prefix = int(update.message.text.strip())
        context.user_data['contact_prefix'] = contact_prefix
    except:
        await update.message.reply_text("```\n❌ Masukkan angka yang valid!\n```", parse_mode="Markdown")
        return ASK_CONTACT_PREFIX
    
    mode_keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("PER KONTAK"), KeyboardButton("PER BAGIAN")],
        [KeyboardButton("❌ BATAL ❌")]
    ], resize_keyboard=True)
    
    text = """```
⚙️ MODE SPLIT
───────────────────────────────────────

Pilih mode split file:

PER KONTAK: Split berdasarkan jumlah
            kontak per file

PER BAGIAN: Bagi file menjadi X bagian

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=mode_keyboard)
    return ASK_SPLIT_MODE

async def split_mode_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'split_file' in context.user_data and os.path.exists(context.user_data['split_file']):
            os.remove(context.user_data['split_file'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```", parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    mode = update.message.text
    
    if mode not in ["PER KONTAK", "PER BAGIAN"]:
        await update.message.reply_text("```\n❌ Pilih mode yang valid!\n```", parse_mode="Markdown")
        return ASK_SPLIT_MODE
    
    context.user_data['split_mode'] = mode
    
    cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
    
    if mode == "PER KONTAK":
        text = """```
🔢 JUMLAH KONTAK PER FILE
───────────────────────────────────────

Masukkan jumlah kontak per file

Contoh: 50
(Setiap file akan berisi 50 kontak)

───────────────────────────────────────
```"""
    else:
        text = """```
🔢 JUMLAH BAGIAN
───────────────────────────────────────

Masukkan berapa bagian file akan dibagi

Contoh: 5
(File akan dibagi menjadi 5 file)

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_SPLIT_VALUE

async def split_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        if 'split_file' in context.user_data and os.path.exists(context.user_data['split_file']):
            os.remove(context.user_data['split_file'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```", parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    try:
        split_value = int(update.message.text.strip())
    except:
        await update.message.reply_text("```\n❌ Masukkan angka yang valid!\n```", parse_mode="Markdown")
        return ASK_SPLIT_VALUE
    
    filepath = context.user_data.get('split_file')
    file_type = context.user_data.get('split_type')
    output_name = context.user_data.get('output_name')
    file_prefix = context.user_data.get('file_prefix')
    contact_prefix = context.user_data.get('contact_prefix')
    split_mode = context.user_data.get('split_mode')
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    output_files = []
    
    try:
        if file_type == 'vcf':
            with open(filepath, 'r', encoding='utf-8') as f:
                vcf_content = f.read()
            contacts = list(vobject.readComponents(vcf_content))
            total_contacts = len(contacts)
            
            if split_mode == "PER KONTAK":
                contacts_per_file = split_value
                num_files = (total_contacts + contacts_per_file - 1) // contacts_per_file
            else:
                num_files = split_value
                contacts_per_file = (total_contacts + num_files - 1) // num_files
            
            global_contact_index = contact_prefix
            
            for i in range(num_files):
                start_idx = i * contacts_per_file
                end_idx = min(start_idx + contacts_per_file, total_contacts)
                chunk = contacts[start_idx:end_idx]
                
                renamed_chunk = rename_contacts_split(chunk, global_contact_index, contact_prefix)
                
                output_file = f"temp_{update.effective_user.id}_{output_name}{file_prefix + i}.vcf"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for contact in renamed_chunk:
                        f.write(contact.serialize())
                
                output_files.append(output_file)
                global_contact_index += len(chunk)
        
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            numbers = re.findall(r'\d+', content)
            total_numbers = len(numbers)
            
            if split_mode == "PER KONTAK":
                numbers_per_file = split_value
                num_files = (total_numbers + numbers_per_file - 1) // numbers_per_file
            else:
                num_files = split_value
                numbers_per_file = (total_numbers + num_files - 1) // num_files
            
            for i in range(num_files):
                start_idx = i * numbers_per_file
                end_idx = min(start_idx + numbers_per_file, total_numbers)
                chunk = numbers[start_idx:end_idx]
                
                output_file = f"temp_{update.effective_user.id}_{output_name}{file_prefix + i}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(chunk))
                
                output_files.append(output_file)
        
        for i, output_file in enumerate(output_files):
            await update.message.reply_document(
                document=open(output_file, 'rb'),
                filename=os.path.basename(output_file).replace(f"temp_{update.effective_user.id}_", "")
            )
        
        await update.message.reply_text(f"✅ Berhasil split!\n📂 Total: {len(output_files)} file\n📁 Nama: {output_name}", parse_mode="Markdown", reply_markup=keyboard)
        
        user_data = get_user_data(update.effective_user.id)
        total_ops = user_data.get("total_operations", 0) + 1
        update_user_data(update.effective_user.id, {"total_operations": total_ops})
        
    except Exception as e:
        await update.message.reply_text(f"```\n❌ Error: {str(e)}\n```", parse_mode="Markdown", reply_markup=keyboard)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        for output_file in output_files:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    return ConversationHandler.END
