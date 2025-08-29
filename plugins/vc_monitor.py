"""
VC Monitor Plugin STANDALONE - Hardcoded Premium Emojis
File: plugins/vc_monitor.py
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 2.0.0 - Standalone
Fitur: Join/Leave VC dengan monitoring durasi, premium emojis hardcoded
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.types import DataJSON
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatAdminRequiredError, UserAlreadyParticipantError, FloodWaitError
from telethon.tl.types import Channel, Chat
import os

# Import database helper
try:
    from database import create_table, insert, select, get_log_channel_id
except ImportError:
    print("[VC Monitor] Database helper not found, using fallback")
    create_table = None
    insert = None
    select = None
    get_log_channel_id = lambda: -1002975804142

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "vc_monitor",
    "version": "2.0.0",
    "description": "Standalone VC monitor with premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".joinvc", ".leavevc", ".vcstatus"],
    "features": ["join vc", "leave vc", "monitor vc", "auto report", "premium emojis", "database logging"]
}

# ===== PREMIUM EMOJI CONFIGURATION (STANDALONE) =====
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
}

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

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
        # Get owner ID from environment (primary method)
        OWNER_ID = os.getenv('OWNER_ID')
        if OWNER_ID:
            return user_id == int(OWNER_ID)
        
        # Fallback: check if user is the bot itself
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

# Global client reference and monitor state
client = None
monitor_state = {
    "vc_active": False,
    "vc_start_time": None,
    "current_topic": None,
    "monitor_task": None,
    "chat_id": None,
    "vc_title": None
}

# ===== Database Helper =====
def init_vc_database():
    """Initialize VC monitor database table"""
    if create_table:
        schema = """
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
        """
        create_table('vc_logs', schema, 'main')
        return True
    return False

def save_vc_log(action, report):
    """Simpan log VC ke database"""
    try:
        if not insert:
            print("[VC Monitor] Database helper not available")
            return False
        
        chat_id = monitor_state["chat_id"] or 0
        chat_title = monitor_state["vc_title"] or "Unknown"
        topic = monitor_state["current_topic"] or "No topic"
        start_time = monitor_state["vc_start_time"].strftime("%Y-%m-%d %H:%M:%S") if monitor_state["vc_start_time"] else "-"
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = get_duration()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_data = {
            'chat_id': chat_id,
            'chat_title': chat_title,
            'action': action,
            'topic': topic,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'report': report,
            'created_at': created_at
        }
        
        result = insert('vc_logs', log_data, 'main')
        return result is not None
    except Exception as e:
        print(f"[VC Monitor] Log save error: {e}")
        return False

def get_duration():
    if monitor_state["vc_start_time"]:
        return str(datetime.now() - monitor_state["vc_start_time"]).split('.')[0]
    return "0:00:00"

async def monitor_vc(chat):
    """Monitor VC status"""
    global client
    try:
        while monitor_state["vc_active"]:
            await asyncio.sleep(10)
            try:
                # Check if we're still in the voice chat
                full_chat = await client(GetFullChannelRequest(chat) if isinstance(chat, Channel) else chat)
                call = getattr(full_chat.full_chat, 'call', None)
                
                if not call:
                    # No active call anymore
                    monitor_state["vc_active"] = False
                    duration = get_duration()
                    topic = monitor_state["current_topic"] or "No topic"
                    vc_title = monitor_state['vc_title'] or "Unknown"
                    
                    report = f"""
{get_emoji('adder5')} **VC telah berakhir!**

{get_emoji('check')} **Detail:**
• Durasi: {duration}
• Channel: {vc_title}
• Topik: {topic}

