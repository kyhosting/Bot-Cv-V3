import asyncio
import time
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityManager:
    def __init__(self):
        self.rate_limits: Dict[int, list] = defaultdict(list)
        self.flood_tracker: Dict[int, int] = defaultdict(int)
        self.spam_patterns: Dict[int, list] = defaultdict(list)
        self.banned_users: Set[int] = set()
        self.quarantine_users: Dict[int, datetime] = {}
        
        self.rate_limit_window = 60
        self.rate_limit_max = 30
        self.flood_threshold = 10
        self.flood_window = 5
        self.spam_threshold = 5
        
        self.max_file_size = 50 * 1024 * 1024
        self.allowed_mime_types = [
            'text/plain',
            'text/csv',
            'text/vcard',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/octet-stream'
        ]
        
        self.link_pattern = re.compile(
            r'(https?://|www\.|t\.me/|telegram\.me/|@)[^\s]+',
            re.IGNORECASE
        )
        
        self.virtex_patterns = [
            r'(.)\1{50,}',
            r'[\u0600-\u06FF]{100,}',
            r'[\u0980-\u09FF]{100,}',
            r'[\u200B-\u200D\uFEFF]{10,}'
        ]
        
    def is_banned(self, user_id: int) -> bool:
        return user_id in self.banned_users
    
    def ban_user(self, user_id: int):
        self.banned_users.add(user_id)
        logger.warning(f"User {user_id} has been banned")
    
    def unban_user(self, user_id: int):
        self.banned_users.discard(user_id)
        logger.info(f"User {user_id} has been unbanned")
    
    def is_quarantined(self, user_id: int) -> bool:
        if user_id in self.quarantine_users:
            if datetime.utcnow() < self.quarantine_users[user_id]:
                return True
            else:
                del self.quarantine_users[user_id]
        return False
    
    def quarantine_user(self, user_id: int, minutes: int = 30):
        self.quarantine_users[user_id] = datetime.utcnow() + timedelta(minutes=minutes)
        logger.warning(f"User {user_id} quarantined for {minutes} minutes")
    
    def check_rate_limit(self, user_id: int) -> bool:
        now = time.time()
        
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id]
            if now - t < self.rate_limit_window
        ]
        
        if len(self.rate_limits[user_id]) >= self.rate_limit_max:
            return False
        
        self.rate_limits[user_id].append(now)
        return True
    
    def check_flood(self, user_id: int) -> bool:
        now = time.time()
        
        if not hasattr(self, '_flood_times'):
            self._flood_times: Dict[int, list] = defaultdict(list)
        
        self._flood_times[user_id] = [
            t for t in self._flood_times[user_id]
            if now - t < self.flood_window
        ]
        
        self._flood_times[user_id].append(now)
        
        if len(self._flood_times[user_id]) > self.flood_threshold:
            self.flood_tracker[user_id] += 1
            if self.flood_tracker[user_id] >= 3:
                self.quarantine_user(user_id, 30)
            return False
        
        return True
    
    def check_spam(self, user_id: int, message: str) -> bool:
        now = time.time()
        
        self.spam_patterns[user_id] = [
            (t, m) for t, m in self.spam_patterns[user_id]
            if now - t < 60
        ]
        
        same_message_count = sum(
            1 for t, m in self.spam_patterns[user_id]
            if m == message
        )
        
        if same_message_count >= self.spam_threshold:
            return False
        
        self.spam_patterns[user_id].append((now, message))
        return True
    
    def contains_link(self, text: str) -> bool:
        return bool(self.link_pattern.search(text))
    
    def is_virtex(self, text: str) -> bool:
        for pattern in self.virtex_patterns:
            if re.search(pattern, text):
                return True
        
        if len(text) > 5000:
            return True
        
        return False
    
    def contains_banned_word(self, text: str, banned_words: list) -> Optional[str]:
        text_lower = text.lower()
        for word in banned_words:
            if word.lower() in text_lower:
                return word
        return None
    
    def validate_file(self, file_size: int, mime_type: str = None) -> tuple:
        if file_size > self.max_file_size:
            return False, f"File terlalu besar. Maksimal {self.max_file_size // (1024*1024)}MB"
        
        return True, None
    
    def sanitize_input(self, text: str) -> str:
        dangerous_patterns = [
            r'\$\{.*?\}',
            r'\{\{.*?\}\}',
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:text/html',
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized.strip()
    
    async def full_security_check(self, user_id: int, message: str = None) -> tuple:
        if self.is_banned(user_id):
            return False, "Anda telah di-banned dari menggunakan bot ini."
        
        if self.is_quarantined(user_id):
            return False, "Anda sedang dalam masa karantina. Silakan tunggu beberapa saat."
        
        if not self.check_rate_limit(user_id):
            return False, "Terlalu banyak request. Silakan tunggu beberapa saat."
        
        if not self.check_flood(user_id):
            return False, "Terdeteksi flood. Silakan tunggu beberapa saat."
        
        if message:
            if not self.check_spam(user_id, message):
                return False, "Pesan spam terdeteksi."
            
            if self.is_virtex(message):
                return False, "Pesan virtex terdeteksi."
        
        return True, None
    
    def reset_user_stats(self, user_id: int):
        self.rate_limits.pop(user_id, None)
        self.flood_tracker.pop(user_id, None)
        self.spam_patterns.pop(user_id, None)
        if hasattr(self, '_flood_times'):
            self._flood_times.pop(user_id, None)


security_manager = SecurityManager()
