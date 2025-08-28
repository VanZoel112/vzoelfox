"""
Message Logger Plugin (SQL3 Murni)
Fitur: Mencatat semua pesan masuk ke database SQLite, bisa query log lewat command.
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import sqlite3
import os
from telethon import events

PLUGIN_INFO = {
    "name": "log",
    "version": "1.0.0",
    "description": "Logger pesan masuk, query log dari SQL3 murni.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".log show", ".log query <keyword>", ".log clear"],
    "features": ["message logging", "sql3 direct", "simple query"]
}

DB_FILE = "plugins/log.db"

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS log_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                username TEXT,
                text TEXT,
                created_at TEXT
            );
        """)
        return conn
    except Exception:
        return None

def log_message(user_id, chat_id, username, text):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        from datetime import datetime
        conn.execute(
            "INSERT INTO log_message (user_id, chat_id, username, text, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                user_id,
                chat_id,
                username,
                text,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def query_logs(chat_id, keyword=None, limit=10):
    try:
        conn = get_db_conn()
        if not conn:
            return []
        if keyword:
            cur = conn.execute(
                "SELECT * FROM log_message WHERE chat_id=? AND text LIKE ? ORDER BY created_at DESC LIMIT ?",
                (chat_id, f"%{keyword}%", limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM log_message WHERE chat_id=? ORDER BY created_at DESC LIMIT ?",
                (chat_id, limit),
            )
        logs = cur.fetchall()
        conn.close()
        return logs
    except Exception:
        return []

def clear_logs(chat_id):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        conn.execute("DELETE FROM log_message WHERE chat_id=?", (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

async def log_handler(event):
    # Log setiap pesan masuk (bisa dimodif untuk filter tertentu)
    user_id = event.sender_id
    chat_id = event.chat_id if hasattr(event, "chat_id") else None
    username = None
    try:
        sender = await event.get_sender()
        username = sender.username if sender and hasattr(sender, "username") else ""
    except Exception:
        username = ""
    text = event.message.message if event.message else ""
    # Jangan log command .log biar ga spam
    if not text.startswith(".log"):
        log_message(user_id, chat_id, username, text)

async def log_cmd_handler(event):
    chat = await event.get_chat()
    chat_id = chat.id
    args = event.text.split(maxsplit=2)
    if len(args) == 2 and args[1] == "show":
        logs = query_logs(chat_id)
        if logs:
            txt = "📝 Log terbaru:\n"
            for row in logs:
                name = row["username"] or row["user_id"]
                t = row["created_at"]
                msg = row["text"]
                txt += f"- [{t}] {name}: {msg}\n"
            await event.reply(txt)
        else:
            await event.reply("Belum ada log pesan di chat ini.")
    elif len(args) >= 3 and args[1] == "query":
        keyword = args[2]
        logs = query_logs(chat_id, keyword=keyword)
        if logs:
            txt = f"🔍 Log dengan kata kunci '{keyword}':\n"
            for row in logs:
                name = row["username"] or row["user_id"]
                t = row["created_at"]
                msg = row["text"]
                txt += f"- [{t}] {name}: {msg}\n"
            await event.reply(txt)
        else:
            await event.reply(f"Tidak ditemukan log dengan kata kunci '{keyword}'.")
    elif len(args) == 2 and args[1] == "clear":
        clear_logs(chat_id)
        await event.reply("Log pesan di chat ini sudah dihapus.")
    else:
        await event.reply(
            "Perintah:\n.log show\n.log query <kata>\n.log clear"
        )

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    client.add_event_handler(log_handler, events.NewMessage(incoming=True, func=lambda e: not e.text.startswith(".log")))
    client.add_event_handler(log_cmd_handler, events.NewMessage(pattern=r"\.log"))