{get_emoji('main')} **Voice chat ended**
                    """.strip()
                    
                    # Send notification to owner
                    try:
                        me = await client.get_me()
                        await client.send_message(me.id, report)
                        save_vc_log("disconnect", report)
                    except Exception as notify_error:
                        print(f"[VC Monitor] Error sending notification: {notify_error}")
                    break
                    
            except Exception as e:
                print(f"[VC Monitor] Error monitoring VC: {e}")
                # Continue monitoring even if there's an error
    except asyncio.CancelledError:
        pass

async def join_vc_handler(event):
    """Join voice chat handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    chat = await event.get_chat()
    
    try:
        full_chat = await client(GetFullChannelRequest(chat) if isinstance(chat, Channel) else chat)
        call = getattr(full_chat.full_chat, 'call', None)
        topic = getattr(full_chat.full_chat, 'about', None)
        
        # Better chat title extraction
        chat_title = "Unknown"
        try:
            if hasattr(full_chat, 'chats') and full_chat.chats:
                chat_title = full_chat.chats[0].title
            elif hasattr(chat, 'title'):
                chat_title = chat.title
            elif hasattr(full_chat, 'full_chat') and hasattr(full_chat.full_chat, 'title'):
                chat_title = full_chat.full_chat.title
        except (AttributeError, IndexError):
            chat_title = "Unknown"

        if not call:
            report = f"""
{get_emoji('adder5')} **Tidak ada VC aktif**

{get_emoji('check')} Chat: {chat_title}
{get_emoji('main')} Status: No active voice chat
            """.strip()
            await safe_send_premium(event, report)
            save_vc_log("join-failed", report)
            return

        # Try to join VC with retry logic for SSRC errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get the bot's info to use as join_as parameter
                me = await client.get_me()
                
                # Create params with unique SSRC for each attempt
                import time
                ssrc = int(time.time() * 1000) % 2147483647  # Generate unique SSRC
                params = DataJSON(data=f'{{"ufrag": "user", "pwd": "pass", "ssrc": {ssrc}}}')
                
                await client(JoinGroupCallRequest(
                    call=call,
                    join_as=me,
                    params=params,
                    muted=False,
                    video_stopped=True
                ))
                
                # If successful, break out of retry loop
                break
                
            except Exception as join_error:
                error_msg = str(join_error).lower()
                
                # Check if it's an SSRC-related error that needs retry
                if "ssrc" in error_msg or "retry joining" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"[VC Monitor] SSRC error on attempt {attempt + 1}, retrying with new SSRC...")
                        await asyncio.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        print(f"[VC Monitor] Failed after {max_retries} attempts: {join_error}")
                        raise join_error
                else:
                    # For non-SSRC errors, don't retry
                    raise join_error
        except FloodWaitError as fe:
            await safe_send_premium(event, f"{get_emoji('adder1')} Flood wait, tunggu {fe.seconds} detik...")
            await asyncio.sleep(fe.seconds)
            # Retry with new SSRC after flood wait
            me = await client.get_me()
            import time
            ssrc = int(time.time() * 1000) % 2147483647  # Generate new SSRC
            params = DataJSON(data=f'{{"ufrag": "user", "pwd": "pass", "ssrc": {ssrc}}}')
            await client(JoinGroupCallRequest(
                call=call,
                join_as=me,
                params=params,
                muted=False,
                video_stopped=True
            ))
        except UserAlreadyParticipantError:
            report = f"{get_emoji('adder5')} **Sudah berada di VC**\n\n{get_emoji('check')} Channel: {chat_title}"
            await safe_send_premium(event, report)
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
        monitor_state["monitor_task"] = asyncio.create_task(monitor_vc(chat))

        report = f"""
{get_emoji('main')} **Berhasil join VC v2.0!**

{get_emoji('check')} **Detail:**
• Channel: {chat_title}
• Durasi: 0:00:00
• Topik: {monitor_state['current_topic']}

{get_emoji('adder2')} **Monitoring aktif**
        """.strip()
        
        await safe_send_premium(event, report)
        save_vc_log("join", report)
        
        # Send to log channel if available  
        try:
            channel_id = get_log_channel_id()
            log_msg = f"{get_emoji('check')} **VC Joined**\n• Channel: {chat_title}\n• Topic: {monitor_state['current_topic']}\n• Time: {datetime.now().strftime('%H:%M:%S')}"
            await client.send_message(channel_id, log_msg)
        except Exception as log_error:
            print(f"[VC Monitor] Error sending to log channel: {log_error}")
            
    except ChatAdminRequiredError:
        report = f"{get_emoji('adder5')} **Butuh hak admin** untuk join VC"
        await safe_send_premium(event, report)
        save_vc_log("join-failed", report)
    except Exception as e:
        report = f"{get_emoji('adder5')} **Error join VC:** {str(e)}"
        print(f"[VC Monitor] Error join VC: {e}")
        await safe_send_premium(event, report)
        save_vc_log("join-failed", report)

