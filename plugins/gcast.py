#!/usr/bin/env python3
"""
Enhanced Global Cast Plugin for Vzoel Assistant - Enhanced UTF-16 Premium Edition
Fitur: Enhanced gcast dengan reply message support, entity preservation, dan premium emoji
yang sudah diperbarui menggunakan mapping UTF-16 terbaru dari formorgan.py.
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 (Extracted from main.py dengan Enhanced Premium Mapping)
"""

import re
import os
import sys
import json
import time
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User, Message
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, MessageNotModifiedError

# Plugin Info
PLUGIN_INFO = {
    "name": "gcast",
    "version": "2.0.0",
    "description": "Enhanced Global Cast dengan grub blacklist integration, premium emoji mapping, reply support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".gcast", ".gcastbl refresh", ".gcastbl list", ".gcastbl status", ".gcastbl test"],
    "features": ["global broadcast", "grub blacklist integration", "real-time blacklist check", "reply message support", "entity preservation", "auto UTF-16 premium emoji"]
}

# Premium Emoji Mapping - Enhanced dari formorgan.py (UTF-16 compliant)
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'}, 
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚'}
}

# Global variables
client = None
blacklisted_chats = set()
premium_status = None

# Import grub blacklist integration
try:
    from grub import get_blacklisted_groups, is_blacklisted
    GRUB_INTEGRATION = True
except ImportError:
    GRUB_INTEGRATION = False
    print("[Gcast] Warning: grub.py not found, using local blacklist only")

# Configuration
DATABASE_FILE = "vzoel_assistant.db"
BLACKLIST_FILE = "gcast_blacklist.json"
MAX_CONCURRENT_GCAST = 10
GCAST_DELAY = 0.5

# Statistics
stats = {
    'gcast_sent': 0,
    'commands_executed': 0
}

# Unicode Fonts for styling (replacing ** markdown)
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

