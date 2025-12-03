import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from config import VIP_BENEFITS, VVIP_BENEFITS, VIP_PRICES, VVIP_PRICES, BOT_CREATOR

logger = logging.getLogger(__name__)


def get_vip_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Beli VIP 🜲")],
        [KeyboardButton("🜲 Lihat Benefit VIP 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_vvip_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Beli VVIP 🜲")],
        [KeyboardButton("🜲 Lihat Benefit VVIP 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def vip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    benefits_list = "\n".join([f"• {b}" for b in VIP_BENEFITS])
    
    text = f"""```
💎 VIP MEMBERSHIP
───────────────────────────────────────

Apa itu VIP?
VIP adalah membership premium yang 
memberikan akses ke fitur-fitur 
eksklusif bot.

───────────────────────────────────────
BENEFIT VIP
───────────────────────────────────────
{benefits_list}

───────────────────────────────────────
HARGA VIP
───────────────────────────────────────
• 1 Hari   : Rp {VIP_PRICES['1_day']:,}
• 7 Hari   : Rp {VIP_PRICES['7_days']:,}
• 30 Hari  : Rp {VIP_PRICES['30_days']:,}

───────────────────────────────────────
📌 Cara Beli:
Hubungi {BOT_CREATOR} untuk pembelian VIP.
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_vip_keyboard()
    )


async def vvip_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    benefits_list = "\n".join([f"• {b}" for b in VVIP_BENEFITS])
    
    text = f"""```
👑 VVIP MEMBERSHIP
───────────────────────────────────────

Apa itu VVIP?
VVIP adalah membership tertinggi 
dengan akses prioritas dan fitur 
eksklusif.

───────────────────────────────────────
BENEFIT VVIP
───────────────────────────────────────
{benefits_list}

───────────────────────────────────────
HARGA VVIP
───────────────────────────────────────
• 1 Hari   : Rp {VVIP_PRICES['1_day']:,}
• 7 Hari   : Rp {VVIP_PRICES['7_days']:,}
• 30 Hari  : Rp {VVIP_PRICES['30_days']:,}

───────────────────────────────────────
📌 Cara Beli:
Hubungi {BOT_CREATOR} untuk pembelian VVIP.
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_vvip_keyboard()
    )


async def vip_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""```
💎 BELI VIP
───────────────────────────────────────

Untuk membeli VIP, silakan hubungi:
{BOT_CREATOR}

───────────────────────────────────────
📌 Langkah Pembelian:
───────────────────────────────────────
1. Hubungi owner via Telegram
2. Pilih paket yang diinginkan
3. Transfer ke rekening yang diberikan
4. Kirim bukti transfer
5. Terima kode redeem

✨ Proses aktivasi instan setelah konfirmasi!
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_vip_keyboard()
    )


async def vvip_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""```
👑 BELI VVIP
───────────────────────────────────────

Untuk membeli VVIP, silakan hubungi:
{BOT_CREATOR}

───────────────────────────────────────
📌 Langkah Pembelian:
───────────────────────────────────────
1. Hubungi owner via Telegram
2. Pilih paket yang diinginkan
3. Transfer ke rekening yang diberikan
4. Kirim bukti transfer
5. Terima kode redeem

✨ Proses aktivasi instan setelah konfirmasi!
───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_vvip_keyboard()
    )


async def show_vip_benefits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    benefits_list = "\n".join([f"• {b}" for b in VIP_BENEFITS])
    
    text = f"""```
💎 BENEFIT VIP
───────────────────────────────────────

{benefits_list}

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_vip_keyboard()
    )


async def show_vvip_benefits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    benefits_list = "\n".join([f"• {b}" for b in VVIP_BENEFITS])
    
    text = f"""```
👑 BENEFIT VVIP
───────────────────────────────────────

{benefits_list}

───────────────────────────────────────
```"""
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_vvip_keyboard()
    )
