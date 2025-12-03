import os
import asyncio
import logging
import asyncpg
from typing import Optional
import json

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.is_connected = False
    
    async def connect(self, uri: str = None):
        try:
            database_url = uri or os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("DATABASE_URL not found in environment variables!")
                return False
            
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
                statement_cache_size=100
            )
            
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            self.is_connected = True
            
            await self._create_tables()
            
            logger.info("PostgreSQL connected successfully!")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            self.is_connected = False
            return False
    
    async def _create_tables(self):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        role VARCHAR(50) DEFAULT 'reguler',
                        is_banned BOOLEAN DEFAULT FALSE,
                        daily_limit INTEGER DEFAULT 10,
                        daily_used INTEGER DEFAULT 0,
                        total_requests INTEGER DEFAULT 0,
                        last_request_date DATE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        username VARCHAR(255),
                        role VARCHAR(50) DEFAULT 'admin',
                        permissions TEXT DEFAULT '{}',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vip_access (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        expired_at TIMESTAMP NOT NULL,
                        daily_limit INTEGER DEFAULT 50,
                        features_enabled TEXT DEFAULT '[]',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vvip_access (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        expired_at TIMESTAMP NOT NULL,
                        daily_limit INTEGER DEFAULT 100,
                        features_enabled TEXT DEFAULT '[]',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS redeem_codes (
                        id SERIAL PRIMARY KEY,
                        code VARCHAR(100) UNIQUE NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        duration_days INTEGER DEFAULT 7,
                        max_uses INTEGER DEFAULT 1,
                        current_uses INTEGER DEFAULT 0,
                        used_by TEXT DEFAULT '[]',
                        status VARCHAR(50) DEFAULT 'active',
                        expired_at TIMESTAMP,
                        issuer_id BIGINT,
                        notes TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        session_token VARCHAR(255),
                        data TEXT DEFAULT '{}',
                        expired_at TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS group_settings (
                        id SERIAL PRIMARY KEY,
                        group_id BIGINT UNIQUE NOT NULL,
                        group_title VARCHAR(255),
                        status VARCHAR(50) DEFAULT 'active',
                        anti_link BOOLEAN DEFAULT FALSE,
                        anti_spam BOOLEAN DEFAULT FALSE,
                        anti_virtex BOOLEAN DEFAULT FALSE,
                        auto_welcome BOOLEAN DEFAULT FALSE,
                        welcome_message TEXT DEFAULT 'Selamat datang di grup!',
                        auto_leave BOOLEAN DEFAULT FALSE,
                        auto_kick_rules TEXT DEFAULT '[]',
                        banned_words TEXT DEFAULT '[]',
                        link_whitelist TEXT DEFAULT '[]',
                        slowmode_seconds INTEGER DEFAULT 0,
                        bot_features_enabled BOOLEAN DEFAULT TRUE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS group_members (
                        id SERIAL PRIMARY KEY,
                        group_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        role VARCHAR(50) DEFAULT 'member',
                        warnings INTEGER DEFAULT 0,
                        is_muted BOOLEAN DEFAULT FALSE,
                        is_banned BOOLEAN DEFAULT FALSE,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(group_id, user_id)
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS forced_group_join (
                        id SERIAL PRIMARY KEY,
                        group_link VARCHAR(255) NOT NULL,
                        group_id BIGINT,
                        group_name VARCHAR(255),
                        is_required BOOLEAN DEFAULT TRUE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS required_groups (
                        id SERIAL PRIMARY KEY,
                        group_name VARCHAR(255) NOT NULL,
                        group_link VARCHAR(255) NOT NULL,
                        group_id BIGINT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_verification (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT UNIQUE NOT NULL,
                        joined_group1 BOOLEAN DEFAULT FALSE,
                        joined_group2 BOOLEAN DEFAULT FALSE,
                        last_verified TIMESTAMP,
                        status VARCHAR(50) DEFAULT 'not_verified',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS guild_modes (
                        id SERIAL PRIMARY KEY,
                        group_id BIGINT UNIQUE NOT NULL,
                        mode VARCHAR(10) DEFAULT 'OFF',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        username VARCHAR(255),
                        group_id BIGINT,
                        action VARCHAR(255) NOT NULL,
                        details TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS monitoring_logs (
                        id SERIAL PRIMARY KEY,
                        type VARCHAR(100) NOT NULL,
                        message TEXT,
                        level VARCHAR(50) DEFAULT 'info',
                        details TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_security (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        type VARCHAR(100) NOT NULL,
                        action VARCHAR(255),
                        ip_address VARCHAR(50),
                        details TEXT DEFAULT '{}',
                        is_blocked BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_processing (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        file_type VARCHAR(50),
                        file_name VARCHAR(255),
                        file_size BIGINT,
                        status VARCHAR(50) DEFAULT 'pending',
                        result TEXT DEFAULT '{}',
                        error_message TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS bot_status (
                        id SERIAL PRIMARY KEY,
                        key VARCHAR(100) UNIQUE NOT NULL,
                        value TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_access_user_id ON vip_access(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_access_expired_at ON vip_access(expired_at)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_vvip_access_user_id ON vvip_access(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_vvip_access_expired_at ON vvip_access(expired_at)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_redeem_codes_code ON redeem_codes(code)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON activity_logs(created_at)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_group_settings_group_id ON group_settings(group_id)")
                
                logger.info("Database tables created successfully!")
                
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
    
    async def close(self):
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("Database connection closed")
    
    async def execute(self, query: str, *args):
        if not self.pool:
            return None
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Database execute error: {e}")
            return None
    
    async def fetch(self, query: str, *args):
        if not self.pool:
            return []
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            return []
    
    async def fetchrow(self, query: str, *args):
        if not self.pool:
            return None
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error(f"Database fetchrow error: {e}")
            return None
    
    async def fetchval(self, query: str, *args):
        if not self.pool:
            return None
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error(f"Database fetchval error: {e}")
            return None

db = Database()

def get_db() -> Database:
    return db

async def init_db(uri: str = None) -> bool:
    return await db.connect(uri)

async def close_db():
    await db.close()
