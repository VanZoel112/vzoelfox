"""
VC Monitor Plugin for Vzoel Assistant - FIXED & ENHANCED VERSION
Fitur: Join/Leave VC dengan monitoring durasi, topik, backup log ke SQLite jika gagal akses database utama.
Kompatibel: main.py v0.1.0.75, plugin_loader.py, assetjson.py v3+
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Fixed compatibility and enhanced features
"""

import asyncio
import sqlite3
import os
import logging
from datetime import datetime
from telethon import events
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatAdminRequiredError, UserAlreadyParticipantError, FloodWaitError
from telethon.tl.types import Channel, Chat

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "vc_monitor",
    "version": "2.0.0",
    "description": "Join/Leave VC with duration monitoring, premium emoji support, database logging",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".joinvc", ".leavevc", ".vcstatus"],
    "features": ["join vc", "leave vc", "monitor vc", "auto report disconnect", "database logging", "premium emoji"]
}

# Global variables
env = None
client = None
logger = None
DB_FILE = "plugins/vc_monitor.db"

# Monitor state
monitor_state = {
    "vc_active": False,
    "vc_start_time": None,
    "current_topic": None,
    "monitor_task": None,
    "chat_id": None,
    "vc_title": None
}

def setup_logger():
    """Setup dedicated logger untuk plugin"""
    global logger
    logger = logging.getLogger("vc_monitor_plugin")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

def get_db_conn():
    """Get database connection dengan fallback ke SQLite lokal"""
    try:
        # Try assetjson environment first
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if logger:
            logger.warning(f"[VC Monitor] DB from assetjson failed: {e}")
    
    # Fallback ke SQLite lokal
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
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
                user_id INTEGER,
                created_at TEXT
            )
        """)
        conn.commit()
        return conn
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Local SQLite error: {e}")
    return None

def save_vc_log(action, report, user_id=None):
    """Simpan log VC ke database dengan enhanced details"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        chat_id = monitor_state.get("chat_id", 0)
        chat_title = monitor_state.get("vc_title", "Unknown")
        topic = monitor_state.get("current_topic", "No topic")
        start_time = monitor_state["vc_start_time"].strftime("%Y-%m-%d %H:%M:%S") if monitor_state.get("vc_start_time") else "-"
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = get_duration()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute(
            "INSERT INTO vc_logs (chat_id, chat_title, action, topic, start_time, end_time, duration, report, user_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (chat_id, chat_title, action, topic, start_time, end_time, duration, report, user_id, created_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Log backup error: {e}")
        return False

def get_duration():
    """Get current VC duration"""
    if monitor_state.get("vc_start_time"):
        duration = datetime.now() - monitor_state["vc_start_time"]
        return str(duration).split('.')[0]
    return "0:00:00"

def get_emoji(emoji_type):
    """Get premium emoji dengan fallback"""
    try:
        if env and 'get_emoji' in env:
            return env['get_emoji'](emoji_type)
    except Exception:
        pass
    
    # Fallback emojis
    fallback_emojis = {
        'main': '🤩',
        'check': '⚙️',
        'adder1': '⛈',
        'adder2': '✅',
        'adder3': '👽',
        'adder4': '✈️',
        'adder5': '😈',
        'adder6': '🎚️'
    }
    return fallback_emojis.get(emoji_type, '🤩')

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts dengan fallback"""
    try:
        if env and 'convert_font' in env:
            return env['convert_font'](text, font_type)
    except Exception:
        pass
    
    # Fallback font conversion
    if font_type == 'bold':
        bold_map = {
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇'
        }
        result = ""
        for char in text:
            result += bold_map.get(char, char)
        return result
    return text

async def is_owner_check(user_id):
    """Check if user is owner dengan multiple fallbacks"""
    try:
        if env and 'is_owner' in env:
            return await env['is_owner'](user_id)
    except Exception:
        pass
    
    try:
        if client:
            owner_id = os.getenv("OWNER_ID")
            if owner_id:
                return user_id == int(owner_id)
            me = await client.get_me()
            return user_id == me.id
    except Exception as e:
        if logger:
            logger.error(f"Error checking owner: {e}")
    
    return False

async def safe_send_message(event_or_chat, text):
    """Send message dengan premium emoji support"""
    try:
        if env and 'safe_send_with_entities' in env:
            return await env['safe_send_with_entities'](event_or_chat, text)
    except Exception:
        pass
    
    try:
        if hasattr(event_or_chat, 'reply'):
            return await event_or_chat.reply(text)
        elif client:
            return await client.send_message(event_or_chat, text)
    except Exception as e:
        if logger:
            logger.error(f"Error sending message: {e}")
    
    return None

async def monitor_vc(telegram_client, chat):
    """Monitor VC connection dan auto-report disconnections"""
    try:
        while monitor_state["vc_active"]:
            await asyncio.sleep(30)  # Check every 30 seconds
            try:
                # Check if we're still in the call
                if isinstance(chat, Channel):
                    full_chat = await telegram_client(GetFullChannelRequest(chat))
                    call = getattr(full_chat.full_chat, 'call', None)
                else:
                    call = getattr(chat, 'call', None)
                
                if not call:
                    # VC ended
                    monitor_state["vc_active"] = False
                    duration = get_duration()
                    topic = monitor_state.get("current_topic", "No topic")
                    vc_title = monitor_state.get('vc_title', "Unknown")
                    
                    report = f"""
{get_emoji('adder3')} {convert_font('VC ENDED AUTOMATICALLY', 'bold')}

