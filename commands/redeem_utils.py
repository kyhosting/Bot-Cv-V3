import random
import string
from datetime import datetime, timedelta

def generate_random_code(length=12):
    """Generate random redeem code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def parse_duration_text(text):
    """
    Parse text input like '2 hari', '1 bulan', '3 bulan 5 hari' to days
    Returns tuple: (days, hours, minutes) - defaults to (0, 0, 0) if invalid
    """
    text = text.strip().lower()
    
    # Pattern: "X hari", "X bulan", "X jam", "X menit", or combinations
    import re
    
    days = 0
    hours = 0
    minutes = 0
    
    # Extract hari
    match_hari = re.search(r'(\d+)\s*hari', text)
    if match_hari:
        days += int(match_hari.group(1))
    
    # Extract bulan
    match_bulan = re.search(r'(\d+)\s*bulan', text)
    if match_bulan:
        days += int(match_bulan.group(1)) * 30
    
    # Extract jam
    match_jam = re.search(r'(\d+)\s*jam', text)
    if match_jam:
        hours += int(match_jam.group(1))
    
    # Extract menit
    match_menit = re.search(r'(\d+)\s*menit', text)
    if match_menit:
        minutes += int(match_menit.group(1))
    
    # Check if any valid pattern was found - return (0,0,0) if nothing found
    if days == 0 and hours == 0 and minutes == 0:
        return 0, 0, 0
    
    return days, hours, minutes

def format_duration_readable(days):
    """Convert days to readable format (X hari / X bulan)"""
    if days <= 0:
        return "Permanent"
    
    months = days // 30
    remaining_days = days % 30
    
    if months > 0 and remaining_days == 0:
        return f"{months} bulan" if months > 1 else "1 bulan"
    elif months > 0 and remaining_days > 0:
        return f"{months} bulan {remaining_days} hari"
    else:
        return f"{days} hari"

def format_duration_text_readable(days, hours, minutes):
    """Format parsed duration to readable display"""
    if days == 0 and hours == 0 and minutes == 0:
        return "Permanent"
    
    parts = []
    if days > 0:
        parts.append(f"{days} hari")
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    
    return " ".join(parts) if parts else "Permanent"

def is_code_expired(code_data):
    """Check if redeem code has expired"""
    if not code_data.get("code_expired"):
        return False
    
    try:
        expired_dt = datetime.strptime(code_data["code_expired"], "%Y-%m-%d %H:%M:%S")
        return datetime.now() > expired_dt
    except:
        return False

def format_code_expiry_readable(days=0, hours=0, minutes=0):
    """Format code expiry dengan hari jam menit detail"""
    if days == 0 and hours == 0 and minutes == 0:
        return "Permanent"
    
    parts = []
    if days > 0:
        parts.append(f"{days} hari")
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    
    return " ".join(parts) if parts else "Permanent"
