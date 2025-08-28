"""
Sudo Manager Plugin (SQL3 murni, dengan durasi & akses fitur)
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import sqlite3
import os
import re
from telethon import events

PLUGIN_INFO = {
    "name": "sudo",
    "version": "1.0.0",
    "description": "Manajemen sudo user untuk akses fitur tertentu dengan durasi di SQLite.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".sudo <username/reply> <durasi> <fitur>", ".sudo list", ".sudo revoke <user_id>"],
    "features": ["sudo by reply/username", "akses fitur", "durasi otomatis", "sql3 direct"]
}

DB_FILE = "plugins/sudo.db"

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sudo_access (
                user_id INTEGER,
                username TEXT,
                feature TEXT,
                expire_at INTEGER,
                granted_at INTEGER,
                PRIMARY KEY (user_id, feature)
            );
        """)
        return conn
    except Exception:
        return None

def parse_duration(text):
    # Mendukung format: 10 (menit), 1h (jam), 2d (hari)
    m = re.match(r"(\d+)([mhd]?)", text)
    if not m: return 0
    val = int(m.group(1))
    unit = m.group(2)
    if unit == "h":
        return val * 3600
    elif unit == "d":
        return val * 86400
    else:
        return val * 60  # default menit

def add_sudo(user_id, username, feature, duration_sec):
    try:
        from time import time
        expire = int(time()) + duration_sec
        granted = int(time())
        conn = get_db_conn()
        if not conn: return False
        conn.execute("INSERT OR REPLACE INTO sudo_access (user_id, username, feature, expire_at, granted_at) VALUES (?, ?, ?, ?, ?)",
                     (user_id, username, feature, expire, granted))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def check_sudo(user_id, feature):
    try:
        from time import time
        now = int(time())
        conn = get_db_conn()
        if not conn: return False
        cur = conn.execute("SELECT expire_at FROM sudo_access WHERE user_id=? AND feature=?", (user_id, feature))
        row = cur.fetchone()
        conn.close()
        return row and row["expire_at"] > now
    except Exception:
        return False

def sudo_list():
    try:
        from time import time
        now = int(time())
        conn = get_db_conn()
        if not conn: return []
        cur = conn.execute("SELECT * FROM sudo_access WHERE expire_at > ?", (now,))
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def sudo_revoke(user_id, feature=None):
    try:
        conn = get_db_conn()
        if not conn: return False
        if feature:
            conn.execute("DELETE FROM sudo_access WHERE user_id=? AND feature=?", (user_id, feature))
        else:
            conn.execute("DELETE FROM sudo_access WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

async def sudo_cmd_handler(event):
    args = event.text.split()
    if len(args) == 1:
        await event.reply("Format: reply/mention .sudo <durasi> <fitur>\n.sudo list\n.sudo revoke <user_id>")
        return
    if args[1] == "list":
        rows = sudo_list()
        if rows:
            from time import time
            now = int(time())
            txt = "👑 Sudo aktif:\n"
            for row in rows:
                sisa = int((row["expire_at"] - now) / 60)
                txt += f"- {row['username'] or row['user_id']} | {row['feature']} | {sisa} menit lagi\n"
            await event.reply(txt)
        else:
            await event.reply("Tidak ada sudo aktif.")
        return
    if args[1] == "revoke" and len(args) >= 3:
        target_id = int(args[2])
        feature = args[3] if len(args) >= 4 else None
        sudo_revoke(target_id, feature)
        await event.reply(f"Sudo untuk {target_id}{' fitur '+feature if feature else ''} direvoke.")
        return

    # Grant sudo (reply/mention/ID)
    # Format: .sudo <durasi> <fitur>
    # Target dari reply atau mention di arg1
    duration_sec = parse_duration(args[1])
    feature = args[2] if len(args) >= 3 else "all"
    # Cek reply
    if event.is_reply:
        reply = await event.get_reply_message()
        user_id = reply.sender_id
        sender = await reply.get_sender()
        username = sender.username if sender and hasattr(sender, "username") else ""
    elif args[1].startswith("@"):
        username = args[1][1:]
        user_id = None
        # Try to get user_id via get_entity
        try:
            entity = await event.client.get_entity(username)
            user_id = entity.id
        except Exception:
            await event.reply("User tidak ditemukan.")
            return
    else:
        try:
            user_id = int(args[1])
            username = ""
        except Exception:
            await event.reply("Format: reply/mention .sudo <durasi> <fitur>")
            return

    if not user_id:
        await event.reply("User ID tidak ditemukan.")
        return
    add_sudo(user_id, username, feature, duration_sec)
    await event.reply(f"User [{username or user_id}] diberikan sudo untuk fitur **{feature}** selama {int(duration_sec/60)} menit.")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    client.add_event_handler(sudo_cmd_handler, events.NewMessage(pattern=r"\.sudo"))