"""
CheckID Plugin for Vzoel Assistant - FIXED & ENHANCED VERSION
Fitur: Cek ID Telegram seseorang dengan mereply pesan atau menulis username.
Kompatibel: main.py v0.1.0.75, plugin_loader.py, assetjson.py v3+
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Fixed compatibility and added premium emoji support
"""

import sqlite3
import os
import logging
from datetime import datetime
from telethon import events

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "checkid",
    "version": "2.0.0",
    "description": "Cek ID Telegram dengan reply atau username, backup log ke SQLite, premium emoji support",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".id", ".id @username", ".id (reply)"],
    "features": ["check user id", "premium emoji support", "database logging", "enhanced error handling"]
}

# Global variables untuk plugin
env = None
client = None
logger = None
DB_FILE = "plugins/checkid.db"

def setup_logger():
    """Setup dedicated logger untuk plugin"""
    global logger
    logger = logging.getLogger("checkid_plugin")
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
            logger.warning(f"[CheckID] DB from assetjson failed: {e}")
    
    # Fallback ke SQLite lokal
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS id_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                chat_id INTEGER,
                chat_title TEXT,
                requester_id INTEGER,
                requester_username TEXT,
                method TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        return conn
    except Exception as e:
        if logger:
            logger.error(f"[CheckID] Local SQLite error: {e}")
    return None

def save_id_log(user, chat, requester, method):
    """Save ID check log to database"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        user_id = getattr(user, 'id', 0)
        username = getattr(user, 'username', None)
        full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        chat_id = getattr(chat, 'id', 0)
        chat_title = getattr(chat, 'title', 'Unknown')
        requester_id = getattr(requester, 'id', 0)
        requester_username = getattr(requester, 'username', None)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.execute(
            "INSERT INTO id_logs (user_id, username, full_name, chat_id, chat_title, requester_id, requester_username, method, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, chat_id, chat_title, requester_id, requester_username, method, created_at)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if logger:
            logger.error(f"[CheckID] Log backup error: {e}")
        return False

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
        'adder3': '👽'
    }
    return fallback_emojis.get(emoji_type, '🤩')

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts dengan fallback"""
    try:
        if env and 'convert_font' in env:
            return env['convert_font'](text, font_type)
    except Exception:
        pass
    
    # Fallback: basic bold Unicode conversion
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
        }
        result = ""
        for char in text:
            result += bold_map.get(char, char)
        return result
    return text

async def is_owner_check(user_id):
    """Check if user is owner dengan multiple fallbacks"""
    try:
        # Try environment function first
        if env and 'is_owner' in env:
            return await env['is_owner'](user_id)
    except Exception:
        pass
    
    # Try client method
    try:
        if client:
            # Check OWNER_ID from environment
            owner_id = os.getenv("OWNER_ID")
            if owner_id:
                return user_id == int(owner_id)
            
            # Fallback to client.get_me()
            me = await client.get_me()
            return user_id == me.id
    except Exception as e:
        if logger:
            logger.error(f"Error checking owner: {e}")
    
    return False

async def safe_send_message(event, text):
    """Send message dengan premium emoji support dan fallbacks"""
    try:
        # Try environment function first (with premium emoji support)
        if env and 'safe_send_with_entities' in env:
            return await env['safe_send_with_entities'](event, text)
    except Exception:
        pass
    
    # Try client method
    try:
        if client:
            return await event.reply(text)
    except Exception as e:
        if logger:
            logger.error(f"Error sending message: {e}")
    
    return None

