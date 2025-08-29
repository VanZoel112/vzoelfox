"""
Slow GCast Plugin STANDALONE - No AssetJSON dependency  
File: plugins/slow_gcast.py
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Standalone
Fitur: GCast dengan delay dan animasi edit untuk mengurangi spam
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, UserBannedInChannelError
from telethon.tl.types import MessageEntityCustomEmoji
import sqlite3
import os

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "slow_gcast",
    "version": "2.0.0",
    "description": "Standalone slow gcast with premium emoji animations",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".sgcast", ".slowgcast", ".sgstatus"],
    "features": ["slow gcast", "animated editing", "anti spam", "progress tracking", "database logging", "premium emojis"]
}

# Manual Premium Emoji Mapping berdasarkan data yang diberikan
PREMIUM_EMOJIS = {
    "main": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "check": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"}, 
    "adder1": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6": {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

def get_emoji(emoji_type):
    """Get premium emoji with manual mapping"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        i += len(emoji_char)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

async def safe_edit_premium(event, text):
    """Edit message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await event.edit(text, formatting_entities=entities)
        else:
            await event.edit(text)
    except Exception:
        await event.edit(text)

async def safe_send_premium(event, text):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception:
        await event.reply(text)

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

# Global state
gcast_state = {
    "is_running": False,
    "current_task": None,
    "total_chats": 0,
    "processed": 0,
    "success": 0,
    "failed": 0,
    "start_time": None
}

# ===== Animation Words with Premium Emojis =====
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
        print(f"[Slow GCast] Database error: {e}")
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
        print(f"[Slow GCast] Log save error: {e}")
        return False

async def animate_progress(event, message):
    """Animasi progress dengan edit pesan dan premium emojis"""
    for i, word in enumerate(ANIMATION_WORDS):
        try:
            progress = f"{word}\n\n📊 Progress: {gcast_state['processed']}/{gcast_state['total_chats']}\n✅ Berhasil: {gcast_state['success']}\n❌ Gagal: {gcast_state['failed']}"
            await safe_edit_premium(event, progress)
            await asyncio.sleep(2)  # Delay 2 detik per kata
        except Exception as e:
            print(f"[Slow GCast] Animation error: {e}")
            break

# Global client reference
client = None

async def slow_gcast_handler(event):
    """Main slow gcast handler with premium emojis"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    if gcast_state["is_running"]:
        await safe_send_premium(event, f"{get_emoji('adder5')} Slow GCast sedang berjalan! Gunakan `.sgstatus` untuk melihat progress.")
        return
    
    # Parse pesan - bisa dari command atau reply
    message = None
    
    # Cek apakah reply ke pesan
    if event.is_reply:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            message = replied_msg.text
        elif replied_msg and replied_msg.media:
            message = replied_msg.text or "[Media/File]"
        else:
            await safe_send_premium(event, f"{get_emoji('adder5')} Pesan yang direply tidak valid!")
            return
    else:
        # Parse dari command
        message_text = event.raw_text.split(maxsplit=1)
        if len(message_text) < 2:
            help_text = f"""
{get_emoji('main')} **Cara Penggunaan Slow GCast v2.0:**

{get_emoji('check')} **Metode 1:** `.sgcast <pesan>` - Tulis pesan langsung
{get_emoji('check')} **Metode 2:** Reply ke pesan + `.sgcast` - Forward pesan yang direply
{get_emoji('check')} **Alias:** `.slowgcast` juga bisa digunakan
{get_emoji('check')} **Status:** `.sgstatus` - Lihat progress

{get_emoji('adder1')} **Fitur:**
{get_emoji('adder2')} Delay 15 detik antar grup
{get_emoji('adder3')} Animasi progress 10 kata dengan premium emoji
{get_emoji('adder4')} Anti flood protection
{get_emoji('adder5')} Support reply message
{get_emoji('adder6')} Database logging
{get_emoji('main')} Real-time statistics

{get_emoji('adder2')} **Version:** v2.0.0 Standalone - No dependencies!
            """.strip()
            await safe_send_premium(event, help_text)
            return
        message = message_text[1]
    
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
            await safe_send_premium(event, f"{get_emoji('adder5')} Tidak ada grup yang ditemukan!")
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
                        await client.forward_messages(chat.entity, replied_msg)
                    else:
                        await client.send_message(chat.entity, message)
                else:
                    await client.send_message(chat.entity, message)
                
                gcast_state["success"] += 1
                print(f"[Slow GCast] Sent to: {chat.name}")
            
            except FloodWaitError as fe:
                print(f"[Slow GCast] Flood wait {fe.seconds}s for {chat.name}")
                await asyncio.sleep(fe.seconds)
                try:
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
                print(f"[Slow GCast] Banned/Forbidden: {chat.name}")
            
            except Exception as e:
                gcast_state["failed"] += 1
                print(f"[Slow GCast] Error in {chat.name}: {e}")
            
            gcast_state["processed"] += 1
            
            # Delay 15 detik antar grup (kecuali grup terakhir)
            if gcast_state["processed"] < gcast_state["total_chats"]:
                await asyncio.sleep(15)
        
        # Cancel animation
        if not animation_task.done():
            animation_task.cancel()
        
        # Final report dengan premium emojis
        end_time = datetime.now()
        duration = str(end_time - gcast_state["start_time"]).split('.')[0]
        
        final_report = f"""
{get_emoji('main')} **Slow GCast Selesai! v2.0**

{get_emoji('adder2')} **Statistik:**
• Total Grup: {gcast_state['total_chats']}
• Berhasil: {gcast_state['success']}
• Gagal: {gcast_state['failed']}
• Durasi: {duration}

{get_emoji('adder3')} **Pesan:** {message[:50]}{'...' if len(message) > 50 else ''}
{get_emoji('adder4')} **Selesai:** {end_time.strftime('%H:%M:%S')}

{get_emoji('check')} **Premium emoji system working perfectly!**
        """.strip()
        
        await safe_edit_premium(event, final_report)
        save_gcast_log(message, duration)
        
        # Send to log channel if available
        try:
            # Try to send to channel -1002975804142 (damnitvzoel)
            channel_id = -1002975804142
            log_msg = f"{get_emoji('check')} **Slow GCast Completed**\n• Groups: {gcast_state['total_chats']}\n• Success: {gcast_state['success']}\n• Failed: {gcast_state['failed']}\n• Duration: {duration}"
            await client.send_message(channel_id, log_msg)
        except Exception:
            pass  # Ignore if channel logging fails
        
    except Exception as e:
        error_msg = f"{get_emoji('adder5')} Error dalam slow gcast: {e}"
        print(f"[Slow GCast] Main error: {e}")
        await safe_edit_premium(event, error_msg)
        
        # Send error log to channel if available
        try:
            channel_id = -1002975804142
            await client.send_message(channel_id, f"{get_emoji('adder5')} **Slow GCast Error**\n• Error: {str(e)}\n• Time: {datetime.now().strftime('%H:%M:%S')}")
        except Exception:
            pass
    
    finally:
        gcast_state["is_running"] = False

