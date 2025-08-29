"""
VC Monitor Plugin for Vzoel Assistant
Fitur: Join/Leave VC dengan monitoring durasi, topik, backup log ke SQLite jika gagal akses database utama.
Kompatibel: main.py, plugin_loader.py, assetjson.py (v3+)
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.2.0
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatAdminRequiredError, UserAlreadyParticipantError, FloodWaitError
from telethon.tl.types import Channel, Chat
import sqlite3
import os

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "vc_monitor",
    "version": "1.2.0",
    "description": "Join/Leave VC dengan monitoring durasi, topik, backup log ke SQLite jika gagal akses database utama.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".joinvc", ".leavevc", ".vcstatus", ".leavevc"],
    "features": ["join vc", "leave vc", "monitor vc", "auto report disconnect", "auto backup log to SQLite"]
}

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None
monitor_state = {
    "vc_active": False,
    "vc_start_time": None,
    "current_topic": None,
    "monitor_task": None,
    "chat_id": None,
    "vc_title": None
}

# ===== Database Helper =====
DB_FILE = "plugins/vc_monitor.db"

def get_db_conn():
    # Coba ambil dari assetjson environment
    try:
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].warning(f"[VC Monitor] DB from assetjson failed: {e}")
    # Fallback ke SQLite lokal
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        # Buat tabel jika belum ada
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vc_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                chat_title TEXT,
                action TEXT,
                topic TEXT,
                start_time TEXT,
                end_time TEXT,
                duration TEXT,
                report TEXT,
                created_at TEXT
            )
        """)
        return conn
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[VC Monitor] Local SQLite error: {e}")
    return None

