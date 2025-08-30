"""
Channel Logger Plugin STANDALONE - No AssetJSON dependency
File: plugins/channel_logger.py  
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Standalone
Fitur: Auto log ke channel damnitvzoel untuk monitoring bot activities
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.errors import ChatWriteForbiddenError, UserBannedInChannelError, FloodWaitError
from telethon.tl.types import MessageEntityCustomEmoji
import sqlite3
import os

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "channel_logger",
    "version": "2.0.0", 
    "description": "Standalone auto log ke channel damnitvzoel untuk monitoring bot activities",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".logtest", ".logstatus", ".setchannel"],
    "features": ["channel logging", "auto monitoring", "event tracking", "status reports", "error logging", "premium emojis"]
}

# ===== PREMIUM EMOJI CONFIGURATION (STANDALONE) =====
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
}

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        i += len(emoji_char)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

async def safe_send_premium(event, text):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception:
        await event.reply(text)

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

# ===== Channel Configuration =====
LOG_CHANNEL = "damnitvzoel"  # Channel username tanpa @
CHANNEL_ID = -1002975804142  # Channel ID for @damnitvzoel

# ===== Database Helper =====
DB_FILE = "plugins/channel_logger.db"

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                message TEXT,
                status TEXT,
                channel_sent INTEGER,
                error_message TEXT,
                created_at TEXT
            )
        """)
        return conn
    except Exception as e:
        print(f"[Channel Logger] Local SQLite error: {e}")
    return None

