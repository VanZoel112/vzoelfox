"""
CheckID Plugin for Vzoel Assistant
Fitur: Cek ID Telegram seseorang dengan mereply pesan atau menulis username.
Kompatibel: main.py, plugin_loader.py, assetjson.py (v3+), backup log ke SQLite jika gagal akses database utama.
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0
"""

import sqlite3
import os
from datetime import datetime
from telethon import events

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "checkid",
    "version": "1.0.0",
    "description": "Cek ID Telegram seseorang dengan reply atau username, backup log ke SQLite jika gagal akses database utama.",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".id", ".id @username", ".id (reply)"],
    "features": ["check user id", "log to sql if needed"]
}

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

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
                if env and 'safe_send_with_entities' in env:
                    await env['safe_send_with_entities'](event, f"❌ Tidak bisa menemukan user dengan username: @{uname}")
                else:
                    await event.reply(f"❌ Tidak bisa menemukan user dengan username: @{uname}")
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
    # Build result text with fallbacks for missing env functions
    if env and 'get_emoji' in env and 'convert_font' in env:
        result_text = (
            f"{env['get_emoji']('main')} {env['convert_font']('User Info', 'bold')}\n\n"
            f"{env['get_emoji']('check')} ID: `{user_id}`\n"
            f"{env['get_emoji']('check')} Username: @{username if username else '-'}\n"
            f"{env['get_emoji']('check')} Name: `{full_name}`\n"
        )
    else:
        result_text = (
            f"🤩 **User Info**\n\n"
            f"⚙️ ID: `{user_id}`\n"
            f"⚙️ Username: @{username if username else '-'}\n"
            f"⚙️ Name: `{full_name}`\n"
        )
    
    if env and 'safe_send_with_entities' in env:
        await env['safe_send_with_entities'](event, result_text)
    else:
        await event.reply(result_text)
    save_id_log(user, chat, requester, method)

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