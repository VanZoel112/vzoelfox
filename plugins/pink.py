"""
Pink Plugin for Vzoel Assistant
Fitur: Respon PING minimalis dengan 2 baris, emoji premium dari json, font dari json asset, query ke sql3 murni.
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.1.0
"""

import sqlite3
import os
from telethon import events

PLUGIN_INFO = {
    "name": "pink",
    "version": "1.1.0",
    "description": "PING minimalis dengan emoji premium dan font dari json asset, query sql3 murni. Adder bug fix (pakai adder5).",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".pink"],
    "features": ["minimal ping", "premium emoji json", "font json", "sql3 direct"]
}

# Path emoji json asset
EMOJI_JSON = "data/emoji.json"
FONT_JSON = "data/font.json"
DB_FILE = "plugins/pink.db"

def load_json(path, default=None):
    try:
        import json
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default or {}

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        # Simple log for ping usage
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pink_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                created_at TEXT
            );
        """)
        return conn
    except Exception:
        return None

def log_ping(user_id, chat_id):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        from datetime import datetime
        conn.execute(
            "INSERT INTO pink_log (user_id, chat_id, created_at) VALUES (?, ?, ?)",
            (user_id, chat_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_emoji(name):
    emoji_map = load_json(EMOJI_JSON, {
        "main": "🤩",
        "adder5": "😈",
        "check": "✅"
    })
    # Fix: pakai adder5 (bukan adder/adder1)
    return emoji_map.get(name, "🤩")

def convert_font(text, font_type="bold"):
    font_map = load_json(FONT_JSON, {})
    if font_type in font_map:
        fm = font_map[font_type]
        return "".join([fm.get(c, c) for c in text])
    return text

async def pink_handler(event):
    user_id = event.sender_id
    chat_id = event.chat_id if hasattr(event, "chat_id") else None
    log_ping(user_id, chat_id)

    line1 = f"{get_emoji('main')} {convert_font('PONG !!!', 'bold')}"
    line2 = f"{get_emoji('adder5')} {convert_font('Vzoel Assistant anti delay', 'mono')} {get_emoji('check')}"
    response = f"{line1}\n{line2}"

    try:
        await event.reply(response)
    except Exception:
        await event.reply("PONG !!!\nVzoel Assistant anti delay")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    client.add_event_handler(pink_handler, events.NewMessage(pattern=r"\.pink"))