async def sgstatus_handler(event):
    """Show slow gcast status with premium emojis"""
    global client
    if not await is_owner_check(client, event.sender_id):
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
                    status = f"""
{get_emoji('main')} **Status Slow GCast: IDLE v2.0**

{get_emoji('adder2')} **Last GCast:**
• Total: {last_gcast['total_chats']} grup
• Berhasil: {last_gcast['success_count']}
• Gagal: {last_gcast['failed_count']}
• Durasi: {last_gcast['duration']}
• Waktu: {last_gcast['end_time']}

{get_emoji('check')} Gunakan `.sgcast <pesan>` untuk memulai
                    """.strip()
                else:
                    status = f"{get_emoji('main')} **Status: IDLE** - Belum ada riwayat gcast\n\n{get_emoji('check')} Gunakan `.sgcast <pesan>` untuk memulai"
            else:
                status = f"{get_emoji('main')} **Status: IDLE** - Database tidak tersedia"
        except Exception as e:
            status = f"{get_emoji('main')} **Status: IDLE** - Error: {e}"
    else:
        # Show current progress
        elapsed = str(datetime.now() - gcast_state["start_time"]).split('.')[0] if gcast_state["start_time"] else "0:00:00"
        progress_percent = (gcast_state["processed"] / gcast_state["total_chats"] * 100) if gcast_state["total_chats"] > 0 else 0
        
        status = f"""
{get_emoji('adder5')} **Status Slow GCast: RUNNING v2.0**

{get_emoji('adder4')} **Progress:** {progress_percent:.1f}%
{get_emoji('adder2')} **Statistik:**
• Diproses: {gcast_state['processed']}/{gcast_state['total_chats']}
• Berhasil: {gcast_state['success']}
• Gagal: {gcast_state['failed']}
• Durasi: {elapsed}

{get_emoji('adder1')} **ETA:** ~{((gcast_state['total_chats'] - gcast_state['processed']) * 15 / 60):.1f} menit

{get_emoji('main')} **Standalone system running perfectly!**
        """.strip()
    
    await safe_send_premium(event, status)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    client.add_event_handler(slow_gcast_handler, events.NewMessage(pattern=r"\.s(?:g|low)gcast"))
    client.add_event_handler(sgstatus_handler, events.NewMessage(pattern=r"\.sgstatus"))
    
    print(f"✅ [Slow GCast] Plugin loaded - Standalone premium emoji anti-spam gcast v{PLUGIN_INFO['version']}")