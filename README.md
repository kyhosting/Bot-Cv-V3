
# 🤖 KIFZL DEV BOT

> **⚠️ CREATOR MESSAGE & PROTECTION NOTICE:**
> 
> This bot was created and developed by **@KIFZLDEV** 
> 
> **IMPORTANT:**
> - This bot is PROTECTED with anti-theft technology
> - Changing the creator name or attempting to claim this bot will cause automatic ERROR OUT
> - Only @KIFZLDEV can modify and restore this bot
> - Do NOT attempt to rename, redistribute, or claim this bot as your own
> - All credits must remain intact and visible
> 
> **Contact & Support:**
> - Creator: @KIFZLDEV
> - Support: @KIFZLDEV
> - For issues or modifications, contact the creator directly
> 
> Respect the creator's work and the protection system in place.

---

## 📋 Overview

Bot Telegram lengkap dengan sistem role (FREE/VIP/PREMIUM/OWNER), redeem code, converter tools (TXT/VCF/XLSX), split system, dan fitur Create Admin & Navy.

## 👑 Owner Configuration

- **Owner ID:** 8317563450
- **Owner Username:** @KIFZLDEV
- **VIP Groups (auto-grant VIP 1 minggu):**
  - https://t.me/agentviber12
  - https://t.me/channelviber

## 📁 Project Structure

```
/KIFZL_DEV_BOT
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md                  # Documentation & Creator Message
├── users.json                 # Auto-created: User database
├── redeem.json               # Auto-created: Redeem codes (VIP only)
├── sessions.json             # Auto-created: Session tracking
├── admins.json               # Auto-created: Admin data
├── project_banner.png        # KIFZL PROJECT banner
└── commands/                 # Modular command handlers
    ├── vip_system.py         # Role authorization system
    ├── start.py              # Start command with user status
    ├── menu.py               # Main menu keyboard
    ├── msg_to_txt.py         # MSG to TXT converter
    ├── rapikan_txt.py        # Clean TXT files
    ├── convert_txt_vcf.py    # TXT to VCF converter
    ├── convert_vcf_txt.py    # VCF to TXT extractor
    ├── convert_xlsx_vcf.py   # Excel to VCF converter
    ├── hitung_kontak.py      # Count contacts
    ├── cek_nama_kontak.py    # Check contact names
    ├── gabung_file.py        # Merge files (TXT/VCF)
    ├── split_file.py         # Split files (per kontak/bagian)
    ├── create_admin_navy.py  # Create Admin & Navy (3 modes)
    ├── redeem.py             # Redeem code system (VIP only, single-use)
    ├── redeem_utils.py       # Redeem helpers (random code, duration format)
    ├── upgradeprem.py        # Premium upgrade with inline buttons
    ├── aksesvip.py           # VIP access information
    ├── menu_owner.py         # Owner management panel
    └── expiry_checker.py     # Expiry notifications for access & codes
```

## ✨ Features

### 🔐 Role System
- **FREE:** Limited access
- **VIP:** Partial features (7 days default)
- **PREMIUM:** All features (1/7/30 days packages)
- **OWNER:** Unlimited access + management

### 🔄 Converter Tools
- MSG → TXT
- TXT → VCF (with custom naming)
- VCF → TXT (extract phone numbers)
- XLSX → VCF (Excel to contacts)

### 📂 File Management
- Rapikan TXT (clean formatting)
- Gabung File (merge multiple files)
- Split File (per kontak atau per bagian)
- Hitung Kontak (count contacts)
- Cek Nama Kontak (check contact names)

### 👥 Admin & Navy Creator (3 Modes)
- **Mode A - Guided:** Step-by-step input
- **Mode B - Auto Parse:** Block text parsing
- **Mode C - Minimal:** Single number input

### 💎 Premium System
- Inline quantity controller [-] [+]
- Paket: 1 Day, 7 Days, 30 Days
- Checkout with owner confirmation

### 🎟 Redeem System (VIP ONLY - GRATIS)
- **Code Generation:** Random (12-char alphanumeric) or Custom input
- **Code Expiry:** Owner set berapa hari kode berlaku (dengan jam:menit detail)
- **User Duration:** Terpisah durasi akses VIP user (dalam format readable: hari/bulan/tahun)
- **Single-Use:** Setiap kode hanya bisa dipakai 1x, tidak bisa ulang
- **Validation:** Check code expired, used status, dan tampilkan alasan jelas ke user
- **Note:** PREMIUM hanya bisa dibeli paket, tidak ada redeem code untuk PREMIUM

### 👨‍💼 Owner Panel
- View all users
- Add/Edit user roles
- Create redeem codes
- View statistics

## 🔒 Anti-Theft Protection

This bot includes automatic protection against unauthorized use:
- Bot creator name verification on startup
- Automatic ERROR OUT if creator name is changed
- Only @KIFZLDEV can restore the bot if tampering is detected

## 📝 Recent Changes

- **2024-11-24:** Initial project setup
- All features implemented with keyboard button navigation
- Modular architecture for easy maintenance
- Auto-create JSON files on first run
- Session tracking functions implemented
- **2024-11-24:** Optimized file delivery speed (10x faster)
  - File uploads now send INSTANTLY with plain text captions
  - Banner only on text/menu responses, excluded from file uploads
- **2024-11-24:** Enhanced Redeem System (VIP ONLY - GRATIS)
  - **Random/Custom Code:** Owner bisa pilih 🎲 RANDOM (auto-generate) atau ✍️ CUSTOM
  - **Code Expiry with Time:** Kode berlaku X hari dengan jam:menit detail (format: DD-MM-YYYY HH:MM:SS)
  - **Duration Display:** Tampilkan durasi VIP dalam format readable (hari/bulan/tahun)
  - **Single-Use Code:** Setiap kode hanya bisa redeem 1x, tidak bisa dipakai ulang
  - **Detailed Expiry Messages:** User dapat notifikasi jelas alasan kode/akses tidak valid
  - **PREMIUM = BELI ONLY:** Redeem hanya untuk VIP, PREMIUM hanya bisa dibeli paket
- **2024-11-24:** Added Anti-Theft Protection
  - Automatic startup verification of creator name
  - Protection against bot name tampering and unauthorized claims

## 🔑 Environment Variables

- `TELEGRAM_BOT_TOKEN`: Telegram bot API token (required)

## ⚙️ User Preferences

- All interactions via keyboard buttons (no `/` commands)
- Markdown formatting for all bot messages
- Auto-cleanup temporary files
- Session tracking for multi-step processes

---

**Created by:** @KIFZLDEV  
**Support:** @KIFZLDEV  
**Protected & Secured** 🔐
