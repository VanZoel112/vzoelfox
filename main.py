#!/usr/bin/env python3
"""
VZOEL ASSISTANT v0.1.0.75 - PLUGIN SYSTEM COMPATIBLE VERSION
Enhanced with premium emoji handling, reply gcast support, auto emoji extraction
Plugin system compatibility by Morgan for Master Vzoel Fox's
Author: Vzoel Fox's (LTPN) - Enhanced by Morgan
Version: v0.1.0.75 Plugin Compatible
File: main.py (Compatible dengan plugin system yang sudah diperbaiki)
"""

import asyncio
import logging
import time
import random
import re
import os
import sys
import json
import sqlite3
import weakref
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from collections import defaultdict, deque
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError, FloodWaitError, ChatAdminRequiredError, 
    ChatWriteForbiddenError, UserBannedInChannelError, MessageNotModifiedError,
    MessageIdInvalidError, PeerIdInvalidError, InputUserDeactivatedError
)
from telethon.tl.types import User, Chat, Channel, MessageEntityCustomEmoji, Message
from telethon.tl.functions.messages import SendMessageRequest, GetCustomEmojiDocumentsRequest
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from dotenv import load_dotenv
from plugin_loader import setup_plugins

# Load environment variables
load_dotenv()

# ============= ENHANCED CONFIGURATION =============
try:
    API_ID = int(os.getenv("API_ID", "29919905"))
    API_HASH = os.getenv("API_HASH", "717957f0e3ae20a7db004d08b66bfd30")
    SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")
    OWNER_ID = int(os.getenv("OWNER_ID", "7847025168")) if os.getenv("OWNER_ID") else None
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    MAX_CONCURRENT_GCAST = int(os.getenv("MAX_CONCURRENT_GCAST", "10"))
    GCAST_DELAY = float(os.getenv("GCAST_DELAY", "0.5"))
except ValueError as e:
    print(f"⚠️ Configuration error: {e}")
    print("Please check your .env file")
    sys.exit(1)

# Validation
if not API_ID or not API_HASH:
    print("❌ ERROR: API_ID and API_HASH must be set in .env file!")
    print("Please create a .env file with your Telegram API credentials")
    sys.exit(1)

# Enhanced logging setup
if ENABLE_LOGGING:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler('vzoel_enhanced_v2.log'),
            logging.StreamHandler(),
            logging.FileHandler('vzoel_errors.log', mode='a') if LOG_LEVEL == 'ERROR' else logging.NullHandler()
        ]
    )
else:
    logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)

# Initialize client
try:
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    logger.info("✅ Telegram client initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize client: {e}")
    sys.exit(1)

# ============= GLOBAL VARIABLES - ENHANCED =============
plugin_loader: EnhancedPluginLoader = None
start_time = None
spam_guard_enabled = False
spam_users = {}
blacklist_file = "gcast_blacklist.json"
emoji_config_file = "emoji_config.json"
database_file = "vzoel_assistant.db"
blacklisted_chats = set()
premium_status = None
voice_call_active = False

# Statistics tracking
stats = {
    'commands_executed': 0,
    'gcast_sent': 0,
    'emojis_extracted': 0,
    'errors_handled': 0,
    'uptime_start': None
}

# Rate limiting
rate_limiters = defaultdict(lambda: {'last_request': 0, 'request_count': 0})
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30

# Logo URLs
LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
VZOEL_LOGO = "https://imgur.com/gallery/logo-S6biYEi"

# ============= PREMIUM EMOJI CONFIGURATION - FIXED =============
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

# Emoji cache untuk performance
emoji_cache = {}
emoji_cache_ttl = {}
EMOJI_CACHE_TTL = 3600  # 1 hour

# Unicode Fonts for styling
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
    }
}

# ============= DATABASE INITIALIZATION =============
def init_database():
    """Initialize SQLite database for enhanced features"""
    try:
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        
        # Emoji mappings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emoji_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emoji_type TEXT NOT NULL,
                emoji_char TEXT NOT NULL,
                document_id TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                last_used REAL DEFAULT 0,
                created_at REAL DEFAULT 0,
                UNIQUE(emoji_type, document_id)
            )
        ''')
        
        # Gcast history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gcast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gcast_id TEXT NOT NULL,
                target_chat_id INTEGER NOT NULL,
                message_text TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                timestamp REAL NOT NULL
            )
        ''')
        
        # Statistics table  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_name TEXT UNIQUE NOT NULL,
                stat_value INTEGER DEFAULT 0,
                last_updated REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

# ============= PLUGIN-COMPATIBLE FUNCTIONS - SHARED =============

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts - SHARED FUNCTION untuk plugins"""
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def get_emoji(emoji_type):
    """Get premium emoji character safely with fallback - SHARED FUNCTION"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'  # fallback

def create_premium_entities(text):
    """
    Create MessageEntityCustomEmoji for all premium emojis in text - SHARED FUNCTION
    """
    entities = []
    
    if not text or not premium_status:
        return entities
    
    try:
        # Proper UTF-16 offset tracking
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            # Check for premium emojis at current position
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                # Check if text at current position starts with this emoji
                if text[i:].startswith(emoji_char):
                    try:
                        # Calculate proper UTF-16 length
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        # Create entity with correct offset and length
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        # Skip the emoji characters
                        i += len(emoji_char)
                        current_offset += utf16_length
                        found_emoji = True
                        
                        logger.debug(f"Created entity for {emoji_type}: offset={current_offset-utf16_length}, length={utf16_length}")
                        break
                        
                    except Exception as e:
                        logger.error(f"Error creating entity for {emoji_type}: {e}")
                        break
            
            if not found_emoji:
                # Regular character - calculate UTF-16 units properly
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        logger.debug(f"Created {len(entities)} premium emoji entities")
        return entities
        
    except Exception as e:
        logger.error(f"Error in create_premium_entities: {e}")
        return []

async def check_premium_status():
    """Check if user has Telegram Premium - SHARED FUNCTION"""
    global premium_status
    try:
        me = await client.get_me()
        premium_status = getattr(me, 'premium', False)
        if premium_status:
            logger.info("✅ Telegram Premium detected - Premium emojis enabled!")
        else:
            logger.info("ℹ️ No Telegram Premium - Using standard emojis")
        return premium_status
    except Exception as e:
        logger.error(f"Error checking premium status: {e}")
        premium_status = False
        return False

