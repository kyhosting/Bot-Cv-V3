from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from commands.menu import get_main_menu_keyboard

PACKAGES = {
    "PREM_DAY": {"name": "1 Hari", "duration": "24 Jam", "price": 5000},
    "PREM_WEEK": {"name": "7 Hari", "duration": "Mingguan", "price": 25000},
    "PREM_MONTH": {"name": "30 Hari", "duration": "Bulanan", "price": 75000}
}

async def upgradeprem_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """```
💎 UPGRADE PREMIUM
───────────────────────────────────────

Pilih paket premium yang sesuai:

🔸 1 HARI    - Rp 5.000
🔸 7 HARI    - Rp 25.000
🔸 30 HARI   - Rp 75.000

Pilih paket di bawah ini:
───────────────────────────────────────
```"""
    
    keyboard = [
        [
            InlineKeyboardButton("🕐 1 Hari", callback_data="prem_select_PREM_DAY"),
            InlineKeyboardButton("📅 7 Hari", callback_data="prem_select_PREM_WEEK"),
        ],
        [InlineKeyboardButton("📆 30 Hari", callback_data="prem_select_PREM_MONTH")],
        [InlineKeyboardButton("❌ Batalkan", callback_data="prem_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def handle_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    
    if query.data == "prem_cancel":
        keyboard = get_main_menu_keyboard(update.effective_user.id)
        await query.edit_message_text("```\n❌ Pembelian dibatalkan\n```", parse_mode="HTML")
        await query.message.reply_text("Ketik 'menu' untuk kembali", parse_mode="HTML", reply_markup=keyboard)
        return
    
    if query.data.startswith("prem_select_"):
        package_code = query.data.replace("prem_select_", "")
        context.user_data['selected_package'] = package_code
        context.user_data['quantity'] = 1
        
        await show_quantity_selector(query, context, package_code)
    
    elif query.data == "prem_qty_minus":
        qty = context.user_data.get('quantity', 1)
        if qty > 1:
            context.user_data['quantity'] = qty - 1
        package_code = context.user_data.get('selected_package')
        await show_quantity_selector(query, context, package_code)
    
    elif query.data == "prem_qty_plus":
        qty = context.user_data.get('quantity', 1)
        context.user_data['quantity'] = qty + 1
        package_code = context.user_data.get('selected_package')
        await show_quantity_selector(query, context, package_code)
    
    elif query.data == "prem_checkout":
        package_code = context.user_data.get('selected_package')
        quantity = context.user_data.get('quantity', 1)
        package = PACKAGES.get(package_code, {})
        
        total_price = package.get('price', 0) * quantity
        
        text = f"""```
🛒 CHECKOUT PREMIUM
───────────────────────────────────────

Paket       : {package.get('name')}
Durasi      : {package.get('duration')}
Jumlah      : {quantity}x
Total       : Rp {total_price:,}

───────────────────────────────────────

Silakan hubungi owner untuk pembayaran:
@KIFZLDEV

Setelah transfer, kirim bukti pembayaran
beserta username Anda ke owner.

───────────────────────────────────────
```"""
        
        keyboard = [
            [InlineKeyboardButton("📩 Chat Owner", url=f"https://t.me/KIFZLDEV")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text,
                parse_mode="HTML", reply_markup=reply_markup)

async def show_quantity_selector(query, context, package_code):
    package = PACKAGES.get(package_code, {})
    quantity = context.user_data.get('quantity', 1)
    total_price = package.get('price', 0) * quantity
    
    text = f"""```
💎 {package.get('name')} - {package.get('duration')}
───────────────────────────────────────

Harga per paket: Rp {package.get('price', 0):,}
Jumlah         : {quantity}
Total          : Rp {total_price:,}

───────────────────────────────────────
Pilih jumlah:
```"""
    
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data="prem_qty_minus"),
            InlineKeyboardButton(f"  {quantity}  ", callback_data="prem_qty_display"),
            InlineKeyboardButton("➕", callback_data="prem_qty_plus"),
        ],
        [InlineKeyboardButton("🛒 Checkout", callback_data="prem_checkout")],
        [InlineKeyboardButton("❌ Batalkan", callback_data="prem_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text,
                parse_mode="HTML", reply_markup=reply_markup)