{get_emoji('check')} {convert_font('Duration:', 'bold')} {duration}
{get_emoji('check')} {convert_font('Channel:', 'bold')} {vc_title}
{get_emoji('check')} {convert_font('Topic:', 'bold')} {topic}
{get_emoji('adder1')} {convert_font('Reason:', 'bold')} VC session ended
                    """.strip()
                    
                    me = await telegram_client.get_me()
                    await safe_send_message(me.id, report)
                    save_vc_log("auto-disconnect", report)
                    break
                    
            except Exception as e:
                if logger:
                    logger.error(f"[VC Monitor] Error monitoring VC: {e}")
                await asyncio.sleep(5)  # Wait before retry
                
    except asyncio.CancelledError:
        if logger:
            logger.info("[VC Monitor] Monitoring task cancelled")
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Monitor error: {e}")

async def join_vc_handler(event):
    """Enhanced join VC handler"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        if not client:
            await safe_send_message(event, f"{get_emoji('adder3')} Client not available")
            return
        
        chat = await event.get_chat()
        
        try:
            # Get full chat info for call details
            if isinstance(chat, Channel):
                full_chat = await client(GetFullChannelRequest(chat))
                call = getattr(full_chat.full_chat, 'call', None)
                topic = getattr(full_chat.full_chat, 'about', None)
            else:
                call = getattr(chat, 'call', None)
                topic = getattr(chat, 'about', None)
            
            chat_title = getattr(chat, 'title', 'Unknown')
            
            if not call:
                report = f"{get_emoji('adder3')} {convert_font('No active voice chat in this chat', 'bold')}"
                await safe_send_message(event, report)
                save_vc_log("join-failed", report, event.sender_id)
                return
            
            # Check if already in VC
            if monitor_state["vc_active"]:
                current_duration = get_duration()
                current_title = monitor_state.get('vc_title', 'Unknown')
                report = f"""
{get_emoji('adder1')} {convert_font('ALREADY IN VOICE CHAT', 'bold')}

{get_emoji('check')} {convert_font('Current VC:', 'bold')} {current_title}
{get_emoji('check')} {convert_font('Duration:', 'bold')} {current_duration}
                """.strip()
                await safe_send_message(event, report)
                return
            
            try:
                # Join the voice chat
                await client(JoinGroupCallRequest(
                    call=call,
                    muted=False,
                    video_stopped=True
                ))
                
            except FloodWaitError as fe:
                await safe_send_message(event, f"{get_emoji('adder1')} Flood wait, please wait {fe.seconds} seconds...")
                await asyncio.sleep(fe.seconds)
                await client(JoinGroupCallRequest(
                    call=call,
                    muted=False,
                    video_stopped=True
                ))
                
            except UserAlreadyParticipantError:
                report = f"{get_emoji('adder1')} {convert_font('Already in voice chat', 'bold')}"
                await safe_send_message(event, report)
                save_vc_log("already-in", report, event.sender_id)
                return
            
            # Update monitor state
            monitor_state["vc_active"] = True
            monitor_state["vc_start_time"] = datetime.now()
            monitor_state["current_topic"] = topic or "No topic"
            monitor_state["chat_id"] = chat.id
            monitor_state["vc_title"] = chat_title
            
            # Start monitoring task
            if monitor_state.get("monitor_task") and not monitor_state["monitor_task"].done():
                monitor_state["monitor_task"].cancel()
            monitor_state["monitor_task"] = asyncio.create_task(monitor_vc(client, chat))
            
            report = f"""
{get_emoji('adder2')} {convert_font('JOINED VOICE CHAT!', 'bold')}

{get_emoji('check')} {convert_font('Channel:', 'bold')} {chat_title}
{get_emoji('check')} {convert_font('Topic:', 'bold')} {monitor_state['current_topic']}
{get_emoji('check')} {convert_font('Duration:', 'bold')} 0:00:00
{get_emoji('main')} {convert_font('Monitoring active...', 'bold')}
            """.strip()
            
            await safe_send_message(event, report)
            save_vc_log("join", report, event.sender_id)
            
        except ChatAdminRequiredError:
            report = f"{get_emoji('adder3')} {convert_font('Admin rights required to join voice chat', 'bold')}"
            await safe_send_message(event, report)
            save_vc_log("join-failed", report, event.sender_id)
            
        except Exception as e:
            report = f"{get_emoji('adder3')} {convert_font('Error joining VC:', 'bold')} {str(e)}"
            if logger:
                logger.error(f"[VC Monitor] Error join VC: {e}")
            await safe_send_message(event, report)
            save_vc_log("join-failed", report, event.sender_id)
            
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Join handler error: {e}")
        try:
            await safe_send_message(event, f"{get_emoji('adder3')} Unexpected error occurred")
        except Exception:
            pass

