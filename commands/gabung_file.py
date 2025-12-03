import os
import re
import vobject
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from commands.vip_system import check_access, send_access_denied, get_user_role, update_user_data, get_user_data
from commands.menu import get_main_menu_keyboard

ASK_FILES, ASK_FILENAME = range(2)

async def gabung_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not check_access(user_id, "VIP"):
        user_role = get_user_role(user_id)
        await send_access_denied(update, user_role, "VIP")
        return ConversationHandler.END
    
    context.user_data['merge_files'] = []
    
    cancel_keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("✅ SELESAI ✅")],
        [KeyboardButton("❌ BATAL ❌")]
    ], resize_keyboard=True)
    
    text = """```
🗄️ GABUNG FILE
───────────────────────────────────────

Kirim file-file yang ingin digabung
(format .txt atau .vcf)

Kirim satu per satu, lalu tekan
"✅ SELESAI ✅" jika sudah

───────────────────────────────────────
```"""
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
    return ASK_FILES

async def gabung_file_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        for filepath in context.user_data.get('merge_files', []):
            if os.path.exists(filepath['path']):
                os.remove(filepath['path'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    if update.message.text == "✅ SELESAI ✅":
        if len(context.user_data.get('merge_files', [])) < 2:
            await update.message.reply_text("```\n❌ Minimal 2 file untuk digabung!\n```", parse_mode="Markdown")
            return ASK_FILES
        
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ BATAL ❌")]], resize_keyboard=True)
        
        text = f"""```
📝 NAMA FILE OUTPUT
───────────────────────────────────────

Total file: {len(context.user_data['merge_files'])}

Masukkan nama file hasil gabungan
(tanpa ekstensi)

───────────────────────────────────────
```"""
        
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=cancel_keyboard)
        return ASK_FILENAME
    
    if not update.message.document:
        await update.message.reply_text("```\n❌ Kirim file .txt atau .vcf!\n```", parse_mode="Markdown")
        return ASK_FILES
    
    filename = update.message.document.file_name
    
    if not (filename.endswith('.txt') or filename.endswith('.vcf')):
        await update.message.reply_text("```\n❌ File harus .txt atau .vcf!\n```", parse_mode="Markdown")
        return ASK_FILES
    
    file_type = 'txt' if filename.endswith('.txt') else 'vcf'
    
    if context.user_data.get('merge_files'):
        first_type = context.user_data['merge_files'][0]['type']
        if file_type != first_type:
            await update.message.reply_text(f"```\n❌ Semua file harus format .{first_type}!\n```", parse_mode="Markdown")
            return ASK_FILES
    
    file = await update.message.document.get_file()
    filepath = f"temp_{update.effective_user.id}_{len(context.user_data.get('merge_files', []))}_{filename}"
    await file.download_to_drive(filepath)
    
    context.user_data['merge_files'].append({
        'path': filepath,
        'type': file_type,
        'name': filename
    })
    
    await update.message.reply_text(f"```\n✅ File #{len(context.user_data['merge_files'])} ditambahkan!\n\nKirim file lagi atau tekan SELESAI\n```", parse_mode="Markdown")
    return ASK_FILES

async def gabung_file_merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ BATAL ❌":
        for filepath in context.user_data.get('merge_files', []):
            if os.path.exists(filepath['path']):
                os.remove(filepath['path'])
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await update.message.reply_text("```\n❌ Proses dibatalkan\n```",
                parse_mode="Markdown", reply_markup=keyboard)
        return ConversationHandler.END
    
    output_name = update.message.text.strip()
    merge_files = context.user_data.get('merge_files', [])
    file_type = merge_files[0]['type']
    
    output_filepath = f"temp_{update.effective_user.id}_{output_name}.{file_type}"
    
    keyboard = get_main_menu_keyboard(update.effective_user.id)
    
    try:
        if file_type == 'txt':
            with open(output_filepath, 'w', encoding='utf-8') as outfile:
                for file_info in merge_files:
                    with open(file_info['path'], 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read() + '\n')
            
            with open(output_filepath, 'r') as f:
                total_numbers = len(re.findall(r'\d+', f.read()))
            total_count = total_numbers
        else:
            all_vcards = []
            for file_info in merge_files:
                with open(file_info['path'], 'r', encoding='utf-8') as f:
                    vcf_content = f.read()
                all_vcards.extend(list(vobject.readComponents(vcf_content)))
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                for vcard in all_vcards:
                    f.write(vcard.serialize())
            
            total_count = len(all_vcards)
        
        await update.message.reply_document(
            document=open(output_filepath, 'rb'),
            filename=f"{output_name}.{file_type}",
            caption=f"✅ Berhasil gabung {len(merge_files)} file!\n📂 Total: {total_count} kontak",
            reply_markup=keyboard
        )
        
        user_data = get_user_data(update.effective_user.id)
        total_ops = user_data.get("total_operations", 0) + 1
        update_user_data(update.effective_user.id, {"total_operations": total_ops})
        
    except Exception as e:
        await update.message.reply_text(f"```\n❌ Error: {str(e)}\n```",
                parse_mode="Markdown", reply_markup=keyboard)
    finally:
        for file_info in merge_files:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
        if os.path.exists(output_filepath):
            os.remove(output_filepath)
    
    return ConversationHandler.END
