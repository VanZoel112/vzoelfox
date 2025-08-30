"""
CheckID Plugin for Vzoel Assistant - Enhanced UTF-16 Premium Edition
Fitur: Cek ID Telegram seseorang dengan mereply pesan atau menulis username.
Kompatibel: main.py, plugin_loader.py, assetjson.py (v3+), backup log ke SQLite jika gagal akses database utama.
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.1.0 (Enhanced Premium Emoji Support)
"""

import sqlite3
import os
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "checkid",
    "version": "1.1.0",
    "description": "Cek ID Telegram seseorang dengan reply atau username, backup log ke SQLite jika gagal akses database utama.",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".id", ".id @username", ".id (reply)"],
    "features": ["check user id", "log to sql if needed", "premium emojis"]
}

# Premium Emoji Mapping - Updated with UTF-16 support
PREMIUM_EMOJIS = {
    "main":    {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check":   {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1":  {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2":  {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3":  {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4":  {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5":  {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6":  {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

def get_emoji(emoji_name):
    """Get emoji from premium mapping"""
    return PREMIUM_EMOJIS.get(emoji_name, {}).get("emoji", "❓")

def convert_font(text):
    """Convert text to bold font"""
    return f"**{text}**"

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
                emoji = emoji_data["emoji"]
                custom_emoji_id = int(emoji_data["custom_emoji_id"])
                
                if text[i:].startswith(emoji):
                    try:
                        # Calculate UTF-16 length properly
                        emoji_bytes = emoji.encode('utf-16le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=custom_emoji_id
                        ))
                        
                        i += len(emoji)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

async def safe_send_message(event, text):
    """Send message with premium emoji entities"""
    try:
        entities = create_premium_entities(text)
        await event.reply(text, formatting_entities=entities)
    except Exception as e:
        # Fallback to regular message if premium emojis fail
        await event.reply(text)

env = None
DB_FILE = "plugins/checkid.db"

def get_db_conn():
    # Coba ambil dari assetjson environment
    try:
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].warning(f"[CheckID] DB from assetjson failed: {e}")
    # Fallback ke SQLite lokal
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS id_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                chat_id INTEGER,
                chat_title TEXT,
                requester_id INTEGER,
                requester_username TEXT,
                method TEXT,
                created_at TEXT
            )
        """)
        return conn
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[CheckID] Local SQLite error: {e}")
    return None

def save_id_log(user, chat, requester, method):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        user_id = getattr(user, 'id', 0)
        username = getattr(user, 'username', None)
        full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        chat_id = getattr(chat, 'id', 0)
        chat_title = getattr(chat, 'title', 'Unknown')
        requester_id = getattr(requester, 'id', 0)
        requester_username = getattr(requester, 'username', None)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO id_logs (user_id, username, full_name, chat_id, chat_title, requester_id, requester_username, method, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, chat_id, chat_title, requester_id, requester_username, method, created_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[CheckID] Log backup error: {e}")
        return False

@events.register(events.NewMessage(pattern=r'^\.id(?:\s+@?(\w+))?$', outgoing=True))
async def id_handler(event):
    print(f"[CheckID] Handler triggered by: {event.text}")
    print(f"[CheckID] Sender ID: {event.sender_id}")
    print(f"[CheckID] Environment available: {env is not None}")
    
    # Check if env is properly initialized and has is_owner function
    if env is None or 'is_owner' not in env:
        print("[CheckID] Environment not available or missing is_owner function")
        return
    
    try:
        is_owner = await env['is_owner'](event.sender_id)
        print(f"[CheckID] Is owner check result: {is_owner}")
        if not is_owner:
            print("[CheckID] User is not owner, returning")
            return
    except Exception as e:
        print(f"[CheckID] Error checking owner: {e}")
        return
    # Get client safely
    if 'get_client' not in env:
        return
    client = env['get_client']()
    if client is None:
        return
        
    user = None
    method = None
    chat = await event.get_chat()
    requester = await client.get_entity(event.sender_id)

    # Cek reply
    if event.is_reply:
        reply = await event.get_reply_message()
        user = await client.get_entity(reply.sender_id)
        method = "reply"
    else:
        # Cek argumen username
        args = event.text.split()
        if len(args) > 1:
            uname = args[1].strip('@')
            try:
                user = await client.get_entity(uname)
                method = "username"
            except Exception as e:
                error_text = f"{get_emoji('adder5')} {convert_font(f'Tidak bisa menemukan user dengan username: @{uname}')}"
                await safe_send_message(event, error_text)
                return
        else:
            # Jika tidak reply dan tidak username, cek id pengirim
            user = requester
            method = "self"

    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', None)
    first_name = getattr(user, 'first_name', '')
    last_name = getattr(user, 'last_name', '')
    full_name = (first_name + " " + last_name).strip()
    # Build result text with premium emoji support
    result_text = f"""
{get_emoji('main')} {convert_font('User Info')}

{get_emoji('check')} **ID:** `{user_id}`
{get_emoji('adder2')} **Username:** @{username if username else 'Tidak ada'}
{get_emoji('adder3')} **Name:** `{full_name if full_name else 'Tidak ada'}`
{get_emoji('adder4')} **Bot:** {'Ya' if getattr(user, 'bot', False) else 'Tidak'}
{get_emoji('adder1')} **Premium:** {'Ya' if getattr(user, 'premium', False) else 'Tidak'}

{get_emoji('adder6')} {convert_font('By Vzoel Fox Ltpn')}
    """.strip()
    
    await safe_send_message(event, result_text)
    save_id_log(user, chat, requester, method)

def setup(client):
    """Setup function to register event handlers with client"""
    if client:
        client.add_event_handler(id_handler)
        print("⚙️ CheckID handler registered to client")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    global env
    try:
        env = create_plugin_environment(client)
        print(f"[CheckID] Environment created: {env is not None}")
        print(f"[CheckID] Available env functions: {list(env.keys()) if env else 'None'}")
        
        client.add_event_handler(id_handler, events.NewMessage(pattern=r"\.id(\s.*|$)"))
        print("[CheckID] Event handler registered successfully")
        
        if env and 'logger' in env:
            env['logger'].info("[CheckID] Plugin loaded and command registered.")
        else:
            print("[CheckID] Plugin loaded - no logger available")
    except Exception as e:
        print(f"[CheckID] Setup error: {e}")
        import traceback
        traceback.print_exc()