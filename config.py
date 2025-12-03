import os

OWNER_ID = 8317563450
OWNER_USERNAME = "@KIFZLDEV"
OWNER_IDS = [8317563450]

REQUIRED_GROUPS = [
    {
        "name": "MFA_1STC",
        "link": "https://t.me/MFA_1STC",
        "chat_id": -1001234567890,
        "username": "MFA_1STC"
    },
    {
        "name": "Channel Viber",
        "link": "https://t.me/channelviber",
        "chat_id": -1001234567891,
        "username": "channelviber"
    }
]

FORCED_JOIN_GROUPS = [
    {"link": "https://t.me/MFA_1STC", "chat_id": None},
    {"link": "https://t.me/channelviber", "chat_id": None}
]

VIP_GROUPS = [
    "https://t.me/MFA_1STC",
    "https://t.me/channelviber"
]

VIP_DURATION_DAYS = 7
VVIP_DURATION_DAYS = 30

USERS_FILE = "users.json"
REDEEM_FILE = "redeem.json"
SESSIONS_FILE = "sessions.json"
ADMINS_FILE = "admins.json"

VIP_EXPIRY_WARNING_HOURS = 24

ROLE_HIERARCHY = {
    "reguler": 0,
    "vip": 1,
    "vvip": 2,
    "owner": 3
}

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

BOT_CREATOR = "@KIFZLDEV"
BOT_SUPPORT = "@KIFZLDEV"
BOT_NAME = "KIFZL DEV BOT"

VIP_DAILY_LIMIT = 50
VVIP_DAILY_LIMIT = 100
FREE_DAILY_LIMIT = 10

VIP_BENEFITS = [
    "Akses semua fitur konversi",
    "Limit harian 50 request",
    "Prioritas support",
    "Akses file tools lengkap"
]

VVIP_BENEFITS = [
    "Semua benefit VIP",
    "Limit harian 100 request",
    "Prioritas tertinggi",
    "Fitur eksklusif",
    "Support 24/7"
]

VIP_PRICES = {
    "1_day": 10000,
    "7_days": 50000,
    "30_days": 150000
}

VVIP_PRICES = {
    "1_day": 25000,
    "7_days": 100000,
    "30_days": 300000
}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

MAX_FILE_SIZE = 50 * 1024 * 1024
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS
