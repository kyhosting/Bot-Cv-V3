from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from database.connection import get_db
import logging
import json

logger = logging.getLogger(__name__)


class UserModel:
    ROLE_REGULER = "reguler"
    ROLE_VIP = "vip"
    ROLE_VVIP = "vvip"
    ROLE_OWNER = "owner"
    
    @classmethod
    async def create_or_update(cls, user_id: int, username: str = None, first_name: str = None, 
                                last_name: str = None, role: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        
        if user:
            await db.execute("""
                UPDATE users SET username = COALESCE($2, username), 
                first_name = COALESCE($3, first_name), 
                last_name = COALESCE($4, last_name),
                role = COALESCE($5, role),
                updated_at = $6 
                WHERE user_id = $1
            """, user_id, username, first_name, last_name, role, now)
        else:
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, role, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $6)
            """, user_id, username, first_name, last_name, role or cls.ROLE_REGULER, now)
        
        row = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def get_by_id(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def update_role(cls, user_id: int, role: str):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute("""
            UPDATE users SET role = $2, updated_at = $3 WHERE user_id = $1
        """, user_id, role, datetime.utcnow())
        return result is not None
    
    @classmethod
    async def ban_user(cls, user_id: int, is_banned: bool = True):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute("""
            UPDATE users SET is_banned = $2, updated_at = $3 WHERE user_id = $1
        """, user_id, is_banned, datetime.utcnow())
        return result is not None
    
    @classmethod
    async def increment_usage(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        today = datetime.utcnow().date()
        user = await cls.get_by_id(user_id)
        
        if user:
            if user.get("last_request_date") != today:
                await db.execute("""
                    UPDATE users SET daily_used = 1, last_request_date = $2, 
                    total_requests = total_requests + 1, updated_at = $3 WHERE user_id = $1
                """, user_id, today, datetime.utcnow())
            else:
                await db.execute("""
                    UPDATE users SET daily_used = daily_used + 1, 
                    total_requests = total_requests + 1, updated_at = $2 WHERE user_id = $1
                """, user_id, datetime.utcnow())
        return True
    
    @classmethod
    async def reset_daily_limit(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute("""
            UPDATE users SET daily_used = 0, updated_at = $2 WHERE user_id = $1
        """, user_id, datetime.utcnow())
        return result is not None
    
    @classmethod
    async def set_daily_limit(cls, user_id: int, limit: int):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute("""
            UPDATE users SET daily_limit = $2, updated_at = $3 WHERE user_id = $1
        """, user_id, limit, datetime.utcnow())
        return result is not None
    
    @classmethod
    async def get_all_users(cls):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM users")
        return [dict(row) for row in rows]
    
    @classmethod
    async def get_users_by_role(cls, role: str):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM users WHERE role = $1", role)
        return [dict(row) for row in rows]
    
    @classmethod
    async def count_by_role(cls):
        db = get_db()
        if not db.is_connected:
            return {}
        rows = await db.fetch("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        return {row["role"]: row["count"] for row in rows}
    
    @classmethod
    async def count_total(cls):
        db = get_db()
        if not db.is_connected:
            return 0
        return await db.fetchval("SELECT COUNT(*) FROM users") or 0


class AdminModel:
    @classmethod
    async def add_admin(cls, user_id: int, admin_number: str, navy_number: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        await db.execute("""
            INSERT INTO admins (user_id, username, role, created_at, updated_at)
            VALUES ($1, $2, 'admin', $3, $3)
            ON CONFLICT (user_id) DO UPDATE SET updated_at = $3
        """, user_id, admin_number, now)
        row = await db.fetchrow("SELECT * FROM admins WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def get_by_id(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM admins WHERE user_id = $1", user_id)
        return dict(row) if row else None


class SessionModel:
    @classmethod
    async def create_session(cls, user_id: int, session_type: str, data: dict = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        await db.execute("""
            INSERT INTO sessions (user_id, session_token, data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $4)
        """, user_id, session_type, json.dumps(data or {}), now)
        row = await db.fetchrow("SELECT * FROM sessions WHERE user_id = $1 ORDER BY id DESC LIMIT 1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def update_session(cls, user_id: int, session_type: str, data: dict):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute("""
            UPDATE sessions SET data = $3, updated_at = $4 
            WHERE user_id = $1 AND session_token = $2 AND is_active = TRUE
        """, user_id, session_type, json.dumps(data), datetime.utcnow())
        return result is not None
    
    @classmethod
    async def end_session(cls, user_id: int, session_type: str = None):
        db = get_db()
        if not db.is_connected:
            return False
        if session_type:
            result = await db.execute("""
                UPDATE sessions SET is_active = FALSE, updated_at = $3 
                WHERE user_id = $1 AND session_token = $2
            """, user_id, session_type, datetime.utcnow())
        else:
            result = await db.execute("""
                UPDATE sessions SET is_active = FALSE, updated_at = $2 WHERE user_id = $1
            """, user_id, datetime.utcnow())
        return result is not None
    
    @classmethod
    async def get_active_session(cls, user_id: int, session_type: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        if session_type:
            row = await db.fetchrow("""
                SELECT * FROM sessions WHERE user_id = $1 AND session_token = $2 AND is_active = TRUE
            """, user_id, session_type)
        else:
            row = await db.fetchrow("""
                SELECT * FROM sessions WHERE user_id = $1 AND is_active = TRUE ORDER BY id DESC LIMIT 1
            """, user_id)
        return dict(row) if row else None


class VIPAccessModel:
    @classmethod
    async def grant_access(cls, user_id: int, days: int, features: list = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        expired_at = now + timedelta(days=days)
        
        existing = await db.fetchrow("SELECT * FROM vip_access WHERE user_id = $1", user_id)
        
        if existing and existing["status"] == "active":
            current_expiry = existing["expired_at"]
            if current_expiry > now:
                expired_at = current_expiry + timedelta(days=days)
        
        await db.execute("""
            INSERT INTO vip_access (user_id, status, expired_at, daily_limit, features_enabled, created_at, updated_at)
            VALUES ($1, 'active', $2, 50, $3, $4, $4)
            ON CONFLICT (user_id) DO UPDATE SET status = 'active', expired_at = $2, updated_at = $4
        """, user_id, expired_at, json.dumps(features or ["all"]), now)
        
        await UserModel.update_role(user_id, UserModel.ROLE_VIP)
        
        row = await db.fetchrow("SELECT * FROM vip_access WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def get_access(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM vip_access WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def check_and_expire(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        access = await db.fetchrow("""
            SELECT * FROM vip_access WHERE user_id = $1 AND status = 'active'
        """, user_id)
        if access and access["expired_at"] < datetime.utcnow():
            await db.execute("""
                UPDATE vip_access SET status = 'expired', updated_at = $2 WHERE user_id = $1
            """, user_id, datetime.utcnow())
            await UserModel.update_role(user_id, UserModel.ROLE_REGULER)
            return True
        return False
    
    @classmethod
    async def count_active(cls):
        db = get_db()
        if not db.is_connected:
            return 0
        return await db.fetchval("SELECT COUNT(*) FROM vip_access WHERE status = 'active'") or 0
    
    @classmethod
    async def get_all_active(cls):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM vip_access WHERE status = 'active'")
        return [dict(row) for row in rows]


class VVIPAccessModel:
    @classmethod
    async def grant_access(cls, user_id: int, days: int, features: list = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        expired_at = now + timedelta(days=days)
        
        existing = await db.fetchrow("SELECT * FROM vvip_access WHERE user_id = $1", user_id)
        
        if existing and existing["status"] == "active":
            current_expiry = existing["expired_at"]
            if current_expiry > now:
                expired_at = current_expiry + timedelta(days=days)
        
        await db.execute("""
            INSERT INTO vvip_access (user_id, status, expired_at, daily_limit, features_enabled, created_at, updated_at)
            VALUES ($1, 'active', $2, 100, $3, $4, $4)
            ON CONFLICT (user_id) DO UPDATE SET status = 'active', expired_at = $2, updated_at = $4
        """, user_id, expired_at, json.dumps(features or ["all", "priority"]), now)
        
        await UserModel.update_role(user_id, UserModel.ROLE_VVIP)
        
        row = await db.fetchrow("SELECT * FROM vvip_access WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def get_access(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM vvip_access WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def check_and_expire(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        access = await db.fetchrow("""
            SELECT * FROM vvip_access WHERE user_id = $1 AND status = 'active'
        """, user_id)
        if access and access["expired_at"] < datetime.utcnow():
            await db.execute("""
                UPDATE vvip_access SET status = 'expired', updated_at = $2 WHERE user_id = $1
            """, user_id, datetime.utcnow())
            await UserModel.update_role(user_id, UserModel.ROLE_REGULER)
            return True
        return False
    
    @classmethod
    async def count_active(cls):
        db = get_db()
        if not db.is_connected:
            return 0
        return await db.fetchval("SELECT COUNT(*) FROM vvip_access WHERE status = 'active'") or 0
    
    @classmethod
    async def get_all_active(cls):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM vvip_access WHERE status = 'active'")
        return [dict(row) for row in rows]


class RedeemCodeModel:
    TYPE_VIP = "vip"
    TYPE_VVIP = "vvip"
    TYPE_CREDIT = "credit"
    
    STATUS_ACTIVE = "active"
    STATUS_USED = "used"
    STATUS_FULL = "full"
    STATUS_EXPIRED = "expired"
    
    @classmethod
    async def create_code(cls, code: str, code_type: str, duration_days: int, 
                          max_uses: int = 1, expired_days: int = 30, 
                          issuer_id: int = None, notes: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        expired_at = now + timedelta(days=expired_days)
        
        try:
            await db.execute("""
                INSERT INTO redeem_codes (code, type, duration_days, max_uses, current_uses, used_by, status, expired_at, issuer_id, notes, created_at, updated_at)
                VALUES ($1, $2, $3, $4, 0, '[]', 'active', $5, $6, $7, $8, $8)
            """, code.upper(), code_type, duration_days, max_uses, expired_at, issuer_id, notes, now)
            row = await db.fetchrow("SELECT * FROM redeem_codes WHERE code = $1", code.upper())
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error creating redeem code: {e}")
            return None
    
    @classmethod
    async def get_code(cls, code: str):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM redeem_codes WHERE code = $1", code.upper())
        return dict(row) if row else None
    
    @classmethod
    async def redeem(cls, code: str, user_id: int):
        db = get_db()
        if not db.is_connected:
            return {"success": False, "message": "Database tidak tersedia"}
        
        now = datetime.utcnow()
        code_data = await cls.get_code(code)
        
        if not code_data:
            return {"success": False, "message": "Kode tidak ditemukan"}
        
        if code_data.get("status") == cls.STATUS_EXPIRED:
            return {"success": False, "message": "Kode sudah expired"}
        
        if code_data.get("status") == cls.STATUS_FULL:
            return {"success": False, "message": "Kode sudah mencapai batas penggunaan"}
        
        if code_data.get("expired_at") < now:
            await db.execute("""
                UPDATE redeem_codes SET status = 'expired', updated_at = $2 WHERE code = $1
            """, code.upper(), now)
            return {"success": False, "message": "Kode sudah expired"}
        
        used_by = json.loads(code_data.get("used_by", "[]"))
        if user_id in used_by:
            return {"success": False, "message": "Anda sudah pernah menggunakan kode ini"}
        
        new_uses = code_data.get("current_uses", 0) + 1
        new_status = cls.STATUS_ACTIVE
        if new_uses >= code_data.get("max_uses", 1):
            new_status = cls.STATUS_FULL
        
        used_by.append(user_id)
        
        await db.execute("""
            UPDATE redeem_codes SET current_uses = $2, status = $3, used_by = $4, updated_at = $5 WHERE code = $1
        """, code.upper(), new_uses, new_status, json.dumps(used_by), now)
        
        code_type = code_data.get("type")
        duration = code_data.get("duration_days", 7)
        
        if code_type == cls.TYPE_VIP:
            await VIPAccessModel.grant_access(user_id, duration)
        elif code_type == cls.TYPE_VVIP:
            await VVIPAccessModel.grant_access(user_id, duration)
        
        return {
            "success": True,
            "message": "Redeem berhasil!",
            "type": code_type,
            "duration": duration
        }
    
    @classmethod
    async def get_all_codes(cls, status: str = None):
        db = get_db()
        if not db.is_connected:
            return []
        
        if status:
            rows = await db.fetch("SELECT * FROM redeem_codes WHERE status = $1 ORDER BY created_at DESC", status)
        else:
            rows = await db.fetch("SELECT * FROM redeem_codes ORDER BY created_at DESC")
        return [dict(row) for row in rows]
    
    @classmethod
    async def delete_code(cls, code: str):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute("DELETE FROM redeem_codes WHERE code = $1", code.upper())
        return result is not None


class GroupSettingsModel:
    @classmethod
    async def get_or_create(cls, group_id: int, group_title: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        settings = await db.fetchrow("SELECT * FROM group_settings WHERE group_id = $1", group_id)
        
        if not settings:
            await db.execute("""
                INSERT INTO group_settings (group_id, group_title, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
            """, group_id, group_title, now)
            settings = await db.fetchrow("SELECT * FROM group_settings WHERE group_id = $1", group_id)
        
        return dict(settings) if settings else None
    
    @classmethod
    async def update_setting(cls, group_id: int, key: str, value: Any):
        db = get_db()
        if not db.is_connected:
            return False
        result = await db.execute(f"""
            UPDATE group_settings SET {key} = $2, updated_at = $3 WHERE group_id = $1
        """, group_id, value, datetime.utcnow())
        return result is not None
    
    @classmethod
    async def add_banned_word(cls, group_id: int, word: str):
        db = get_db()
        if not db.is_connected:
            return False
        settings = await cls.get_or_create(group_id)
        if settings:
            banned = json.loads(settings.get("banned_words", "[]"))
            if word.lower() not in banned:
                banned.append(word.lower())
                await db.execute("""
                    UPDATE group_settings SET banned_words = $2, updated_at = $3 WHERE group_id = $1
                """, group_id, json.dumps(banned), datetime.utcnow())
        return True
    
    @classmethod
    async def remove_banned_word(cls, group_id: int, word: str):
        db = get_db()
        if not db.is_connected:
            return False
        settings = await cls.get_or_create(group_id)
        if settings:
            banned = json.loads(settings.get("banned_words", "[]"))
            if word.lower() in banned:
                banned.remove(word.lower())
                await db.execute("""
                    UPDATE group_settings SET banned_words = $2, updated_at = $3 WHERE group_id = $1
                """, group_id, json.dumps(banned), datetime.utcnow())
        return True
    
    @classmethod
    async def get_all_groups(cls):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM group_settings")
        return [dict(row) for row in rows]
    
    @classmethod
    async def count_groups(cls):
        db = get_db()
        if not db.is_connected:
            return 0
        return await db.fetchval("SELECT COUNT(*) FROM group_settings") or 0


class ActivityLogModel:
    @classmethod
    async def log(cls, user_id: int, action: str, details: dict = None, 
                  username: str = None, group_id: int = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        await db.execute("""
            INSERT INTO activity_logs (user_id, username, group_id, action, details, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, username, group_id, action, json.dumps(details or {}), now)
        return True
    
    @classmethod
    async def get_user_logs(cls, user_id: int, limit: int = 100):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM activity_logs WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2
        """, user_id, limit)
        return [dict(row) for row in rows]
    
    @classmethod
    async def get_recent_logs(cls, limit: int = 100):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT $1
        """, limit)
        return [dict(row) for row in rows]
    
    @classmethod
    async def get_logs_by_action(cls, action: str, limit: int = 100):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM activity_logs WHERE action = $1 ORDER BY created_at DESC LIMIT $2
        """, action, limit)
        return [dict(row) for row in rows]


class MonitoringLogModel:
    @classmethod
    async def log(cls, log_type: str, message: str, level: str = "info", details: dict = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        await db.execute("""
            INSERT INTO monitoring_logs (type, message, level, details, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """, log_type, message, level, json.dumps(details or {}), datetime.utcnow())
        return True
    
    @classmethod
    async def get_recent(cls, limit: int = 100):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM monitoring_logs ORDER BY created_at DESC LIMIT $1
        """, limit)
        return [dict(row) for row in rows]
    
    @classmethod
    async def get_by_type(cls, log_type: str, limit: int = 100):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM monitoring_logs WHERE type = $1 ORDER BY created_at DESC LIMIT $2
        """, log_type, limit)
        return [dict(row) for row in rows]
    
    @classmethod
    async def get_errors(cls, limit: int = 50):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM monitoring_logs WHERE level = 'error' ORDER BY created_at DESC LIMIT $1
        """, limit)
        return [dict(row) for row in rows]


class BotStatusModel:
    @classmethod
    async def get(cls, key: str):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM bot_status WHERE key = $1", key)
        return row["value"] if row else None
    
    @classmethod
    async def set(cls, key: str, value: str):
        db = get_db()
        if not db.is_connected:
            return False
        now = datetime.utcnow()
        await db.execute("""
            INSERT INTO bot_status (key, value, created_at, updated_at)
            VALUES ($1, $2, $3, $3)
            ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = $3
        """, key, value, now)
        return True
    
    @classmethod
    async def delete(cls, key: str):
        db = get_db()
        if not db.is_connected:
            return False
        await db.execute("DELETE FROM bot_status WHERE key = $1", key)
        return True


class GroupMemberModel:
    @classmethod
    async def add_member(cls, group_id: int, user_id: int, username: str = None, first_name: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        try:
            await db.execute("""
                INSERT INTO group_members (group_id, user_id, username, first_name, joined_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5, $5)
                ON CONFLICT (group_id, user_id) DO UPDATE SET 
                username = COALESCE($3, group_members.username),
                first_name = COALESCE($4, group_members.first_name),
                is_active = TRUE,
                updated_at = $5
            """, group_id, user_id, username, first_name, now)
            return True
        except Exception as e:
            logger.error(f"Error adding member: {e}")
            return None
    
    @classmethod
    async def remove_member(cls, group_id: int, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        try:
            await db.execute("""
                UPDATE group_members SET is_active = FALSE, updated_at = $3 
                WHERE group_id = $1 AND user_id = $2
            """, group_id, user_id, datetime.utcnow())
            return True
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            return False
    
    @classmethod
    async def get_member(cls, group_id: int, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        
        row = await db.fetchrow("""
            SELECT * FROM group_members WHERE group_id = $1 AND user_id = $2
        """, group_id, user_id)
        return dict(row) if row else None
    
    @classmethod
    async def warn_member(cls, group_id: int, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        await db.execute("""
            UPDATE group_members SET warnings = warnings + 1, updated_at = $3 
            WHERE group_id = $1 AND user_id = $2
        """, group_id, user_id, datetime.utcnow())
        return True
    
    @classmethod
    async def get_group_members(cls, group_id: int, limit: int = 100):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM group_members WHERE group_id = $1 AND is_active = TRUE ORDER BY joined_at DESC LIMIT $2
        """, group_id, limit)
        return [dict(row) for row in rows]


class SystemSecurityModel:
    @classmethod
    async def log_security(cls, user_id: int, sec_type: str, action: str, details: dict = None, is_blocked: bool = False):
        db = get_db()
        if not db.is_connected:
            return None
        
        await db.execute("""
            INSERT INTO system_security (user_id, type, action, details, is_blocked, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, user_id, sec_type, action, json.dumps(details or {}), is_blocked, datetime.utcnow())
        return True
    
    @classmethod
    async def get_user_security_logs(cls, user_id: int, limit: int = 50):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM system_security WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2
        """, user_id, limit)
        return [dict(row) for row in rows]
    
    @classmethod
    async def is_user_blocked(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        row = await db.fetchrow("""
            SELECT * FROM system_security WHERE user_id = $1 AND is_blocked = TRUE 
            ORDER BY created_at DESC LIMIT 1
        """, user_id)
        return row is not None


class FileTaskModel:
    @classmethod
    async def create_task(cls, user_id: int, file_type: str, file_name: str, file_size: int = 0):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        await db.execute("""
            INSERT INTO file_processing (user_id, file_type, file_name, file_size, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, 'pending', $5, $5)
        """, user_id, file_type, file_name, file_size, now)
        row = await db.fetchrow("""
            SELECT * FROM file_processing WHERE user_id = $1 ORDER BY id DESC LIMIT 1
        """, user_id)
        return dict(row) if row else None
    
    @classmethod
    async def update_status(cls, task_id: int, status: str, result: dict = None, error: str = None):
        db = get_db()
        if not db.is_connected:
            return False
        await db.execute("""
            UPDATE file_processing SET status = $2, result = $3, error_message = $4, updated_at = $5 WHERE id = $1
        """, task_id, status, json.dumps(result or {}), error, datetime.utcnow())
        return True
    
    @classmethod
    async def get_user_tasks(cls, user_id: int, limit: int = 20):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("""
            SELECT * FROM file_processing WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2
        """, user_id, limit)
        return [dict(row) for row in rows]


class UserVerificationModel:
    STATUS_VERIFIED = "verified"
    STATUS_NOT_VERIFIED = "not_verified"
    
    @classmethod
    async def get_verification(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return None
        row = await db.fetchrow("SELECT * FROM user_verification WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def create_or_update(cls, user_id: int, joined_group1: bool = False, 
                                joined_group2: bool = False, status: str = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        if status is None:
            status = cls.STATUS_VERIFIED if (joined_group1 and joined_group2) else cls.STATUS_NOT_VERIFIED
        
        existing = await cls.get_verification(user_id)
        
        if existing:
            await db.execute("""
                UPDATE user_verification SET 
                joined_group1 = $2, joined_group2 = $3, status = $4, 
                last_verified = $5, updated_at = $5
                WHERE user_id = $1
            """, user_id, joined_group1, joined_group2, status, now)
        else:
            await db.execute("""
                INSERT INTO user_verification (user_id, joined_group1, joined_group2, status, last_verified, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5, $5)
            """, user_id, joined_group1, joined_group2, status, now)
        
        row = await db.fetchrow("SELECT * FROM user_verification WHERE user_id = $1", user_id)
        return dict(row) if row else None
    
    @classmethod
    async def is_verified(cls, user_id: int):
        verification = await cls.get_verification(user_id)
        if not verification:
            return False
        return (verification.get("joined_group1", False) and 
                verification.get("joined_group2", False) and 
                verification.get("status") == cls.STATUS_VERIFIED)
    
    @classmethod
    async def revoke_access(cls, user_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        
        now = datetime.utcnow()
        await db.execute("""
            UPDATE user_verification SET 
            joined_group1 = FALSE, joined_group2 = FALSE, 
            status = 'not_verified', updated_at = $2
            WHERE user_id = $1
        """, user_id, now)
        
        await db.execute("""
            UPDATE users SET role = 'reguler', daily_limit = 0, updated_at = $2
            WHERE user_id = $1
        """, user_id, now)
        
        await db.execute("""
            UPDATE vip_access SET status = 'revoked', updated_at = $2
            WHERE user_id = $1 AND status = 'active'
        """, user_id, now)
        
        await db.execute("""
            UPDATE vvip_access SET status = 'revoked', updated_at = $2
            WHERE user_id = $1 AND status = 'active'
        """, user_id, now)
        
        return True


class GuildModeModel:
    MODE_ON = "ON"
    MODE_OFF = "OFF"
    
    @classmethod
    async def get_mode(cls, group_id: int):
        db = get_db()
        if not db.is_connected:
            return cls.MODE_OFF
        row = await db.fetchrow("SELECT * FROM guild_modes WHERE group_id = $1", group_id)
        if row:
            return row["mode"]
        return cls.MODE_OFF
    
    @classmethod
    async def set_mode(cls, group_id: int, mode: str):
        db = get_db()
        if not db.is_connected:
            return False
        
        now = datetime.utcnow()
        existing = await db.fetchrow("SELECT * FROM guild_modes WHERE group_id = $1", group_id)
        
        if existing:
            await db.execute("""
                UPDATE guild_modes SET mode = $2, updated_at = $3 WHERE group_id = $1
            """, group_id, mode, now)
        else:
            await db.execute("""
                INSERT INTO guild_modes (group_id, mode, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
            """, group_id, mode, now)
        return True
    
    @classmethod
    async def is_group_enabled(cls, group_id: int):
        mode = await cls.get_mode(group_id)
        return mode == cls.MODE_ON
    
    @classmethod
    async def get_all_groups(cls):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM guild_modes ORDER BY updated_at DESC")
        return [dict(row) for row in rows]


class RequiredGroupModel:
    @classmethod
    async def get_all(cls):
        db = get_db()
        if not db.is_connected:
            return []
        rows = await db.fetch("SELECT * FROM required_groups WHERE is_active = TRUE")
        return [dict(row) for row in rows]
    
    @classmethod
    async def add_group(cls, group_name: str, group_link: str, group_id: int = None):
        db = get_db()
        if not db.is_connected:
            return None
        
        now = datetime.utcnow()
        await db.execute("""
            INSERT INTO required_groups (group_name, group_link, group_id, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $4)
        """, group_name, group_link, group_id, now)
        row = await db.fetchrow("SELECT * FROM required_groups WHERE group_link = $1", group_link)
        return dict(row) if row else None
    
    @classmethod
    async def remove_group(cls, group_id: int):
        db = get_db()
        if not db.is_connected:
            return False
        await db.execute("""
            UPDATE required_groups SET is_active = FALSE, updated_at = $2 WHERE id = $1
        """, group_id, datetime.utcnow())
        return True
