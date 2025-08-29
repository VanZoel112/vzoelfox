"""
Channel Logger Plugin for Vzoel Assistant
Fitur: Auto log ke channel damnitvzoel untuk monitoring bot activities
Kompatibel: main.py, plugin_loader.py, assetjson.py (v3+)
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.errors import ChatWriteForbiddenError, UserBannedInChannelError, FloodWaitError
import sqlite3
import os

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "channel_logger",
    "version": "1.0.0", 
    "description": "Auto log ke channel damnitvzoel untuk monitoring bot activities",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".logtest", ".logstatus", ".setchannel"],
    "features": ["channel logging", "auto monitoring", "event tracking", "status reports", "error logging"]
}

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None

# ===== Channel Configuration =====
LOG_CHANNEL = "damnitvzoel"  # Channel username tanpa @
CHANNEL_ID = -1002975804142  # Channel ID for @damnitvzoel

# ===== Premium Emojis =====
PREMIUM_EMOJIS = {
    'main': {'char': '🤩'}, 'check': {'char': '⚙️'}, 'adder1': {'char': '⛈'},
    'adder2': {'char': '✅'}, 'adder3': {'char': '👽'}, 'adder4': {'char': '✈️'},
    'adder5': {'char': '😈'}, 'adder6': {'char': '🎚️'}
}

def get_emoji(emoji_type):
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

# ===== Database Helper =====
DB_FILE = "plugins/channel_logger.db"

def get_db_conn():
    try:
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].warning(f"[Channel Logger] DB from assetjson failed: {e}")
    
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
        if env and 'logger' in env:
            env['logger'].error(f"[Channel Logger] Local SQLite error: {e}")
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
        if env and 'logger' in env:
            env['logger'].error(f"[Channel Logger] Log save error: {e}")
        return False

async def send_to_log_channel(message, event_type="info"):
    """Send message to log channel with error handling"""
    global CHANNEL_ID
    if not CHANNEL_ID:
        return False
    
    try:
        client = env['get_client']()
        
        # Format message with timestamp and emoji
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"{get_emoji('main')} **VZOEL LOG** | {timestamp}\n\n{message}"
        
        # Send to channel
        await client.send_message(CHANNEL_ID, formatted_message)
        save_log_entry(event_type, message, "success", True)
        return True
        
    except FloodWaitError as fe:
        if env and 'logger' in env:
            env['logger'].warning(f"[Channel Logger] Flood wait {fe.seconds}s")
        save_log_entry(event_type, message, "flood_wait", False, f"Flood wait: {fe.seconds}s")
        return False
        
    except (ChatWriteForbiddenError, UserBannedInChannelError) as e:
        if env and 'logger' in env:
            env['logger'].error(f"[Channel Logger] Channel access error: {e}")
        save_log_entry(event_type, message, "access_error", False, str(e))
        return False
        
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[Channel Logger] Send error: {e}")
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
    if not await env['is_owner'](event.sender_id):
        return
    
    test_message = f"""
{get_emoji('main')} **Channel Logger Test**

{get_emoji('check')} **Test Details:**
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Channel: @{LOG_CHANNEL}
• Status: Testing connection
• User: {event.sender_id}

{get_emoji('adder1')} **System Info:**
• Bot: VZOEL ASSISTANT
• Version: v0.1.0.76
• Plugin: Channel Logger v1.0.0

{get_emoji('adder2')} This is a test log message!
    """.strip()
    
    success = await send_to_log_channel(test_message, "test")
    
    if success:
        response = f"{get_emoji('adder2')} **Test berhasil!**\n\n• Message sent to @{LOG_CHANNEL}\n• Check channel for log entry"
    else:
        response = f"{get_emoji('adder5')} **Test gagal!**\n\n• Failed to send to @{LOG_CHANNEL}\n• Check bot permissions in channel"
    
    await env['safe_send_with_entities'](event, response)

async def logstatus_handler(event):
    """Show channel logger status"""
    if not await env['is_owner'](event.sender_id):
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
{get_emoji('main')} **Channel Logger Status**

{get_emoji('check')} **Configuration:**
• Channel: @{LOG_CHANNEL}
• Channel ID: {CHANNEL_ID or "Not resolved"}
• Database: {"Connected" if get_db_conn() else "Error"}

{get_emoji('adder1')} **Statistics:**
• Total logs: {len(recent_logs) if recent_logs else 0}
• Recent entries: {len(recent_logs)}
• Last activity: {recent_logs[0]['created_at'] if recent_logs else "None"}

{get_emoji('adder2')} **Recent Logs:**
    """.strip()
    
    if recent_logs:
        for log in recent_logs[:3]:
            status_text += f"\n• {log['event_type']}: {log['status']} ({log['created_at']})"
    else:
        status_text += "\n• No recent logs found"
    
    status_text += f"\n\n{get_emoji('adder3')} **Commands:**\n• `.logtest` - Test channel logging\n• `.logstatus` - Show this status\n• `.setchannel <username>` - Change log channel"
    
    await env['safe_send_with_entities'](event, status_text)

async def setchannel_handler(event):
    """Change log channel"""
    global LOG_CHANNEL, CHANNEL_ID
    
    if not await env['is_owner'](event.sender_id):
        return
    
    args = event.raw_text.split(maxsplit=1)
    if len(args) < 2:
        help_text = f"""
{get_emoji('main')} **Set Log Channel**

{get_emoji('check')} **Usage:**
`.setchannel <channel_username>`

{get_emoji('adder1')} **Examples:**
• `.setchannel damnitvzoel`
• `.setchannel mychannel`

{get_emoji('adder2')} **Current:** @{LOG_CHANNEL}
        """.strip()
        await env['safe_send_with_entities'](event, help_text)
        return
    
    new_channel = args[1].replace('@', '')
    
    try:
        client = env['get_client']()
        # Try to resolve the channel
        entity = await client.get_entity(new_channel)
        
        LOG_CHANNEL = new_channel
        CHANNEL_ID = entity.id
        
        # Test send to new channel
        test_msg = f"{get_emoji('main')} **Channel Logger**\n\nChannel changed to @{LOG_CHANNEL}\nTime: {datetime.now().strftime('%H:%M:%S')}"
        await client.send_message(CHANNEL_ID, test_msg)
        
        response = f"{get_emoji('adder2')} **Channel berhasil diubah!**\n\n• New channel: @{LOG_CHANNEL}\n• Channel ID: {CHANNEL_ID}\n• Test message sent"
        await env['safe_send_with_entities'](event, response)
        
        # Log the change
        await log_system_event("config", "Log Channel Changed", f"New channel: @{LOG_CHANNEL}")
        
    except Exception as e:
        response = f"{get_emoji('adder5')} **Error!**\n\n• Failed to set channel: {e}\n• Make sure bot has access to @{new_channel}"
        await env['safe_send_with_entities'](event, response)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    global env
    env = create_plugin_environment(client)
    
    # Register event handlers
    client.add_event_handler(logtest_handler, events.NewMessage(pattern=r"\.logtest"))
    client.add_event_handler(logstatus_handler, events.NewMessage(pattern=r"\.logstatus"))
    client.add_event_handler(setchannel_handler, events.NewMessage(pattern=r"\.setchannel"))
    
    # Make logging functions available globally
    env['send_to_log_channel'] = send_to_log_channel
    env['log_system_event'] = log_system_event
    env['log_plugin_event'] = log_plugin_event
    env['log_command_usage'] = log_command_usage
    
    if env and 'logger' in env:
        env['logger'].info("[Channel Logger] Plugin loaded - Auto logging to @damnitvzoel ready")