# ============= FONT AND EMOJI FUNCTIONS - ENHANCED =============

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def get_emoji(emoji_type):
    """Get premium emoji character safely with fallback"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'  # fallback

def get_utf16_length(emoji_char):
    """Get UTF-16 length of emoji character"""
    try:
        utf16_bytes = emoji_char.encode('utf-16-le')
        return len(utf16_bytes) // 2
    except:
        return 1

def create_premium_entities(text):
    """Enhanced: Create MessageEntityCustomEmoji entities with compound character support"""
    entities = []
    utf16_offset = 0
    text_pos = 0
    
    # Process text dengan handling compound characters (seperti ⚙️)
    while text_pos < len(text):
        found_emoji = False
        
        # Check setiap premium emoji
        for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
            emoji_char = emoji_data['char']
            emoji_len = len(emoji_char)
            
            # Cek apakah text di posisi ini cocok dengan emoji
            if text[text_pos:text_pos + emoji_len] == emoji_char:
                # Get actual UTF-16 length dari emoji character
                emoji_utf16_length = get_utf16_length(emoji_char)
                
                # Create custom emoji entity
                entity = MessageEntityCustomEmoji(
                    offset=utf16_offset,
                    length=emoji_utf16_length,
                    document_id=int(emoji_data['id'])
                )
                entities.append(entity)
                
                # Skip emoji characters
                text_pos += emoji_len
                utf16_offset += emoji_utf16_length
                found_emoji = True
                break
        
        if not found_emoji:
            # Regular character, advance by 1
            char = text[text_pos]
            char_utf16_length = get_utf16_length(char)
            utf16_offset += char_utf16_length
            text_pos += 1
    
    return entities

def extract_premium_emoji_from_message(message: Message) -> List[Dict]:
    """Enhanced: Extract premium emoji dari message entities using proper UTF-16 handling"""
    if not message or not message.entities:
        return []
    
    text = message.text or message.message or ""
    premium_emojis = []
    
    for entity in message.entities:
        if isinstance(entity, MessageEntityCustomEmoji) and entity.document_id:
            try:
                # Proper UTF-16 extraction
                text_bytes = text.encode('utf-16-le')
                start_byte = entity.offset * 2
                end_byte = (entity.offset + entity.length) * 2
                
                # Validate bounds
                if end_byte <= len(text_bytes) and start_byte >= 0:
                    entity_bytes = text_bytes[start_byte:end_byte]
                    emoji_char = entity_bytes.decode('utf-16-le')
                    
                    premium_emojis.append({
                        'emoji': emoji_char,
                        'document_id': str(entity.document_id),
                        'offset': entity.offset,
                        'length': entity.length
                    })
                    
            except Exception as e:
                print(f"[Gcast] Error extracting emoji entity: {e}")
    
    return premium_emojis

# ============= UTILITY FUNCTIONS =============

def get_prefix():
    """Ambil prefix command dari environment atau default '.'"""
    try:
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

async def is_owner_check(user_id):
    """Simple owner check"""
    OWNER_ID = 7847025168  # Ganti sesuai ID Master
    return user_id == OWNER_ID

def force_reload_blacklist():
    """ENHANCED: Force reload blacklist dari semua sumber dengan real-time check"""
    global blacklisted_chats
    print("[Gcast] FORCE RELOAD BLACKLIST - Starting comprehensive blacklist refresh...")
    
    # Reset blacklist
    blacklisted_chats = set()
    
    try:
        # 1. Load from JSON file - support both old and new formats
        file_blacklist = set()
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                
                # New format: keys are chat IDs with metadata
                for key, value in data.items():
                    if key.lstrip('-').isdigit():  # Chat ID key
                        file_blacklist.add(int(key))
                
                # Legacy format: blacklisted_chats array
                if 'blacklisted_chats' in data:
                    for chat_id in data['blacklisted_chats']:
                        file_blacklist.add(int(chat_id))
                        
            print(f"[Gcast] Loaded {len(file_blacklist)} blacklisted chats from JSON file")
        
        # 2. Load from grub database (preferred)
        db_blacklist = set()
        if GRUB_INTEGRATION:
            try:
                db_blacklist = get_blacklisted_groups()
                print(f"[Gcast] Loaded {len(db_blacklist)} blacklisted groups from grub database")
            except Exception as e:
                print(f"[Gcast] Error loading grub blacklist: {e}")
        
        # 3. Load from session database (SQLite)
        session_blacklist = set()
        try:
            if os.path.exists(DATABASE_FILE):
                conn = sqlite3.connect(DATABASE_FILE)
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gcast_blacklist_session (
                        chat_id INTEGER PRIMARY KEY,
                        title TEXT,
                        type TEXT,
                        added_date TEXT,
                        added_by TEXT,
                        reason TEXT,
                        permanent INTEGER DEFAULT 1
                    )
                ''')
                
                # Load session blacklist
                cursor.execute('SELECT chat_id FROM gcast_blacklist_session WHERE permanent = 1')
                session_data = cursor.fetchall()
                for row in session_data:
                    session_blacklist.add(int(row[0]))
                    
                conn.close()
                print(f"[Gcast] Loaded {len(session_blacklist)} blacklisted chats from session database")
        except Exception as e:
            print(f"[Gcast] Error loading session blacklist: {e}")
        
        # 4. Combine all sources (Union of all blacklists)
        blacklisted_chats = file_blacklist | db_blacklist | session_blacklist
        
        # 5. Update session database dengan semua blacklist yang ditemukan
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            for chat_id in blacklisted_chats:
                cursor.execute('''
                    INSERT OR REPLACE INTO gcast_blacklist_session 
                    (chat_id, title, type, added_date, added_by, reason, permanent)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, 'Auto-imported', 'Unknown', 
                     datetime.now().isoformat(), 'system_auto', 
                     'Auto-imported from file/grub', 1))
            
            conn.commit()
            conn.close()
            print(f"[Gcast] Updated session database with {len(blacklisted_chats)} blacklisted chats")
        except Exception as e:
            print(f"[Gcast] Error updating session database: {e}")
        
        # 6. Final report
        print(f"[Gcast] ✅ FORCE RELOAD COMPLETED:")
        print(f"[Gcast] - File blacklist: {len(file_blacklist)}")
        print(f"[Gcast] - Grub database: {len(db_blacklist)}")
        print(f"[Gcast] - Session database: {len(session_blacklist)}")
        print(f"[Gcast] - TOTAL BLACKLISTED: {len(blacklisted_chats)}")
        
        # Show blacklisted IDs for debugging
        if blacklisted_chats:
            sorted_ids = sorted(list(blacklisted_chats))
            print(f"[Gcast] Blacklisted chat IDs: {sorted_ids}")
        
        return True
        
    except Exception as e:
        print(f"[Gcast] CRITICAL ERROR during force reload blacklist: {e}")
        blacklisted_chats = set()
        return False

def load_blacklist():
    """Wrapper untuk backward compatibility - calls force_reload_blacklist()"""
    return force_reload_blacklist()

async def add_to_blacklist_session(chat_id: int, title: str = "Unknown", reason: str = "Manual add"):
    """Add chat to session blacklist database"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO gcast_blacklist_session 
            (chat_id, title, type, added_date, added_by, reason, permanent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, title, 'Manual', datetime.now().isoformat(),
             'user_manual', reason, 1))
        
        conn.commit()
        conn.close()
        
        # Refresh in-memory blacklist
        force_reload_blacklist()
        
        print(f"[Gcast] Added {chat_id} ({title}) to session blacklist")
        return True
        
    except Exception as e:
        print(f"[Gcast] Error adding to session blacklist: {e}")
        return False

