import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from config import OWNER_ID, VIP_GROUPS, USERS_FILE, DATE_FORMAT, ROLE_HIERARCHY, VIP_DURATION_DAYS

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            for uid in data:
                if "expired" in data[uid] and data[uid]["expired"]:
                    try:
                        data[uid]["expired"] = datetime.strptime(data[uid]["expired"], DATE_FORMAT)
                    except:
                        data[uid]["expired"] = None
            return data
    except FileNotFoundError:
        return {}

def save_users(data):
    def serializer(obj):
        if isinstance(obj, datetime):
            return obj.strftime(DATE_FORMAT)
        return obj
    
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=serializer)

def get_user_role(user_id):
    if user_id == OWNER_ID:
        return "OWNER"
    
    users = load_users()
    user_data = users.get(str(user_id), {})
    
    if user_data.get("role") in ["PREMIUM", "VIP"]:
        expired = user_data.get("expired")
        if expired:
            if isinstance(expired, str):
                try:
                    expired = datetime.strptime(expired, DATE_FORMAT)
                except:
                    return "FREE"
            if expired > datetime.now():
                return user_data.get("role", "FREE")
    
    return "FREE"

def check_access(user_id, required_role="VIP"):
    user_role = get_user_role(user_id)
    
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)

async def send_access_denied(update: Update, user_role: str, required_role: str):
    text = f"""```
──────────────────────────
🔒 AKSES DITOLAK
──────────────────────────
Role Anda          : {user_role}
Akses Dibutuhkan   : {required_role}

Silakan pilih opsi di bawah ini untuk
mendapatkan akses:
──────────────────────────
```"""
    
    keyboard = [
        [KeyboardButton("💎 UPGRADE PREMIUM 💎")],
        [KeyboardButton("🎟 AKSES VIP 🎟")],
        [KeyboardButton("🔙 MENU 🔙")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

def get_user_data(user_id):
    users = load_users()
    return users.get(str(user_id), {})

def update_user_data(user_id, data):
    users = load_users()
    user_str = str(user_id)
    
    if user_str not in users:
        users[user_str] = {}
    
    users[user_str].update(data)
    save_users(users)

def load_sessions():
    try:
        with open("sessions.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_session(user_id, session_data):
    sessions = load_sessions()
    user_str = str(user_id)
    
    def serializer(obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return obj
    
    if user_str not in sessions:
        sessions[user_str] = {}
    
    sessions[user_str].update(session_data)
    sessions[user_str]['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("sessions.json", "w") as f:
        json.dump(sessions, f, indent=2, default=serializer)

def get_session(user_id):
    sessions = load_sessions()
    return sessions.get(str(user_id), {})

def clear_session(user_id):
    sessions = load_sessions()
    user_str = str(user_id)
    
    if user_str in sessions:
        del sessions[user_str]
        with open("sessions.json", "w") as f:
            json.dump(sessions, f, indent=2)
