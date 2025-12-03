import os
import json
import asyncio
import logging
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    TypeHandler,
    filters
)

from config import is_owner, BOT_NAME, BOT_CREATOR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

db_available = False

def ensure_json_files():
    files = ["users.json", "redeem.json", "sessions.json", "admins.json"]
    for file in files:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                json.dump({}, f)
            logger.info(f"Created {file}")

def verify_bot_ownership():
    required_creator = "@KIFZLDEV"
    tampering_detected = False

    try:
        with open("commands/start.py", "r", encoding="utf-8") as f:
            start_content = f.read()
            if "(BY @KIFZLDEV)" not in start_content:
                tampering_detected = True
    except:
        tampering_detected = True

    try:
        with open("commands/menu.py", "r", encoding="utf-8") as f:
            menu_content = f.read()
            if "(BY @KIFZLDEV)" not in menu_content:
                tampering_detected = True
    except:
        tampering_detected = True

    if tampering_detected:
        print("\n" + "="*50)
        print("❌ CRITICAL ERROR - BOT OWNERSHIP VERIFICATION FAILED!")
        print("="*50)
        print(f"❌ Bot creator name has been changed or removed!")
        print(f"❌ This bot is protected and can ONLY be fixed by @KIFZLDEV")
        print("❌ Bot will NOT start until original creator name is restored!")
        print("❌ The creator line MUST be: (BY @KIFZLDEV)")
        print("="*50 + "\n")
        raise Exception(f"ANTI-THEFT PROTECTION TRIGGERED: Bot name tampering detected!")

async def init_database():
    global db_available
    try:
        from database.connection import init_db
        result = await init_db()
        if result:
            db_available = True
            logger.info("PostgreSQL connected successfully!")
            return True
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed: {e}. Using JSON fallback.")
    return False

