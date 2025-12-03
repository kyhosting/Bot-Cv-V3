import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from config import is_owner

logger = logging.getLogger(__name__)


def get_main_menu_keyboard(user_id):
    if is_owner(user_id):
        keyboard = [
            [KeyboardButton("🜲 MSG TO TXT 🜲"), KeyboardButton("🜲 TXT TO VCF 🜲")],
            [KeyboardButton("🜲 VCF TO TXT 🜲"), KeyboardButton("🜲 XLS TO VCF 🜲")],
            [KeyboardButton("🜲 RAPIKAN TXT 🜲"), KeyboardButton("🜲 GABUNG FILE 🜲")],
            [KeyboardButton("🜲 HITUNG KONTAK 🜲"), KeyboardButton("🜲 CEK NAMA 🜲")],
            [KeyboardButton("🜲 SPLIT FILE 🜲"), KeyboardButton("🜲 CREATE ADM/NAVY 🜲")],
            [KeyboardButton("🜲 STATUS 🜲"), KeyboardButton("🜲 Redeem 🜲")],
            [KeyboardButton("🜲 Owner Panel 🜲"), KeyboardButton("🜲 Monitoring Bot 🜲")],
            [KeyboardButton("🔙 KEMBALI 🔙")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🜲 MSG TO TXT 🜲"), KeyboardButton("🜲 TXT TO VCF 🜲")],
            [KeyboardButton("🜲 VCF TO TXT 🜲"), KeyboardButton("🜲 XLS TO VCF 🜲")],
            [KeyboardButton("🜲 RAPIKAN TXT 🜲"), KeyboardButton("🜲 GABUNG FILE 🜲")],
            [KeyboardButton("🜲 HITUNG KONTAK 🜲"), KeyboardButton("🜲 CEK NAMA 🜲")],
            [KeyboardButton("🜲 SPLIT FILE 🜲"), KeyboardButton("🜲 CREATE ADM/NAVY 🜲")],
            [KeyboardButton("🜲 STATUS 🜲"), KeyboardButton("🜲 Redeem 🜲")],
            [KeyboardButton("🔙 KEMBALI 🔙")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = get_main_menu_keyboard(user_id)
    
    text = """```
🜲 MENU UTAMA 🜲
───────────────────────────────────────

Pilih menu yang tersedia di bawah ini:

───────────────────────────────────────
⚡ FITUR UTAMA
───────────────────────────────────────
🜲 STATUS             — Cek status akun & akses          
🜲 MSG → TXT          — Ubah pesan menjadi teks          
🜲 TXT → VCF          — Konversi teks menjadi VCF        
🜲 VCF → TXT          — Konversi VCF menjadi teks        
🜲 BUAT ADMIN & NAVY  — Kelola admin/Navy               
🜲 RAPIKAN TXT        — Bersihkan dan rapikan TXT       
🜲 XLS → VCF          — Ekstrak data dari XLS ke VCF    
🜲 GABUNG FILE        — Gabungkan beberapa file         
🜲 HITUNG KONTAK      — Hitung jumlah kontak            
🜲 CEK NAMA KONTAK    — Cek/memperbarui nama kontak     
🜲 SPLIT FILE         — Bagi file menjadi beberapa       
🎁 REDEEM CODE        — Tukarkan kode redeem           

───────────────────────────────────────
KIFZL DEV BOT (BY @KIFZLDEV)                          
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text, 
        parse_mode="Markdown", 
        reply_markup=keyboard
    )