def save_log_entry(event_type, message, status="success", channel_sent=True, error_message=None):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO channel_logs (event_type, message, status, channel_sent, error_message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (event_type, message[:500], status, channel_sent, error_message, created_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Channel Logger] Log save error: {e}")
        return False

# Global client reference
client = None

async def send_to_log_channel(message, event_type="info"):
    """Send message to log channel with error handling"""
    global client
    if not CHANNEL_ID or client is None:
        return False
    
    try:
        # Format message with timestamp and emoji
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"{get_emoji('main')} **VZOEL LOG v2.0** | {timestamp}\n\n{message}"
        
        # Send to channel with premium entities
        entities = create_premium_entities(formatted_message)
        if entities:
            await client.send_message(CHANNEL_ID, formatted_message, formatting_entities=entities)
        else:
            await client.send_message(CHANNEL_ID, formatted_message)
            
        save_log_entry(event_type, message, "success", True)
        return True
        
    except FloodWaitError as fe:
        print(f"[Channel Logger] Flood wait {fe.seconds}s")
        save_log_entry(event_type, message, "flood_wait", False, f"Flood wait: {fe.seconds}s")
        return False
        
    except (ChatWriteForbiddenError, UserBannedInChannelError) as e:
        print(f"[Channel Logger] Channel access error: {e}")
        save_log_entry(event_type, message, "access_error", False, str(e))
        return False
        
    except Exception as e:
        print(f"[Channel Logger] Send error: {e}")
        save_log_entry(event_type, message, "error", False, str(e))
        return False

async def log_system_event(event_type, title, details):
    """Log system events to channel"""
    log_message = f"{get_emoji('check')} **{title}**\n\n{details}"
    await send_to_log_channel(log_message, event_type)

async def log_plugin_event(plugin_name, action, status="success", details=""):
    """Log plugin events to channel"""
    status_emoji = get_emoji('adder2') if status == "success" else get_emoji('adder5') if status == "error" else get_emoji('adder1')
    log_message = f"{status_emoji} **Plugin: {plugin_name}**\n• Action: {action}\n• Status: {status.upper()}"
    if details:
        log_message += f"\n• Details: {details}"
    
    await send_to_log_channel(log_message, "plugin")

async def log_command_usage(command, user_id, success=True, error=None):
    """Log command usage to channel"""
    status_emoji = get_emoji('adder2') if success else get_emoji('adder5')
    status_text = "SUCCESS" if success else "ERROR"
    
    log_message = f"{status_emoji} **Command Usage**\n• Command: {command}\n• User: {user_id}\n• Status: {status_text}"
    if error:
        log_message += f"\n• Error: {error}"
    
    await send_to_log_channel(log_message, "command")

async def logtest_handler(event):
    """Test channel logging functionality"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    test_message = f"""
{get_emoji('main')} **Channel Logger Test v2.0**

{get_emoji('check')} **Test Details:**
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Channel: @{LOG_CHANNEL}
• Status: Testing connection
• User: {event.sender_id}

{get_emoji('adder1')} **System Info:**
• Bot: VZOEL ASSISTANT
• Version: v0.1.0.76 Enhanced
• Plugin: Channel Logger v2.0.0
• Dependencies: None (Standalone)

{get_emoji('adder2')} **Premium Features:**
{get_emoji('check')} Custom emoji entities
{get_emoji('adder3')} UTF-16 encoding support
{get_emoji('adder4')} Error handling & fallbacks
{get_emoji('adder5')} Database logging
{get_emoji('adder6')} Real-time monitoring

{get_emoji('main')} **This is a standalone test log message!**
    """.strip()
    
    success = await send_to_log_channel(test_message, "test")
    
    if success:
        response = f"""
{get_emoji('adder2')} **Test berhasil! v2.0**

{get_emoji('check')} Message sent to @{LOG_CHANNEL}
{get_emoji('adder1')} Premium emojis: Working
{get_emoji('adder3')} Entity formatting: Active
{get_emoji('adder4')} Database logging: Saved
{get_emoji('adder5')} Channel access: Verified

{get_emoji('main')} Check channel for log entry!
        """.strip()
    else:
        response = f"""
{get_emoji('adder5')} **Test gagal! v2.0**

{get_emoji('check')} Failed to send to @{LOG_CHANNEL}
{get_emoji('adder1')} Check bot permissions in channel
{get_emoji('adder3')} Verify channel ID: {CHANNEL_ID}
{get_emoji('adder4')} Database logging: Still working

{get_emoji('main')} Check logs for error details
        """.strip()
    
    await safe_send_premium(event, response)

async def logstatus_handler(event):
    """Show channel logger status"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    # Get recent logs from database
    try:
        conn = get_db_conn()
        if conn:
            cursor = conn.execute("SELECT * FROM channel_logs ORDER BY id DESC LIMIT 5")
            recent_logs = cursor.fetchall()
            conn.close()
        else:
            recent_logs = []
    except Exception:
        recent_logs = []
    
    status_text = f"""
{get_emoji('main')} **Channel Logger Status v2.0**

{get_emoji('check')} **Configuration:**
• Channel: @{LOG_CHANNEL}
• Channel ID: {CHANNEL_ID}
• Database: {"Connected" if get_db_conn() else "Error"}
• System: Standalone (no deps)

{get_emoji('adder1')} **Statistics:**
• Total logs: {len(recent_logs) if recent_logs else 0}
• Recent entries: {len(recent_logs)}
• Last activity: {recent_logs[0]['created_at'] if recent_logs else "None"}
• Status: Active & Monitoring

{get_emoji('adder2')} **Premium Features:**
{get_emoji('check')} Custom emoji entities
{get_emoji('adder3')} UTF-16 encoding
{get_emoji('adder4')} Error handling
{get_emoji('adder5')} Database backup
{get_emoji('adder6')} Real-time logging

{get_emoji('adder3')} **Recent Logs:**
    """.strip()
    
    if recent_logs:
        for log in recent_logs[:3]:
            status_text += f"\n• {log['event_type']}: {log['status']} ({log['created_at']})"
    else:
        status_text += "\n• No recent logs found"
    
    status_text += f"""

{get_emoji('main')} **Commands:**
• `.logtest` - Test channel logging
• `.logstatus` - Show this status  
• `.setchannel <username>` - Change log channel

{get_emoji('adder2')} **Standalone system working perfectly!**
    """.strip()
    
    await safe_send_premium(event, status_text)

async def setchannel_handler(event):
    """Change log channel"""
    global client, LOG_CHANNEL, CHANNEL_ID
    
    if not await is_owner_check(client, event.sender_id):
        return
    
    args = event.raw_text.split(maxsplit=1)
    if len(args) < 2:
        help_text = f"""
{get_emoji('main')} **Set Log Channel v2.0**

{get_emoji('check')} **Usage:**
`.setchannel <channel_username>`

{get_emoji('adder1')} **Examples:**
• `.setchannel damnitvzoel`
• `.setchannel mychannel`

{get_emoji('adder2')} **Current:** @{LOG_CHANNEL}
{get_emoji('adder3')} **ID:** {CHANNEL_ID}

{get_emoji('adder4')} **Note:** Bot needs access to the channel
{get_emoji('main')} **System:** Standalone v2.0.0
        """.strip()
        await safe_send_premium(event, help_text)
        return
    
    new_channel = args[1].replace('@', '')
    
    try:
        # Try to resolve the channel
        entity = await client.get_entity(new_channel)
        
        LOG_CHANNEL = new_channel
        CHANNEL_ID = entity.id
        
        # Test send to new channel
        test_msg = f"{get_emoji('main')} **Channel Logger v2.0**\n\nChannel changed to @{LOG_CHANNEL}\nTime: {datetime.now().strftime('%H:%M:%S')}\n\n{get_emoji('check')} Standalone system active!"
        
        entities = create_premium_entities(test_msg)
        if entities:
            await client.send_message(CHANNEL_ID, test_msg, formatting_entities=entities)
        else:
            await client.send_message(CHANNEL_ID, test_msg)
        
        response = f"""
{get_emoji('adder2')} **Channel berhasil diubah! v2.0**

{get_emoji('check')} New channel: @{LOG_CHANNEL}
{get_emoji('adder1')} Channel ID: {CHANNEL_ID}
{get_emoji('adder3')} Test message sent
{get_emoji('adder4')} Premium emojis working
{get_emoji('main')} System: Standalone v2.0.0
        """.strip()
        await safe_send_premium(event, response)
        
        # Log the change
        await log_system_event("config", "Log Channel Changed", f"New channel: @{LOG_CHANNEL}")
        
    except Exception as e:
        response = f"""
{get_emoji('adder5')} **Error! v2.0**

{get_emoji('check')} Failed to set channel: {e}
{get_emoji('adder1')} Make sure bot has access to @{new_channel}
{get_emoji('adder3')} Check channel username spelling
{get_emoji('main')} Current: @{LOG_CHANNEL} (unchanged)
        """.strip()
        await safe_send_premium(event, response)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Register event handlers
    client.add_event_handler(logtest_handler, events.NewMessage(pattern=r"\.logtest"))
    client.add_event_handler(logstatus_handler, events.NewMessage(pattern=r"\.logstatus"))
    client.add_event_handler(setchannel_handler, events.NewMessage(pattern=r"\.setchannel"))
    
    print(f"✅ [Channel Logger] Plugin loaded - Standalone auto logging to @{LOG_CHANNEL} v{PLUGIN_INFO['version']}")
    
    # Send startup notification to channel
    async def startup_notify():
        try:
            # Wait a bit to ensure client is fully initialized
            await asyncio.sleep(2)
            if client is None:
                print(f"[Channel Logger] Client not initialized, skipping startup notification")
                return
            startup_msg = f"{get_emoji('main')} **VZOEL ASSISTANT Started v2.0**\n• Plugin: Channel Logger\n• Version: v{PLUGIN_INFO['version']}\n• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n• System: Standalone (no deps)\n\n{get_emoji('check')} Auto-logging active!"
            await send_to_log_channel(startup_msg, "startup")
        except Exception as e:
            print(f"[Channel Logger] Startup notification failed: {e}")
    
    # Schedule startup notification
    client.loop.create_task(startup_notify())