#!/usr/bin/env python3
"""
Simple Global Cast Plugin for VzoelFox Userbot
Fitur: Gcast dengan blacklist support dan premium emoji
Founder Userbot: Vzoel Fox's Ltpn
Version: 2.1.0 - Simplified Clean Version
"""

import re
import os
import json
import time
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, MessageNotModifiedError

# Plugin Info
PLUGIN_INFO = {
    "name": "gcast",
    "version": "2.1.0",
    "description": "Simple Global Cast dengan blacklist integration dan premium emoji",
    "author": "Founder Userbot: Vzoel Fox's Ltpn",
    "commands": [".gcast", ".gcastbl refresh", ".gcastbl list", ".gcastbl status"],
    "features": ["global broadcast", "blacklist integration", "premium emoji support"]
}

# Premium Emoji Mapping - Hanya emoji yang ada di mapping
PREMIUM_EMOJIS = {
    'main': {'id': '5260637271702389570', 'char': '🤩', 'length': 2},
    'check': {'id': '5794353925360457382', 'char': '⚙️', 'length': 2},
    'adder1': {'id': '5794407002566300853', 'char': '⛈', 'length': 1},
    'adder2': {'id': '5793913811471700779', 'char': '✅', 'length': 1}, 
    'adder3': {'id': '5321412209992033736', 'char': '👽', 'length': 2},
    'adder4': {'id': '5793973133559993740', 'char': '✈️', 'length': 2},
    'adder5': {'id': '5357404860566235955', 'char': '😈', 'length': 2},
    'adder6': {'id': '5794323465452394551', 'char': '🎚', 'length': 2}
}

# Global variables
client = None
blacklisted_chats = set()
BLACKLIST_FILE = "data/blacklist/gcast_blacklist.json"
MAX_CONCURRENT = 5
GCAST_DELAY = 0.5

# Import font helper
try:
    from utils.font_helper import convert_font
except ImportError:
    def convert_font(text, style):
        return text

# ============= EMOJI FUNCTIONS =============

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def create_premium_entities(text):
    """Create premium emoji entities untuk mapped emojis only (untuk UI display)"""
    entities = []
    
    try:
        utf16_offset = 0
        char_index = 0
        
        while char_index < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_len = len(emoji_char)
                
                if text[char_index:char_index + emoji_len] == emoji_char:
                    try:
                        emoji_utf16_length = emoji_data.get('length', 2)
                        
                        entity = MessageEntityCustomEmoji(
                            offset=utf16_offset,
                            length=emoji_utf16_length,
                            document_id=int(emoji_data['id'])
                        )
                        entities.append(entity)
                        
                        char_index += emoji_len
                        utf16_offset += emoji_utf16_length
                        found_emoji = True
                        break
                        
                    except (ValueError, OverflowError):
                        break
            
            if not found_emoji:
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
        
    except Exception:
        return []

def extract_all_premium_entities(message):
    """Extract semua premium emoji entities dari message (unlimited support)"""
    if not message or not message.entities:
        return []
    
    premium_entities = []
    
    try:
        for entity in message.entities:
            if hasattr(entity, 'document_id') and entity.document_id:
                # This is a custom emoji entity - preserve it
                premium_entities.append(entity)
        
        return premium_entities
        
    except Exception:
        return []