async def leave_vc_handler(event):
    """Leave voice chat handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
        
    try:
        if not monitor_state["vc_active"]:
            report = f"{get_emoji('adder5')} **Tidak sedang di VC**\n\n{get_emoji('check')} Status: Not in voice chat"
            await safe_send_premium(event, report)
            save_vc_log("leave-failed", report)
            return

        # Try to get current call info for leaving
        try:
            # Get current chat where we might be in VC
            if monitor_state.get("chat_id"):
                chat = await client.get_entity(monitor_state["chat_id"])
                full_chat = await client(GetFullChannelRequest(chat) if isinstance(chat, Channel) else chat)
                call = getattr(full_chat.full_chat, 'call', None)
                
                if call:
                    await client(LeaveGroupCallRequest(call=call))
                else:
                    # No active call, just update our state
                    pass
            else:
                # Fallback: try without call parameter (older API)
                await client(LeaveGroupCallRequest())
        except Exception as leave_error:
            print(f"[VC Monitor] Leave call error: {leave_error}")
            # Even if leaving fails, update our state
            pass
        monitor_state["vc_active"] = False
        duration = get_duration()
        topic = monitor_state["current_topic"] or "No topic"
        vc_title = monitor_state['vc_title'] or "Unknown"

        # Stop monitor
        if monitor_state.get("monitor_task"):
            monitor_state["monitor_task"].cancel()
            monitor_state["monitor_task"] = None

        report = f"""
{get_emoji('main')} **Berhasil keluar dari VC!**

{get_emoji('check')} **Summary:**
• Durasi: {duration}
• Channel: {vc_title}
• Topik: {topic}

{get_emoji('adder2')} **Session completed**
        """.strip()
        
        await safe_send_premium(event, report)
        save_vc_log("leave", report)
        
        # Send to log channel if available
        try:
            channel_id = get_log_channel_id()
            log_msg = f"{get_emoji('adder6')} **VC Left**\n• Channel: {vc_title}\n• Duration: {duration}\n• Topic: {topic}\n• Time: {datetime.now().strftime('%H:%M:%S')}"
            await client.send_message(channel_id, log_msg)
        except Exception as log_error:
            print(f"[VC Monitor] Error sending to log channel: {log_error}")
        
        # Reset state
        monitor_state["vc_start_time"] = None
        monitor_state["current_topic"] = None
        monitor_state["chat_id"] = None
        monitor_state["vc_title"] = None
        
    except Exception as e:
        report = f"{get_emoji('adder5')} **Error leave VC:** {str(e)}"
        print(f"[VC Monitor] Error leave VC: {e}")
        await safe_send_premium(event, report)
        save_vc_log("leave-failed", report)

async def vc_status_handler(event):
    """Show VC status"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    status = "AKTIF" if monitor_state["vc_active"] else "TIDAK AKTIF"
    duration = get_duration()
    topic = monitor_state["current_topic"] or "No topic"
    vc_title = monitor_state["vc_title"] or "Unknown"
    
    report = f"""
{get_emoji('main')} **VC Monitor Status v2.0**

{get_emoji('check')} **Current Status:**
• Status: {status}
• Durasi: {duration}
• Channel: {vc_title}
• Topik: {topic}

{get_emoji('adder4')} **Commands Available:**
{get_emoji('adder2')} `.joinvc` - Join voice chat
{get_emoji('adder5')} `.leavevc` - Leave voice chat
{get_emoji('adder6')} `.vcstatus` - Show this status

{get_emoji('main')} **Premium monitoring system!**
    """.strip()
    
    await safe_send_premium(event, report)
    save_vc_log("status", report)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Initialize database
    init_vc_database()
    
    client.add_event_handler(join_vc_handler, events.NewMessage(pattern=r"\.joinvc$"))
    client.add_event_handler(leave_vc_handler, events.NewMessage(pattern=r"\.leavevc$"))
    client.add_event_handler(vc_status_handler, events.NewMessage(pattern=r"\.vcstatus$"))
    
    print(f"✅ [VC Monitor] Plugin loaded - Enhanced with database helper v{PLUGIN_INFO['version']}")