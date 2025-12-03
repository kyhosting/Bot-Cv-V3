from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_user_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Menu Utama 🜲")],
        [KeyboardButton("🜲 VIP 🜲"), KeyboardButton("🜲 VVIP 🜲")],
        [KeyboardButton("🜲 Redeem 🜲"), KeyboardButton("🜲 Profil 🜲")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_owner_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Menu Utama 🜲")],
        [KeyboardButton("🜲 Monitoring Bot 🜲"), KeyboardButton("🜲 Maintenance 🜲")],
        [KeyboardButton("🜲 Manajemen Grup 🜲"), KeyboardButton("🜲 Owner Panel 🜲")],
        [KeyboardButton("🜲 File Tools 🜲"), KeyboardButton("🜲 Pengaturan Grup 🜲")],
        [KeyboardButton("🜲 Sistem Bot 🜲")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_main_menu_keyboard(is_owner: bool = False):
    if is_owner:
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

def get_cancel_keyboard():
    keyboard = [[KeyboardButton("❌ BATAL ❌")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    keyboard = [[KeyboardButton("🔙 KEMBALI 🔙")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_file_tools_keyboard():
    keyboard = [
        [KeyboardButton("🜲 MSG TO TXT 🜲"), KeyboardButton("🜲 TXT TO VCF 🜲")],
        [KeyboardButton("🜲 VCF TO TXT 🜲"), KeyboardButton("🜲 XLS TO VCF 🜲")],
        [KeyboardButton("🜲 RAPIKAN TXT 🜲"), KeyboardButton("🜲 GABUNG FILE 🜲")],
        [KeyboardButton("🜲 HITUNG KONTAK 🜲"), KeyboardButton("🜲 CEK NAMA 🜲")],
        [KeyboardButton("🜲 SPLIT FILE 🜲"), KeyboardButton("🜲 CREATE ADM/NAVY 🜲")],
        [KeyboardButton("🜲 HAPUS DUPLIKAT 🜲"), KeyboardButton("🜲 NORMALIZE NO 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_owner_panel_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Lihat Semua User 🜲")],
        [KeyboardButton("🜲 Ban User 🜲"), KeyboardButton("🜲 Unban User 🜲")],
        [KeyboardButton("🜲 Edit VIP/VVIP 🜲"), KeyboardButton("🜲 Reset Limit 🜲")],
        [KeyboardButton("🜲 Buat Redeem 🜲"), KeyboardButton("🜲 Lihat Redeem 🜲")],
        [KeyboardButton("🜲 Broadcast 🜲"), KeyboardButton("🜲 Export Data 🜲")],
        [KeyboardButton("🜲 Statistik 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_monitoring_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Status Sistem 🜲")],
        [KeyboardButton("🜲 Error Log 🜲"), KeyboardButton("🜲 Activity Log 🜲")],
        [KeyboardButton("🜲 DB Status 🜲"), KeyboardButton("🜲 Running Jobs 🜲")],
        [KeyboardButton("🜲 Force Restart 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_maintenance_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Maintenance ON 🜲"), KeyboardButton("🜲 Maintenance OFF 🜲")],
        [KeyboardButton("🜲 Status Maintenance 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_group_management_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Anti-Link ON 🜲"), KeyboardButton("🜲 Anti-Link OFF 🜲")],
        [KeyboardButton("🜲 Anti-Spam ON 🜲"), KeyboardButton("🜲 Anti-Spam OFF 🜲")],
        [KeyboardButton("🜲 Auto-Welcome ON 🜲"), KeyboardButton("🜲 Auto-Welcome OFF 🜲")],
        [KeyboardButton("🜲 Banned Words 🜲")],
        [KeyboardButton("🜲 Lihat Pengaturan 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_system_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Restart Bot 🜲"), KeyboardButton("🜲 Reload Modules 🜲")],
        [KeyboardButton("🜲 Debug ON 🜲"), KeyboardButton("🜲 Debug OFF 🜲")],
        [KeyboardButton("🜲 Integrity Check 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_vip_info_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Beli VIP 🜲")],
        [KeyboardButton("🜲 Lihat Benefit 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_vvip_info_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Beli VVIP 🜲")],
        [KeyboardButton("🜲 Lihat Benefit 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_redeem_create_keyboard():
    keyboard = [
        [KeyboardButton("🜲 Random Code 🜲"), KeyboardButton("🜲 Custom Code 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_redeem_type_keyboard():
    keyboard = [
        [KeyboardButton("🜲 VIP 🜲"), KeyboardButton("🜲 VVIP 🜲")],
        [KeyboardButton("🔙 KEMBALI 🔙")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