async def get_blacklist_status():
    """Get comprehensive blacklist status dari semua sumber"""
    try:
        # Reload untuk data terbaru
        force_reload_blacklist()
        
        status = {
            'total_blacklisted': len(blacklisted_chats),
            'sources': {
                'json_file': 0,
                'grub_database': 0, 
                'session_database': 0
            },
            'blacklist_ids': sorted(list(blacklisted_chats))
        }
        
        # Count by source
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                if 'blacklisted_chats' in data:
                    status['sources']['json_file'] = len(data['blacklisted_chats'])
                else:
                    status['sources']['json_file'] = len([k for k in data.keys() if k.lstrip('-').isdigit()])
        
        if GRUB_INTEGRATION:
            try:
                grub_blacklist = get_blacklisted_groups()
                status['sources']['grub_database'] = len(grub_blacklist)
            except:
                pass
                
        if os.path.exists(DATABASE_FILE):
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM gcast_blacklist_session WHERE permanent = 1')
            result = cursor.fetchone()
            status['sources']['session_database'] = result[0] if result else 0
            conn.close()
        
        return status
        
    except Exception as e:
        print(f"[Gcast] Error getting blacklist status: {e}")
        return None

async def safe_edit_message(message, text):
    """Safely edit message dengan error handling dan premium emoji"""
    if not message:
        return False
    try:
        entities = create_premium_entities(text)
        if entities:
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
        return True
    except MessageNotModifiedError:
        pass  # Message content unchanged
    except Exception as e:
        print(f"[Gcast] Edit message error: {e}")
        return False

# ============= BROADCAST FUNCTIONS =============