async def safe_send_premium(event, text):
    """Send message dengan premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            return await event.reply(text, formatting_entities=entities)
        else:
            return await event.reply(text)
    except Exception:
        return await event.reply(text)

# ============= BLACKLIST MANAGEMENT =============

def load_blacklist():
    """Load blacklist dari file"""
    global blacklisted_chats
    
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'blacklisted_chats' in data:
                    blacklisted_chats = set(int(chat_id) for chat_id in data['blacklisted_chats'])
                    print(f"[Gcast] Loaded {len(blacklisted_chats)} blacklisted chats")
    except Exception as e:
        print(f"[Gcast] Error loading blacklist: {e}")
    
    if not blacklisted_chats:
        blacklisted_chats = set()
        print("[Gcast] No blacklist loaded")

def is_chat_blacklisted(chat_id):
    """Check if chat is blacklisted"""
    return int(chat_id) in blacklisted_chats

# ============= GCAST FUNCTIONS =============

async def get_broadcast_channels():
    """Get valid channels untuk broadcast dengan blacklist check"""
    print("[Gcast] Getting broadcast channels...")
    
    # Load blacklist terlebih dahulu
    load_blacklist()
    print(f"[Gcast] Blacklist loaded: {len(blacklisted_chats)} chats blocked")
    
    channels = []
    blocked_count = 0
    
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            if isinstance(entity, User):
                continue
            
            # Check blacklist
            if is_chat_blacklisted(entity.id):
                blocked_count += 1
                print(f"[Gcast] Blocked: {getattr(entity, 'title', 'Unknown')} (ID: {entity.id})")
                continue
            
            # Add valid channels and groups
            if isinstance(entity, (Chat, Channel)):
                if isinstance(entity, Channel) and entity.broadcast:
                    if not (entity.creator or (entity.admin_rights and entity.admin_rights.post_messages)):
                        continue
                
                channels.append({
                    'entity': entity,
                    'id': entity.id,
                    'title': getattr(entity, 'title', 'Unknown'),
                    'type': 'Channel' if isinstance(entity, Channel) and entity.broadcast else 'Group'
                })
        
        print(f"[Gcast] Valid targets: {len(channels)}, Blocked: {blocked_count}")
        return channels
        
    except Exception as e:
        print(f"[Gcast] Error getting channels: {e}")
        return []

async def execute_gcast(message_text, entities=None, progress_callback=None):
    """Execute gcast dengan support unlimited premium emoji entities"""
    channels = await get_broadcast_channels()
    
    if not channels:
        return {
            'success': False,
            'error': 'No valid broadcast channels found',
            'channels_total': 0
        }
    
    results = {
        'channels_total': len(channels),
        'channels_success': 0,
        'channels_failed': 0,
        'errors': [],
        'success': True
    }
    
    # Use provided entities (from reply message) or create for UI emojis
    if entities is None:
        entities = create_premium_entities(message_text)
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def send_to_channel(channel_info):
        async with semaphore:
            try:
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
                return True
                
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
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
                except Exception:
                    results['channels_failed'] += 1
                    return False
                    
            except (ChatWriteForbiddenError, Exception) as e:
                results['channels_failed'] += 1
                results['errors'].append(f"Error in {channel_info['title']}: {str(e)}")
                return False
    
    # Execute all sends
    tasks = [send_to_channel(channel_info) for channel_info in channels]
    
    for i, task in enumerate(asyncio.as_completed(tasks)):
        await task
        if progress_callback and (i + 1) % 5 == 0:
            await progress_callback(i + 1, len(channels))
    
    return results

# ============= EVENT HANDLERS =============

async def gcast_handler(event):
    """Main gcast command handler dengan unlimited premium emoji support"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        message_text = ""
        message_entities = None
        
        # Get message text dan entities
        if event.is_reply:
            reply_message = await event.get_reply_message()
            command_text = event.pattern_match.group(2)
            
            if command_text:
                # Use additional text dari command
                message_text = command_text.strip()
                message_entities = None  # Create new entities untuk command text
            else:
                # Use replied message dengan entities aslinya
                message_text = reply_message.text or reply_message.message or ""
                message_entities = extract_all_premium_entities(reply_message)
                
                if message_entities:
                    print(f"[Gcast] Extracted {len(message_entities)} premium emoji entities from reply")
                
            if not message_text:
                await event.reply(f"{get_emoji('adder5')} No text found in message!")
                return
                
        else:
            if not event.pattern_match.group(2):
                usage_text = f"""{get_emoji('main')} GCAST USAGE

{get_emoji('check')} Text Gcast: .gcast <your message>
{get_emoji('adder1')} Reply Gcast: Reply to message + .gcast
{get_emoji('adder2')} Reply with text: Reply + .gcast <additional text>

{get_emoji('adder3')} Premium Emoji: Reply ke message dengan premium emoji untuk broadcast unlimited emojis
{get_emoji('adder4')} Blacklist commands: .gcastbl <refresh|list|status>"""
                
                await safe_send_premium(event, usage_text)
                return
                
            message_text = event.pattern_match.group(2).strip()
            message_entities = None  # Create new entities untuk typed text
        
        # Show starting message dengan info emoji support
        emoji_info = ""
        if message_entities:
            emoji_info = f"\n{get_emoji('adder3')} Premium emojis: {len(message_entities)} entities preserved"
        
        start_msg = f"""{get_emoji('main')} Starting GCAST

{get_emoji('adder1')} Processing blacklist...
{get_emoji('check')} Preparing broadcast...{emoji_info}"""
        
        progress_msg = await safe_send_premium(event, start_msg)
        
        # Progress callback
        async def progress_update(completed, total):
            try:
                progress_text = f"""{get_emoji('main')} GCAST Progress

{get_emoji('check')} Sent: {completed}/{total}
{get_emoji('adder4')} Status: Broadcasting..."""
                
                await progress_msg.edit(progress_text, formatting_entities=create_premium_entities(progress_text))
            except Exception:
                pass
        
        # Execute gcast dengan entities (unlimited support)
        result = await execute_gcast(message_text, message_entities, progress_update)
        
        # Show final results
        if result['success']:
            emoji_sent = ""
            if message_entities:
                emoji_sent = f"\n{get_emoji('adder3')} Premium emojis: {len(message_entities)} entities sent"
            
            success_text = f"""{get_emoji('main')} GCAST Completed

{get_emoji('adder2')} Successfully sent to {result['channels_success']} groups
{get_emoji('check')} Failed: {result['channels_failed']}
{get_emoji('adder4')} Time: {datetime.now().strftime('%H:%M:%S')}{emoji_sent}

{get_emoji('main')} Ready for next GCAST"""
            
            await progress_msg.edit(success_text, formatting_entities=create_premium_entities(success_text))
        else:
            error_text = f"""{get_emoji('adder5')} GCAST Failed

{get_emoji('check')} Error: {result.get('error', 'Unknown error')}
{get_emoji('adder3')} Channels found: {result['channels_total']}"""
            
            await progress_msg.edit(error_text, formatting_entities=create_premium_entities(error_text))
        
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Gcast error: {str(e)}")

