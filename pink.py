"""
Pink Plugin for Vzoel Assistant - FIXED & ENHANCED VERSION
Fitur: Respon PING minimalis dengan 2 baris, emoji premium dari assetjson, font dari assetjson, owner check
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Fixed compatibility and added proper integrations
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from telethon import events

# Plugin Info
PLUGIN_INFO = {
    "name": "pink",
    "version": "2.0.0",
    "description": "PING minimalis dengan assetjson integration, owner check, premium emoji support",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".pink"],
    "features": ["minimal ping", "assetjson integration", "owner check", "database logging", "premium emoji"]
}

# Global variables
env = None
client = None
logger = None
DB_FILE = "plugins/pink.db"

def setup_logger():
    """Setup dedicated logger untuk plugin"""
    global logger
    logger = logging.getLogger("pink_plugin")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

def get_db_conn():
    """Get database connection dengan enhanced error handling"""
    try:
        # Try assetjson environment first
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if logger:
            logger.warning(f"[Pink] AssetJSON DB failed: {e}")
    
    # Fallback to local SQLite
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pink_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                chat_id INTEGER,
                chat_title TEXT,
                response_time REAL,
                created_at TEXT
            )
        """)
        conn.commit()
        return conn
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Local SQLite error: {e}")
    return None

def log_ping_usage(user_id, username, chat_id, chat_title, response_time):
    """Enhanced ping logging with more details"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        conn.execute(
            "INSERT INTO pink_log (user_id, username, chat_id, chat_title, response_time, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, chat_id, chat_title, response_time, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Logging error: {e}")
        return False

def get_emoji(emoji_type):
    """Get premium emoji dengan fallback ke assetjson"""
    try:
        if env and 'get_emoji' in env:
            return env['get_emoji'](emoji_type)
    except Exception:
        pass
    
    # Fallback emojis (sesuai dengan PREMIUM_EMOJIS dari main.py)
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
    """Convert font dengan fallback ke assetjson"""
    try:
        if env and 'convert_font' in env:
            return env['convert_font'](text, font_type)
    except Exception:
        pass
    
    # Fallback font conversion (basic bold)
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
    elif font_type == 'mono':
        mono_map = {
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
            'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
            's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
            'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
            'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉'
        }
        result = ""
        for char in text:
            result += mono_map.get(char, char)
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

async def pink_handler(event):
    """Enhanced pink handler dengan owner check dan response time measurement"""
    import time
    start_time = time.time()
    
    try:
        # Owner check
        if not await is_owner_check(event.sender_id):
            return
        
        # Get user and chat info
        try:
            user = await event.get_sender()
            chat = await event.get_chat()
            
            user_id = getattr(user, 'id', event.sender_id)
            username = getattr(user, 'username', None)
            chat_id = getattr(chat, 'id', event.chat_id if hasattr(event, 'chat_id') else None)
            chat_title = getattr(chat, 'title', 'Private Chat')
        except Exception as e:
            if logger:
                logger.warning(f"[Pink] Error getting user/chat info: {e}")
            user_id = event.sender_id
            username = None
            chat_id = None
            chat_title = 'Unknown'
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
        
        # Create response dengan premium emoji dan font support
        line1 = f"{get_emoji('main')} {convert_font('PONG !!!', 'bold')}"
        line2 = f"{get_emoji('adder5')} {convert_font('Vzoel Assistant anti delay', 'mono')} {get_emoji('check')}"
        response = f"{line1}\n{line2}"
        
        # Send response
        await safe_send_message(event, response)
        
        # Log usage
        log_success = log_ping_usage(user_id, username, chat_id, chat_title, response_time)
        if logger:
            if log_success:
                logger.info(f"[Pink] Ping logged: {user_id} in {chat_title} ({response_time:.2f}ms)")
            else:
                logger.warning(f"[Pink] Failed to log ping for {user_id}")
        
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Handler error: {e}")
        try:
            # Fallback response
            await event.reply("🤩 PONG !!!\n😈 Vzoel Assistant anti delay ⚙️")
        except Exception:
            pass  # Avoid infinite error loops

def get_plugin_info():
    """Return plugin information"""
    return PLUGIN_INFO

def setup(telegram_client):
    """
    Setup function untuk plugin loader compatibility
    
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
                logger.info("[Pink] AssetJSON environment loaded successfully")
        except ImportError:
            if logger:
                logger.warning("[Pink] AssetJSON not available, using fallback functions")
            env = None
        except Exception as e:
            if logger:
                logger.error(f"[Pink] Error loading AssetJSON environment: {e}")
            env = None
        
        # Register event handler
        if client:
            client.add_event_handler(pink_handler, events.NewMessage(pattern=r'\.pink'))
            if logger:
                logger.info("[Pink] Event handler registered successfully")
        else:
            if logger:
                logger.error("[Pink] No client provided to setup")
            return False
        
        # Test database connection
        try:
            conn = get_db_conn()
            if conn:
                conn.close()
                if logger:
                    logger.info("[Pink] Database connection test successful")
            else:
                if logger:
                    logger.warning("[Pink] Database connection test failed")
        except Exception as db_error:
            if logger:
                logger.error(f"[Pink] Database test error: {db_error}")
        
        if logger:
            logger.info("[Pink] Plugin setup completed successfully")
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup function untuk plugin unloading"""
    global client, env, logger
    try:
        if logger:
            logger.info("[Pink] Plugin cleanup initiated")
        client = None
        env = None
        if logger:
            logger.info("[Pink] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'pink_handler']