"""
Grup Otomatisasi & Blacklist Manager (SQL3 murni)
- Otomatis simpan daftar grup dari log.py
- Blacklist grup agar tidak kena gcast
- Cek di mana kamu diban/keluar
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import sqlite3
import os
from telethon import events

PLUGIN_INFO = {
    "name": "grup",
    "version": "1.0.0",
    "description": "Manajemen grup, blacklist, banlist, sinkron log.py dan SQL3 murni.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".grup log",
        ".grup blacklist <id>",
        ".grup unblacklist <id>",
        ".grup blacklistlist",
        ".grup banlist"
    ],
    "features": [
        "auto grup log",
        "blacklist id grup",
        "banlist monitoring",
        "sql3 direct"
    ]
}

DB_FILE = "plugins/grup.db"

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grup_blacklist (
                chat_id INTEGER PRIMARY KEY,
                added_at TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grup_banlist (
                chat_id INTEGER PRIMARY KEY,
                banned_at TEXT
            );
        """)
        return conn
    except Exception:
        return None

def add_blacklist(chat_id):
    try:
        conn = get_db_conn()
        if not conn: return False
        from datetime import datetime
        conn.execute("INSERT OR REPLACE INTO grup_blacklist (chat_id, added_at) VALUES (?, ?)",
                     (chat_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def remove_blacklist(chat_id):
    try:
        conn = get_db_conn()
        if not conn: return False
        conn.execute("DELETE FROM grup_blacklist WHERE chat_id=?", (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_blacklist():
    try:
        conn = get_db_conn()
        if not conn: return []
        cur = conn.execute("SELECT chat_id, added_at FROM grup_blacklist ORDER BY added_at DESC")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def add_banlist(chat_id):
    try:
        conn = get_db_conn()
        if not conn: return False
        from datetime import datetime
        conn.execute("INSERT OR REPLACE INTO grup_banlist (chat_id, banned_at) VALUES (?, ?)",
                     (chat_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_banlist():
    try:
        conn = get_db_conn()
        if not conn: return []
        cur = conn.execute("SELECT chat_id, banned_at FROM grup_banlist ORDER BY banned_at DESC")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

# Otomatis grup log dari log.py
def get_grup_from_log():
    try:
        LOGDB = "plugins/log.db"
        if not os.path.exists(LOGDB):
            return []
        conn = sqlite3.connect(LOGDB)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT DISTINCT chat_id FROM log_message WHERE chat_id IS NOT NULL")
        ids = [row["chat_id"] for row in cur.fetchall() if row["chat_id"]]
        conn.close()
        return ids
    except Exception:
        return []

async def grup_cmd_handler(event):
    args = event.text.split()
    chat = await event.get_chat()
    chat_id = chat.id
    if len(args) == 2 and args[1] == "log":
        # Tampilkan semua grup dari log
        grup_ids = get_grup_from_log()
        if grup_ids:
            txt = "📋 Grup dari log.py:\n"
            txt += "\n".join([f"- {gid}" for gid in grup_ids])
        else:
            txt = "Belum ada grup di log.py."
        await event.reply(txt)
    elif len(args) == 3 and args[1] == "blacklist":
        try:
            target_id = int(args[2])
            add_blacklist(target_id)
            await event.reply(f"Grup {target_id} ditambahkan ke blacklist.")
        except Exception:
            await event.reply("Format: .grup blacklist <id>")
    elif len(args) == 3 and args[1] == "unblacklist":
        try:
            target_id = int(args[2])
            remove_blacklist(target_id)
            await event.reply(f"Grup {target_id} dihapus dari blacklist.")
        except Exception:
            await event.reply("Format: .grup unblacklist <id>")
    elif len(args) == 2 and args[1] == "blacklistlist":
        rows = get_blacklist()
        if rows:
            txt = "🚫 Grup blacklist:\n"
            txt += "\n".join([f"- {r['chat_id']} (sejak {r['added_at']})" for r in rows])
        else:
            txt = "Belum ada grup blacklist."
        await event.reply(txt)
    elif len(args) == 2 and args[1] == "banlist":
        rows = get_banlist()
        if rows:
            txt = "⛔ Grup banlist:\n"
            txt += "\n".join([f"- {r['chat_id']} (sejak {r['banned_at']})" for r in rows])
        else:
            txt = "Belum ada grup banlist."
        await event.reply(txt)
    else:
        await event.reply(
            "Perintah:\n.grup log\n.grup blacklist <id>\n.grup unblacklist <id>\n.grup blacklistlist\n.grup banlist"
        )

async def ban_monitor_handler(event):
    # Monitor jika kamu diban di grup (misal keluar/removed/banned)
    # Telethon event ChatAction
    if getattr(event, "user_left", None) or getattr(event, "user_kicked", None):
        chat = await event.get_chat()
        chat_id = chat.id
        add_banlist(chat_id)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    client.add_event_handler(grup_cmd_handler, events.NewMessage(pattern=r"\.grup"))
    client.add_event_handler(ban_monitor_handler, events.ChatAction(func=lambda e: getattr(e, "user_left", None) or getattr(e, "user_kicked", None)))