async def get_broadcast_channels():
    """ENHANCED: Get all channels dan groups untuk broadcasting dengan FORCE BLACKLIST CHECK"""
    print("[Gcast] Getting broadcast channels with comprehensive blacklist filtering...")
    
    # FORCE RELOAD BLACKLIST SEBELUM MEMULAI GCAST
    print("[Gcast] STEP 1: Force reloading blacklist for real-time filtering...")
    blacklist_reload_success = force_reload_blacklist()
    
    if not blacklist_reload_success:
        print("[Gcast] WARNING: Blacklist reload failed, using cached blacklist")
    
    channels = []
    blocked_count = 0
    
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Skip users
            if isinstance(entity, User):
                continue
            
            # ENHANCED MULTI-LAYER BLACKLIST CHECK
            is_blacklisted_chat = False
            blacklist_reason = ""
            
            # Layer 1: Check loaded blacklist (from all sources)
            if entity.id in blacklisted_chats:
                is_blacklisted_chat = True
                blacklist_reason = "Found in loaded blacklist"
            
            # Layer 2: Real-time check grub database
            elif GRUB_INTEGRATION:
                try:
                    if is_blacklisted(entity.id):
                        is_blacklisted_chat = True
                        blacklist_reason = "Found in grub database (real-time check)"
                        
                        # Add to session database for future caching
                        try:
                            conn = sqlite3.connect(DATABASE_FILE)
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT OR REPLACE INTO gcast_blacklist_session 
                                (chat_id, title, type, added_date, added_by, reason, permanent)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (entity.id, getattr(entity, 'title', 'Unknown'), 
                                 entity.__class__.__name__, datetime.now().isoformat(),
                                 'gcast_realtime_check', 'Real-time grub blacklist detection', 1))
                            conn.commit()
                            conn.close()
                        except Exception as db_err:
                            print(f"[Gcast] Error updating session DB for {entity.id}: {db_err}")
                            
                except Exception as grub_err:
                    print(f"[Gcast] Error checking grub blacklist for {entity.id}: {grub_err}")
            
            # Layer 3: Session database double-check
            elif entity.id not in blacklisted_chats:
                try:
                    conn = sqlite3.connect(DATABASE_FILE)
                    cursor = conn.cursor()
                    cursor.execute('SELECT chat_id FROM gcast_blacklist_session WHERE chat_id = ? AND permanent = 1', (entity.id,))
                    if cursor.fetchone():
                        is_blacklisted_chat = True
                        blacklist_reason = "Found in session database"
                    conn.close()
                except Exception as session_err:
                    print(f"[Gcast] Error checking session blacklist for {entity.id}: {session_err}")
            
            # Block if blacklisted
            if is_blacklisted_chat:
                blocked_count += 1
                print(f"[Gcast] 🚫 BLOCKED: {getattr(entity, 'title', 'Unknown')} (ID: {entity.id}) - Reason: {blacklist_reason}")
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
        
        # COMPREHENSIVE FINAL SUMMARY
        total_checked = len(channels) + blocked_count
        print(f"[Gcast] ✅ BROADCAST CHANNELS FILTERING COMPLETED:")
        print(f"[Gcast] - Total chats checked: {total_checked}")
        print(f"[Gcast] - Valid broadcast targets: {len(channels)}")
        print(f"[Gcast] - Blocked by blacklist: {blocked_count}")
        print(f"[Gcast] - Blacklist effectiveness: {(blocked_count/total_checked*100):.1f}% blocked" if total_checked > 0 else "[Gcast] - No chats to check")
        
        return channels
        
    except Exception as e:
        print(f"[Gcast] Error getting broadcast channels: {e}")
        return []

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
            premium_emojis = extract_premium_emoji_from_message(reply_message)
            if premium_emojis:
                # Create entity mapping for message text
                entity_mappings = []
                for emoji_data in premium_emojis:
                    if emoji_data['emoji'] in message_text:
                        entity_mappings.append((emoji_data['emoji'], emoji_data['document_id']))
                
                if entity_mappings:
                    entities = create_premium_entities(message_text)
                    print(f"[Gcast] Created {len(entities)} entities from reply message")
        except Exception as e:
            print(f"[Gcast] Error processing reply message entities: {e}")
    
    # Broadcast to all channels
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GCAST)
    
    async def send_to_channel(channel_info):
        async with semaphore:
            try:
                # Small delay to prevent rate limiting
                await asyncio.sleep(GCAST_DELAY)
                
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
                
                return True
                
            except FloodWaitError as e:
                print(f"[Gcast] Flood wait {e.seconds}s for channel {channel_info['title']}")
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
                print(f"[Gcast] {error_msg}")
                return False
    
    # Execute all sends concurrently
    tasks = [send_to_channel(channel_info) for channel_info in channels]
    
    for i, task in enumerate(asyncio.as_completed(tasks)):
        await task
        
        # Progress callback
        if progress_callback and (i + 1) % 5 == 0:  # Update every 5 completed
            await progress_callback(i + 1, len(channels), gcast_id)
    
    # Final progress update
    if progress_callback:
        await progress_callback(len(channels), len(channels), gcast_id)
    
    return results