async def gcastbl_handler(event):
    """Handle blacklist management commands"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        args = event.text.split()
        
        if len(args) < 2:
            help_text = f"""{get_emoji('main')} GCAST BLACKLIST COMMANDS

{get_emoji('check')} .gcastbl refresh - Reload blacklist
{get_emoji('check')} .gcastbl list - Show blacklisted groups  
{get_emoji('check')} .gcastbl status - Show blacklist status

{get_emoji('adder2')} Current blacklisted: {len(blacklisted_chats)} groups"""
            
            await safe_send_premium(event, help_text)
            return
        
        cmd = args[1].lower()
        
        if cmd == 'refresh':
            old_count = len(blacklisted_chats)
            load_blacklist()
            new_count = len(blacklisted_chats)
            
            refresh_text = f"""{get_emoji('adder2')} Blacklist Refreshed

{get_emoji('check')} Previous: {old_count} groups
{get_emoji('check')} Current: {new_count} groups
{get_emoji('main')} Status: Updated"""
            
            await safe_send_premium(event, refresh_text)
        
        elif cmd == 'list':
            if not blacklisted_chats:
                await event.reply(f"{get_emoji('check')} No groups are blacklisted.")
            else:
                sample_ids = list(blacklisted_chats)[:10]
                list_text = f"""{get_emoji('main')} Blacklisted Groups

{get_emoji('check')} Total: {len(blacklisted_chats)} groups
{get_emoji('adder2')} Sample IDs:
"""
                for i, group_id in enumerate(sample_ids, 1):
                    list_text += f"{get_emoji('adder4')} {i}. `{group_id}`\n"
                
                if len(blacklisted_chats) > 10:
                    list_text += f"\n{get_emoji('adder3')} ... and {len(blacklisted_chats) - 10} more groups"
            
                await safe_send_premium(event, list_text)
        
        elif cmd == 'status':
            status_text = f"""{get_emoji('main')} Blacklist Status

{get_emoji('check')} Total blacklisted: {len(blacklisted_chats)} groups
{get_emoji('adder1')} File: {BLACKLIST_FILE}
{get_emoji('adder2')} Last refresh: On command
{get_emoji('adder4')} Protection: Active"""
            
            await safe_send_premium(event, status_text)
    
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Blacklist command error: {str(e)}")

async def is_owner_check(user_id):
    """Simple owner check"""
    OWNER_ID = 7847025168
    return user_id == OWNER_ID

# ============= PLUGIN SETUP =============

def get_plugin_info():
    """Return plugin info"""
    return PLUGIN_INFO

def setup(client_instance):
    """Setup plugin"""
    global client
    client = client_instance
    
    # Load blacklist
    load_blacklist()
    
    # Register handlers
    client.add_event_handler(
        gcast_handler, 
        events.NewMessage(pattern=re.compile(r'\.gcast(\s+(.+))?', re.DOTALL))
    )
    
    client.add_event_handler(
        gcastbl_handler,
        events.NewMessage(pattern=re.compile(r'\.gcastbl(\s+(.+))?', re.DOTALL))
    )
    
    print(f"✅ [Gcast] Simple version loaded v{PLUGIN_INFO['version']}")
    print(f"✅ [Gcast] Blacklist: {len(blacklisted_chats)} groups protected")

# Export functions
__all__ = ['setup', 'get_plugin_info', 'gcast_handler', 'gcastbl_handler']