async def leave_vc_handler(event):
    """Enhanced leave VC handler"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        if not client:
            await safe_send_message(event, f"{get_emoji('adder3')} Client not available")
            return
        
        try:
            if not monitor_state["vc_active"]:
                report = f"{get_emoji('adder1')} {convert_font('Not currently in voice chat', 'bold')}"
                await safe_send_message(event, report)
                save_vc_log("leave-failed", report, event.sender_id)
                return
            
            # Leave voice chat
            await client(LeaveGroupCallRequest())
            
            # Get final stats
            duration = get_duration()
            topic = monitor_state.get("current_topic", "No topic")
            vc_title = monitor_state.get('vc_title', "Unknown")
            
            # Update monitor state
            monitor_state["vc_active"] = False
            
            # Stop monitoring task
            if monitor_state.get("monitor_task"):
                monitor_state["monitor_task"].cancel()
                monitor_state["monitor_task"] = None
            
            report = f"""
{get_emoji('check')} {convert_font('LEFT VOICE CHAT!', 'bold')}

{get_emoji('adder2')} {convert_font('Final Stats:', 'bold')}
{get_emoji('check')} {convert_font('Duration:', 'bold')} {duration}
{get_emoji('check')} {convert_font('Channel:', 'bold')} {vc_title}
{get_emoji('check')} {convert_font('Topic:', 'bold')} {topic}
{get_emoji('main')} {convert_font('Session ended successfully', 'bold')}
            """.strip()
            
            await safe_send_message(event, report)
            save_vc_log("leave", report, event.sender_id)
            
            # Reset monitor state
            monitor_state["vc_start_time"] = None
            monitor_state["current_topic"] = None
            monitor_state["chat_id"] = None
            monitor_state["vc_title"] = None
            
        except Exception as e:
            report = f"{get_emoji('adder3')} {convert_font('Error leaving VC:', 'bold')} {str(e)}"
            if logger:
                logger.error(f"[VC Monitor] Error leave VC: {e}")
            await safe_send_message(event, report)
            save_vc_log("leave-failed", report, event.sender_id)
            
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Leave handler error: {e}")
        try:
            await safe_send_message(event, f"{get_emoji('adder3')} Unexpected error occurred")
        except Exception:
            pass

async def vc_status_handler(event):
    """Enhanced VC status handler"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        status = convert_font("ACTIVE", "bold") if monitor_state["vc_active"] else convert_font("INACTIVE", "bold")
        status_emoji = get_emoji('adder2') if monitor_state["vc_active"] else get_emoji('adder1')
        duration = get_duration()
        topic = monitor_state.get("current_topic", "No topic")
        vc_title = monitor_state.get("vc_title", "Unknown")
        
        report = f"""
{get_emoji('main')} {convert_font('VC MONITOR STATUS', 'bold')}

{status_emoji} {convert_font('Status:', 'bold')} {status}
{get_emoji('check')} {convert_font('Duration:', 'bold')} {duration}
{get_emoji('check')} {convert_font('Channel:', 'bold')} {vc_title}
{get_emoji('check')} {convert_font('Topic:', 'bold')} {topic}
{get_emoji('adder4')} {convert_font('Monitor Task:', 'bold')} {'Running' if monitor_state.get("monitor_task") and not monitor_state["monitor_task"].done() else 'Stopped'}

{get_emoji('adder6')} {convert_font('Available Commands:', 'bold')}
{get_emoji('check')} .joinvc - Join voice chat
{get_emoji('check')} .leavevc - Leave voice chat  
{get_emoji('check')} .vcstatus - Show this status
        """.strip()
        
        await safe_send_message(event, report)
        save_vc_log("status", report, event.sender_id)
        
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Status handler error: {e}")
        try:
            await safe_send_message(event, f"{get_emoji('adder3')} Error getting status")
        except Exception:
            pass