async def id_handler(event):
    """Enhanced ID handler dengan premium emoji support"""
    try:
        # Check if user is owner
        if not await is_owner_check(event.sender_id):
            return
        
        user = None
        method = None
        
        # Get chat and requester info
        try:
            chat = await event.get_chat()
            if client:
                requester = await client.get_entity(event.sender_id)
            else:
                requester = await event.get_sender()
        except Exception as e:
            if logger:
                logger.error(f"Error getting chat/requester info: {e}")
            chat = None
            requester = None

        # Determine user to check
        if event.is_reply:
            try:
                reply = await event.get_reply_message()
                if client:
                    user = await client.get_entity(reply.sender_id)
                else:
                    user = await reply.get_sender()
                method = "reply"
            except Exception as e:
                await safe_send_message(event, f"❌ Error getting replied user: {str(e)}")
                return
        else:
            # Check for username argument
            args = event.text.split()
            if len(args) > 1:
                uname = args[1].strip('@')
                try:
                    if client:
                        user = await client.get_entity(uname)
                    method = "username"
                except Exception as e:
                    await safe_send_message(event, f"❌ Tidak bisa menemukan user dengan username: @{uname}")
                    return
            else:
                # Check self
                user = requester
                method = "self"

        if not user:
            await safe_send_message(event, f"❌ {convert_font('Error: Could not get user info', 'bold')}")
            return

        # Extract user information
        user_id = getattr(user, 'id', None)
        username = getattr(user, 'username', None)
        first_name = getattr(user, 'first_name', '')
        last_name = getattr(user, 'last_name', '')
        full_name = (first_name + " " + last_name).strip()
        
        # Check if user is bot
        is_bot = getattr(user, 'bot', False)
        is_verified = getattr(user, 'verified', False)
        is_premium = getattr(user, 'premium', False)
        
        # Create enhanced result text dengan premium emoji support
        result_text = f"""
{get_emoji('main')} {convert_font('USER INFORMATION', 'bold')}

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('IDENTITY DETAILS', 'bold')} {get_emoji('check')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('User ID:', 'bold')} `{user_id}`
{get_emoji('check')} {convert_font('Username:', 'bold')} @{username if username else 'None'}
{get_emoji('check')} {convert_font('Full Name:', 'bold')} `{full_name if full_name else 'Unknown'}`
{get_emoji('adder1')} {convert_font('First Name:', 'bold')} `{first_name if first_name else 'None'}`
{get_emoji('adder1')} {convert_font('Last Name:', 'bold')} `{last_name if last_name else 'None'}`

{get_emoji('adder2')} {convert_font('Account Status:', 'bold')}
{get_emoji('check')} Bot: {'Yes' if is_bot else 'No'}
{get_emoji('check')} Verified: {'Yes' if is_verified else 'No'}  
{get_emoji('check')} Premium: {'Yes' if is_premium else 'No'}

{get_emoji('adder3')} {convert_font('Query Info:', 'bold')}
{get_emoji('check')} Method: {method.title()}
{get_emoji('check')} Checked by: {requester.first_name if requester else 'Unknown'}
{get_emoji('check')} Time: {datetime.now().strftime("%H:%M:%S")}

{get_emoji('main')} {convert_font('ID check completed successfully!', 'bold')}
        """.strip()

        # Send result
        await safe_send_message(event, result_text)
        
        # Log to database
        if chat and requester:
            log_success = save_id_log(user, chat, requester, method)
            if logger:
                if log_success:
                    logger.info(f"[CheckID] Logged ID check: {user_id} by {requester.id}")
                else:
                    logger.warning(f"[CheckID] Failed to log ID check for {user_id}")

    except Exception as e:
        if logger:
            logger.error(f"[CheckID] Handler error: {e}")
        try:
            error_text = f"❌ {convert_font('CheckID Error:', 'bold')} {str(e)}"
            await safe_send_message(event, error_text)
        except Exception:
            pass  # Avoid infinite error loops

def get_plugin_info():
    """Return plugin information"""
    return PLUGIN_INFO

def setup(telegram_client):
    """
    FIXED: Setup function untuk plugin loader compatibility
    
    Args:
        telegram_client: The Telegram client instance
    """
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
                logger.info("[CheckID] AssetJSON environment loaded successfully")
        except ImportError:
            if logger:
                logger.warning("[CheckID] AssetJSON not available, using fallback functions")
            env = None
        except Exception as e:
            if logger:
                logger.error(f"[CheckID] Error loading AssetJSON environment: {e}")
            env = None
        
        # Register event handler dengan proper pattern
        if client:
            client.add_event_handler(id_handler, events.NewMessage(pattern=r'\.id'))
            if logger:
                logger.info("[CheckID] Event handler registered successfully")
        else:
            if logger:
                logger.error("[CheckID] No client provided to setup")
            return False
        
        # Test database connection
        try:
            conn = get_db_conn()
            if conn:
                conn.close()
                if logger:
                    logger.info("[CheckID] Database connection test successful")
            else:
                if logger:
                    logger.warning("[CheckID] Database connection test failed")
        except Exception as db_error:
            if logger:
                logger.error(f"[CheckID] Database test error: {db_error}")
        
        if logger:
            logger.info("[CheckID] Plugin setup completed successfully")
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[CheckID] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup function untuk plugin unloading"""
    global client, env, logger
    try:
        if logger:
            logger.info("[CheckID] Plugin cleanup initiated")
        client = None
        env = None
        if logger:
            logger.info("[CheckID] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[CheckID] Cleanup error: {e}")

# Export functions untuk backward compatibility
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'id_handler']