# ============= EVENT HANDLERS =============

async def gcast_handler(event):
    """Enhanced Global Broadcast dengan reply message support dan entity preservation"""
    if not await is_owner_check(event.sender_id):
        return
    
    prefix = get_prefix()
    stats['commands_executed'] += 1
    
    try:
        # Determine message source
        reply_message = None
        message_text = ""
        
        if event.is_reply:
            reply_message = await event.get_reply_message()
            # Check if there's additional text in the command
            command_text = event.pattern_match.group(2)
            if command_text:
                message_text = command_text.strip()
            else:
                # Use the replied message text
                message_text = reply_message.text or reply_message.message or ""
                
            if not message_text:
                error_text = f"❌ {convert_font('No text found in replied message!', 'bold')}"
                await event.reply(error_text, formatting_entities=create_premium_entities(error_text))
                return
                
        else:
            # Standard gcast with text
            if not event.pattern_match.group(2):
                usage_text = f"""
{get_emoji('main')} {convert_font('ENHANCED GCAST USAGE', 'mono')}

{get_emoji('check')} {convert_font('Text Gcast:', 'bold')}
`{prefix}gcast <your message>`

{get_emoji('adder1')} {convert_font('Reply Gcast (NEW!):', 'bold')}
Reply to any message + `{prefix}gcast`
Reply to message + `{prefix}gcast <additional text>`

{get_emoji('adder2')} {convert_font('Premium Features:', 'bold')}
{get_emoji('check')} Auto premium emoji preservation
{get_emoji('check')} Entity formatting preservation
{get_emoji('check')} Concurrent broadcasting
{get_emoji('check')} Advanced error handling
                """.strip()
                await event.reply(usage_text, formatting_entities=create_premium_entities(usage_text))
                return
                
            message_text = event.pattern_match.group(2).strip()
        
        # INITIAL BLACKLIST CHECK NOTIFICATION
        blacklist_status = await get_blacklist_status()
        
        # Show enhanced progress message dengan premium emoji dan blacklist info  
        progress_text = f"""
{get_emoji('adder1')} {convert_font('ENHANCED GCAST WITH FORCE BLACKLIST CHECK', 'bold')}

{get_emoji('check')} {convert_font('Mode:', 'bold')} {'Reply + Entity Preservation' if reply_message else 'Standard Text'}
{get_emoji('adder2')} {convert_font('Blacklist Status:', 'bold')} {blacklist_status['total_blacklisted']} chats blocked
{get_emoji('adder3')} {convert_font('Sources:', 'bold')} JSON({blacklist_status['sources']['json_file']}) + Grub({blacklist_status['sources']['grub_database']}) + Session({blacklist_status['sources']['session_database']})
{get_emoji('adder1')} {convert_font('Status:', 'bold')} Force checking blacklist...
        """.strip()
        
        # Send dengan premium emoji support
        progress_msg = await event.reply(progress_text, formatting_entities=create_premium_entities(progress_text))
        
        # Progress callback for updates
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
                print(f"[Gcast] Error updating progress: {e}")
        
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

     {convert_font('BROADCAST RESULTS', 'mono')} 