def save_vc_log(action, report):
    """Simpan log VC ke database utama, jika gagal backup ke SQLite lokal"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        chat_id = monitor_state["chat_id"] or 0
        chat_title = monitor_state["vc_title"] or "Unknown"
        topic = monitor_state["current_topic"] or "No topic"
        start_time = monitor_state["vc_start_time"].strftime("%Y-%m-%d %H:%M:%S") if monitor_state["vc_start_time"] else "-"
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = get_duration()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO vc_logs (chat_id, chat_title, action, topic, start_time, end_time, duration, report, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (chat_id, chat_title, action, topic, start_time, end_time, duration, report, created_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[VC Monitor] Log backup error: {e}")
        return False

def get_duration():
    if monitor_state["vc_start_time"]:
        return str(datetime.now() - monitor_state["vc_start_time"]).split('.')[0]
    return "0:00:00"

async def monitor_vc(client, chat):
    try:
        while monitor_state["vc_active"]:
            await asyncio.sleep(8)
            try:
                participants = await client.get_participants(chat)
                me = await client.get_me()
                if me.id not in [p.id for p in participants]:
                    monitor_state["vc_active"] = False
                    duration = get_duration()
                    topic = monitor_state["current_topic"] or "No topic"
                    vc_title = monitor_state['vc_title'] or "Unknown"
                    report = (
                        f"⚠️ Bot keluar dari VC!\n"
                        f"🕒 Durasi: {duration}\n"
                        f"🔊 Channel: {vc_title}\n"
                        f"📜 Topik: {topic}"
                    )
                    me = await client.get_me()
                    await env['safe_send_with_entities'](me.id, report)
                    save_vc_log("disconnect", report)
                    break
            except Exception as e:
                env['logger'].error(f"[VC Monitor] Error monitoring VC: {e}")
    except asyncio.CancelledError:
        pass

async def join_vc_handler(event):
    if not await env['is_owner'](event.sender_id):
        return
    client = env['get_client']()
    chat = await event.get_chat()
    try:
        full_chat = await client(GetFullChannelRequest(chat) if isinstance(chat, Channel) else chat)
        call = getattr(full_chat.full_chat, 'call', None)
        topic = getattr(full_chat.full_chat, 'about', None)
        chat_title = getattr(full_chat, 'chats', [])[0].title if hasattr(full_chat, 'chats') and full_chat.chats else getattr(chat, 'title', 'Unknown')

        if not call:
            report = "❌ Tidak ada VC aktif di chat ini."
            await env['safe_send_with_entities'](event, report)
            save_vc_log("join-failed", report)
            return

        try:
            await client(JoinGroupCallRequest(call=call, muted=False, video_stopped=True))
        except FloodWaitError as fe:
            await env['safe_send_with_entities'](event, f"⚠️ Flood wait, tunggu {fe.seconds} detik...")
            await asyncio.sleep(fe.seconds)
            await client(JoinGroupCallRequest(call=call, muted=False, video_stopped=True))
        except UserAlreadyParticipantError:
            report = "⚠️ Sudah berada di VC."
            await env['safe_send_with_entities'](event, report)
            save_vc_log("already-in", report)
            return

        monitor_state["vc_active"] = True
        monitor_state["vc_start_time"] = datetime.now()
        monitor_state["current_topic"] = topic or "No topic"
        monitor_state["chat_id"] = chat.id
        monitor_state["vc_title"] = chat_title

        # Mulai monitor
        if monitor_state.get("monitor_task") and not monitor_state["monitor_task"].done():
            monitor_state["monitor_task"].cancel()
        monitor_state["monitor_task"] = asyncio.create_task(monitor_vc(client, chat))

        report = (
            f"✅ Berhasil join VC!\n"
            f"🔊 Channel: {chat_title}\n"
            f"🕒 Durasi: 0:00:00\n"
            f"📜 Topik: {monitor_state['current_topic']}"
        )
        await env['safe_send_with_entities'](event, report)
        save_vc_log("join", report)
    except ChatAdminRequiredError:
        report = "❌ Butuh hak admin untuk join VC."
        await env['safe_send_with_entities'](event, report)
        save_vc_log("join-failed", report)
    except Exception as e:
        report = f"❌ Error join VC: {e}"
        env['logger'].error(f"[VC Monitor] Error join VC: {e}")
        await env['safe_send_with_entities'](event, report)
        save_vc_log("join-failed", report)

async def leave_vc_handler(event):
    if not await env['is_owner'](event.sender_id):
        return
    client = env['get_client']()
    try:
        if not monitor_state["vc_active"]:
            report = "⚠️ Tidak sedang berada di VC."
            await env['safe_send_with_entities'](event, report)
            save_vc_log("leave-failed", report)
            return

        await client(LeaveGroupCallRequest())
        monitor_state["vc_active"] = False
        duration = get_duration()
        topic = monitor_state["current_topic"] or "No topic"
        vc_title = monitor_state['vc_title'] or "Unknown"

        # Stop monitor
        if monitor_state.get("monitor_task"):
            monitor_state["monitor_task"].cancel()
            monitor_state["monitor_task"] = None

        report = (
            f"✅ Berhasil keluar dari VC!\n"
            f"🕒 Durasi: {duration}\n"
            f"🔊 Channel: {vc_title}\n"
            f"📜 Topik: {topic}"
        )
        await env['safe_send_with_entities'](event, report)
        save_vc_log("leave", report)
        monitor_state["vc_start_time"] = None
        monitor_state["current_topic"] = None
        monitor_state["chat_id"] = None
        monitor_state["vc_title"] = None
    except Exception as e:
        report = f"❌ Error leave VC: {e}"
        env['logger'].error(f"[VC Monitor] Error leave VC: {e}")
        await env['safe_send_with_entities'](event, report)
        save_vc_log("leave-failed", report)

async def vc_status_handler(event):
    if not await env['is_owner'](event.sender_id):
        return
    status = "AKTIF" if monitor_state["vc_active"] else "TIDAK AKTIF"
    duration = get_duration()
    topic = monitor_state["current_topic"] or "No topic"
    vc_title = monitor_state["vc_title"] or "Unknown"
    report = (
        f"🔎 Status VC Monitor:\n"
        f"• Status: {status}\n"
        f"• Durasi: {duration}\n"
        f"• Channel: {vc_title}\n"
        f"• Topik: {topic}"
    )
    await env['safe_send_with_entities'](event, report)
    save_vc_log("status", report)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    global env
    env = create_plugin_environment(client)
    client.add_event_handler(join_vc_handler, events.NewMessage(pattern=r"\.joinvc"))
    client.add_event_handler(leave_vc_handler, events.NewMessage(pattern=r"\.leavevc"))
    client.add_event_handler(vc_status_handler, events.NewMessage(pattern=r"\.vcstatus"))
    if env and 'logger' in env:
        env['logger'].info("[VC Monitor] Plugin loaded and commands registered.")