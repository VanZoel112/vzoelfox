"""
Global Ban (GBan) Plugin for Vzoel Assistant
Fitur: Global ban/unban users across all groups dengan premium emoji support
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0
"""

import sqlite3
import os
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User
from telethon.errors import UserAdminInvalidError, ChatAdminRequiredError, UserNotParticipantError

# Plugin Info
PLUGIN_INFO = {
    "name": "gban",
    "version": "1.0.0",
    "description": "Global ban system with auto UTF-16 premium emoji detection and SQLite database.",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".gban", ".ungban", ".gbanlist", ".gbancheck", ".testgban"],
    "features": ["global ban", "global unban", "SQLite storage", "auto UTF-16 premium emoji", "cross-group enforcement"]
}

# Auto Premium Emoji Mapping (UTF-16 auto-detection)
PREMIUM_EMOJIS = {
    "main": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "ban": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "unban": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "warning": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "success": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "error": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "info": {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

# Database file
DB_FILE = "plugins/gban.db"
client = None

def get_utf16_length(emoji_char):
    """Get UTF-16 length of emoji character"""
    try:
        utf16_bytes = emoji_char.encode('utf-16le')
        return len(utf16_bytes) // 2
    except:
        return 1

def create_premium_emoji_entities(text):
    """Automatically create MessageEntityCustomEmoji entities for premium emojis"""
    entities = []
    utf16_offset = 0
    
    for i, char in enumerate(text):
        for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
            if char == emoji_data["emoji"]:
                emoji_length = get_utf16_length(char)
                entity = MessageEntityCustomEmoji(
                    offset=utf16_offset,
                    length=emoji_length,
                    document_id=int(emoji_data["custom_emoji_id"])
                )
                entities.append(entity)
                break
        utf16_offset += get_utf16_length(char)
    
    return entities

async def safe_send_with_premium_emojis(event, text):
    """Send message with premium emoji entities"""
    try:
        entities = create_premium_emoji_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception as e:
        await event.reply(text)

def get_emoji(emoji_type):
    """Get premium emoji with fallback"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

async def is_owner_check(user_id):
    """Simple owner check"""
    OWNER_ID = 7847025168
    return user_id == OWNER_ID

def init_database():
    """Initialize GBan database"""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gbanned_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                reason TEXT,
                banned_by INTEGER,
                banned_date TEXT,
                total_groups INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gban_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                chat_id INTEGER,
                chat_title TEXT,
                success INTEGER,
                error_msg TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[GBan] Database init error: {e}")
        return False

def add_gban(user_id, username, first_name, reason, banned_by):
    """Add user to global ban list"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""
            INSERT OR REPLACE INTO gbanned_users 
            (user_id, username, first_name, reason, banned_by, banned_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, reason, banned_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[GBan] Add error: {e}")
        return False

def remove_gban(user_id):
    """Remove user from global ban list"""
    try:
        conn = sqlite3.connect(DB_FILE)
        result = conn.execute("DELETE FROM gbanned_users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return result.rowcount > 0
    except Exception as e:
        print(f"[GBan] Remove error: {e}")
        return False

def is_gbanned(user_id):
    """Check if user is globally banned"""
    try:
        conn = sqlite3.connect(DB_FILE)
        result = conn.execute("SELECT * FROM gbanned_users WHERE user_id = ?", (user_id,))
        row = result.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        return False

def get_gban_info(user_id):
    """Get gban information for user"""
    try:
        conn = sqlite3.connect(DB_FILE)
        result = conn.execute("SELECT * FROM gbanned_users WHERE user_id = ?", (user_id,))
        row = result.fetchone()
        conn.close()
        if row:
            return {
                'user_id': row[0], 'username': row[1], 'first_name': row[2],
                'reason': row[3], 'banned_by': row[4], 'banned_date': row[5],
                'total_groups': row[6]
            }
        return None
    except Exception as e:
        return None

def get_all_gbanned():
    """Get all globally banned users"""
    try:
        conn = sqlite3.connect(DB_FILE)
        result = conn.execute("SELECT * FROM gbanned_users ORDER BY banned_date DESC")
        rows = result.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []

def log_gban_action(user_id, action, chat_id, chat_title, success, error_msg=None):
    """Log gban actions"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""
            INSERT INTO gban_logs 
            (user_id, action, chat_id, chat_title, success, error_msg, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, action, chat_id, chat_title, success, error_msg, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[GBan] Log error: {e}")

async def get_user_info(event, user_identifier):
    """Get user info from ID, username, or reply"""
    try:
        # If replying to a message
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.sender:
                return reply_msg.sender
        
        # If user provided ID or username
        if user_identifier:
            if user_identifier.isdigit():
                user_id = int(user_identifier)
                return await client.get_entity(user_id)
            else:
                # Remove @ if present
                username = user_identifier.replace('@', '')
                return await client.get_entity(username)
        
        return None
    except Exception as e:
        return None

async def gban_handler(event):
    """Global ban handler"""
    if not await is_owner_check(event.sender_id):
        return
    
    args = event.text.split(maxsplit=2)
    user_identifier = args[1] if len(args) > 1 else None
    reason = args[2] if len(args) > 2 else "No reason provided"
    
    user = await get_user_info(event, user_identifier)
    if not user:
        text = f"{get_emoji('error')} **GBan Error:** User tidak ditemukan!\n\n{get_emoji('info')} **Usage:** `.gban <user_id/@username/reply> [reason]`"
        await safe_send_with_premium_emojis(event, text)
        return
    
    # Don't ban yourself or bot accounts
    if user.id == event.sender_id:
        text = f"{get_emoji('warning')} **GBan Warning:** Tidak bisa gban diri sendiri!"
        await safe_send_with_premium_emojis(event, text)
        return
    
    if user.bot:
        text = f"{get_emoji('warning')} **GBan Warning:** Tidak bisa gban bot accounts!"
        await safe_send_with_premium_emojis(event, text)
        return
    
    # Add to global ban list
    username = getattr(user, 'username', None) or 'None'
    first_name = getattr(user, 'first_name', None) or 'Unknown'
    
    if add_gban(user.id, username, first_name, reason, event.sender_id):
        text = f"""
{get_emoji('ban')} **GLOBAL BAN ACTIVATED**

{get_emoji('main')} **Target:** [{first_name}](tg://user?id={user.id})
{get_emoji('info')} **User ID:** `{user.id}`
{get_emoji('warning')} **Reason:** {reason}
{get_emoji('success')} **Status:** Added to global ban database

{get_emoji('ban')} Executing ban across all groups...
        """.strip()
        
        status_msg = await safe_send_with_premium_emojis(event, text)
        
        # Execute ban across all groups
        success_count = 0
        total_groups = 0
        
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                total_groups += 1
                try:
                    await client.ban_participant(dialog.id, user.id)
                    success_count += 1
                    log_gban_action(user.id, "ban", dialog.id, dialog.title, True)
                except Exception as e:
                    log_gban_action(user.id, "ban", dialog.id, dialog.title, False, str(e))
                
                # Update every 5 groups
                if total_groups % 5 == 0:
                    try:
                        progress_text = f"""
{get_emoji('ban')} **GLOBAL BAN IN PROGRESS**

{get_emoji('main')} **Target:** [{first_name}](tg://user?id={user.id})
{get_emoji('success')} **Progress:** {success_count}/{total_groups} groups processed
{get_emoji('info')} **Processing...**
                        """.strip()
                        await status_msg.edit(progress_text)
                    except:
                        pass
        
        # Update database with total count
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("UPDATE gbanned_users SET total_groups = ? WHERE user_id = ?", (success_count, user.id))
            conn.commit()
            conn.close()
        except:
            pass
        
        # Final status
        final_text = f"""
{get_emoji('ban')} **GLOBAL BAN COMPLETED**

{get_emoji('main')} **Target:** [{first_name}](tg://user?id={user.id})
{get_emoji('info')} **User ID:** `{user.id}`
{get_emoji('warning')} **Reason:** {reason}
{get_emoji('success')} **Banned from:** {success_count}/{total_groups} groups
{get_emoji('ban')} **Status:** User globally banned
        """.strip()
        
        try:
            await status_msg.edit(final_text)
        except:
            await safe_send_with_premium_emojis(event, final_text)
    
    else:
        text = f"{get_emoji('error')} **GBan Error:** Failed to add user to ban database"
        await safe_send_with_premium_emojis(event, text)

async def ungban_handler(event):
    """Global unban handler"""
    if not await is_owner_check(event.sender_id):
        return
    
    args = event.text.split(maxsplit=1)
    user_identifier = args[1] if len(args) > 1 else None
    
    user = await get_user_info(event, user_identifier)
    if not user:
        text = f"{get_emoji('error')} **UnGBan Error:** User tidak ditemukan!\n\n{get_emoji('info')} **Usage:** `.ungban <user_id/@username/reply>`"
        await safe_send_with_premium_emojis(event, text)
        return
    
    # Check if user is gbanned
    gban_info = get_gban_info(user.id)
    if not gban_info:
        text = f"{get_emoji('warning')} **UnGBan Warning:** User tidak ada dalam global ban list!"
        await safe_send_with_premium_emojis(event, text)
        return
    
    # Remove from global ban list
    if remove_gban(user.id):
        first_name = getattr(user, 'first_name', None) or 'Unknown'
        
        text = f"""
{get_emoji('unban')} **GLOBAL UNBAN ACTIVATED**

{get_emoji('main')} **Target:** [{first_name}](tg://user?id={user.id})
{get_emoji('info')} **User ID:** `{user.id}`
{get_emoji('success')} **Status:** Removed from global ban database

{get_emoji('unban')} Executing unban across all groups...
        """.strip()
        
        status_msg = await safe_send_with_premium_emojis(event, text)
        
        # Execute unban across all groups
        success_count = 0
        total_groups = 0
        
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                total_groups += 1
                try:
                    await client.unban_participant(dialog.id, user.id)
                    success_count += 1
                    log_gban_action(user.id, "unban", dialog.id, dialog.title, True)
                except Exception as e:
                    log_gban_action(user.id, "unban", dialog.id, dialog.title, False, str(e))
                
                # Update every 5 groups
                if total_groups % 5 == 0:
                    try:
                        progress_text = f"""
{get_emoji('unban')} **GLOBAL UNBAN IN PROGRESS**

{get_emoji('main')} **Target:** [{first_name}](tg://user?id={user.id})
{get_emoji('success')} **Progress:** {success_count}/{total_groups} groups processed
{get_emoji('info')} **Processing...**
                        """.strip()
                        await status_msg.edit(progress_text)
                    except:
                        pass
        
        # Final status
        final_text = f"""
{get_emoji('unban')} **GLOBAL UNBAN COMPLETED**

{get_emoji('main')} **Target:** [{first_name}](tg://user?id={user.id})
{get_emoji('info')} **User ID:** `{user.id}`
{get_emoji('success')} **Unbanned from:** {success_count}/{total_groups} groups
{get_emoji('unban')} **Status:** User globally unbanned
        """.strip()
        
        try:
            await status_msg.edit(final_text)
        except:
            await safe_send_with_premium_emojis(event, final_text)
    
    else:
        text = f"{get_emoji('error')} **UnGBan Error:** Failed to remove user from ban database"
        await safe_send_with_premium_emojis(event, text)

async def gbanlist_handler(event):
    """List all globally banned users"""
    if not await is_owner_check(event.sender_id):
        return
    
    gbanned_users = get_all_gbanned()
    if not gbanned_users:
        text = f"{get_emoji('info')} **GBan List:** Tidak ada user yang di-gban"
        await safe_send_with_premium_emojis(event, text)
        return
    
    text = f"""
{get_emoji('ban')} **GLOBAL BAN LIST**

{get_emoji('info')} **Total:** {len(gbanned_users)} users

"""
    
    for i, user_data in enumerate(gbanned_users[:10], 1):  # Limit to 10 users
        user_id, username, first_name, reason, banned_by, banned_date, total_groups = user_data
        username_str = f"@{username}" if username != 'None' else 'No username'
        date_str = datetime.fromisoformat(banned_date).strftime('%d/%m/%Y %H:%M')
        
        text += f"""
{get_emoji('main')} **#{i}** [{first_name}](tg://user?id={user_id})
{get_emoji('info')} **ID:** `{user_id}` | **Username:** {username_str}
{get_emoji('warning')} **Reason:** {reason[:50]}{'...' if len(reason) > 50 else ''}
{get_emoji('success')} **Groups:** {total_groups} | **Date:** {date_str}
"""
    
    if len(gbanned_users) > 10:
        text += f"\n{get_emoji('info')} ...and {len(gbanned_users) - 10} more users"
    
    await safe_send_with_premium_emojis(event, text.strip())

async def gbancheck_handler(event):
    """Check if user is globally banned"""
    if not await is_owner_check(event.sender_id):
        return
    
    args = event.text.split(maxsplit=1)
    user_identifier = args[1] if len(args) > 1 else None
    
    user = await get_user_info(event, user_identifier)
    if not user:
        text = f"{get_emoji('error')} **GBan Check Error:** User tidak ditemukan!\n\n{get_emoji('info')} **Usage:** `.gbancheck <user_id/@username/reply>`"
        await safe_send_with_premium_emojis(event, text)
        return
    
    gban_info = get_gban_info(user.id)
    first_name = getattr(user, 'first_name', None) or 'Unknown'
    username = getattr(user, 'username', None) or 'None'
    
    if gban_info:
        date_str = datetime.fromisoformat(gban_info['banned_date']).strftime('%d/%m/%Y %H:%M')
        text = f"""
{get_emoji('ban')} **GBAN STATUS: BANNED**

{get_emoji('main')} **User:** [{first_name}](tg://user?id={user.id})
{get_emoji('info')} **ID:** `{user.id}`
{get_emoji('info')} **Username:** @{username} 
{get_emoji('warning')} **Reason:** {gban_info['reason']}
{get_emoji('success')} **Banned from:** {gban_info['total_groups']} groups
{get_emoji('info')} **Date:** {date_str}
{get_emoji('ban')} **Status:** User is globally banned
        """.strip()
    else:
        text = f"""
{get_emoji('unban')} **GBAN STATUS: CLEAN**

{get_emoji('main')} **User:** [{first_name}](tg://user?id={user.id})
{get_emoji('info')} **ID:** `{user.id}`
{get_emoji('info')} **Username:** @{username}
{get_emoji('success')} **Status:** User is not globally banned
        """.strip()
    
    await safe_send_with_premium_emojis(event, text)

async def test_gban_emoji_handler(event):
    """Test UTF-16 emoji detection for GBan plugin"""
    if not await is_owner_check(event.sender_id):
        return
    
    test_text = f"""
{get_emoji('main')} **GBAN PLUGIN EMOJI TEST**

{get_emoji('ban')} **GBan commands:**
• `.gban <user> [reason]` - Global ban user
• `.ungban <user>` - Global unban user  
• `.gbanlist` - List banned users
• `.gbancheck <user>` - Check ban status

{get_emoji('info')} **Status emojis:**
• {get_emoji('ban')} Ban action
• {get_emoji('unban')} Unban/success
• {get_emoji('warning')} Warning/reason
• {get_emoji('error')} Error occurred
• {get_emoji('success')} Success/progress
• {get_emoji('info')} Information

{get_emoji('main')} Auto UTF-16 premium emoji detection active!
{get_emoji('success')} Database: SQLite with full logging
    """.strip()
    
    await safe_send_with_premium_emojis(event, test_text)

def get_plugin_info():
    """Return plugin info for plugin loader"""
    return PLUGIN_INFO

def setup(client_instance):
    """Setup plugin handlers"""
    global client
    client = client_instance
    
    # Initialize database
    if not init_database():
        print("[GBan] Failed to initialize database!")
        return
    
    # Register event handlers
    client.add_event_handler(gban_handler, events.NewMessage(pattern=r"\.gban"))
    client.add_event_handler(ungban_handler, events.NewMessage(pattern=r"\.ungban"))
    client.add_event_handler(gbanlist_handler, events.NewMessage(pattern=r"\.gbanlist"))
    client.add_event_handler(gbancheck_handler, events.NewMessage(pattern=r"\.gbancheck"))
    client.add_event_handler(test_gban_emoji_handler, events.NewMessage(pattern=r"\.testgban"))
    
    print(f"[GBan] Plugin loaded with auto UTF-16 emoji detection v{PLUGIN_INFO['version']}")