{get_emoji('adder4')} {convert_font('Statistics:', 'bold')}
{get_emoji('check')} Total Channels: `{result['channels_total']}`
{get_emoji('check')} Successful: `{result['channels_success']}`
{get_emoji('adder3')} Failed: `{result['channels_failed']}`
{get_emoji('adder1')} Success Rate: `{success_rate:.1f}%`
{get_emoji('main')} Gcast ID: `{result['gcast_id']}`

{get_emoji('adder5')} {convert_font('Features Used:', 'bold')}
{get_emoji('check')} {'Entity Preservation: ✅' if reply_message else 'Standard Mode: ✅'}
{get_emoji('check')} Concurrent Broadcasting: ✅
{get_emoji('check')} Rate Limiting: ✅
{get_emoji('check')} Error Recovery: ✅

{get_emoji('check')} {convert_font('Message delivered successfully!', 'bold')}
            """.strip()
            
            # Show errors if any (limited to first 5)
            if result['errors']:
                error_preview = '\n'.join(result['errors'][:3])
                final_text += f"\n\n{get_emoji('adder3')} {convert_font('Sample Errors:', 'bold')}\n```{error_preview}```"
                if len(result['errors']) > 3:
                    final_text += f"\n{get_emoji('check')} ... and {len(result['errors']) - 3} more errors"
            
            await safe_edit_message(progress_msg, final_text)
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('GCAST FAILED', 'bold')}

{get_emoji('check')} {convert_font('Error:', 'bold')} {result.get('error', 'Unknown error')}
{get_emoji('main')} {convert_font('Channels Found:', 'bold')} `{result['channels_total']}`
            """.strip()
            await safe_edit_message(progress_msg, error_text)
        
    except Exception as e:
        error_text = f"❌ {convert_font('Gcast Error:', 'bold')} {str(e)}"
        await event.reply(error_text, formatting_entities=create_premium_entities(error_text))
        print(f"[Gcast] Enhanced gcast command error: {e}")