def get_plugin_info():
    """Return plugin information"""
    return PLUGIN_INFO

def setup(telegram_client):
    """Setup function untuk plugin loader compatibility"""
    global client, env, logger
    
    # Setup logger first
    setup_logger()
    
    try:
        # Store client reference
        client = telegram_client
        
        # Try to get assetjson environment
        try:
            from assetjson import create_plugin_environment
            env = create_plugin_environment(client)
            if logger:
                logger.info("[VC Monitor] AssetJSON environment loaded successfully")
        except ImportError:
            if logger:
                logger.warning("[VC Monitor] AssetJSON not available, using fallback functions")
            env = None
        except Exception as e:
            if logger:
                logger.error(f"[VC Monitor] Error loading AssetJSON environment: {e}")
            env = None
        
        # Register event handlers
        if client:
            client.add_event_handler(join_vc_handler, events.NewMessage(pattern=r'\.joinvc'))
            client.add_event_handler(leave_vc_handler, events.NewMessage(pattern=r'\.leavevc'))
            client.add_event_handler(vc_status_handler, events.NewMessage(pattern=r'\.vcstatus'))
            if logger:
                logger.info("[VC Monitor] Event handlers registered successfully")
        else:
            if logger:
                logger.error("[VC Monitor] No client provided to setup")
            return False
        
        # Test database connection
        try:
            conn = get_db_conn()
            if conn:
                conn.close()
                if logger:
   logger.info("[VC Monitor] Database connection test successful")
        except Exception as db_error:
        if logger:
            logger.error(f"[VC Monitor] Database test error: {db_error}")
        
        if logger:
            logger.info("[VC Monitor] Plugin setup completed successfully")
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup function untuk plugin unloading"""
    global client, env, logger, monitor_state
    try:
        if logger:
            logger.info("[VC Monitor] Plugin cleanup initiated")
        
        # Cancel monitoring task if running
        if monitor_state.get("monitor_task"):
            monitor_state["monitor_task"].cancel()
            monitor_state["monitor_task"] = None
        
        # Reset monitor state
        monitor_state["vc_active"] = False
        monitor_state["vc_start_time"] = None
        monitor_state["current_topic"] = None
        monitor_state["chat_id"] = None
        monitor_state["vc_title"] = None
        
        client = None
        env = None
        
        if logger:
            logger.info("[VC Monitor] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[VC Monitor] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'join_vc_handler', 'leave_vc_handler', 'vc_status_handler']