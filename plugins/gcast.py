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
    "version": "1.0.0",
    "description": "Enhanced Global Cast dengan premium emoji mapping, reply support, entity preservation",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".gcast"],
    "features": ["global broadcast", "reply message support", "entity preservation", "auto UTF-16 premium emoji"]
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
        utf16_bytes = emoji_char.encode('utf-16le')
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
                text_bytes = text.encode('utf-16le')
                start_byte = entity.offset * 2
                end_byte = (entity.offset + entity.length) * 2
                
                # Validate bounds
                if end_byte <= len(text_bytes) and start_byte >= 0:
                    entity_bytes = text_bytes[start_byte:end_byte]
                    emoji_char = entity_bytes.decode('utf-16le')
                    
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

def load_blacklist():
    """Load blacklisted chat IDs from file"""
    global blacklisted_chats
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                blacklisted_chats = set(data.get('blacklisted_chats', []))
        else:
            blacklisted_chats = set()
    except Exception as e:
        print(f"[Gcast] Error loading blacklist: {e}")
        blacklisted_chats = set()

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
        
        print(f"[Gcast] Found {len(channels)} valid broadcast targets")
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
        
        # Show enhanced progress message dengan premium emoji
        progress_text = f"""
{get_emoji('adder1')} {convert_font('Gcast Gacor by Vzoel')}

{get_emoji('check')} {convert_font('Mode:', 'bold')} {'Reply + Entity Preservation' if reply_message else 'Standard Text'}
{get_emoji('adder1')} {convert_font('Status:', 'bold')} Gasss...
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
    
    print(f"✅ [Enhanced Gcast] Plugin loaded with UTF-16 premium emoji support v{PLUGIN_INFO['version']}")