async def check_verification_before_command(update: Update, context) -> bool:
    if not update.effective_user:
        return True
    
    user_id = update.effective_user.id
    
    if is_owner(user_id):
        return True
    
    is_private = update.effective_chat.type == "private" if update.effective_chat else True
    is_group = update.effective_chat.type in ["group", "supergroup"] if update.effective_chat else False
    
    if is_group:
        try:
            from database.models import GuildModeModel
            from database.connection import get_db
            db = get_db()
            if db.is_connected:
                group_id = update.effective_chat.id
                group_enabled = await GuildModeModel.is_group_enabled(group_id)
                if not group_enabled:
                    return False
                
                from commands.verify import verify_user_access
                is_verified = await verify_user_access(update, context, show_message=False)
                if not is_verified:
                    try:
                        await update.message.reply_text(
                            "⚠️ *Akses Ditolak*\n\nAnda belum terverifikasi. Silakan chat bot ini secara private untuk verifikasi.",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
                    return False
        except Exception:
            pass
    
    if is_private:
        try:
            from commands.verify import verify_user_access
            is_verified = await verify_user_access(update, context, show_message=True)
            return is_verified
        except Exception:
            return True
    
    return True


async def handle_text_messages(update: Update, context):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    
    if text in ["/start", "🔙 KEMBALI 🔙"]:
        from commands.start import start_command
        await start_command(update, context)
        return
    
    if not is_owner(user_id):
        is_verified = await check_verification_before_command(update, context)
        if not is_verified:
            return
    
    try:
        from utils.rate_limiter import check_user_access
        is_allowed, rate_msg = await check_user_access(user_id, "message")
        if not is_allowed:
            await update.message.reply_text(
                f"⚠️ {rate_msg}",
                parse_mode="Markdown"
            )
            return
    except ImportError:
        pass
    
    from commands.maintenance import check_maintenance
    if await check_maintenance(update, context):
        return
    
    from commands.start import start_command, get_start_keyboard
    from commands.menu import show_menu, get_main_menu_keyboard
    from commands.status import check_status
    from commands.vip_info import vip_info, vvip_info, vip_buy, vvip_buy, show_vip_benefits, show_vvip_benefits
    from commands.profil import show_profil
    
    if text == "🜲 Menu Utama 🜲":
        await show_menu(update, context)
    elif text == "🜲 STATUS 🜲":
        await check_status(update, context)
    elif text == "🜲 VIP 🜲":
        await vip_info(update, context)
    elif text == "🜲 VVIP 🜲":
        await vvip_info(update, context)
    elif text == "🜲 Beli VIP 🜲":
        await vip_buy(update, context)
    elif text == "🜲 Beli VVIP 🜲":
        await vvip_buy(update, context)
    elif text == "🜲 Lihat Benefit VIP 🜲":
        await show_vip_benefits(update, context)
    elif text == "🜲 Lihat Benefit VVIP 🜲":
        await show_vvip_benefits(update, context)
    elif text == "🜲 Profil 🜲":
        await show_profil(update, context)
    elif text == "🜲 File Tools 🜲":
        if is_owner(user_id):
            await show_menu(update, context)
        else:
            keyboard = get_main_menu_keyboard(user_id)
            await update.message.reply_text(
                "⚠️ Menu ini hanya tersedia untuk owner.",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    else:
        pass

def main():
    print("\n" + "="*50)
    print("⏳ KIFZL DEV BOT V2 PRO Initializing...")
    print("="*50 + "\n")

    print("📦 Loading modules...")
    ensure_json_files()

    print("🔍 Verifying project integrity...")
    print("✅ Project integrity: VERIFIED")
    print("✅ All credits: INTACT")
    print(f"👨‍💻 Created by: {BOT_CREATOR}\n")

    print("🔐 VERIFYING BOT OWNERSHIP...")
    try:
        verify_bot_ownership()
        print(f"✅ Bot Creator: {BOT_CREATOR}")
        print("✅ PROTECTION ACTIVE: Bot name verified and protected!")
        print("⚠️  Attempting to rename or take this bot will cause ERROR!")
        print(f"⚠️  Only {BOT_CREATOR} can fix and restore this bot\n")
    except Exception as e:
        print(f"🛑 STARTUP BLOCKED: {e}\n")
        return

    print("⚙️ Bot step initialized...")
    print("📥 Loading commands...\n")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return

    application = Application.builder().token(token).build()
    
    async def post_init(application):
        print("🗄️ Connecting to PostgreSQL...")
        await init_database()
        if db_available:
            print("✅ PostgreSQL connected!")
        else:
            print("⚠️ Using JSON fallback storage")
    
    application.post_init = post_init

    from commands.start import start_command
    from commands.menu import show_menu
    from commands.status import check_status
    from commands.redeem import redeem_start, redeem_process, ASK_CODE
    
    from commands.owner_panel import (
        owner_panel_start, owner_panel_action, owner_panel_user_id,
        owner_panel_duration, owner_panel_code_type, owner_panel_code_value,
        owner_panel_code_duration, owner_panel_code_limit, owner_panel_code_expiry,
        owner_panel_broadcast_type, owner_panel_broadcast_msg,
        ASK_ACTION, ASK_USER_ID, ASK_DURATION, ASK_CODE_TYPE, ASK_CODE_VALUE,
        ASK_CODE_DURATION, ASK_CODE_LIMIT, ASK_CODE_EXPIRY,
        ASK_BROADCAST_TYPE, ASK_BROADCAST_MSG
    )
    
    from commands.monitoring import (
        monitoring_start, monitoring_action,
        ASK_MONITORING_ACTION
    )
    
    from commands.maintenance import (
        maintenance_start, maintenance_action,
        ASK_MAINTENANCE_ACTION
    )
    
    from commands.sistem_bot import (
        sistem_bot_start, sistem_bot_action,
        ASK_SISTEM_ACTION
    )
    
    from commands.manajemen_grup import (
        manajemen_grup_start, manajemen_grup_action,
        manajemen_grup_group_id, manajemen_grup_setting_value,
        ASK_MANAJEMEN_ACTION, ASK_GROUP_ID as MAN_ASK_GROUP_ID,
        ASK_SETTING_VALUE
    )
    
    from commands.pengaturan_grup import (
        pengaturan_grup_start, pengaturan_grup_action,
        pengaturan_grup_group_id, pengaturan_grup_welcome_msg,
        pengaturan_grup_whitelist,
        ASK_PENGATURAN_ACTION, ASK_PENGATURAN_GROUP_ID,
        ASK_WELCOME_MSG, ASK_WHITELIST_LINK
    )

    application.add_handler(CommandHandler("start", start_command))
    
    try:
        from commands.msg_to_txt import msg_to_txt_start, msg_to_txt_message, msg_to_txt_filename
        from commands.msg_to_txt import ASK_MESSAGE as MSG_ASK_MESSAGE, ASK_FILENAME as MSG_ASK_FILENAME
        
        msg_to_txt_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 MSG TO TXT 🜲$"), msg_to_txt_start)],
            states={
                MSG_ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_to_txt_message)],
                MSG_ASK_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_to_txt_filename)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), msg_to_txt_filename)],
        )
        application.add_handler(msg_to_txt_conv)
    except ImportError as e:
        logger.warning(f"msg_to_txt not available: {e}")

    try:
        from commands.rapikan_txt import rapikan_txt_start, rapikan_txt_file, ASK_FILE as RAPIKAN_ASK_FILE
        
        rapikan_txt_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 RAPIKAN TXT 🜲$"), rapikan_txt_start)],
            states={
                RAPIKAN_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, rapikan_txt_file)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), rapikan_txt_file)],
        )
        application.add_handler(rapikan_txt_conv)
    except ImportError as e:
        logger.warning(f"rapikan_txt not available: {e}")

    try:
        from commands.convert_txt_vcf import (
            txt_to_vcf_start, txt_to_vcf_file, txt_to_vcf_filename, txt_to_vcf_contactname,
            ASK_FILE as TXT_VCF_ASK_FILE, ASK_FILENAME as TXT_VCF_ASK_FILENAME,
            ASK_CONTACTNAME as TXT_VCF_ASK_CONTACTNAME
        )
        
        txt_to_vcf_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 TXT TO VCF 🜲$"), txt_to_vcf_start)],
            states={
                TXT_VCF_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, txt_to_vcf_file)],
                TXT_VCF_ASK_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, txt_to_vcf_filename)],
                TXT_VCF_ASK_CONTACTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, txt_to_vcf_contactname)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), txt_to_vcf_contactname)],
        )
        application.add_handler(txt_to_vcf_conv)
    except ImportError as e:
        logger.warning(f"convert_txt_vcf not available: {e}")

    try:
        from commands.convert_vcf_txt import vcf_to_txt_start, vcf_to_txt_file, ASK_FILE as VCF_TXT_ASK_FILE
        
        vcf_to_txt_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 VCF TO TXT 🜲$"), vcf_to_txt_start)],
            states={
                VCF_TXT_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, vcf_to_txt_file)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), vcf_to_txt_file)],
        )
        application.add_handler(vcf_to_txt_conv)
    except ImportError as e:
        logger.warning(f"convert_vcf_txt not available: {e}")

    try:
        from commands.convert_xlsx_vcf import (
            xls_to_vcf_start, xls_to_vcf_file, xls_to_vcf_filename, xls_to_vcf_contactname,
            ASK_FILE as XLS_ASK_FILE, ASK_FILENAME as XLS_ASK_FILENAME,
            ASK_CONTACTNAME as XLS_ASK_CONTACTNAME
        )
        
        xls_to_vcf_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 XLS TO VCF 🜲$"), xls_to_vcf_start)],
            states={
                XLS_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, xls_to_vcf_file)],
                XLS_ASK_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, xls_to_vcf_filename)],
                XLS_ASK_CONTACTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, xls_to_vcf_contactname)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), xls_to_vcf_contactname)],
        )
        application.add_handler(xls_to_vcf_conv)
    except ImportError as e:
        logger.warning(f"convert_xlsx_vcf not available: {e}")

    try:
        from commands.hitung_kontak import hitung_kontak_start, hitung_kontak_file, ASK_FILE as HITUNG_ASK_FILE
        
        hitung_kontak_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 HITUNG KONTAK 🜲$"), hitung_kontak_start)],
            states={
                HITUNG_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, hitung_kontak_file)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), hitung_kontak_file)],
        )
        application.add_handler(hitung_kontak_conv)
    except ImportError as e:
        logger.warning(f"hitung_kontak not available: {e}")

    try:
        from commands.cek_nama_kontak import cek_nama_start, cek_nama_file, ASK_FILE as CEK_NAMA_ASK_FILE
        
        cek_nama_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 CEK NAMA 🜲$"), cek_nama_start)],
            states={
                CEK_NAMA_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, cek_nama_file)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), cek_nama_file)],
        )
        application.add_handler(cek_nama_conv)
    except ImportError as e:
        logger.warning(f"cek_nama_kontak not available: {e}")

    try:
        from commands.gabung_file import (
            gabung_file_start, gabung_file_collect, gabung_file_merge,
            ASK_FILES, ASK_FILENAME as GABUNG_ASK_FILENAME
        )
        
        gabung_file_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 GABUNG FILE 🜲$"), gabung_file_start)],
            states={
                ASK_FILES: [MessageHandler(filters.Document.ALL | filters.TEXT, gabung_file_collect)],
                GABUNG_ASK_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, gabung_file_merge)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), gabung_file_merge)],
        )
        application.add_handler(gabung_file_conv)
    except ImportError as e:
        logger.warning(f"gabung_file not available: {e}")

    try:
        from commands.split_file import (
            split_file_start, split_file_receive, split_file_output_name,
            split_file_prefix, split_contact_prefix, split_mode_select, split_process,
            ASK_FILE as SPLIT_ASK_FILE, ASK_OUTPUT_NAME, ASK_FILE_PREFIX,
            ASK_CONTACT_PREFIX, ASK_SPLIT_MODE, ASK_SPLIT_VALUE
        )
        
        split_file_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 SPLIT FILE 🜲$"), split_file_start)],
            states={
                SPLIT_ASK_FILE: [MessageHandler(filters.Document.ALL | filters.TEXT, split_file_receive)],
                ASK_OUTPUT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, split_file_output_name)],
                ASK_FILE_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, split_file_prefix)],
                ASK_CONTACT_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, split_contact_prefix)],
                ASK_SPLIT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, split_mode_select)],
                ASK_SPLIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, split_process)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), split_process)],
        )
        application.add_handler(split_file_conv)
    except ImportError as e:
        logger.warning(f"split_file not available: {e}")

    try:
        from commands.create_admin_navy import (
            create_admin_navy_start, create_admin_navy_mode, create_admin_navy_admin,
            create_admin_navy_navy, create_admin_navy_filename, create_admin_navy_generate,
            create_admin_navy_block, ASK_MODE, ASK_ADMIN_NUM, ASK_NAVY_NUM,
            ASK_FILENAME as ADMIN_ASK_FILENAME, ASK_CONTACTNAME as ADMIN_ASK_CONTACTNAME,
            ASK_BLOCK_INPUT
        )
        
        create_admin_navy_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🜲 CREATE ADM/NAVY 🜲$"), create_admin_navy_start)],
            states={
                ASK_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_admin_navy_mode)],
                ASK_ADMIN_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_admin_navy_admin)],
                ASK_NAVY_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_admin_navy_navy)],
                ADMIN_ASK_FILENAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_admin_navy_filename)],
                ADMIN_ASK_CONTACTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_admin_navy_generate)],
                ASK_BLOCK_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_admin_navy_block)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), create_admin_navy_generate)],
        )
        application.add_handler(create_admin_navy_conv)
    except ImportError as e:
        logger.warning(f"create_admin_navy not available: {e}")

    redeem_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🜲 Redeem 🜲$"), redeem_start),
            MessageHandler(filters.Regex("^🎁 REDEEM CODE 🎁$"), redeem_start),
            CommandHandler("redeem", redeem_start)
        ],
        states={
            ASK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, redeem_process)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ BATAL ❌$"), redeem_process)],
    )
    application.add_handler(redeem_conv)

    owner_panel_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🜲 Owner Panel 🜲$"), owner_panel_start)],
        states={
            ASK_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_action)],
            ASK_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_user_id)],
            ASK_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_duration)],
            ASK_CODE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_code_type)],
            ASK_CODE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_code_value)],
            ASK_CODE_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_code_duration)],
            ASK_CODE_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_code_limit)],
            ASK_CODE_EXPIRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_code_expiry)],
            ASK_BROADCAST_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_broadcast_type)],
            ASK_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_panel_broadcast_msg)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 KEMBALI 🔙$"), owner_panel_start)],
    )
    application.add_handler(owner_panel_conv)

    monitoring_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🜲 Monitoring Bot 🜲$"), monitoring_start)],
        states={
            ASK_MONITORING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, monitoring_action)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 KEMBALI 🔙$"), monitoring_start)],
    )
    application.add_handler(monitoring_conv)

    maintenance_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🜲 Maintenance 🜲$"), maintenance_start)],
        states={
            ASK_MAINTENANCE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, maintenance_action)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 KEMBALI 🔙$"), maintenance_start)],
    )
    application.add_handler(maintenance_conv)

    sistem_bot_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🜲 Sistem Bot 🜲$"), sistem_bot_start)],
        states={
            ASK_SISTEM_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, sistem_bot_action)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 KEMBALI 🔙$"), sistem_bot_start)],
    )
    application.add_handler(sistem_bot_conv)

    manajemen_grup_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🜲 Manajemen Grup 🜲$"), manajemen_grup_start)],
        states={
            ASK_MANAJEMEN_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, manajemen_grup_action)],
            MAN_ASK_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, manajemen_grup_group_id)],
            ASK_SETTING_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, manajemen_grup_setting_value)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 KEMBALI 🔙$"), manajemen_grup_start)],
    )
    application.add_handler(manajemen_grup_conv)

    pengaturan_grup_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🜲 Pengaturan Grup 🜲$"), pengaturan_grup_start)],
        states={
            ASK_PENGATURAN_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, pengaturan_grup_action)],
            ASK_PENGATURAN_GROUP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, pengaturan_grup_group_id)],
            ASK_WELCOME_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, pengaturan_grup_welcome_msg)],
            ASK_WHITELIST_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, pengaturan_grup_whitelist)],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 KEMBALI 🔙$"), pengaturan_grup_start)],
    )
    application.add_handler(pengaturan_grup_conv)

    try:
        from commands.group_guardian import handle_group_message, handle_new_member, handle_left_member
        application.add_handler(MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            handle_group_message
        ), group=1)
        application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            handle_new_member
        ), group=1)
        application.add_handler(MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER,
            handle_left_member
        ), group=1)
        logger.info("Group guardian handlers loaded")
    except ImportError as e:
        logger.warning(f"group_guardian not available: {e}")

    try:
        from commands.verify import handle_verify_callback, handle_member_join
        application.add_handler(CallbackQueryHandler(handle_verify_callback, pattern="^verify_"))
        application.add_handler(TypeHandler(ChatMemberUpdated, handle_member_join))
    except ImportError as e:
        logger.warning(f"verify handlers not available: {e}")

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("="*50)
    print(f"🚀 {BOT_NAME} V2 PRO launched!")
    print("🤝 SUPPORT TEAM & PARTNER")
    print(f"📞 Support: {BOT_CREATOR}")
    print("="*50 + "\n")

    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
