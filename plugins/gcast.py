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

# Premium Emoji Mapping - Fixed dengan entity data yang benar
PREMIUM_EMOJIS = {
    'main': {'id': '5260637271702389570', 'char': '🤩', 'length': 2},
    'check': {'id': '5794353925360457382', 'char': '⚙️', 'length': 2},
    'adder1': {'id': '5794407002566300853', 'char': '⛈', 'length': 1},
    'adder2': {'id': '5793913811471700779', 'char': '✅', 'length': 1}, 
    'adder3': {'id': '5321412209992033736', 'char': '👽', 'length': 2},
    'adder4': {'id': '5793973133559993740', 'char': '✈️', 'length': 2},
    'adder5': {'id': '5357404860566235955', 'char': '😈', 'length': 2},
    'adder6': {'id': '5794323465452394551', 'char': '🎚', 'length': 2},
    'santa': {'id': '5260687265121712272', 'char': '🎅', 'length': 2},
    'party': {'id': '5260471374295613818', 'char': '🥳', 'length': 2}
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
BLACKLIST_FILE = "data/blacklist/gcast_blacklist.json"
LEGACY_BLACKLIST_FILE = "gcast_blacklist.json"  # For backward compatibility
MAX_CONCURRENT_GCAST = 10
GCAST_DELAY = 0.5

# Statistics
stats = {
    'gcast_sent': 0,
    'commands_executed': 0
}

# Import from central font system - STANDARDIZED
from utils.font_helper import convert_font

# ============= BLACKLIST MANAGEMENT SYSTEM =============

def load_blacklist():
    """Load blacklist from JSON file with fallback support"""
    global blacklisted_chats
    
    # Try new location first
    blacklist_files = [BLACKLIST_FILE, LEGACY_BLACKLIST_FILE]
    
    for blacklist_file in blacklist_files:
        try:
            if os.path.exists(blacklist_file):
                with open(blacklist_file, 'r') as f:
                    data = json.load(f)
                    
                    if isinstance(data, dict):
                        # Handle both old and new formats
                        if 'blacklisted_chats' in data:
                            # Old format compatibility
                            blacklisted_chats = set(int(chat_id) for chat_id in data['blacklisted_chats'])
                        else:
                            # New format - extract keys as chat IDs
                            blacklisted_chats = set(int(chat_id) for chat_id in data.keys() 
                                                  if str(chat_id).lstrip('-').isdigit())
                        
                        print(f"[Gcast] Loaded blacklist: {len(blacklisted_chats)} chats from {blacklist_file}")
                        return True
                        
        except Exception as e:
            print(f"[Gcast] Error loading {blacklist_file}: {e}")
            continue
    
    # Initialize empty blacklist if no file found
    blacklisted_chats = set()
    print("[Gcast] No blacklist file found, using empty blacklist")
    return False

def save_blacklist():
    """Save current blacklist to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(BLACKLIST_FILE), exist_ok=True)
        
        # Prepare data in new format
        blacklist_data = {}
        
        for chat_id in blacklisted_chats:
            blacklist_data[str(chat_id)] = {
                'title': f'Chat {chat_id}',
                'type': 'Unknown',
                'added_date': datetime.now().isoformat(),
                'added_by': 'gcast_sync'
            }
        
        # Add legacy format for backward compatibility
        blacklist_data['blacklisted_chats'] = list(blacklisted_chats)
        blacklist_data['metadata'] = {
            'last_updated': datetime.now().isoformat(),
            'total_blacklisted': len(blacklisted_chats),
            'version': '2.0.0'
        }
        
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(blacklist_data, f, indent=2)
        
        print(f"[Gcast] Saved blacklist: {len(blacklisted_chats)} chats")
        return True
        
    except Exception as e:
        print(f"[Gcast] Error saving blacklist: {e}")
        return False

def force_reload_blacklist():
    """ENHANCED: Force reload blacklist dari semua sumber dengan real-time check"""
    global blacklisted_chats
    print("[Gcast] FORCE RELOAD BLACKLIST - Starting comprehensive blacklist refresh...")
    
    # Step 1: Load from JSON file
    original_count = len(blacklisted_chats)
    load_blacklist()
    json_count = len(blacklisted_chats)
    
    # Step 2: Load from grub.py if available
    grub_count = 0
    if GRUB_INTEGRATION:
        try:
            from grub import get_blacklisted_groups
            grub_blacklisted = get_blacklisted_groups()
            if grub_blacklisted:
                blacklisted_chats.update(grub_blacklisted)
                grub_count = len(grub_blacklisted)
                print(f"[Gcast] Added {grub_count} chats from grub.py")
        except Exception as e:
            print(f"[Gcast] Error loading from grub.py: {e}")
    
    # Step 3: Session database integration
    session_count = 0
    try:
        # Try to load from session database if available
        if os.path.exists(DATABASE_FILE):
            import sqlite3
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gcast_blacklist'")
            if cursor.fetchone():
                cursor = conn.execute("SELECT chat_id FROM gcast_blacklist WHERE is_blacklisted=1")
                session_blacklist = [row[0] for row in cursor.fetchall()]
                blacklisted_chats.update(session_blacklist)
                session_count = len(session_blacklist)
                print(f"[Gcast] Added {session_count} chats from session database")
            conn.close()
    except Exception as e:
        print(f"[Gcast] Session database not available: {e}")
    
    total_count = len(blacklisted_chats)
    
    # Save consolidated blacklist
    save_blacklist()
    
    print(f"[Gcast] FORCE RELOAD COMPLETE:")
    print(f"  • Original: {original_count} chats")
    print(f"  • JSON: {json_count} chats")
    print(f"  • Grub: {grub_count} chats")
    print(f"  • Session: {session_count} chats")
    print(f"  • TOTAL: {total_count} chats blacklisted")
    
    return total_count

def is_chat_blacklisted(chat_id):
    """Enhanced check if chat is blacklisted with multiple sources"""
    try:
        chat_id = int(chat_id)
        
        # Check local blacklist
        if chat_id in blacklisted_chats:
            return True
        
        # Check grub integration if available
        if GRUB_INTEGRATION:
            try:
                from grub import is_blacklisted
                if is_blacklisted(chat_id):
                    return True
            except Exception:
                pass
        
        return False
        
    except Exception:
        return False

# ============= EMOJI FUNCTIONS - ENHANCED =============

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
    """Fixed: Create MessageEntityCustomEmoji entities dengan length yang benar dari entity data"""
    entities = []
    
    try:
        utf16_offset = 0
        char_index = 0
        
        while char_index < len(text):
            found_emoji = False
            
            # Check each premium emoji
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_len = len(emoji_char)
                
                # Check if text matches emoji at current position
                if text[char_index:char_index + emoji_len] == emoji_char:
                    try:
                        # Use predefined length from entity data instead of calculating
                        emoji_utf16_length = emoji_data.get('length', 2)
                        
                        # Create custom emoji entity
                        entity = MessageEntityCustomEmoji(
                            offset=utf16_offset,
                            length=emoji_utf16_length,
                            document_id=int(emoji_data['id'])
                        )
                        entities.append(entity)
                        
                        # Move position
                        char_index += emoji_len
                        utf16_offset += emoji_utf16_length
                        found_emoji = True
                        break
                        
                    except (ValueError, OverflowError) as e:
                        print(f"[Gcast] Error creating entity for {emoji_type}: {e}")
                        break
            
            if not found_emoji:
                # Regular character - calculate UTF-16 length
                try:
                    char = text[char_index]
                    char_utf16_bytes = char.encode('utf-16-le')
                    char_utf16_length = len(char_utf16_bytes) // 2
                    utf16_offset += char_utf16_length
                    char_index += 1
                except Exception:
                    char_index += 1
                    utf16_offset += 1
        
        return entities
        
    except Exception as e:
        print(f"[Gcast] Error creating premium entities: {e}")
        return []

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

# Cleaned up duplicate force_reload_blacklist function

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
    """Safely edit message with premium emoji support"""
    if not message:
        return False
    try:
        # Always create premium entities for consistent emoji display
        entities = create_premium_entities(text)
        if entities and len(entities) > 0:
            await message.edit(text, formatting_entities=entities)
        else:
            # Fallback to regular edit if no premium emojis found
            await message.edit(text)
        return True
    except MessageNotModifiedError:
        pass  # Message content unchanged
    except Exception as e:
        print(f"[Gcast] Edit message error: {e}")
        # Fallback to basic edit if entity fails
        try:
            await message.edit(text)
            return True
        except:
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
    
    # Always create premium entities for consistent emoji support
    entities = None
    try:
        # First, try to extract from reply message if available
        if reply_message and preserve_entities:
            premium_emojis = extract_premium_emoji_from_message(reply_message)
            if premium_emojis:
                print(f"[Gcast] Found {len(premium_emojis)} premium emojis in reply message")
        
        # Always create entities for the message text to ensure premium emoji support
        entities = create_premium_entities(message_text)
        if entities:
            print(f"[Gcast] Created {len(entities)} premium entities for broadcast")
        
    except Exception as e:
        print(f"[Gcast] Error creating premium entities: {e}")
        entities = None
    
    # Broadcast to all channels
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GCAST)
    
    async def send_to_channel(channel_info):
        async with semaphore:
            try:
                # Small delay to prevent rate limiting
                await asyncio.sleep(GCAST_DELAY)
                
                # Send with premium emoji support
                if entities and len(entities) > 0:
                    await client.send_message(
                        channel_info['id'], 
                        message_text,
                        formatting_entities=entities
                    )
                else:
                    # Fallback: create entities on the fly if none exist
                    fallback_entities = create_premium_entities(message_text)
                    if fallback_entities and len(fallback_entities) > 0:
                        await client.send_message(
                            channel_info['id'], 
                            message_text,
                            formatting_entities=fallback_entities
                        )
                    else:
                        await client.send_message(channel_info['id'], message_text)
                
                results['channels_success'] += 1
                stats['gcast_sent'] += 1
                
                return True
                
            except FloodWaitError as e:
                print(f"[Gcast] Flood wait {e.seconds}s for channel {channel_info['title']}")
                await asyncio.sleep(e.seconds)
                # Retry once after flood wait with premium emoji support
                try:
                    if entities and len(entities) > 0:
                        await client.send_message(
                            channel_info['id'], 
                            message_text,
                            formatting_entities=entities
                        )
                    else:
                        # Fallback for retry
                        retry_entities = create_premium_entities(message_text)
                        if retry_entities and len(retry_entities) > 0:
                            await client.send_message(
                                channel_info['id'], 
                                message_text,
                                formatting_entities=retry_entities
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
        
        # Show blacklist info before starting gcast
        blacklist_info_text = f"""{get_emoji('main')} **Starting GCAST with Blacklist Check**

{get_emoji('adder2')} **Blacklist Status:** {blacklist_status['total_blacklisted']} groups blocked
{get_emoji('adder1')} **Sources:** JSON({blacklist_status['sources']['json_file']}) + Grub({blacklist_status['sources']['grub_database']}) + Session({blacklist_status['sources']['session_database']})
{get_emoji('adder4')} **Mode:** {'Reply Mode' if reply_message else 'Text Mode'}

{get_emoji('santa')} **Checking all groups and starting broadcast...**"""
        
        # Send blacklist info message with proper emoji support
        progress_msg = await event.reply(blacklist_info_text)
        
        # Simple progress callback
        async def progress_update(completed, total, gcast_id):
            try:
                progress_percentage = (completed/total)*100 if total > 0 else 0
                simple_progress = f"""{get_emoji('main')} **GCAST in Progress**

{get_emoji('santa')} **Sending:** {completed}/{total} groups ({progress_percentage:.0f}%)
{get_emoji('adder4')} **Status:** Broadcasting..."""
                await safe_edit_message(progress_msg, simple_progress)
            except Exception as e:
                print(f"[Gcast] Error updating progress: {e}")
        
        # Execute enhanced gcast
        result = await enhanced_gcast(
            message_text=message_text,
            reply_message=reply_message,
            preserve_entities=True,
            progress_callback=progress_update
        )
        
        # Show simple final results
        if result['success']:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Simple completion message as requested
            simple_final_text = f"""{get_emoji('main')} **GCAST by vzoel assistant done**

{get_emoji('adder2')} **Sent to {result['channels_success']} groups** at {current_time}

{get_emoji('santa')} **Siap untuk GCAST berikutnya**
**Userbot by Vzoel Fox's** {get_emoji('main')}"""
            
            await safe_edit_message(progress_msg, simple_final_text)
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
{get_emoji('adder4')} JSON File: {get_emoji('adder2')} Always active
{get_emoji('adder4')} Grub Database: {'{} Connected'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} Not available'.format(get_emoji('adder5'))}
{get_emoji('adder4')} Session Database: {get_emoji('adder2')} Always active
{get_emoji('adder4')} Real-time Check: {'{} Active'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} Limited'.format(get_emoji('adder5'))}

{get_emoji('adder6')} {convert_font('Current Status:', 'bold')} {len(blacklisted_chats)} groups protected
{get_emoji('main')} {convert_font('Protection Level:', 'bold')} {'{} MAXIMUM'.format(get_emoji('party')) if GRUB_INTEGRATION else '{} BASIC'.format(get_emoji('adder1'))}
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
{get_emoji('main')} Integration: {'{} grub.py'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} local only'.format(get_emoji('adder1'))}

{get_emoji('adder2')} {get_emoji('adder2')} All blacklist sources synchronized!
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
{get_emoji('adder6')} Grub Integration: {'{} Connected'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} Not available'.format(get_emoji('adder5'))}
{get_emoji('adder6')} Real-time Check: {'{} Active'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} Disabled'.format(get_emoji('adder5'))}
{get_emoji('adder6')} Force Reload: {get_emoji('adder2')} Available

{get_emoji('adder3')} {convert_font('PROTECTION LEVEL:', 'bold')} {'{} MAXIMUM PROTECTION'.format(get_emoji('party')) if GRUB_INTEGRATION else '{} BASIC PROTECTION'.format(get_emoji('adder1'))}

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
            grub_test = "{} Not available".format(get_emoji('adder5'))
            if GRUB_INTEGRATION:
                try:
                    db_groups = get_blacklisted_groups()
                    grub_test = f"{get_emoji('adder2')} {len(db_groups)} groups from database"
                except Exception as e:
                    grub_test = f"{get_emoji('adder5')} Error: {str(e)}"
            
            final_test_text = f"""
{get_emoji('main')} {convert_font('BLACKLIST TEST RESULTS', 'bold')}

{get_emoji('check')} {convert_font('File Loading:', 'mono')} {get_emoji('adder2')} Success
{get_emoji('adder2')} {convert_font('Database Integration:', 'mono')} {grub_test}
{get_emoji('adder4')} {convert_font('Total Groups:', 'mono')} {new_count}
{get_emoji('adder6')} {convert_font('Real-time Protection:', 'mono')} {'{} Active'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} Limited'.format(get_emoji('adder1'))}

{get_emoji('adder3')} {convert_font('Test Status:', 'mono')} {'{} All systems working'.format(get_emoji('adder2')) if GRUB_INTEGRATION else '{} Limited functionality'.format(get_emoji('adder1'))}
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
    print(f"[Gcast] Blacklist integration: {'{} grub.py'.format('✅') if GRUB_INTEGRATION else '{} local only'.format('⚠️')}")
    
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