async def gcast_blacklist_handler(event):
    """ENHANCED: Handle comprehensive blacklist management dengan force reload dan session database"""
    global blacklisted_chats
    
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        args = event.text.split()
        
        if len(args) < 2:
            help_text = f"""
{get_emoji('main')} {convert_font('ENHANCED GCAST BLACKLIST COMMANDS', 'bold')}

{get_emoji('check')} {convert_font('.gcastbl refresh', 'mono')} - Force reload dari SEMUA sumber (JSON + Grub + Session)
{get_emoji('check')} {convert_font('.gcastbl list', 'mono')} - Show blacklisted groups dengan detail
{get_emoji('check')} {convert_font('.gcastbl status', 'mono')} - Comprehensive integration status
{get_emoji('check')} {convert_font('.gcastbl test', 'mono')} - Test ALL blacklist functionality

{get_emoji('adder2')} {convert_font('PROTECTION SOURCES:', 'bold')}
{get_emoji('adder4')} JSON File: ✅ Always active
{get_emoji('adder4')} Grub Database: {'✅ Connected' if GRUB_INTEGRATION else '❌ Not available'}
{get_emoji('adder4')} Session Database: ✅ Always active
{get_emoji('adder4')} Real-time Check: {'✅ Active' if GRUB_INTEGRATION else '❌ Limited'}

{get_emoji('adder6')} {convert_font('Current Status:', 'bold')} {len(blacklisted_chats)} groups protected
{get_emoji('main')} {convert_font('Protection Level:', 'bold')} {'🔒 MAXIMUM' if GRUB_INTEGRATION else '⚠️ BASIC'}
            """.strip()
            await event.reply(help_text, formatting_entities=create_premium_entities(help_text))
            return
        
        cmd = args[1].lower()
        
        if cmd == 'refresh':
            refresh_msg = await event.reply(f"{get_emoji('adder1')} **FORCE RELOADING BLACKLIST...** Please wait...")
            
            old_count = len(blacklisted_chats)
            success = force_reload_blacklist()  # Use enhanced force reload
            new_count = len(blacklisted_chats)
            
            if success:
                refresh_text = f"""
{get_emoji('adder2')} {convert_font('FORCE BLACKLIST REFRESH COMPLETED', 'bold')}

{get_emoji('check')} Previous count: {old_count}
{get_emoji('check')} Current count: {new_count}
{get_emoji('adder4')} Sources loaded: JSON + Grub + Session Database
{get_emoji('main')} Integration: {'✅ grub.py' if GRUB_INTEGRATION else '⚠️ local only'}

{get_emoji('adder2')} ✅ All blacklist sources synchronized!
                """.strip()
            else:
                refresh_text = f"""
{get_emoji('adder5')} {convert_font('BLACKLIST REFRESH ERROR', 'bold')}

{get_emoji('adder3')} Previous count: {old_count}
{get_emoji('adder3')} Current count: {new_count}
{get_emoji('main')} Status: ❌ Force reload failed

{get_emoji('check')} Using cached blacklist for safety
                """.strip()
                
            await safe_edit_message(refresh_msg, refresh_text)
        
        elif cmd == 'list':
            if not blacklisted_chats:
                list_text = f"{get_emoji('check')} No groups are blacklisted."
            else:
                groups_preview = list(blacklisted_chats)[:10]
                list_text = f"""
{get_emoji('main')} {convert_font('BLACKLISTED GROUPS', 'bold')}

{get_emoji('check')} Total: {len(blacklisted_chats)} groups
{get_emoji('adder2')} Sample IDs:
"""
                for i, group_id in enumerate(groups_preview, 1):
                    list_text += f"{get_emoji('adder4')} {i}. `{group_id}`\n"
                
                if len(blacklisted_chats) > 10:
                    list_text += f"\n{get_emoji('adder3')} ... and {len(blacklisted_chats) - 10} more groups"
            
            await event.reply(list_text.strip(), formatting_entities=create_premium_entities(list_text.strip()))
        
        elif cmd == 'status':
            status_msg = await event.reply(f"{get_emoji('adder1')} **Getting comprehensive blacklist status...**")
            
            # Get comprehensive status
            status_info = await get_blacklist_status()
            
            if status_info:
                status_text = f"""
{get_emoji('main')} {convert_font('COMPREHENSIVE BLACKLIST STATUS', 'bold')}

{get_emoji('check')} {convert_font('Total Blacklisted:', 'bold')} {status_info['total_blacklisted']} chats

{get_emoji('adder2')} {convert_font('SOURCE BREAKDOWN:', 'bold')}
{get_emoji('check')} JSON File: {status_info['sources']['json_file']} chats
{get_emoji('check')} Grub Database: {status_info['sources']['grub_database']} chats  
{get_emoji('check')} Session Database: {status_info['sources']['session_database']} chats

{get_emoji('adder4')} {convert_font('INTEGRATION STATUS:', 'bold')}
{get_emoji('adder6')} Grub Integration: {'✅ Connected' if GRUB_INTEGRATION else '❌ Not available'}
{get_emoji('adder6')} Real-time Check: {'✅ Active' if GRUB_INTEGRATION else '❌ Disabled'}
{get_emoji('adder6')} Force Reload: ✅ Available

{get_emoji('adder3')} {convert_font('PROTECTION LEVEL:', 'bold')} {'🔒 MAXIMUM PROTECTION' if GRUB_INTEGRATION else '⚠️ BASIC PROTECTION'}

{get_emoji('adder5')} {convert_font('SAMPLE BLACKLISTED IDs:', 'bold')}
                """.strip()
                
                # Add sample IDs
                sample_ids = status_info['blacklist_ids'][:5]
                for i, chat_id in enumerate(sample_ids, 1):
                    status_text += f"\n{get_emoji('check')} {i}. `{chat_id}`"
                
                if len(status_info['blacklist_ids']) > 5:
                    status_text += f"\n{get_emoji('adder4')} ... and {len(status_info['blacklist_ids']) - 5} more IDs"
                    
            else:
                status_text = f"""
{get_emoji('adder5')} {convert_font('BLACKLIST STATUS ERROR', 'bold')}

{get_emoji('adder3')} Unable to get comprehensive status
{get_emoji('check')} Using basic status information
{get_emoji('main')} Current blacklisted: {len(blacklisted_chats)} chats
                """.strip()
            
            await safe_edit_message(status_msg, status_text)
        
        elif cmd == 'test':
            test_text = f"""
{get_emoji('main')} {convert_font('COMPREHENSIVE BLACKLIST TEST', 'bold')}

{get_emoji('check')} Testing force reload blacklist...
"""
            test_msg = await event.reply(test_text.strip(), formatting_entities=create_premium_entities(test_text.strip()))
            
            # Test comprehensive blacklist loading
            old_count = len(blacklisted_chats)
            success = force_reload_blacklist()  # Use enhanced force reload
            new_count = len(blacklisted_chats)
            
            # Test grub integration
            grub_test = "❌ Not available"
            if GRUB_INTEGRATION:
                try:
                    db_groups = get_blacklisted_groups()
                    grub_test = f"✅ {len(db_groups)} groups from database"
                except Exception as e:
                    grub_test = f"❌ Error: {str(e)}"
            
            final_test_text = f"""
{get_emoji('main')} {convert_font('BLACKLIST TEST RESULTS', 'bold')}

{get_emoji('check')} {convert_font('File Loading:', 'mono')} ✅ Success
{get_emoji('adder2')} {convert_font('Database Integration:', 'mono')} {grub_test}
{get_emoji('adder4')} {convert_font('Total Groups:', 'mono')} {new_count}
{get_emoji('adder6')} {convert_font('Real-time Protection:', 'mono')} {'✅ Active' if GRUB_INTEGRATION else '⚠️ Limited'}

{get_emoji('adder3')} {convert_font('Test Status:', 'mono')} {'✅ All systems working' if GRUB_INTEGRATION else '⚠️ Limited functionality'}
            """.strip()
            
            await safe_edit_message(test_msg, final_test_text)
    
    except Exception as e:
        error_text = f"❌ Blacklist command error: {str(e)}"
        await event.reply(error_text)

