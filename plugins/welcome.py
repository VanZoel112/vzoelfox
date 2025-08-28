"""
Custom Welcome Plugin (SQL3 + Emoji Premium JSON)
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import sqlite3
import os
from telethon import events

PLUGIN_INFO = {
    "name": "welcome",
    "version": "1.0.0",
    "description": "Custom welcome dengan emoji premium JSON dan SQL3 murni.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".welcome set", ".welcome show", ".welcome on", ".welcome off"],
    "features": ["custom welcome", "premium emoji json", "sql3 direct"]
}

EMOJI_JSON = "data/emoji.json"
DB_FILE = "plugins/welcome.db"

def load_json(path, default=None):
    try:
        import json
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default or {}

def get_emoji(name):
    emoji_map = load_json(EMOJI_JSON, {
        "main": "🤩",
        "check": "✅"
    })
    return emoji_map.get(name, "🤩")

def render_emoji_in_text(text):
    # Replace {emoji:name} with corresponding emoji
    import re
    def repl(m):
        return get_emoji(m.group(1))
    return re.sub(r"{emoji:([a-zA-Z0-9_]+)}", repl, text)

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS welcome (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 1,
                message TEXT DEFAULT '',
                updated_at TEXT
            );
        """)
        return conn
    except Exception:
        return None

def set_welcome(chat_id, message=None, enabled=None):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # check exist
        cur = conn.execute("SELECT * FROM welcome WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        if row:
            msg = message if message is not None else row['message']
            en = enabled if enabled is not None else row['enabled']
            conn.execute("UPDATE welcome SET message=?, enabled=?, updated_at=? WHERE chat_id=?",
                         (msg, en, now, chat_id))
        else:
            msg = message if message is not None else ''
            en = enabled if enabled is not None else 1
            conn.execute("INSERT INTO welcome (chat_id, enabled, message, updated_at) VALUES (?, ?, ?, ?)",
                         (chat_id, en, msg, now))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_welcome(chat_id):
    try:
        conn = get_db_conn()
        if not conn:
            return None
        cur = conn.execute("SELECT * FROM welcome WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None

async def welcome_cmd_handler(event):
    chat = await event.get_chat()
    chat_id = chat.id
    args = event.text.split(maxsplit=2)
    if len(args) == 1:
        await event.reply("Format: .welcome set <pesan>, .welcome show, .welcome on, .welcome off")
        return
    cmd = args[1].lower()
    if cmd == "set":
        if len(args) < 3:
            await event.reply("Format: .welcome set <pesan>")
            return
        msg = args[2]
        set_welcome(chat_id, message=msg)
        await event.reply(f"{get_emoji('main')} Pesan welcome di-set!\n\n{render_emoji_in_text(msg)}")
    elif cmd == "show":
        row = get_welcome(chat_id)
        if row and row['message']:
            status = "Aktif" if row['enabled'] else "Nonaktif"
            await event.reply(f"{get_emoji('main')} Status Welcome: {status}\n\n{render_emoji_in_text(row['message'])}")
        else:
            await event.reply("Welcome belum di-set.")
    elif cmd == "on":
        set_welcome(chat_id, enabled=1)
        await event.reply(f"{get_emoji('check')} Welcome aktif di grup ini.")
    elif cmd == "off":
        set_welcome(chat_id, enabled=0)
        await event.reply(f"{get_emoji('check')} Welcome nonaktif di grup ini.")
    else:
        await event.reply("Format: .welcome set <pesan>, .welcome show, .welcome on, .welcome off")

async def member_join_handler(event):
    # Only trigger if new user joined
    if hasattr(event, "user_joined"):
        chat = await event.get_chat()
        chat_id = chat.id
        row = get_welcome(chat_id)
        if row and row['enabled'] and row['message']:
            name = event.user_joined.first_name
            msg = row['message'].replace("{name}", name)
            await event.reply(render_emoji_in_text(msg))

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    client.add_event_handler(welcome_cmd_handler, events.NewMessage(pattern=r"\.welcome"))
    client.add_event_handler(member_join_handler, events.ChatAction(func=lambda e: getattr(e, "user_joined", None) is not None))