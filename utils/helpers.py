import random
import string
import re
from datetime import datetime, timedelta
from typing import Optional
import phonenumbers


def format_datetime(dt: datetime, format_str: str = "%d-%m-%Y %H:%M:%S") -> str:
    if dt is None:
        return "—"
    return dt.strftime(format_str)


def format_duration(days: int) -> str:
    if days < 1:
        return "< 1 hari"
    elif days == 1:
        return "1 hari"
    elif days < 7:
        return f"{days} hari"
    elif days < 30:
        weeks = days // 7
        remaining_days = days % 7
        if remaining_days == 0:
            return f"{weeks} minggu"
        return f"{weeks} minggu {remaining_days} hari"
    elif days < 365:
        months = days // 30
        remaining_days = days % 30
        if remaining_days == 0:
            return f"{months} bulan"
        return f"{months} bulan {remaining_days} hari"
    else:
        years = days // 365
        remaining_days = days % 365
        if remaining_days == 0:
            return f"{years} tahun"
        return f"{years} tahun {remaining_days} hari"


def format_remaining_time(expired_at: datetime) -> str:
    if expired_at is None:
        return "—"
    
    now = datetime.utcnow()
    if expired_at < now:
        return "Expired"
    
    diff = expired_at - now
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} hari {hours} jam"
    elif hours > 0:
        return f"{hours} jam {minutes} menit"
    else:
        return f"{minutes} menit"


def generate_random_code(length: int = 12) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def normalize_phone_number(phone: str, default_country: str = "ID") -> Optional[str]:
    try:
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        if cleaned.startswith('0'):
            cleaned = '+62' + cleaned[1:]
        elif not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        
        parsed = phonenumbers.parse(cleaned, default_country)
        
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, 
                phonenumbers.PhoneNumberFormat.E164
            )
        
        return None
    except Exception:
        return None


def extract_phone_numbers(text: str) -> list:
    patterns = [
        r'\+?\d{10,15}',
        r'\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{4,6}',
        r'\(\d{2,4}\)\s?\d{6,10}'
    ]
    
    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)
    
    normalized = []
    seen = set()
    for phone in phones:
        norm = normalize_phone_number(phone)
        if norm and norm not in seen:
            normalized.append(norm)
            seen.add(norm)
    
    return normalized


def remove_duplicates(items: list, key=None) -> list:
    seen = set()
    result = []
    
    for item in items:
        check_value = key(item) if key else item
        if check_value not in seen:
            seen.add(check_value)
            result.append(item)
    
    return result


def chunk_list(lst: list, chunk_size: int) -> list:
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def escape_markdown(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def safe_markdown(text: str) -> str:
    text = text.replace('*', '')
    text = text.replace('_', '')
    text = text.replace('`', '')
    text = text.replace('[', '(')
    text = text.replace(']', ')')
    return text


def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_user_display_name(user) -> str:
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"User {user.id}"


def format_stats(stats: dict) -> str:
    lines = []
    for key, value in stats.items():
        formatted_key = key.replace('_', ' ').title()
        lines.append(f"• {formatted_key}: {value}")
    return '\n'.join(lines)
