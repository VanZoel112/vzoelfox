#!/usr/bin/env python3
"""
AssetJSON - Universal Plugin Bridge & Asset Manager
File: plugins/assetjson.py
Fungsi: Pusat import dan konfigurasi untuk semua plugin VZOEL ASSISTANT
Author: Vzoel Fox's (Enhanced by Morgan)
Version: v2.0.0 - Universal Bridge Edition

PENGGUNAAN DALAM PLUGIN BARU:
from assetjson import *
# Semua fungsi, emoji, fonts, dan utilitas langsung tersedia
"""

import re
import os
import sys
import json
import time
import logging
import asyncio
import sqlite3
import weakref
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User, Chat, Channel, Message
from telethon.errors import (
    FloodWaitError, ChatWriteForbiddenError, MessageNotModifiedError, 
    PeerIdInvalidError, ChatAdminRequiredError
)
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from collections import defaultdict

# ============= GLOBAL LOGGER SETUP =============
def setup_logger(name):
    """Setup logger untuk plugin"""
    logger = logging.getLogger(f"plugin.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# Global logger instance
logger = setup_logger("assetjson")

# ============= CONFIGURATION & PATHS =============
# Asset file paths
ASSET_FILES = {
    'emoji': 'plugins/assets/emoji_config.json',
    'fonts': 'plugins/assets/fonts_config.json', 
    'settings': 'plugins/assets/bot_settings.json',
    'blacklist': 'plugins/assets/gcast_blacklist.json',
    'statistics': 'plugins/assets/bot_statistics.json',
    'plugin_config': 'plugins/assets/plugin_configs.json'
}

# Database files
DATABASE_FILES = {
    'main': 'vzoel_assistant.db',
    'plugins': 'plugins/assets/plugins.db',
    'cache': 'plugins/assets/cache.db'
}

# ============= PREMIUM EMOJI CONFIGURATION =============
# Data yang sudah divalidasi dan fix dari main.py
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

# ============= UNICODE FONTS CONFIGURATION =============
FONTS = {
    'bold': {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
        'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
        's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
        'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
        'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    },
    'mono': {
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
        'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
        's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
        'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
        'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
        '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
    },
    'italic': {
        'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪',
        'j': '𝘫', 'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳',
        's': '𝘴', 't': '𝘵', 'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻',
        'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐',
        'J': '𝘑', 'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙',
        'S': '𝘚', 'T': '𝘛', 'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡'
    }
}

# ============= GLOBAL CACHE & STATE =============
# Cache untuk performance
_emoji_cache = {}
_font_cache = {}
_config_cache = {}
_premium_status = None
_command_prefix = None
_blacklisted_chats = set()
_plugin_configs = {}

# Statistics tracking
_stats = {
    'plugin_loads': 0,
    'asset_accesses': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'errors_handled': 0
}

# Rate limiting per plugin
_rate_limiters = defaultdict(lambda: {'last_request': 0, 'request_count': 0})
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 100

# ============= CORE UTILITY FUNCTIONS =============

def ensure_assets_directory():
    """Pastikan semua directory assets exists"""
    directories = [
        'plugins/assets',
        'plugins/cache', 
        'plugins/configs'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def get_client():
    """Get client reference dengan error handling"""
    try:
        # Coba ambil dari global scope
        if 'client' in globals():
            return globals()['client']
        
        # Coba ambil dari __main__
        import __main__
        if hasattr(__main__, 'client'):
            return __main__.client
            
        # Coba ambil dari sys.modules
        for module_name, module in sys.modules.items():
            if hasattr(module, 'client') and hasattr(module.client, 'get_me'):
                return module.client
        
        logger.warning("Client reference not found")
        return None
    except Exception as e:
        logger.error(f"Error getting client: {e}")
        return None

# ============= CONFIGURATION MANAGEMENT =============

def load_all_configs():
    """Load semua konfigurasi dari file"""
    global _premium_status, _command_prefix, _blacklisted_chats, _plugin_configs
    
    ensure_assets_directory()
    
    try:
        # Load emoji config
        if os.path.exists(ASSET_FILES['emoji']):
            with open(ASSET_FILES['emoji'], 'r') as f:
                data = json.load(f)
                if 'premium_emojis' in data:
                    PREMIUM_EMOJIS.update(data['premium_emojis'])
                _premium_status = data.get('premium_status', False)
        
        # Load settings
        if os.path.exists(ASSET_FILES['settings']):
            with open(ASSET_FILES['settings'], 'r') as f:
                data = json.load(f)
                _command_prefix = data.get('command_prefix', '.')
        
        # Load blacklist
        if os.path.exists(ASSET_FILES['blacklist']):
            with open(ASSET_FILES['blacklist'], 'r') as f:
                data = json.load(f)
                _blacklisted_chats = set(data.get('blacklisted_chats', []))
        
        # Load plugin configs
        if os.path.exists(ASSET_FILES['plugin_config']):
            with open(ASSET_FILES['plugin_config'], 'r') as f:
                _plugin_configs = json.load(f)
        
        logger.info("All configurations loaded successfully")
        
    except Exception as e:
        logger.error(f"Error loading configurations: {e}")

def save_all_configs():
    """Save semua konfigurasi ke file"""
    ensure_assets_directory()
    
    try:
        # Save emoji config
        emoji_data = {
            'premium_emojis': PREMIUM_EMOJIS,
            'premium_status': _premium_status,
            'last_updated': datetime.now().isoformat(),
            'version': 'v2.0.0'
        }
        with open(ASSET_FILES['emoji'], 'w') as f:
            json.dump(emoji_data, f, indent=2)
        
        # Save settings
        settings_data = {
            'command_prefix': _command_prefix or '.',
            'last_updated': datetime.now().isoformat(),
            'stats': _stats
        }
        with open(ASSET_FILES['settings'], 'w') as f:
            json.dump(settings_data, f, indent=2)
        
        # Save blacklist
        blacklist_data = {
            'blacklisted_chats': list(_blacklisted_chats),
            'last_updated': datetime.now().isoformat(),
            'total': len(_blacklisted_chats)
        }
        with open(ASSET_FILES['blacklist'], 'w') as f:
            json.dump(blacklist_data, f, indent=2)
        
        # Save plugin configs
        with open(ASSET_FILES['plugin_config'], 'w') as f:
            json.dump(_plugin_configs, f, indent=2)
        
        logger.info("All configurations saved successfully")
        
    except Exception as e:
        logger.error(f"Error saving configurations: {e}")

# ============= PREMIUM EMOJI FUNCTIONS =============

def get_emoji(emoji_type: str) -> str:
    """Get premium emoji character dengan caching"""
    _stats['asset_accesses'] += 1
    
    if emoji_type in _emoji_cache:
        _stats['cache_hits'] += 1
        return _emoji_cache[emoji_type]
    
    _stats['cache_misses'] += 1
    
    if emoji_type in PREMIUM_EMOJIS:
        char = PREMIUM_EMOJIS[emoji_type]['char']
        _emoji_cache[emoji_type] = char
        return char
    
    # Fallback emoji
    fallback = '🤩'
    _emoji_cache[emoji_type] = fallback
    return fallback

def get_emoji_id(emoji_type: str) -> str:
    """Get premium emoji document ID"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['id']
    return ''

def create_premium_entities(text: str) -> List[MessageEntityCustomEmoji]:
    """
    Create premium emoji entities - FIXED VERSION dari main.py
    """
    entities = []
    
    if not text or not _premium_status:
        return entities
    
    try:
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        # FIXED: Proper UTF-16 length calculation
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
                        
                    except Exception as e:
                        logger.error(f"Error creating entity for {emoji_type}: {e}")
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
        
    except Exception as e:
        logger.error(f"Error in create_premium_entities: {e}")
        return []

# ============= FONT FUNCTIONS =============

def convert_font(text: str, font_type: str = 'bold') -> str:
    """Convert text to Unicode fonts dengan caching"""
    _stats['asset_accesses'] += 1
    
    cache_key = f"{font_type}_{hash(text)}"
    if cache_key in _font_cache:
        _stats['cache_hits'] += 1
        return _font_cache[cache_key]
    
    _stats['cache_misses'] += 1
    
    if font_type not in FONTS:
        _font_cache[cache_key] = text
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    
    _font_cache[cache_key] = result
    return result

def get_available_fonts() -> List[str]:
    """Get list of available font types"""
    return list(FONTS.keys())

# ============= MESSAGE FUNCTIONS =============

async def safe_send_with_entities(event_or_client, text: str, use_premium: bool = True):
    """
    Universal function untuk send message dengan premium entities
    Compatible dengan event.reply() dan client.send_message()
    """
    try:
        if use_premium and _premium_status:
            entities = create_premium_entities(text)
            if entities:
                if hasattr(event_or_client, 'reply'):
                    # Event object
                    return await event_or_client.reply(text, formatting_entities=entities)
                else:
                    # Client object - requires chat_id
                    logger.warning("safe_send_with_entities: client mode requires chat_id parameter")
                    return None
        
        # Fallback to normal send
        if hasattr(event_or_client, 'reply'):
            return await event_or_client.reply(text)
        else:
            logger.warning("safe_send_with_entities: cannot send without event context")
            return None
            
    except Exception as e:
        logger.error(f"Error in safe_send_with_entities: {e}")
        # Final fallback
        try:
            if hasattr(event_or_client, 'reply'):
                return await event_or_client.reply(text)
        except Exception as e2:
            logger.error(f"Fallback send failed: {e2}")
            return None

async def safe_edit_with_entities(message, text: str, use_premium: bool = True):
    """
    Safe message edit dengan premium entity support - FIXED VERSION
    """
    try:
        if use_premium and _premium_status:
            entities = create_premium_entities(text)
            if entities:
                await message.edit(text, formatting_entities=entities)
                return
        
        # Fallback to normal edit
        await message.edit(text)
        
    except MessageNotModifiedError:
        # Message unchanged, skip
        pass
    except Exception as e:
        error_str = str(e).lower()
        if any(phrase in error_str for phrase in ["can't parse entities", "bad request", "invalid entities"]):
            # Try without entities
            try:
                await message.edit(text)
                logger.warning(f"Edited without entities due to parsing error: {e}")
            except Exception as e2:
                logger.error(f"Fallback edit failed: {e2}")
        else:
            logger.error(f"Error editing message: {e}")

# ============= USER & PERMISSION FUNCTIONS =============

async def is_owner(user_id: int) -> bool:
    """Check if user is bot owner"""
    try:
        # Check environment variable first
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        # Fallback to client.get_me()
        client = get_client()
        if client:
            me = await client.get_me()
            return user_id == me.id
        
        return False
    except Exception as e:
        logger.error(f"Error checking owner: {e}")
        return False

async def get_user_info(event, user_input: Optional[str] = None) -> Optional[User]:
    """Enhanced user info retrieval"""
    try:
        client = get_client()
        if not client:
            return None
        
        if event.is_reply and not user_input:
            reply_msg = await event.get_reply_message()
            return await client.get_entity(reply_msg.sender_id)
        elif user_input:
            user_input = user_input.strip()
            if user_input.isdigit():
                return await client.get_entity(int(user_input))
            else:
                username = user_input.lstrip('@')
                return await client.get_entity(username)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None

# ============= RATE LIMITING =============

async def apply_rate_limit(plugin_name: str, operation: str = "default") -> bool:
    """Apply rate limiting per plugin"""
    key = f"{plugin_name}_{operation}"
    current_time = time.time()
    limiter = _rate_limiters[key]
    
    # Reset counter if window passed
    if current_time - limiter['last_request'] > RATE_LIMIT_WINDOW:
        limiter['request_count'] = 0
        limiter['last_request'] = current_time
    
    # Check rate limit
    if limiter['request_count'] >= RATE_LIMIT_MAX_REQUESTS:
        wait_time = RATE_LIMIT_WINDOW - (current_time - limiter['last_request'])
        if wait_time > 0:
            logger.warning(f"Rate limit hit for {key}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            limiter['request_count'] = 0
            limiter['last_request'] = time.time()
    
    limiter['request_count'] += 1
    return True

# ============= DATABASE FUNCTIONS =============

def get_db_connection(db_name: str = 'main') -> sqlite3.Connection:
    """Get database connection dengan error handling"""
    try:
        db_file = DATABASE_FILES.get(db_name, DATABASE_FILES['main'])
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database {db_name}: {e}")
        raise

def save_plugin_data(plugin_name: str, data: Dict) -> bool:
    """Save plugin-specific data to database"""
    try:
        conn = get_db_connection('plugins')
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugin_data (
                plugin_name TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                last_updated REAL NOT NULL
            )
        ''')
        
        # Insert or update data
        cursor.execute('''
            INSERT OR REPLACE INTO plugin_data (plugin_name, data_json, last_updated)
            VALUES (?, ?, ?)
        ''', (plugin_name, json.dumps(data), time.time()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error saving plugin data for {plugin_name}: {e}")
        return False

def load_plugin_data(plugin_name: str) -> Dict:
    """Load plugin-specific data from database"""
    try:
        conn = get_db_connection('plugins')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data_json FROM plugin_data WHERE plugin_name = ?
        ''', (plugin_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return {}
        
    except Exception as e:
        logger.error(f"Error loading plugin data for {plugin_name}: {e}")
        return {}

# ============= CONFIGURATION FUNCTIONS =============

def get_prefix() -> str:
    """Get command prefix"""
    global _command_prefix
    if _command_prefix:
        return _command_prefix
    
    # Try from environment
    _command_prefix = os.getenv("COMMAND_PREFIX", ".")
    return _command_prefix

def get_premium_status() -> bool:
    """Get premium status"""
    return _premium_status or False

def get_blacklist() -> set:
    """Get blacklisted chat IDs"""
    return _blacklisted_chats.copy()

def add_to_blacklist(chat_id: int) -> bool:
    """Add chat to blacklist"""
    try:
        _blacklisted_chats.add(chat_id)
        save_all_configs()
        return True
    except Exception as e:
        logger.error(f"Error adding to blacklist: {e}")
        return False

def remove_from_blacklist(chat_id: int) -> bool:
    """Remove chat from blacklist"""
    try:
        _blacklisted_chats.discard(chat_id)
        save_all_configs()
        return True
    except Exception as e:
        logger.error(f"Error removing from blacklist: {e}")
        return False

# ============= PLUGIN CONFIGURATION =============

def get_plugin_config(plugin_name: str) -> Dict:
    """Get configuration for specific plugin"""
    return _plugin_configs.get(plugin_name, {})

def set_plugin_config(plugin_name: str, config: Dict) -> bool:
    """Set configuration for specific plugin"""
    try:
        _plugin_configs[plugin_name] = config
        save_all_configs()
        return True
    except Exception as e:
        logger.error(f"Error setting plugin config for {plugin_name}: {e}")
        return False

def update_plugin_config(plugin_name: str, updates: Dict) -> bool:
    """Update plugin configuration"""
    try:
        if plugin_name not in _plugin_configs:
            _plugin_configs[plugin_name] = {}
        
        _plugin_configs[plugin_name].update(updates)
        save_all_configs()
        return True
    except Exception as e:
        logger.error(f"Error updating plugin config for {plugin_name}: {e}")
        return False

# ============= STATISTICS & MONITORING =============

def get_asset_stats() -> Dict:
    """Get asset system statistics"""
    return {
        'stats': _stats.copy(),
        'cache_info': {
            'emoji_cache_size': len(_emoji_cache),
            'font_cache_size': len(_font_cache),
            'config_cache_size': len(_config_cache)
        },
        'config_info': {
            'premium_emojis_count': len(PREMIUM_EMOJIS),
            'fonts_count': len(FONTS),
            'blacklisted_chats': len(_blacklisted_chats),
            'plugin_configs': len(_plugin_configs)
        }
    }

def clear_caches():
    """Clear all caches"""
    global _emoji_cache, _font_cache, _config_cache
    _emoji_cache.clear()
    _font_cache.clear()
    _config_cache.clear()
    logger.info("All caches cleared")

# ============= ANIMATION & UI HELPERS =============

async def animate_text(message, texts: List[str], delay: float = 1.5, use_premium: bool = True):
    """Animate text with premium emoji support"""
    for i, text in enumerate(texts):
        try:
            await safe_edit_with_entities(message, text, use_premium)
            if i < len(texts) - 1:
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Animation error at step {i+1}: {e}")
            if i < len(texts) - 1:
                await asyncio.sleep(delay * 0.5)

def create_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Create text progress bar"""
    if total == 0:
        return f"[{'█' * width}] 0%"
    
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = int(progress * 100)
    
    return f"[{bar}] {percentage}%"

# ============= COMMAND HANDLERS - ASSET MANAGEMENT =============

@client.on(events.NewMessage(pattern=r'\.assetinfo'))
async def asset_info_handler(event):
    """Command untuk melihat informasi lengkap asset system"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        stats = get_asset_stats()
        
        info_text = f"""
{get_emoji('main')} {convert_font('ASSET SYSTEM INFO', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('SYSTEM STATISTICS', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Access Stats:', 'bold')}
{get_emoji('check')} Asset Accesses: `{stats['stats']['asset_accesses']}`
{get_emoji('check')} Cache Hits: `{stats['stats']['cache_hits']}`
{get_emoji('check')} Cache Misses: `{stats['stats']['cache_misses']}`
{get_emoji('check')} Plugin Loads: `{stats['stats']['plugin_loads']}`
{get_emoji('check')} Errors Handled: `{stats['stats']['errors_handled']}`

{get_emoji('adder2')} {convert_font('Cache Status:', 'bold')}
{get_emoji('check')} Emoji Cache: `{stats['cache_info']['emoji_cache_size']}` items
{get_emoji('check')} Font Cache: `{stats['cache_info']['font_cache_size']}` items
{get_emoji('check')} Config Cache: `{stats['cache_info']['config_cache_size']}` items

{get_emoji('adder3')} {convert_font('Configuration:', 'bold')}
{get_emoji('check')} Premium Emojis: `{stats['config_info']['premium_emojis_count']}`
{get_emoji('check')} Font Types: `{stats['config_info']['fonts_count']}`
{get_emoji('check')} Blacklisted Chats: `{stats['config_info']['blacklisted_chats']}`
{get_emoji('check')} Plugin Configs: `{stats['config_info']['plugin_configs']}`

{get_emoji('adder4')} {convert_font('System Status:', 'bold')}
{get_emoji('check')} Premium: {'Active' if get_premium_status() else 'Standard'}
{get_emoji('check')} Prefix: `{get_prefix()}`
{get_emoji('check')} Assets Bridge: `v2.0.0`

{get_emoji('main')} {convert_font('AssetJSON Bridge Online!', 'bold')}
        """.strip()
        
        await safe_send_with_entities(event, info_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"❌ {convert_font('Asset Info Error:', 'bold')} {str(e)}")

@client.on(events.NewMessage(pattern=r'\.clearcache'))
async def clear_cache_handler(event):
    """Command untuk clear semua cache"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        old_stats = get_asset_stats()
        clear_caches()
        
        clear_text = f"""
{get_emoji('main')} {convert_font('CACHE CLEARED', 'mono')}

{get_emoji('check')} {convert_font('Cleared Caches:', 'bold')}
{get_emoji('adder1')} Emoji Cache: `{old_stats['cache_info']['emoji_cache_size']}` items
{get_emoji('adder1')} Font Cache: `{old_stats['cache_info']['font_cache_size']}` items
{get_emoji('adder1')} Config Cache: `{old_stats['cache_info']['config_cache_size']}` items

{get_emoji('adder2')} {convert_font('Cache will rebuild automatically on next access', 'bold')}
        """.strip()
        
        await safe_send_with_entities(event, clear_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"❌ {convert_font('Clear Cache Error:', 'bold')} {str(e)}")

@client.on(events.NewMessage(pattern=r'\.saveconfigs'))
async def save_configs_handler(event):
    """Command untuk save semua konfigurasi"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        save_all_configs()
        
        save_text = f"""
{get_emoji('check')} {convert_font('CONFIGURATIONS SAVED', 'mono')}

{get_emoji('main')} {convert_font('Saved Files:', 'bold')}
{get_emoji('adder1')} Emoji Config: `{ASSET_FILES['emoji']}`
{get_emoji('adder1')} Settings: `{ASSET_FILES['settings']}`
{get_emoji('adder1')} Blacklist: `{ASSET_FILES['blacklist']}`
{get_emoji('adder1')} Plugin Configs: `{ASSET_FILES['plugin_config']}`

{get_emoji('adder2')} {convert_font('All configurations saved successfully!', 'bold')}
        """.strip()
        
        await safe_send_with_entities(event, save_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"❌ {convert_font('Save Config Error:', 'bold')} {str(e)}")

# ============= AUTO-INITIALIZATION =============

def auto_initialize():
    """Auto-initialize asset system saat plugin dimuat"""
    try:
        global _stats
        _stats['plugin_loads'] += 1
        
        logger.info("🔄 Auto-initializing AssetJSON Bridge v2.0.0...")
        
        # Load all configurations
        load_all_configs()
        
        # Extract assets from main if available
        extract_from_main_module()
        
        # Ensure directories exist
        ensure_assets_directory()
        
        logger.info("✅ AssetJSON Bridge initialized successfully")
        logger.info(f"📊 Premium Status: {get_premium_status()}")
        logger.info(f"🔧 Command Prefix: {get_prefix()}")
        logger.info(f"📝 Blacklisted Chats: {len(_blacklisted_chats)}")
        
    except Exception as e:
        logger.error(f"⚠️ AssetJSON auto-initialization error: {e}")
        _stats['errors_handled'] += 1

def extract_from_main_module():
    """Extract assets dari main module (enhanced version)"""
    try:
        global _premium_status, _command_prefix
        
        # Try to get main module
        main_module = None
        for name, module in sys.modules.items():
            if hasattr(module, 'PREMIUM_EMOJIS') and hasattr(module, 'FONTS'):
                main_module = module
                break
        
        if not main_module:
            import __main__
            main_module = __main__
        
        if main_module:
            # Extract premium emojis
            if hasattr(main_module, 'PREMIUM_EMOJIS'):
                main_emojis = getattr(main_module, 'PREMIUM_EMOJIS', {})
                PREMIUM_EMOJIS.update(main_emojis)
                logger.info(f"Extracted {len(main_emojis)} premium emojis from main")
            
            # Extract fonts
            if hasattr(main_module, 'FONTS'):
                main_fonts = getattr(main_module, 'FONTS', {})
                FONTS.update(main_fonts)
                logger.info(f"Extracted {len(main_fonts)} font types from main")
            
            # Extract premium status
            if hasattr(main_module, 'premium_status'):
                _premium_status = getattr(main_module, 'premium_status', False)
            
            # Extract command prefix
            if hasattr(main_module, 'COMMAND_PREFIX'):
                _command_prefix = getattr(main_module, 'COMMAND_PREFIX', '.')
            
            # Extract blacklist if available
            if hasattr(main_module, 'blacklisted_chats'):
                main_blacklist = getattr(main_module, 'blacklisted_chats', set())
                _blacklisted_chats.update(main_blacklist)
            
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error extracting from main module: {e}")
        return False

# ============= PLUGIN INFO & EXPORTS =============

# Plugin metadata
PLUGIN_INFO = {
    'name': 'assetjson',
    'version': '2.0.0',
    'description': 'Universal Asset Bridge & Configuration Manager untuk semua plugin VZOEL ASSISTANT',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['assetinfo', 'clearcache', 'saveconfigs'],
    'exports': [
        # Core functions
        'get_emoji', 'get_emoji_id', 'convert_font', 'create_premium_entities',
        
        # Message functions
        'safe_send_with_entities', 'safe_edit_with_entities', 'animate_text',
        
        # User functions
        'is_owner', 'get_user_info',
        
        # Configuration functions  
        'get_prefix', 'get_premium_status', 'get_blacklist',
        'add_to_blacklist', 'remove_from_blacklist',
        
        # Plugin functions
        'get_plugin_config', 'set_plugin_config', 'update_plugin_config',
        'save_plugin_data', 'load_plugin_data',
        
        # Utility functions
        'apply_rate_limit', 'get_db_connection', 'create_progress_bar',
        'get_asset_stats', 'clear_caches',
        
        # Data access
        'PREMIUM_EMOJIS', 'FONTS', 'ASSET_FILES', 'DATABASE_FILES'
    ],
    'requirements': ['telethon', 'asyncio', 'sqlite3', 'json'],
    'compatibility': 'VZOEL ASSISTANT v0.1.0.75+'
}

def get_plugin_info():
    """Return plugin information"""
    return PLUGIN_INFO

# ============= EXPORTS FOR PLUGIN IMPORTS =============

# Export semua fungsi yang dibutuhkan plugin lain
__all__ = [
    # Core emoji & font functions
    'get_emoji', 'get_emoji_id', 'convert_font', 'create_premium_entities',
    'get_available_fonts',
    
    # Message handling functions
    'safe_send_with_entities', 'safe_edit_with_entities', 'animate_text',
    
    # User & permission functions
    'is_owner', 'get_user_info',
    
    # Configuration functions
    'get_prefix', 'get_premium_status', 'get_blacklist',
    'add_to_blacklist', 'remove_from_blacklist',
    
    # Plugin configuration functions
    'get_plugin_config', 'set_plugin_config', 'update_plugin_config',
    'save_plugin_data', 'load_plugin_data',
    
    # Utility functions
    'apply_rate_limit', 'get_db_connection', 'create_progress_bar',
    'get_asset_stats', 'clear_caches', 'ensure_assets_directory',
    
    # Data constants
    'PREMIUM_EMOJIS', 'FONTS', 'ASSET_FILES', 'DATABASE_FILES',
    
    # Logger
    'logger', 'setup_logger',
    
    # Client access
    'get_client'
]

# Auto-initialize saat plugin dimuat
auto_initialize()

print("✅ AssetJSON Universal Bridge v2.0.0 loaded successfully!")
print(f"📊 Available exports: {len(__all__)} functions & objects")
print(f"🔧 Premium Status: {get_premium_status()}")
print(f"📝 Ready to serve {len(_plugin_configs)} plugin configurations")

# ============= USAGE EXAMPLES FOR NEW PLUGINS =============

"""
CARA MENGGUNAKAN ASSETJSON DALAM PLUGIN BARU:

1. IMPORT SEDERHANA:
```python
from assetjson import *

# Semua fungsi langsung tersedia:
@client.on(events.NewMessage(pattern=r'\.mycommand'))
async def my_command(event):
    if not await is_owner(event.sender_id):
        return
    
    text = f"{get_emoji('main')} {convert_font('Hello World!', 'bold')}"
    await safe_send_with_entities(event, text)
```

2. KONFIGURASI PLUGIN:
```python
from assetjson import *

# Save plugin config
set_plugin_config('myplugin', {
    'setting1': 'value1',
    'enabled': True
})

# Load plugin config
config = get_plugin_config('myplugin')
enabled = config.get('enabled', False)
```

3. DATABASE OPERATIONS:
```python
from assetjson import *

# Save plugin data
save_plugin_data('myplugin', {
    'user_data': {...},
    'last_run': time.time()
})

# Load plugin data
data = load_plugin_data('myplugin')
```

4. RATE LIMITING:
```python
from assetjson import *

@client.on(events.NewMessage(pattern=r'\.heavycommand'))
async def heavy_command(event):
    await apply_rate_limit('myplugin', 'heavy_operation')
    # Your heavy operation here
```

5. FULL EXAMPLE PLUGIN:
```python
#!/usr/bin/env python3
from assetjson import *

@client.on(events.NewMessage(pattern=r'\.example'))
async def example_handler(event):
    if not await is_owner(event.sender_id):
        return
    
    # Apply rate limiting
    await apply_rate_limit('example_plugin')
    
    # Create message with premium emojis
    text = f'''
{get_emoji('main')} {convert_font('EXAMPLE PLUGIN', 'mono')}

{get_emoji('check')} {convert_font('Status:', 'bold')} Active
{get_emoji('adder1')} {convert_font('User:', 'bold')} {event.sender_id}
{get_emoji('adder2')} {convert_font('Prefix:', 'bold')} {get_prefix()}
    '''.strip()
    
    # Send with premium entities
    await safe_send_with_entities(event, text)

# Plugin info
PLUGIN_INFO = {
    'name': 'example',
    'version': '1.0.0',
    'description': 'Example plugin using AssetJSON',
    'author': 'Your Name',
    'commands': ['example']
}
```

KEUNTUNGAN MENGGUNAKAN ASSETJSON:
✅ Tidak perlu copy-paste kode emoji/font handling
✅ Automatic premium emoji support
✅ Built-in error handling & fallbacks
✅ Database integration ready
✅ Rate limiting included
✅ Configuration management
✅ Consistent UI/UX across all plugins
✅ Auto-caching untuk performance
"""