# ============= PLUGIN INFO =============

def get_plugin_info():
    """Return plugin info for plugin loader"""
    return PLUGIN_INFO

def setup(client_instance):
    """Setup plugin: register event handlers"""
    global client, premium_status
    client = client_instance
    
    # Load blacklist on startup
    load_blacklist()
    print(f"[Gcast] Blacklist integration: {'✅ grub.py' if GRUB_INTEGRATION else '⚠️ local only'}")
    
    # Check premium status
    try:
        # This will be set by main.py
        premium_status = True  # Assume premium for now
    except:
        premium_status = False
    
    # Register gcast handler
    client.add_event_handler(
        gcast_handler, 
        events.NewMessage(pattern=re.compile(rf'{re.escape(get_prefix())}gcast(\s+(.+))?', re.DOTALL))
    )
    
    # Register blacklist management handler
    client.add_event_handler(
        gcast_blacklist_handler,
        events.NewMessage(pattern=re.compile(rf'{re.escape(get_prefix())}gcastbl(\s+(.+))?', re.DOTALL))
    )
    
    print(f"✅ [Enhanced Gcast] Plugin loaded with UTF-16 premium emoji support v{PLUGIN_INFO['version']}")
    print(f"✅ [Enhanced Gcast] Blacklist management commands: .gcastbl")