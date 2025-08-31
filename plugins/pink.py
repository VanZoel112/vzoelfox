"""
Pink Plugin for Vzoel Assistant - FIXED & ENHANCED VERSION
Fitur: Respon PING minimalis dengan 2 baris, premium emoji independent (tanpa assetjson), font fallback, owner check
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.3.0 - Database compatibility support
"""

import sqlite3
import os
import logging
from datetime import datetime
from telethon import events, types

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('pink')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

# Plugin Info
PLUGIN_INFO = {
    "name": "pink",
    "version": "2.3.0",
    "description": "PING minimalis dengan premium emoji independent, owner check, centralized database logging",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".pink"],
    "features": ["minimal ping", "independent premium emoji", "owner check", "centralized database", "premium entity generator"]
}

# Global variables
env = None
client = None
logger = None
DB_FILE = "plugins/pink.db"

# Independent Premium Emoji Mapping (UTF-16 validated)
PREMIUM_EMOJIS = {
    'main':   {'id': '6156784006194009426', 'char': '🤩'},   # UTF-16 length: 2
    'check':  {'id': '5794353925360457382', 'char': '⚙️'},   # UTF-16 length: 2
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},    # UTF-16 length: 1
    'adder2': {'id': '5793913811471700779', 'char': '✅'},    # UTF-16 length: 1
    'adder3': {'id': '5321412209992033736', 'char': '👽'},    # UTF-16 length: 2
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},   # UTF-16 length: 2
    'adder5': {'id': '5357404860566235955', 'char': '😈'},    # UTF-16 length: 2
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}    # UTF-16 length: 2
}

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
    """Get database connection with compatibility layer"""
    if DB_COMPATIBLE and plugin_db:
        # Initialize table with centralized database
        table_schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            chat_id INTEGER,
            chat_title TEXT,
            response_time REAL,
            created_at TEXT
        """
        plugin_db.create_table('pink_log', table_schema)
        return plugin_db
    else:
        # Fallback to legacy individual database
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
    """Enhanced ping logging with database compatibility"""
    try:
        db = get_db_conn()
        if not db:
            return False
        
        data = {
            'user_id': user_id,
            'username': username,
            'chat_id': chat_id,
            'chat_title': chat_title,
            'response_time': response_time,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.insert('pink_log', data)
        else:
            # Legacy database operations
            db.execute(
                "INSERT INTO pink_log (user_id, username, chat_id, chat_title, response_time, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                tuple(data.values())
            )
            db.commit()
            db.close()
            return True
            
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Logging error: {e}")
        return False

def get_emoji(emoji_type):
    """Get premium emoji dari mapping independent"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def create_premium_entities(text):
    """Generate MessageEntityCustomEmoji list sesuai mapping independent"""
    entities = []
    text_utf16 = text.encode('utf-16-le')
    pos = 0
    
    for key, data in PREMIUM_EMOJIS.items():
        char = data['char']
        emoji_id = int(data['id'])
        
        start = text.find(char)
        while start != -1:
            offset_utf16 = len(text[:start].encode('utf-16-le')) // 2
            length_utf16 = len(char.encode('utf-16-le')) // 2
            entities.append(
                types.MessageEntityCustomEmoji(
                    offset=offset_utf16,
                    length=length_utf16,
                    document_id=emoji_id
                )
            )
            start = text.find(char, start + len(char))
    
    return entities

def convert_font(text, font_type='bold'):
    """Convert font basic (bold & mono)"""
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
        }
        return ''.join([bold_map.get(c, c) for c in text])
    elif font_type == 'mono':
        mono_map = {
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
            'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
            's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
            'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
            'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉'
        }
        return ''.join([mono_map.get(c, c) for c in text])
    return text

async def is_owner_check(user_id):
    """Check if user is owner"""
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

async def safe_send_message(event, text):
    """Send message dengan premium entity support"""
    try:
        if client:
            entities = create_premium_entities(text)
            return await event.reply(text, formatting_entities=entities)
    except Exception as e:
        if logger:
            logger.error(f"Error sending message: {e}")
    return None

async def pink_handler(event):
    """Enhanced pink handler dengan owner check dan response time measurement"""
    import time
    start_time = time.time()
    
    try:
        if not await is_owner_check(event.sender_id):
            return

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
        
        response_time = (time.time() - start_time) * 1000

        line1 = f"{get_emoji('main')} {convert_font('PONG !!!', 'bold')}"
        line2 = f"{get_emoji('adder5')} {convert_font('Vzoel Assistant anti delay', 'mono')} {get_emoji('check')}"
        response = f"{line1}\n{line2}"
        
        await safe_send_message(event, response)
        
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
            await event.reply("🤩 PONG !!!\n😈 Vzoel Assistant anti delay ⚙️")
        except Exception:
            pass

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    global client, logger
    setup_logger()
    try:
        client = telegram_client
        if client:
            client.add_event_handler(pink_handler, events.NewMessage(pattern=r'\.pink'))
            if logger:
                logger.info("[Pink] Event handler registered successfully")
        conn = get_db_conn()
        if conn:
            conn.close()
        return True
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Setup error: {e}")
        return False

def cleanup_plugin():
    global client, logger
    try:
        if logger:
            logger.info("[Pink] Plugin cleanup initiated")
        client = None
        if logger:
            logger.info("[Pink] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[Pink] Cleanup error: {e}")

__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'pink_handler']
