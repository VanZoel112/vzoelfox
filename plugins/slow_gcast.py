"""
Slow GCast Plugin for Vzoel Assistant
Fitur: GCast dengan delay dan animasi edit untuk mengurangi spam
Kompatibel: main.py, plugin_loader.py, assetjson.py (v3+)
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, UserBannedInChannelError
import sqlite3
import os

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "slow_gcast",
    "version": "1.0.0",
    "description": "GCast dengan delay dan animasi edit untuk mengurangi spam",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".sgcast", ".slowgcast", ".sgstatus"],
    "features": ["slow gcast", "animated editing", "anti spam", "progress tracking", "database logging"]
}

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None
gcast_state = {
    "is_running": False,
    "current_task": None,
    "total_chats": 0,
    "processed": 0,
    "success": 0,
    "failed": 0,
    "start_time": None
}

# ===== Premium Emojis =====
PREMIUM_EMOJIS = {
    'main': {'char': '🤩'}, 'check': {'char': '⚙️'}, 'adder1': {'char': '⛈'},
    'adder2': {'char': '✅'}, 'adder3': {'char': '👽'}, 'adder4': {'char': '✈️'},
    'adder5': {'char': '😈'}, 'adder6': {'char': '🎚️'}
}

def get_emoji(emoji_type):
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

# ===== Animation Words =====
ANIMATION_WORDS = [
    f"{get_emoji('check')} Memulai proses...",
    f"{get_emoji('adder1')} Mengambil daftar grup...",
    f"{get_emoji('adder3')} Menganalisis target...",
    f"{get_emoji('adder4')} Mempersiapkan pesan...",
    f"{get_emoji('main')} Memulai pengiriman...",
    f"{get_emoji('adder6')} Mengirim ke grup...",
    f"{get_emoji('adder5')} Proses berlangsung...",
    f"{get_emoji('adder2')} Hampir selesai...",
    f"{get_emoji('check')} Finalisasi...",
    f"{get_emoji('main')} Selesai!"
]

# ===== Database Helper =====
DB_FILE = "plugins/slow_gcast.db"

def get_db_conn():
    try:
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].warning(f"[Slow GCast] DB from assetjson failed: {e}")
    
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gcast_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                total_chats INTEGER,
                success_count INTEGER,
                failed_count INTEGER,
                duration TEXT,
                start_time TEXT,
                end_time TEXT,
                created_at TEXT
            )
        """)
        return conn
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[Slow GCast] Local SQLite error: {e}")
    return None

