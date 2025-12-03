import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

db_available = False
try:
    from database.models import ActivityLogModel
    from database.connection import get_db
    db_available = True
except ImportError:
    pass


class RateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[int, list] = defaultdict(list)
        self.blocked_users: Dict[int, datetime] = {}
        self.warning_counts: Dict[int, int] = defaultdict(int)
    
    def is_allowed(self, user_id: int) -> tuple:
        now = datetime.now()
        
        if user_id in self.blocked_users:
            block_until = self.blocked_users[user_id]
            if now < block_until:
                remaining = (block_until - now).total_seconds()
                return False, f"Anda diblokir sementara. Coba lagi dalam {int(remaining)} detik."
            else:
                del self.blocked_users[user_id]
                self.warning_counts[user_id] = 0
        
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.requests[user_id] = [req for req in self.requests[user_id] if req > cutoff]
        
        if len(self.requests[user_id]) >= self.max_requests:
            self.warning_counts[user_id] += 1
            
            if self.warning_counts[user_id] >= 3:
                block_duration = min(300, 60 * self.warning_counts[user_id])
                self.blocked_users[user_id] = now + timedelta(seconds=block_duration)
                return False, f"Terlalu banyak request. Anda diblokir selama {block_duration} detik."
            
            return False, "Terlalu banyak request. Mohon tunggu sebentar."
        
        self.requests[user_id].append(now)
        return True, None
    
    def get_remaining(self, user_id: int) -> int:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.requests[user_id] = [req for req in self.requests[user_id] if req > cutoff]
        return max(0, self.max_requests - len(self.requests[user_id]))
    
    def reset_user(self, user_id: int):
        if user_id in self.requests:
            del self.requests[user_id]
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
        if user_id in self.warning_counts:
            del self.warning_counts[user_id]


class AntiFlood:
    def __init__(self, max_messages: int = 5, window_seconds: int = 3):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.message_times: Dict[int, list] = defaultdict(list)
        self.flood_warnings: Dict[int, int] = defaultdict(int)
    
    def check_flood(self, user_id: int) -> tuple:
        now = time.time()
        
        cutoff = now - self.window_seconds
        self.message_times[user_id] = [t for t in self.message_times[user_id] if t > cutoff]
        
        self.message_times[user_id].append(now)
        
        if len(self.message_times[user_id]) > self.max_messages:
            self.flood_warnings[user_id] += 1
            return True, self.flood_warnings[user_id]
        
        return False, 0
    
    def reset_user(self, user_id: int):
        if user_id in self.message_times:
            del self.message_times[user_id]
        if user_id in self.flood_warnings:
            del self.flood_warnings[user_id]


class SecurityManager:
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
        self.anti_flood = AntiFlood(max_messages=5, window_seconds=3)
        self.suspicious_users: Dict[int, dict] = {}
        self.banned_users: set = set()
    
    async def check_request(self, user_id: int, action: str = None) -> tuple:
        if user_id in self.banned_users:
            return False, "Akun Anda telah dibanned dari menggunakan bot ini."
        
        is_allowed, rate_msg = self.rate_limiter.is_allowed(user_id)
        if not is_allowed:
            await self._log_security_event(user_id, "rate_limit", action)
            return False, rate_msg
        
        is_flood, flood_count = self.anti_flood.check_flood(user_id)
        if is_flood:
            if flood_count >= 5:
                self._mark_suspicious(user_id, "repeated_flood")
            await self._log_security_event(user_id, "flood_detected", action)
            return False, "Mohon tunggu sebentar sebelum mengirim pesan lagi."
        
        return True, None
    
    def _mark_suspicious(self, user_id: int, reason: str):
        now = datetime.now()
        
        if user_id not in self.suspicious_users:
            self.suspicious_users[user_id] = {
                "first_detected": now,
                "reasons": [reason],
                "count": 1
            }
        else:
            self.suspicious_users[user_id]["reasons"].append(reason)
            self.suspicious_users[user_id]["count"] += 1
            
            if self.suspicious_users[user_id]["count"] >= 10:
                self.banned_users.add(user_id)
                logger.warning(f"User {user_id} auto-banned due to suspicious activity")
    
    async def _log_security_event(self, user_id: int, event_type: str, action: str = None):
        if db_available:
            try:
                db = get_db()
                if db.is_connected:
                    from database.models import SystemSecurityModel
                    await SystemSecurityModel.log_security(
                        user_id=user_id,
                        security_type=event_type,
                        action=action or "unknown",
                        details={}
                    )
            except Exception as e:
                logger.error(f"Error logging security event: {e}")
    
    def ban_user(self, user_id: int):
        self.banned_users.add(user_id)
        logger.info(f"User {user_id} banned")
    
    def unban_user(self, user_id: int):
        self.banned_users.discard(user_id)
        self.rate_limiter.reset_user(user_id)
        self.anti_flood.reset_user(user_id)
        if user_id in self.suspicious_users:
            del self.suspicious_users[user_id]
        logger.info(f"User {user_id} unbanned")
    
    def is_banned(self, user_id: int) -> bool:
        return user_id in self.banned_users
    
    def get_stats(self) -> dict:
        return {
            "banned_users": len(self.banned_users),
            "suspicious_users": len(self.suspicious_users),
            "active_trackers": len(self.rate_limiter.requests)
        }


security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    return security_manager


async def check_user_access(user_id: int, action: str = None) -> tuple:
    return await security_manager.check_request(user_id, action)
