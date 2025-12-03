# KIFZL DEV BOT V2 PRO

## Overview
A premium Telegram bot with VIP/VVIP membership system, file processing tools, and comprehensive owner panel. Built with Python and PostgreSQL.

## Project Structure
```
├── main.py              # Main bot entry point
├── config.py            # Configuration and settings
├── database/
│   ├── connection.py    # PostgreSQL connection pool
│   └── models.py        # Database models for all 14 tables
├── commands/
│   ├── start.py           # Start command with welcome message
│   ├── menu.py            # Main menu handler
│   ├── redeem.py          # Redeem code system
│   ├── owner_panel.py     # Owner management panel
│   ├── monitoring.py      # Bot monitoring tools
│   ├── maintenance.py     # Maintenance mode system
│   ├── sistem_bot.py      # System Bot menu (Status, Debug, Integrity Check)
│   ├── manajemen_grup.py  # Group Management (Anti-Link/Spam/Virtex, Welcome)
│   ├── pengaturan_grup.py # Group Settings (Configure group features)
│   ├── group_guardian.py  # Group protection handlers (Auto moderation)
│   ├── status.py          # User status display
│   ├── vip_info.py        # VIP/VVIP information
│   ├── profil.py          # User profile display
│   └── ... (file conversion tools)
└── utils/
    ├── helpers.py         # Helper functions
    └── rate_limiter.py    # Rate limiting and security
```

## Database Tables (PostgreSQL)
1. users - User accounts and roles
2. admins - Admin management
3. sessions - Active user sessions
4. vip_access - VIP membership tracking
5. vvip_access - VVIP membership tracking
6. redeem_codes - Redeemable access codes
7. group_settings - Group configuration
8. activity_logs - User activity logging
9. monitoring_logs - System monitoring
10. bot_status - Bot state/settings
11. system_security - Security events
12. file_processing - File task tracking
13. messages - Message storage
14. rate_limits - Rate limiting data
15. required_groups - Mandatory group join configuration
16. user_verification - User verification status tracking
17. guild_modes - Group mode settings (enable/disable bot in groups)

## Key Features
- VIP/VVIP membership system with time-based expiry
- Redeem code generation and redemption
- Owner panel with user management
- Monitoring dashboard with system stats
- Maintenance mode for scheduled downtime
- All messages use Markdown format
- Keyboard buttons use 🜲 format
- Sistem Bot: Status, Debug Mode, Integrity Check, Reload Modules, Clear Cache, System Info
- Manajemen Grup: Anti-Link, Anti-Spam, Anti-Virtex, Auto Welcome, Slowmode, Banned Words
- Pengaturan Grup: View Settings, Set Welcome Message, Whitelist Links, Reset Settings
- Group Guardian: Automatic group moderation and protection handlers
- Rate Limiter: Protection against spam and flood attacks

## 2-Group Verification System
- Mandatory verification for all users (except owner)
- Users must join 2 required groups before using the bot
- Inline buttons with 🜲 format for group joining
- Automatic access revocation when user leaves required groups
- Access revoked = status reset to REGULER with limit 0
- Separate functionality: Private mode vs Group mode
- Owner (ID: 8317563450, @KIFZLDEV) bypasses all verification
- Required groups configured in config.py as REQUIRED_GROUPS list

## Environment Variables
- TELEGRAM_BOT_TOKEN: Bot token from @BotFather
- DATABASE_URL: PostgreSQL connection string (auto-set by Replit)

## User Preferences
- All bot messages use `parse_mode="Markdown"`
- Keyboard buttons use format: 🜲 <Button Name> 🜲
- Creator credit: @KIFZLDEV (protected, cannot be changed)
- Owner ID: 8317563450

## Recent Changes
- 2024-12-03: Migrated from MongoDB to PostgreSQL
- 2024-12-03: Updated all command files with Markdown formatting
- 2024-12-03: Implemented 🜲 button format throughout
- 2024-12-03: Added forced group join system
- 2024-12-03: Created 14 SQL tables with proper structure
- 2024-12-03: Added Sistem Bot menu with status/debug/integrity features
- 2024-12-03: Added Manajemen Grup with anti-link/spam/virtex protection
- 2024-12-03: Added Pengaturan Grup for group configuration
- 2024-12-03: Added Group Guardian for automatic moderation
- 2024-12-03: Added Rate Limiter for security protection
- 2024-12-03: Added GroupMemberModel to database models
- 2024-12-03: Integrated rate limiting into main message handler
- 2024-12-03: Implemented comprehensive 2-group mandatory verification system
- 2024-12-03: Added 3 new database tables: required_groups, user_verification, guild_modes
- 2024-12-03: Added inline button verification with 🜲 format
- 2024-12-03: Added automatic access revocation on group leave
- 2024-12-03: Added separate Private/Group mode handling
- 2024-12-03: Added owner bypass for all verification (ID: 8317563450)