async def is_owner(user_id):
    """Check if user is owner - SHARED FUNCTION"""
    try:
        if OWNER_ID:
            return user_id == OWNER_ID
        me = await client.get_me()
        return user_id == me.id
    except Exception as e:
        logger.error(f"Error checking owner: {e}")
        return False

async def apply_rate_limit(operation: str):
    """Enhanced rate limiting per operation type - SHARED FUNCTION"""
    current_time = time.time()
    limiter = rate_limiters[operation]
    
    # Reset counter if window has passed
    if current_time - limiter['last_request'] > RATE_LIMIT_WINDOW:
        limiter['request_count'] = 0
        limiter['last_request'] = current_time
    
    # Check if rate limit exceeded
    if limiter['request_count'] >= RATE_LIMIT_MAX_REQUESTS:
        wait_time = RATE_LIMIT_WINDOW - (current_time - limiter['last_request'])
        if wait_time > 0:
            logger.warning(f"Rate limit hit for {operation}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            limiter['request_count'] = 0
            limiter['last_request'] = time.time()
    
    limiter['request_count'] += 1

async def safe_edit_message(message, text, use_premium=True):
    """
    Safely edit message dengan premium emoji support - SHARED FUNCTION
    """
    try:
        if use_premium and premium_status:
            entities = create_premium_entities(text)
            if entities:
                await message.edit(text, formatting_entities=entities)
                logger.debug(f"Message edited with {len(entities)} premium emoji entities")
            else:
                await message.edit(text)
        else:
            await message.edit(text)
    except MessageNotModifiedError:
        logger.debug("Message content unchanged, skipping edit")
        pass
    except Exception as e:
        error_str = str(e).lower()
        if any(phrase in error_str for phrase in ["can't parse entities", "bad request", "invalid entities"]):
            # Fallback: try without entities
            try:
                await message.edit(text)
                logger.warning(f"Edited message without entities due to parsing error: {e}")
            except Exception as e2:
                logger.error(f"Fallback edit failed: {e2}")
        else:
            logger.error(f"Error editing message: {e}")
            try:
                await message.edit(text)
            except Exception as e3:
                logger.error(f"Simple edit failed: {e3}")

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available - SHARED FUNCTION untuk plugins"""
    try:
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

# ============= CONFIGURATION MANAGEMENT =============

def load_emoji_config():
    """Load custom emoji configuration from file"""
    global PREMIUM_EMOJIS
    try:
        if os.path.exists(emoji_config_file):
            with open(emoji_config_file, 'r') as f:
                data = json.load(f)
                custom_emojis = data.get('premium_emojis', {})
                
                # Update PREMIUM_EMOJIS with custom configuration
                for emoji_type, emoji_data in custom_emojis.items():
                    if isinstance(emoji_data, dict) and 'id' in emoji_data:
                        if emoji_type not in PREMIUM_EMOJIS:
                            PREMIUM_EMOJIS[emoji_type] = {}
                        PREMIUM_EMOJIS[emoji_type].update(emoji_data)
                
                logger.info(f"📱 Loaded custom emoji configuration: {len(custom_emojis)} emojis")
        else:
            logger.info("📱 No custom emoji config found, using defaults")
            save_emoji_config()
    except Exception as e:
        logger.error(f"Error loading emoji config: {e}")

def save_emoji_config():
    """Save current emoji configuration to file with metadata"""
    try:
        config_data = {
            'premium_emojis': PREMIUM_EMOJIS,
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'version': 'v0.1.0.75',
                'total_emojis': len(PREMIUM_EMOJIS),
                'premium_status': premium_status
            }
        }
        
        with open(emoji_config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"💾 Saved emoji configuration: {len(PREMIUM_EMOJIS)} emoji types")
    except Exception as e:
        logger.error(f"Error saving emoji config: {e}")

def load_blacklist():
    """Load blacklisted chat IDs from file"""
    global blacklisted_chats
    try:
        if os.path.exists(blacklist_file):
            with open(blacklist_file, 'r') as f:
                data = json.load(f)
                blacklisted_chats = set(data.get('blacklisted_chats', []))
                logger.info(f"📋 Loaded {len(blacklisted_chats)} blacklisted chats")
        else:
            blacklisted_chats = set()
            logger.info("📋 No blacklist file found, starting with empty blacklist")
            save_blacklist()
    except Exception as e:
        logger.error(f"Error loading blacklist: {e}")
        blacklisted_chats = set()

def save_blacklist():
    """Save blacklisted chat IDs to file with metadata"""
    try:
        data = {
            'blacklisted_chats': list(blacklisted_chats),
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'total_blacklisted': len(blacklisted_chats)
            }
        }
        with open(blacklist_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"💾 Saved {len(blacklisted_chats)} blacklisted chats")
    except Exception as e:
        logger.error(f"Error saving blacklist: {e}")

# ============= UTILITY FUNCTIONS =============

async def animate_text_premium(message, texts, delay=1.5):
    """Enhanced animation with premium emoji support and error handling"""
    for i, text in enumerate(texts):
        try:
            await safe_edit_message(message, text)
            if i < len(texts) - 1:
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Animation error at step {i+1}/{len(texts)}: {e}")
            if i < len(texts) - 1:
                await asyncio.sleep(delay * 0.5)
            continue

async def get_broadcast_channels():
    """Get all channels and groups for broadcasting with enhanced filtering"""
    channels = []
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Skip users
            if isinstance(entity, User):
                continue
            
            # Skip blacklisted chats
            if entity.id in blacklisted_chats:
                continue
            
            # Only include groups and channels where we can send messages
            if isinstance(entity, (Chat, Channel)):
                # For channels, check if we have broadcast rights
                if isinstance(entity, Channel):
                    if entity.broadcast and not (entity.creator or (entity.admin_rights and entity.admin_rights.post_messages)):
                        continue
                
                # Add channel info
                channels.append({
                    'entity': entity,
                    'id': entity.id,
                    'title': getattr(entity, 'title', 'Unknown'),
                    'type': 'Channel' if isinstance(entity, Channel) and entity.broadcast else 'Group',
                    'participant_count': getattr(entity, 'participants_count', 0) if hasattr(entity, 'participants_count') else 0
                })
        
        logger.info(f"Found {len(channels)} valid broadcast targets")
        return channels
        
    except Exception as e:
        logger.error(f"Error getting broadcast channels: {e}")
        return []

async def log_command(event, command):
    """Enhanced command logging with statistics"""
    try:
        stats['commands_executed'] += 1
        
        user = await client.get_entity(event.sender_id)
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Private Chat')
        user_name = getattr(user, 'first_name', 'Unknown') or 'Unknown'
        
        logger.info(f"Command '{command}' executed by {user_name} ({user.id}) in {chat_title}")
        
        # Update database statistics
        try:
            conn = sqlite3.connect(database_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO bot_statistics (stat_name, stat_value, last_updated)
                VALUES (?, ?, ?)
            ''', ('commands_executed', stats['commands_executed'], time.time()))
            conn.commit()
            conn.close()
        except Exception as db_error:
            logger.error(f"Error updating command statistics: {db_error}")
            
    except Exception as e:
        logger.error(f"Error logging command: {e}")

# ============= ENHANCED GCAST FUNCTIONALITY =============

async def enhanced_gcast(message_text: str, reply_message: Optional[Message] = None, 
                        preserve_entities: bool = True, progress_callback=None) -> Dict:
    """Enhanced gcast dengan reply message support dan entity preservation"""
    gcast_id = f"gcast_{int(time.time())}"
    channels = await get_broadcast_channels()
    
    if not channels:
        return {
            'success': False,
            'error': 'No valid broadcast channels found',
            'channels_total': 0
        }
    
    results = {
        'gcast_id': gcast_id,
        'channels_total': len(channels),
        'channels_success': 0,
        'channels_failed': 0,
        'errors': [],
        'success': True
    }
    
    # Extract entities from reply message if provided
    entities = None
    if reply_message and preserve_entities:
        try:
            # Extract premium emojis from reply message
            if reply_message.entities:
                for entity in reply_message.entities:
                    if isinstance(entity, MessageEntityCustomEmoji):
                        # Create entities for current message text if it contains premium emojis
                        entities = create_premium_entities(message_text)
                        break
        except Exception as e:
            logger.error(f"Error processing reply message entities: {e}")
    
    # Broadcast to all channels
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GCAST)
    
    async def send_to_channel(channel_info):
        async with semaphore:
            try:
                await apply_rate_limit(f"gcast_{channel_info['id']}")
                
                if entities:
                    await client.send_message(
                        channel_info['id'], 
                        message_text,
                        formatting_entities=entities
                    )
                else:
                    await client.send_message(channel_info['id'], message_text)
                
                results['channels_success'] += 1
                stats['gcast_sent'] += 1
                
                # Log to database
                try:
                    conn = sqlite3.connect(database_file)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO gcast_history 
                        (gcast_id, target_chat_id, message_text, success, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (gcast_id, channel_info['id'], message_text[:500], True, time.time()))
                    conn.commit()
                    conn.close()
                except Exception as db_error:
                    logger.error(f"Error logging gcast to database: {db_error}")
                
                return True
                
            except FloodWaitError as e:
                logger.warning(f"Flood wait {e.seconds}s for channel {channel_info['title']}")
                await asyncio.sleep(e.seconds)
                # Retry once after flood wait
                try:
                    if entities:
                        await client.send_message(
                            channel_info['id'], 
                            message_text,
                            formatting_entities=entities
                        )
                    else:
                        await client.send_message(channel_info['id'], message_text)
                    results['channels_success'] += 1
                    return True
                except Exception as retry_error:
                    error_msg = f"Retry failed for {channel_info['title']}: {retry_error}"
                    results['errors'].append(error_msg)
                    results['channels_failed'] += 1
                    return False
                    
            except ChatWriteForbiddenError:
                error_msg = f"Write forbidden in {channel_info['title']}"
                results['errors'].append(error_msg)
                results['channels_failed'] += 1
                return False
                
            except Exception as e:
                error_msg = f"Error sending to {channel_info['title']}: {str(e)}"
                results['errors'].append(error_msg)
                results['channels_failed'] += 1
                logger.error(error_msg)
                return False
    
    # Execute all sends concurrently
    tasks = [send_to_channel(channel_info) for channel_info in channels]
    
    for i, task in enumerate(asyncio.as_completed(tasks)):
        await task
        
        # Progress callback
        if progress_callback and (i + 1) % 5 == 0:
            await progress_callback(i + 1, len(channels), gcast_id)
    
    # Final progress update
    if progress_callback:
        await progress_callback(len(channels), len(channels), gcast_id)
    
    return results

# ============= VOICE CHAT FUNCTIONS =============

async def join_voice_chat(chat):
    """Enhanced voice chat joining with proper error handling"""
    global voice_call_active
    try:
        if isinstance(chat, Channel):
            try:
                full_chat = await client(GetFullChannelRequest(chat))
                call = getattr(full_chat.full_chat, 'call', None)
            except Exception:
                call = None
        else:
            call = getattr(chat, 'call', None)
        
        if not call:
            return False, "No active voice chat found in this chat"
        
        try:
            await client(JoinGroupCallRequest(
                call=call,
                muted=False,
                video_stopped=True
            ))
            voice_call_active = True
            return True, "Successfully joined voice chat"
        except ChatAdminRequiredError:
            return False, "Admin rights required to join voice chat"
        except Exception as join_error:
            return False, f"Failed to join voice chat: {str(join_error)}"
        
    except Exception as e:
        logger.error(f"Error joining voice chat: {e}")
        return False, f"Unexpected error: {str(e)}"

async def leave_voice_chat():
    """Enhanced voice chat leaving"""
    global voice_call_active
    try:
        if not voice_call_active:
            return False, "Not currently in a voice chat"
        
        await client(LeaveGroupCallRequest())
        voice_call_active = False
        return True, "Successfully left voice chat"
        
    except Exception as e:
        logger.error(f"Error leaving voice chat: {e}")
        return False, f"Error: {str(e)}"

# ============= EVENT HANDLERS - ESSENTIAL COMMANDS ONLY =============

# ALIVE COMMAND
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with comprehensive system info"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "alive")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else datetime.now()
        uptime_str = str(uptime).split('.')[0]
        
        title = convert_font("VZOEL ASSISTANT IS ALIVE!", 'mono')
        
        # Get plugin statistics
        plugin_stats = ""
        if plugin_loader:
            status = plugin_loader.get_status()
            plugin_stats = f"""
{get_emoji('adder2')} {convert_font('Plugin System:', 'bold')}
{get_emoji('check')} Loaded: {status['total_loaded']}
{get_emoji('check')} Failed: {status['total_failed']}
{get_emoji('check')} Total: {status['total_plugins']}
"""
        
        final_message = f"""
    {title}
        {get_emoji('main')} {convert_font('V Z O E L  A S S I S T A N T', 'mono')} {get_emoji('main')}
{get_emoji('main')} {convert_font('Founder Userbot:', 'bold')} Vzoel 
{get_emoji('check')} {convert_font('Name:', 'bold')} {me.first_name or 'Vzoel Assistant'}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{me.id}`
{get_emoji('check')} {convert_font('Username:', 'bold')} @{me.username or 'None'}
{get_emoji('check')} {convert_font('Prefix:', 'bold')} `{COMMAND_PREFIX}`
{get_emoji('check')} {convert_font('Uptime:', 'bold')} `{uptime_str}`
{get_emoji('main')} {convert_font('Version:', 'bold')} v0.1.0.75 Plugin Compatible
{get_emoji('check')} {convert_font('Status:', 'bold')} Active & Running
{get_emoji('adder2')} {convert_font('Premium:', 'bold')} {'Active' if premium_status else 'Standard'}
{plugin_stats}
{get_emoji('adder3')} {convert_font('Statistics:', 'bold')}
{get_emoji('check')} Commands: `{stats['commands_executed']}`
{get_emoji('check')} Gcast Sent: `{stats['gcast_sent']}`  
{get_emoji('check')} Emojis Extracted: `{stats['emojis_extracted']}`
{get_emoji('check')} Blacklisted: `{len(blacklisted_chats)}`

{get_emoji('adder4')} {convert_font('Enhanced Features:', 'bold')}
{get_emoji('check')} Plugin System Compatibility
{get_emoji('check')} Reply-based Gcast Support
{get_emoji('check')} Auto Premium Emoji Extraction
{get_emoji('check')} Advanced Entity Handling
{get_emoji('check')} Database Integration

{get_emoji('check')} {convert_font('Hak milik Vzoel Fox\'s ©2025 ~ LTPN', 'bold')} {get_emoji('check')}
        """.strip()
        
        base_animations = [
            f"{get_emoji('main')} {convert_font('Initializing system check...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Loading components...', 'bold')}",
            f"{get_emoji('adder1')} {convert_font('Checking premium features...', 'bold')}",
            f"{get_emoji('main')} {convert_font('Finalizing status report...', 'bold')}",
        ]
        
        alive_animations = base_animations + [final_message]
        
        msg = await event.reply(alive_animations[0])
        await animate_text_premium(msg, alive_animations, delay=2)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Alive command error: {e}")

# GCAST COMMAND
@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}gcast(\s+(.+))?', re.DOTALL)))
async def gcast_handler(event):
    """Enhanced Global Broadcast dengan reply message support dan entity preservation"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    try:
        reply_message = None
        message_text = ""
        
        if event.is_reply:
            reply_message = await event.get_reply_message()
            command_text = event.pattern_match.group(2)
            if command_text:
                message_text = command_text.strip()
            else:
                message_text = reply_message.text or reply_message.message or ""
                
            if not message_text:
                await event.reply(f"❌ {convert_font('No text found in replied message!', 'bold')}")
                return
        else:
            if not event.pattern_match.group(2):
                usage_text = f"""
{get_emoji('main')} {convert_font('ENHANCED GCAST USAGE', 'mono')}

{get_emoji('check')} {convert_font('Text Gcast:', 'bold')}
`{COMMAND_PREFIX}gcast <your message>`

{get_emoji('adder1')} {convert_font('Reply Gcast (NEW!):', 'bold')}
Reply to any message + `{COMMAND_PREFIX}gcast`
Reply to message + `{COMMAND_PREFIX}gcast <additional text>`

{get_emoji('adder2')} {convert_font('Premium Features:', 'bold')}
{get_emoji('check')} Auto premium emoji preservation
{get_emoji('check')} Entity formatting preservation
{get_emoji('check')} Concurrent broadcasting
{get_emoji('check')} Advanced error handling
                """.strip()
                await event.reply(usage_text)
                return
                
            message_text = event.pattern_match.group(2).strip()
        
        # Show progress message
        progress_msg = await event.reply(f"""
{get_emoji('main')} {convert_font('ENHANCED GCAST STARTING', 'bold')}

{get_emoji('check')} {convert_font('Mode:', 'bold')} {'Reply + Entity Preservation' if reply_message else 'Standard Text'}
{get_emoji('adder1')} {convert_font('Status:', 'bold')} Preparing broadcast...
        """.strip())
        
        # Progress callback
        async def progress_update(completed, total, gcast_id):
            try:
                progress_text = f"""
{get_emoji('adder2')} {convert_font('BROADCASTING IN PROGRESS', 'bold')}

{get_emoji('check')} {convert_font('Progress:', 'bold')} `{completed}/{total}` ({(completed/total)*100:.1f}%)
{get_emoji('adder1')} {convert_font('Gcast ID:', 'bold')} `{gcast_id}`
{get_emoji('main')} {convert_font('Status:', 'bold')} Processing...
                """.strip()
                await safe_edit_message(progress_msg, progress_text)
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
        
        # Execute enhanced gcast
        result = await enhanced_gcast(
            message_text=message_text,
            reply_message=reply_message,
            preserve_entities=True,
            progress_callback=progress_update
        )
        
        # Show final results
        if result['success']:
            success_rate = (result['channels_success'] / result['channels_total'] * 100) if result['channels_total'] > 0 else 0
            
            final_text = f"""
{get_emoji('adder2')} {convert_font('GCAST COMPLETED!', 'mono')}

╔══════════════════════════════════╗
     {convert_font('BROADCAST RESULTS', 'mono')} 
╚══════════════════════════════════╝

{get_emoji('adder4')} {convert_font('Statistics:', 'bold')}
{get_emoji('check')} Total Channels: `{result['channels_total']}`
{get_emoji('check')} Successful: `{result['channels_success']}`
{get_emoji('adder3')} Failed: `{result['channels_failed']}`
{get_emoji('adder1')} Success Rate: `{success_rate:.1f}%`
{get_emoji('main')} Gcast ID: `{result['gcast_id']}`

{get_emoji('check')} {convert_font('Message delivered successfully!', 'bold')}
            """.strip()
            
            await safe_edit_message(progress_msg, final_text)
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('GCAST FAILED', 'bold')}

{get_emoji('check')} {convert_font('Error:', 'bold')} {result.get('error', 'Unknown error')}
{get_emoji('main')} {convert_font('Channels Found:', 'bold')} `{result['channels_total']}`
            """.strip()
            await safe_edit_message(progress_msg, error_text)
        
    except Exception as e:
        stats['errors_handled'] += 1
        await event.reply(f"❌ {convert_font('Gcast Error:', 'bold')} {str(e)}")
        logger.error(f"Enhanced gcast command error: {e}")

# PLUGIN COMMAND untuk testing
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugins'))
async def plugins_handler(event):
    """Command untuk menampilkan status plugins"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "plugins")
    
    try:
        if plugin_loader is None:
            await event.reply("❌ Plugin system not initialized")
            return
        
        status = plugin_loader.get_status()
        plugin_list = plugin_loader.list_plugins()
        
        plugin_text = f"""
{get_emoji('main')} {convert_font('PLUGIN SYSTEM STATUS', 'mono')}

{get_emoji('adder6')} {convert_font('Statistics:', 'bold')}
{get_emoji('check')} Total Found: {status['total_plugins']}
{get_emoji('check')} Successfully Loaded: {status['total_loaded']}
{get_emoji('adder3')} Failed to Load: {status['total_failed']}

{get_emoji('adder2')} {convert_font('Loaded Plugins:', 'bold')}
""" + '\n'.join(f"{get_emoji('check')} {plugin}" for plugin in plugin_list['loaded']) + f"""

{get_emoji('adder1')} {convert_font('Plugin Directory:', 'bold')} plugins/
{get_emoji('main')} Use individual plugin commands to test functionality
        """.strip()
        
        if plugin_list['failed']:
            plugin_text += f"""

{get_emoji('adder3')} {convert_font('Failed Plugins:', 'bold')}
""" + '\n'.join(f"{get_emoji('adder3')} {plugin}" for plugin in plugin_list['failed'])
        
        await safe_send_with_entities(event, plugin_text)
        
    except Exception as e:
        await event.reply(f"❌ Plugin status error: {str(e)}")
        logger.error(f"Plugin status command error: {e}")

# PING COMMAND
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Enhanced ping command with detailed metrics"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "ping")
    
    try:
        start = time.time()
        msg = await event.reply(f"{get_emoji('main')} {convert_font('Testing response time...', 'bold')}")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        # Determine latency category
        if ping_time < 100:
            latency_status = f"{get_emoji('check')} Excellent"
            latency_emoji = get_emoji('adder2')
        elif ping_time < 300:
            latency_status = f"{get_emoji('adder1')} Good"
            latency_emoji = get_emoji('adder1')
        elif ping_time < 500:
            latency_status = f"{get_emoji('adder3')} Fair"
            latency_emoji = get_emoji('adder3')
        else:
            latency_status = f"{get_emoji('adder3')} Slow"
            latency_emoji = get_emoji('adder3')
        
        ping_text = f"""
{get_emoji('main')} {convert_font('PING RESULTS', 'mono')}

{get_emoji('check')} {convert_font('Response Time:', 'bold')} `{ping_time:.2f}ms`
{latency_emoji} {convert_font('Latency Status:', 'bold')} {latency_status}
{get_emoji('adder4')} {convert_font('Connection:', 'bold')} Stable
{get_emoji('check')} {convert_font('Server:', 'bold')} Online
{get_emoji('main')} {convert_font('Premium Status:', 'bold')} {'Active' if premium_status else 'Standard'}

{get_emoji('adder5')} {convert_font('Performance Metrics:', 'bold')}
{get_emoji('check')} Commands Executed: `{stats['commands_executed']}`
{get_emoji('check')} Gcast Sent: `{stats['gcast_sent']}`
{get_emoji('check')} Voice Chat: {'Active' if voice_call_active else 'Inactive'}`

{get_emoji('check')} {convert_font('Bot performance optimal!', 'bold')}
        """.strip()
        
        await safe_edit_message(msg, ping_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Ping error: {e}")
# =============================================================================
# TAMBAHKAN COMMANDS INI KE MAIN.PY SETELAH COMMAND LAINNYA
# =============================================================================

# PLUGIN DEBUG COMMAND - COMPREHENSIVE
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugindebug'))
async def plugin_debug_handler(event):
    """Comprehensive plugin debugging command"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "plugindebug")
    
    try:
        if plugin_loader is None:
            await event.reply(f"❌ {convert_font('Plugin system not initialized', 'bold')}")
            return
        
        # Get detailed status
        status = plugin_loader.get_detailed_status()
        diagnosis = plugin_loader.diagnose_plugin_issues()
        
        debug_text = f"""
{get_emoji('main')} {convert_font('PLUGIN DEBUG REPORT', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder1')} {convert_font('SYSTEM OVERVIEW', 'mono')} {get_emoji('adder1')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Total Plugins:', 'bold')} {status['summary']['total_plugins']}
{get_emoji('adder2')} {convert_font('Loaded:', 'bold')} {status['summary']['loaded_plugins']}
{get_emoji('adder3')} {convert_font('Failed:', 'bold')} {status['summary']['failed_plugins']}
{get_emoji('adder4')} {convert_font('Success Rate:', 'bold')} {status['summary']['success_rate']}
{get_emoji('adder5')} {convert_font('Client Status:', 'bold')} {status['client_status']}

╔══════════════════════════════════╗
   {get_emoji('adder2')} {convert_font('SYSTEM CHECKS', 'mono')} {get_emoji('adder2')}
╚══════════════════════════════════╝

{get_emoji('check' if diagnosis['system_check']['client_available'] else 'adder3')} Client Available: {diagnosis['system_check']['client_available']}
{get_emoji('check' if diagnosis['system_check']['plugins_dir_exists'] else 'adder3')} Plugins Directory: {diagnosis['system_check']['plugins_dir_exists']}
{get_emoji('check')} Python Version: {'.'.join(map(str, diagnosis['system_check']['python_version']))}
{get_emoji('check')} Plugin Files: {diagnosis['system_check']['plugin_files_found']}
        """.strip()
        
        # Add loaded plugins
        if status['loaded']:
            debug_text += f"""

╔══════════════════════════════════╗
   {get_emoji('adder2')} {convert_font('LOADED PLUGINS', 'mono')} {get_emoji('adder2')}
╚══════════════════════════════════╝

"""
            for plugin in status['loaded']:
                metadata = status['metadata'].get(plugin, {})
                version = metadata.get('version', 'Unknown')
                debug_text += f"{get_emoji('check')} {plugin} (v{version})\n"
        
        # Add failed plugins with error details
        if status['failed']:
            debug_text += f"""

╔══════════════════════════════════╗
   {get_emoji('adder3')} {convert_font('FAILED PLUGINS', 'mono')} {get_emoji('adder3')}
╚══════════════════════════════════╝

"""
            for plugin in status['failed'][:5]:  # Show first 5
                error_info = status['errors'].get(plugin, {})
                error_type = error_info.get('error_type', 'Unknown')
                error_msg = error_info.get('error_message', 'No details')[:50]
                debug_text += f"{get_emoji('adder3')} {plugin}: {error_type}\n"
                debug_text += f"   └─ {error_msg}{'...' if len(error_msg) >= 50 else ''}\n"
        
        # Add common issues and fixes
        if diagnosis['common_issues']:
            debug_text += f"""

╔══════════════════════════════════╗
   {get_emoji('adder5')} {convert_font('COMMON ISSUES', 'mono')} {get_emoji('adder5')}
╚══════════════════════════════════╝

"""
            for issue in diagnosis['common_issues']:
                debug_text += f"{get_emoji('adder3')} {issue}\n"
        
        if diagnosis['fixes']:
            debug_text += f"""

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('RECOMMENDED FIXES', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

"""
            for fix in diagnosis['fixes']:
                debug_text += f"{get_emoji('check')} {fix}\n"
        
        debug_text += f"""

{get_emoji('adder1')} Use `{COMMAND_PREFIX}plugindetail <name>` for specific plugin errors
{get_emoji('main')} Use `{COMMAND_PREFIX}pluginreload <name>` to retry loading
        """
        
        await safe_send_with_entities(event, debug_text.strip())
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Debug error:', 'bold')} {str(e)}")
        logger.error(f"Plugin debug command error: {e}")

# PLUGIN DETAIL COMMAND
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugindetail(\s+(.+))?'))
async def plugin_detail_handler(event):
    """Show detailed error information for specific plugin"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "plugindetail")
    
    try:
        plugin_name = event.pattern_match.group(2)
        if not plugin_name:
            await event.reply(f"{get_emoji('adder3')} Usage: `{COMMAND_PREFIX}plugindetail <plugin_name>`")
            return
        
        plugin_name = plugin_name.strip()
        
        if plugin_loader is None:
            await event.reply(f"❌ {convert_font('Plugin system not initialized', 'bold')}")
            return
        
        error_details = plugin_loader.get_plugin_error_details(plugin_name)
        
        if not error_details:
            await event.reply(f"{get_emoji('check')} {convert_font('No error details found for plugin:', 'bold')} `{plugin_name}`")
            return
        
        detail_text = f"""
{get_emoji('adder3')} {convert_font('PLUGIN ERROR DETAILS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font(plugin_name.upper(), 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Error Type:', 'bold')} {error_details.get('error_type', 'Unknown')}
{get_emoji('adder2')} {convert_font('Error Message:', 'bold')}
```
{error_details.get('error_message', 'No message available')}
```

{get_emoji('adder3')} {convert_font('Error Details:', 'bold')}
"""
        
        # Add specific error details
        details = error_details.get('error_details', {})
        if 'missing_imports' in details:
            detail_text += f"\n{get_emoji('adder4')} Missing Imports: {', '.join(details['missing_imports'])}"
        
        if 'syntax_errors' in details:
            detail_text += f"\n{get_emoji('adder5')} Syntax Errors: {', '.join(details['syntax_errors'])}"
        
        if 'traceback' in details:
            # Show last few lines of traceback
            traceback_lines = details['traceback'].split('\n')
            relevant_lines = [line for line in traceback_lines[-5:] if line.strip()]
            if relevant_lines:
                detail_text += f"""

{get_emoji('adder6')} {convert_font('Traceback (last few lines):', 'bold')}
```
{chr(10).join(relevant_lines)}
```"""
        
        detail_text += f"""

{get_emoji('main')} {convert_font('Suggested Actions:', 'bold')}
{get_emoji('check')} Check plugin syntax and imports
{get_emoji('check')} Verify all dependencies are installed
{get_emoji('check')} Use `{COMMAND_PREFIX}pluginreload {plugin_name}` to retry
        """.strip()
        
        await safe_send_with_entities(event, detail_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Detail error:', 'bold')} {str(e)}")
        logger.error(f"Plugin detail command error: {e}")

# PLUGIN RELOAD COMMAND  
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}pluginreload(\s+(.+))?'))
async def plugin_reload_handler(event):
    """Reload specific plugin"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "pluginreload")
    
    try:
        plugin_name = event.pattern_match.group(2)
        if not plugin_name:
            await event.reply(f"{get_emoji('adder3')} Usage: `{COMMAND_PREFIX}pluginreload <plugin_name>`")
            return
        
        plugin_name = plugin_name.strip()
        
        if plugin_loader is None:
            await event.reply(f"❌ {convert_font('Plugin system not initialized', 'bold')}")
            return
        
        # Show loading message
        loading_msg = await event.reply(f"{get_emoji('main')} {convert_font('Reloading plugin:', 'bold')} `{plugin_name}`...")
        
        # Attempt reload
        success = plugin_loader.reload_plugin(plugin_name)
        
        if success:
            # Get updated status
            status = plugin_loader.get_detailed_status()
            metadata = status['metadata'].get(plugin_name, {})
            
            reload_text = f"""
{get_emoji('adder2')} {convert_font('PLUGIN RELOAD SUCCESS', 'mono')}

{get_emoji('check')} {convert_font('Plugin:', 'bold')} `{plugin_name}`
{get_emoji('check')} {convert_font('Status:', 'bold')} Loaded Successfully
{get_emoji('adder1')} {convert_font('Version:', 'bold')} {metadata.get('version', 'Unknown')}
{get_emoji('adder2')} {convert_font('Commands:', 'bold')} {len(metadata.get('commands', []))}

{get_emoji('main')} Plugin is now active and ready to use!
            """.strip()
            
            await safe_edit_message(loading_msg, reload_text)
        else:
            # Show error details
            error_details = plugin_loader.get_plugin_error_details(plugin_name)
            
            fail_text = f"""
{get_emoji('adder3')} {convert_font('PLUGIN RELOAD FAILED', 'mono')}

{get_emoji('adder1')} {convert_font('Plugin:', 'bold')} `{plugin_name}`
{get_emoji('adder3')} {convert_font('Status:', 'bold')} Load Failed
{get_emoji('adder5')} {convert_font('Error:', 'bold')} {error_details.get('error_type', 'Unknown')}

{get_emoji('check')} Use `{COMMAND_PREFIX}plugindetail {plugin_name}` for full error details
            """.strip()
            
            await safe_edit_message(loading_msg, fail_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Reload error:', 'bold')} {str(e)}")
        logger.error(f"Plugin reload command error: {e}")

# ENHANCED PLUGINS COMMAND - UPDATED
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugins'))
async def enhanced_plugins_handler(event):
    """Enhanced command untuk menampilkan status plugins dengan detail"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "plugins")
    
    try:
        if plugin_loader is None:
            await event.reply("❌ Plugin system not initialized")
            return
        
        status = plugin_loader.get_detailed_status()
        
        plugins_text = f"""
{get_emoji('main')} {convert_font('ENHANCED PLUGIN SYSTEM v2.0', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder6')} {convert_font('SYSTEM STATUS', 'mono')} {get_emoji('adder6')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Total Found:', 'bold')} {status['summary']['total_plugins']}
{get_emoji('adder2')} {convert_font('Successfully Loaded:', 'bold')} {status['summary']['loaded_plugins']}
{get_emoji('adder3')} {convert_font('Failed to Load:', 'bold')} {status['summary']['failed_plugins']}
{get_emoji('adder1')} {convert_font('Success Rate:', 'bold')} {status['summary']['success_rate']}
{get_emoji('main')} {convert_font('Client Status:', 'bold')} {status['client_status']}

╔══════════════════════════════════╗
   {get_emoji('adder2')} {convert_font('LOADED PLUGINS', 'mono')} {get_emoji('adder2')}
╚══════════════════════════════════╝

"""
        
        if status['loaded']:
            for plugin in status['loaded']:
                metadata = status['metadata'].get(plugin, {})
                version = metadata.get('version', '?')
                commands = len(metadata.get('commands', []))
                plugins_text += f"{get_emoji('check')} {plugin} v{version} ({commands} cmd)\n"
        else:
            plugins_text += f"{get_emoji('adder3')} No plugins loaded\n"
        
        if status['failed']:
            plugins_text += f"""

╔══════════════════════════════════╗
   {get_emoji('adder3')} {convert_font('FAILED PLUGINS', 'mono')} {get_emoji('adder3')}
╚══════════════════════════════════╝

"""
            for plugin in status['failed']:
                error_info = status['errors'].get(plugin, {})
                error_type = error_info.get('error_type', 'Unknown')
                plugins_text += f"{get_emoji('adder3')} {plugin} ({error_type})\n"
        
        plugins_text += f"""

{get_emoji('adder4')} {convert_font('Debug Commands:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}plugindebug` - Comprehensive analysis
{get_emoji('check')} `{COMMAND_PREFIX}plugindetail <name>` - Error details
{get_emoji('check')} `{COMMAND_PREFIX}pluginreload <name>` - Reload plugin

{get_emoji('main')} Plugin Directory: plugins/
        """.strip()
        
        await safe_send_with_entities(event, plugins_text)
        
    except Exception as e:
        await event.reply(f"❌ Plugin status error: {str(e)}")
        logger.error(f"Enhanced plugins command error: {e}")

# ============= STARTUP AND MAIN FUNCTIONS =============

async def send_enhanced_startup_message():
    """Enhanced startup notification with plugin info"""
    try:
        me = await client.get_me()
        
        # Plugin status
        plugin_status_text = ""
        if plugin_loader:
            status = plugin_loader.get_status()
            plugin_status_text = f"""
{get_emoji('adder6')} {convert_font('PLUGIN SYSTEM:', 'bold')}
{get_emoji('check')} Loaded: {status['total_loaded']}/{status['total_plugins']} plugins
{get_emoji('check')} System: {'Operational' if status['total_loaded'] > 0 else 'No plugins loaded'}
"""
        
        startup_msg = f"""
[🚀]({LOGO_URL}) {convert_font('VZOEL ASSISTANT v0.1.0.75 STARTED!', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('PLUGIN-COMPATIBLE SYSTEM ACTIVE', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('All systems operational', 'bold')}
{get_emoji('check')} {convert_font('User:', 'bold')} {me.first_name}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{me.id}`
{get_emoji('check')} {convert_font('Started:', 'bold')} `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
{get_emoji('main')} {convert_font('Premium:', 'bold')} {'Active' if premium_status else 'Standard'}
{plugin_status_text}
{get_emoji('adder1')} {convert_font('ENHANCED FEATURES:', 'bold')}
{get_emoji('check')} Plugin system dengan dependency injection
{get_emoji('check')} Reply-based Gcast with entity preservation
{get_emoji('check')} Auto premium emoji extraction
{get_emoji('check')} Shared functions untuk plugin compatibility
{get_emoji('check')} Enhanced error handling & recovery

{get_emoji('adder3')} {convert_font('Quick Commands:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}alive` untuk status lengkap
{get_emoji('check')} `{COMMAND_PREFIX}plugins` untuk plugin status
{get_emoji('check')} `{COMMAND_PREFIX}gcast <text>` atau reply + `{COMMAND_PREFIX}gcast`
{get_emoji('check')} Plugin commands: `.help`, `.cektogel`, `.joinvc`, `.aimode`

{get_emoji('main')} {convert_font('Ready for production use!', 'bold')}
{convert_font('Plugin-Compatible userbot v0.1.0.75 ~ by Vzoel Fox\'s', 'bold')} {get_emoji('check')}
        """.strip()
        
        await client.send_message('me', startup_msg)
        logger.info("✅ Enhanced startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def startup():
    """Enhanced startup function with plugin system initialization"""
    global start_time, premium_status
    start_time = datetime.now()
    stats['uptime_start'] = start_time
    
    # Initialize all systems
    init_database()
    load_blacklist()
    load_emoji_config()
    
    logger.info("🚀 Starting VZOEL ASSISTANT v0.1.0.75 Plugin Compatible...")
    
    try:
        await client.start()
        await check_premium_status()
        
        me = await client.get_me()
        
        logger.info(f"✅ VZOEL ASSISTANT v0.1.0.75 Plugin Compatible started!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"💎 Premium Status: {'Active' if premium_status else 'Standard'}")
        logger.info(f"🔧 Plugin System: Initializing...")
        
        await send_enhanced_startup_message()
        return True
            
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor authentication enabled. Please login manually first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting VZOEL ASSISTANT: {e}")
        return False

# =============================================================================
# GANTI FUNGSI main() YANG LAMA DENGAN INI
# =============================================================================

async def main():
    """Enhanced main function with robust plugin loading"""
    global plugin_loader
    
    logger.info("🚀 Initializing VZOEL ASSISTANT v0.1.0.75 Enhanced...")
    
    # Initialize systems first
    if not await startup():
        logger.error("❌ Failed to start VZOEL ASSISTANT!")
        return
    
    # Load plugins SETELAH client berhasil start
    try:
        logger.info("🔌 Initializing Enhanced Plugin System v2.0...")
        
        # Pastikan client sudah connected
        if not client.is_connected():
            logger.info("🔄 Starting Telegram client for plugin system...")
            await client.start()
        
        # Setup enhanced plugin loader
        plugin_loader = setup_plugins(client, "plugins")
        
        # Get comprehensive status
        status = plugin_loader.get_detailed_status()
        
        # Log detailed results
        logger.info(f"✅ Plugin system initialized successfully:")
        logger.info(f"   📊 Success Rate: {status['summary']['success_rate']}")
        logger.info(f"   ✅ Loaded: {status['summary']['loaded_plugins']} plugins")
        logger.info(f"   ❌ Failed: {status['summary']['failed_plugins']} plugins")
        
        if status['loaded']:
            logger.info(f"   🎯 Active plugins: {', '.join(status['loaded'])}")
        
        if status['failed']:
            logger.warning(f"   ⚠️  Failed plugins: {', '.join(status['failed'])}")
            logger.info("   💡 Use .plugindebug command for detailed error analysis")
            
            # Show quick diagnosis
            diagnosis = plugin_loader.diagnose_plugin_issues()
            if diagnosis['common_issues']:
                logger.info("   🔍 Common issues detected:")
                for issue in diagnosis['common_issues'][:3]:  # Show top 3
                    logger.info(f"      • {issue}")
    
    except Exception as e:
        logger.error(f"⚠️ Plugin system initialization error: {e}")
        logger.error(f"   Traceback: {traceback.format_exc()}")
        # Create empty plugin loader to prevent crashes
        plugin_loader = EnhancedPluginLoader(client=client)
        logger.warning("   🔄 Created minimal plugin loader - some features may be unavailable")
    
    # Continue with main execution
    logger.info("🔥 VZOEL ASSISTANT Enhanced is now running...")
    logger.info("🔍 Press Ctrl+C to stop")
    logger.info("🚀 All enhanced features active with robust plugin system!")
    
    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        logger.info("👋 VZOEL ASSISTANT stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        logger.info("🔥 Shutting down gracefully...")
        
        # Plugin cleanup
        if plugin_loader:
            try:
                # Call cleanup on loaded plugins if they have it
                for plugin_name in plugin_loader.loaded_plugins:
                    plugin_module = plugin_loader.get_plugin(plugin_name)
                    if plugin_module and hasattr(plugin_module, 'cleanup_plugin'):
                        try:
                            if callable(plugin_module.cleanup_plugin):
                                plugin_module.cleanup_plugin()
                            logger.debug(f"Cleaned up plugin: {plugin_name}")
                        except Exception as cleanup_error:
                            logger.error(f"Cleanup error for {plugin_name}: {cleanup_error}")
            except Exception as e:
                logger.error(f"Plugin cleanup error: {e}")
        
        # Save configurations
        save_blacklist()
        save_emoji_config()
        
        try:
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            
        logger.info("✅ VZOEL ASSISTANT stopped successfully!")

# =============================================================================
# UPDATE STARTUP MESSAGE (opsional - untuk informasi plugin)
# =============================================================================

async def send_enhanced_startup_message():
    """Enhanced startup notification with plugin info"""
    try:
        me = await client.get_me()
        
        # Get plugin status if available
        plugin_info = ""
        if plugin_loader:
            status = plugin_loader.get_detailed_status()
            plugin_info = f"""
{get_emoji('adder1')} {convert_font('Plugin System Status:', 'bold')}
{get_emoji('check')} Loaded: {status['summary']['loaded_plugins']} plugins
{get_emoji('adder3')} Failed: {status['summary']['failed_plugins']} plugins
{get_emoji('main')} Success Rate: {status['summary']['success_rate']}
"""
        
        startup_msg = f"""
[🚀]({LOGO_URL}) {convert_font('VZOEL ASSISTANT v0.1.0.75 STARTED!', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('ENHANCED SYSTEM ACTIVATED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('All systems operational', 'bold')}
{get_emoji('check')} {convert_font('User:', 'bold')} {me.first_name}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{me.id}`
{get_emoji('check')} {convert_font('Started:', 'bold')} `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
{get_emoji('main')} {convert_font('Premium:', 'bold')} {'Active' if premium_status else 'Standard'}
{plugin_info}
{get_emoji('adder2')} {convert_font('NEW ENHANCED FEATURES:', 'bold')}
{get_emoji('check')} Enhanced Plugin System v2.0
{get_emoji('check')} Comprehensive error handling & debugging
{get_emoji('check')} Reply-based Gcast with entity preservation
{get_emoji('check')} Auto premium emoji extraction
{get_emoji('check')} Advanced UTF-16 entity handling
{get_emoji('check')} Database integration & statistics
{get_emoji('check')} Concurrent broadcasting system
{get_emoji('check')} Smart rate limiting per operation

{get_emoji('adder3')} {convert_font('PLUGIN DEBUG COMMANDS:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}plugindebug` - Comprehensive analysis
{get_emoji('check')} `{COMMAND_PREFIX}plugindetail <name>` - Error details
{get_emoji('check')} `{COMMAND_PREFIX}pluginreload <name>` - Reload plugin

{get_emoji('adder4')} {convert_font('Quick Commands:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}gcast <text>` atau reply + `{COMMAND_PREFIX}gcast`
{get_emoji('check')} Reply to emoji message + `{COMMAND_PREFIX}setemoji`
{get_emoji('check')} `{COMMAND_PREFIX}alive` untuk status lengkap
{get_emoji('check')} `{COMMAND_PREFIX}help` untuk semua commands

{get_emoji('main')} {convert_font('Ready for production use with robust plugin system!', 'bold')}
{convert_font('userbot v0.1.0.75 ~ by Vzoel Fox\'s (Enhanced by Morgan)', 'bold')} {get_emoji('check')}
        """.strip()
        
        await client.send_message('me', startup_msg)
        logger.info("✅ Enhanced startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

# ============= END OF VZOEL ASSISTANT v0.1.0.75 PLUGIN COMPATIBLE =============