def save_gcast_log(message, duration):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_time = gcast_state["start_time"].strftime("%Y-%m-%d %H:%M:%S") if gcast_state["start_time"] else "-"
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute(
            "INSERT INTO gcast_logs (message, total_chats, success_count, failed_count, duration, start_time, end_time, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (message[:100], gcast_state["total_chats"], gcast_state["success"], gcast_state["failed"], duration, start_time, end_time, created_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].error(f"[Slow GCast] Log save error: {e}")
        return False

async def animate_progress(event, message):
    """Animasi progress dengan edit pesan"""
    for i, word in enumerate(ANIMATION_WORDS):
        try:
            progress = f"{word}\n\n📊 Progress: {gcast_state['processed']}/{gcast_state['total_chats']}\n✅ Berhasil: {gcast_state['success']}\n❌ Gagal: {gcast_state['failed']}"
            await event.edit(progress)
            await asyncio.sleep(2)  # Delay 2 detik per kata
        except Exception as e:
            if env and 'logger' in env:
                env['logger'].error(f"[Slow GCast] Animation error: {e}")
            break

async def slow_gcast_handler(event):
    if not await env['is_owner'](event.sender_id):
        return
    
    if gcast_state["is_running"]:
        await env['safe_send_with_entities'](event, "⚠️ Slow GCast sedang berjalan! Gunakan `.sgstatus` untuk melihat progress.")
        return
    
    # Parse pesan - bisa dari command atau reply
    message = None
    
    # Cek apakah reply ke pesan
    if event.is_reply:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            message = replied_msg.text
        elif replied_msg and replied_msg.media:
            # Jika reply ke media, ambil caption atau gunakan media
            message = replied_msg.text or "[Media/File]"
        else:
            await env['safe_send_with_entities'](event, "❌ Pesan yang direply tidak valid!")
            return
    else:
        # Parse dari command
        message_text = event.raw_text.split(maxsplit=1)
        if len(message_text) < 2:
            help_text = (
                f"{get_emoji('main')} **Cara Penggunaan Slow GCast:**\n\n"
                f"**Metode 1:** `.sgcast <pesan>` - Tulis pesan langsung\n"
                f"**Metode 2:** Reply ke pesan + `.sgcast` - Forward pesan yang direply\n"
                f"**Alias:** `.slowgcast` juga bisa digunakan\n"
                f"**Status:** `.sgstatus` - Lihat progress\n\n"
                f"{get_emoji('check')} **Fitur:**\n"
                f"{get_emoji('adder2')} Delay 15 detik antar grup\n"
                f"{get_emoji('adder3')} Animasi progress 10 kata\n"
                f"{get_emoji('adder4')} Anti flood protection\n"
                f"{get_emoji('adder5')} Support reply message\n"
                f"{get_emoji('adder6')} Database logging\n"
                f"{get_emoji('adder1')} Real-time statistics"
            )
            await env['safe_send_with_entities'](event, help_text)
            return
        message = message_text[1]
    client = env['get_client']()
    
    # Reset state
    gcast_state.update({
        "is_running": True,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "start_time": datetime.now()
    })
    
    try:
        # Get all chats
        all_chats = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group and not dialog.entity.broadcast:
                all_chats.append(dialog)
        
        gcast_state["total_chats"] = len(all_chats)
        
        if gcast_state["total_chats"] == 0:
            await env['safe_send_with_entities'](event, "❌ Tidak ada grup yang ditemukan!")
            gcast_state["is_running"] = False
            return
        
        # Start animation task
        animation_task = asyncio.create_task(animate_progress(event, message))
        
        # Process chats with delay
        for chat in all_chats:
            if not gcast_state["is_running"]:  # Check if cancelled
                break
                
            try:
                # Cek apakah dari reply message untuk forward
                if event.is_reply:
                    replied_msg = await event.get_reply_message()
                    if replied_msg:
                        # Forward pesan yang direply
                        await client.forward_messages(chat.entity, replied_msg)
                    else:
                        # Fallback ke text biasa
                        await client.send_message(chat.entity, message)
                else:
                    # Kirim pesan text biasa
                    await client.send_message(chat.entity, message)
                
                gcast_state["success"] += 1
                if env and 'logger' in env:
                    env['logger'].info(f"[Slow GCast] Sent to: {chat.name}")
            
            except FloodWaitError as fe:
                if env and 'logger' in env:
                    env['logger'].warning(f"[Slow GCast] Flood wait {fe.seconds}s for {chat.name}")
                await asyncio.sleep(fe.seconds)
                try:
                    # Retry dengan method yang sama
                    if event.is_reply:
                        replied_msg = await event.get_reply_message()
                        if replied_msg:
                            await client.forward_messages(chat.entity, replied_msg)
                        else:
                            await client.send_message(chat.entity, message)
                    else:
                        await client.send_message(chat.entity, message)
                    gcast_state["success"] += 1
                except:
                    gcast_state["failed"] += 1
            
            except (ChatWriteForbiddenError, UserBannedInChannelError):
                gcast_state["failed"] += 1
                if env and 'logger' in env:
                    env['logger'].warning(f"[Slow GCast] Banned/Forbidden: {chat.name}")
            
            except Exception as e:
                gcast_state["failed"] += 1
                if env and 'logger' in env:
                    env['logger'].error(f"[Slow GCast] Error in {chat.name}: {e}")
            
            gcast_state["processed"] += 1
            
            # Delay 15 detik antar grup (kecuali grup terakhir)
            if gcast_state["processed"] < gcast_state["total_chats"]:
                await asyncio.sleep(15)
        
        # Cancel animation
        if not animation_task.done():
            animation_task.cancel()
        
        # Final report
        end_time = datetime.now()
        duration = str(end_time - gcast_state["start_time"]).split('.')[0]
        
        final_report = (
            f"🎉 **Slow GCast Selesai!**\n\n"
            f"📊 **Statistik:**\n"
            f"• Total Grup: {gcast_state['total_chats']}\n"
            f"• Berhasil: {gcast_state['success']}\n"
            f"• Gagal: {gcast_state['failed']}\n"
            f"• Durasi: {duration}\n\n"
            f"📝 **Pesan:** {message[:50]}{'...' if len(message) > 50 else ''}\n"
            f"🕒 **Selesai:** {end_time.strftime('%H:%M:%S')}"
        )
        
        await event.edit(final_report)
        save_gcast_log(message, duration)
        
    except Exception as e:
        error_msg = f"❌ Error dalam slow gcast: {e}"
        if env and 'logger' in env:
            env['logger'].error(f"[Slow GCast] Main error: {e}")
        await event.edit(error_msg)
    
    finally:
        gcast_state["is_running"] = False

async def sgstatus_handler(event):
    if not await env['is_owner'](event.sender_id):
        return
    
    if not gcast_state["is_running"]:
        # Show last gcast stats from database
        try:
            conn = get_db_conn()
            if conn:
                cursor = conn.execute("SELECT * FROM gcast_logs ORDER BY id DESC LIMIT 1")
                last_gcast = cursor.fetchone()
                conn.close()
                
                if last_gcast:
                    status = (
                        f"📊 **Status Slow GCast: IDLE**\n\n"
                        f"📈 **Last GCast:**\n"
                        f"• Total: {last_gcast['total_chats']} grup\n"
                        f"• Berhasil: {last_gcast['success_count']}\n"
                        f"• Gagal: {last_gcast['failed_count']}\n"
                        f"• Durasi: {last_gcast['duration']}\n"
                        f"• Waktu: {last_gcast['end_time']}\n\n"
                        f"💡 Gunakan `.sgcast <pesan>` untuk memulai"
                    )
                else:
                    status = "📊 **Status: IDLE** - Belum ada riwayat gcast\n\n💡 Gunakan `.sgcast <pesan>` untuk memulai"
            else:
                status = "📊 **Status: IDLE** - Database tidak tersedia"
        except Exception as e:
            status = f"📊 **Status: IDLE** - Error: {e}"
    else:
        # Show current progress
        elapsed = str(datetime.now() - gcast_state["start_time"]).split('.')[0] if gcast_state["start_time"] else "0:00:00"
        progress_percent = (gcast_state["processed"] / gcast_state["total_chats"] * 100) if gcast_state["total_chats"] > 0 else 0
        
        status = (
            f"🔥 **Status Slow GCast: RUNNING**\n\n"
            f"📊 **Progress:** {progress_percent:.1f}%\n"
            f"📈 **Statistik:**\n"
            f"• Diproses: {gcast_state['processed']}/{gcast_state['total_chats']}\n"
            f"• Berhasil: {gcast_state['success']}\n"
            f"• Gagal: {gcast_state['failed']}\n"
            f"• Durasi: {elapsed}\n\n"
            f"⏱️ **ETA:** ~{((gcast_state['total_chats'] - gcast_state['processed']) * 15 / 60):.1f} menit"
        )
    
    await env['safe_send_with_entities'](event, status)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    global env
    env = create_plugin_environment(client)
    client.add_event_handler(slow_gcast_handler, events.NewMessage(pattern=r"\.s(?:g|low)gcast"))
    client.add_event_handler(sgstatus_handler, events.NewMessage(pattern=r"\.sgstatus"))
    if env and 'logger' in env:
        env['logger'].info("[Slow GCast] Plugin loaded - Anti-spam gcast with animation ready.")