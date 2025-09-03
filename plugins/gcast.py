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

# Premium Emoji Mapping - Enhanced dengan semua emoji yang tersedia
PREMIUM_EMOJIS = {
    'main': {'id': '5260637271702389570', 'char': '🤩', 'length': 2},
    'check': {'id': '5794353925360457382', 'char': '⚙️', 'length': 2},
    'adder1': {'id': '5794407002566300853', 'char': '⛈', 'length': 1},
    'adder2': {'id': '5793913811471700779', 'char': '✅', 'length': 1}, 
    'adder3': {'id': '5321412209992033736', 'char': '👽', 'length': 2},
    'adder4': {'id': '5793973133559993740', 'char': '✈️', 'length': 2},
    'adder5': {'id': '5357404860566235955', 'char': '😈', 'length': 2},
    'adder6': {'id': '5794323465452394551', 'char': '🎚', 'length': 2},
    'adder7': {'id': '5794424002667300874', 'char': '🔥', 'length': 2},
    'adder8': {'id': '5794353925360457333', 'char': '🎅', 'length': 2},
    'adder9': {'id': '5262927296725007707', 'char': '🤪', 'length': 2},
    'adder10': {'id': '5794407002566300999', 'char': '🥳', 'length': 2}
}

# Global variables
client = None
blacklisted_chats = {-1002785371546}  # PV REVERIES permanent blacklist
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
    """Create premium emoji entities dengan improved error handling"""
    if not text:
        return []
        
    entities = []
    
    try:
        # Convert text to bytes untuk accurate UTF-16 calculation
        text_bytes = text.encode('utf-8')
        utf16_text = text_bytes.decode('utf-8').encode('utf-16-le')
        
        utf16_offset = 0
        char_index = 0
        
        while char_index < len(text):
            found_emoji = False
            
            # Check untuk setiap premium emoji
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_len = len(emoji_char)
                
                # Match emoji di posisi saat ini
                if char_index + emoji_len <= len(text) and text[char_index:char_index + emoji_len] == emoji_char:
                    try:
                        # Validate document_id
                        doc_id = int(emoji_data['id'])
                        if doc_id <= 0:
                            char_index += emoji_len
                            utf16_offset += emoji_data.get('length', 2)
                            found_emoji = True
                            break
                        
                        # Create entity dengan proper UTF-16 length
                        entity = MessageEntityCustomEmoji(
                            offset=utf16_offset,
                            length=emoji_data.get('length', 2),
                            document_id=doc_id
                        )
                        entities.append(entity)
                        
                        char_index += emoji_len
                        utf16_offset += emoji_data.get('length', 2)
                        found_emoji = True
                        break
                        
                    except (ValueError, OverflowError, TypeError) as e:
                        # Skip invalid emoji dan continue
                        char_index += emoji_len
                        utf16_offset += emoji_data.get('length', 2)
                        found_emoji = True
                        break
            
            # Jika bukan premium emoji, hitung UTF-16 offset untuk character biasa
            if not found_emoji:
                try:
                    char = text[char_index]
                    # Calculate proper UTF-16 length untuk character ini
                    char_utf16_bytes = char.encode('utf-16-le')
                    char_utf16_length = len(char_utf16_bytes) // 2
                    utf16_offset += char_utf16_length
                    char_index += 1
                except (UnicodeEncodeError, UnicodeDecodeError):
                    # Fallback untuk problematic characters
                    utf16_offset += 1
                    char_index += 1
        
        return entities
        
    except Exception as e:
        # Return empty list jika ada error
        return []

def extract_all_premium_entities(message):
    """Extract dan validate semua premium emoji entities dari message"""
    if not message:
        return []
        
    # Check untuk entities di message
    if not hasattr(message, 'entities') or not message.entities:
        return []
    
    premium_entities = []
    
    try:
        for entity in message.entities:
            # Validate custom emoji entity
            if (hasattr(entity, 'document_id') and 
                hasattr(entity, 'offset') and 
                hasattr(entity, 'length') and
                entity.document_id is not None):
                
                try:
                    # Validate document_id adalah valid integer
                    doc_id = int(entity.document_id)
                    if doc_id > 0:  # Valid document_id harus positive
                        # Create clean entity copy untuk avoid reference issues
                        clean_entity = MessageEntityCustomEmoji(
                            offset=int(entity.offset),
                            length=int(entity.length),
                            document_id=doc_id
                        )
                        premium_entities.append(clean_entity)
                        
                except (ValueError, TypeError, OverflowError):
                    # Skip invalid entities
                    continue
        
        return premium_entities
        
    except Exception as e:
        # Return empty list untuk prevent errors
        return []

async def safe_send_premium(event, text):
    """Send message dengan premium entities dan error handling"""
    if not text:
        return None
        
    try:
        # Create entities untuk premium emojis
        entities = create_premium_entities(text)
        
        if entities:
            # Try send dengan formatting entities
            try:
                return await event.reply(text, formatting_entities=entities)
            except Exception:
                # Fallback ke plain text jika entities failed
                return await event.reply(text)
        else:
            # Send plain text jika no premium emojis
            return await event.reply(text)
            
    except Exception as e:
        # Ultimate fallback - send simple text
        try:
            return await event.reply(text)
        except Exception:
            # If even plain text fails, send minimal error message
            return await event.reply(f"{get_emoji('adder5')} Message send failed")

# ============= BLACKLIST MANAGEMENT =============

def load_blacklist():
    """Load blacklist dengan improved error handling dan validation"""
    global blacklisted_chats
    
    try:
        # Ensure blacklist directory exists
        os.makedirs(os.path.dirname(BLACKLIST_FILE), exist_ok=True)
        
        if os.path.exists(BLACKLIST_FILE) and os.path.getsize(BLACKLIST_FILE) > 0:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    
                    # Validate data structure
                    if isinstance(data, dict) and 'blacklisted_chats' in data:
                        # Validate dan convert chat IDs
                        valid_ids = set()
                        for chat_id in data['blacklisted_chats']:
                            try:
                                # Convert ke int dan validate
                                validated_id = int(chat_id)
                                # Skip invalid IDs (0 atau positive - Telegram IDs should be negative for groups)
                                if validated_id != 0:
                                    valid_ids.add(validated_id)
                            except (ValueError, TypeError):
                                continue
                        
                        blacklisted_chats = valid_ids
                        print(f"[Gcast] Loaded {len(blacklisted_chats)} blacklisted chats")
                        return blacklisted_chats
                        
                    else:
                        print("[Gcast] Invalid blacklist format, using empty blacklist")
                        
                except json.JSONDecodeError as e:
                    print(f"[Gcast] JSON decode error: {e}")
                except Exception as e:
                    print(f"[Gcast] Error parsing blacklist: {e}")
        else:
            print("[Gcast] Blacklist file not found atau empty")
            
    except Exception as e:
        print(f"[Gcast] Error loading blacklist: {e}")
    
    # Fallback ke empty set
    blacklisted_chats = {-1002785371546}  # PV REVERIES permanent blacklist
    print("[Gcast] Using empty blacklist")
    return blacklisted_chats

def is_chat_blacklisted(chat_id):
    """Check if chat is blacklisted dengan validation - ENHANCED"""
    if not chat_id:
        return True  # Protect against None/empty IDs
        
    try:
        # Convert dan validate chat_id
        validated_id = int(chat_id)
        
        # Hard-coded check untuk PV REVERIES
        if validated_id == -1002785371546:
            print(f"[Blacklist] PERMANENT BLOCK: PV REVERIES (ID: {validated_id})")
            return True
            
        # Check dalam blacklist set
        is_blocked = validated_id in blacklisted_chats
        
        if is_blocked:
            print(f"[Blacklist] BLOCKED: Chat {validated_id} - blacklisted")
            
        return is_blocked
        
    except (ValueError, TypeError):
        # If can't convert, treat as blacklisted untuk safety
        return True

# ============= GCAST FUNCTIONS =============

async def get_broadcast_channels():
    """Get valid channels dengan enhanced filtering dan blacklist protection"""
    print("[Gcast] Getting broadcast channels...")
    
    # Load dan validate blacklist dengan logging detail
    load_blacklist()
    print(f"[Gcast] Blacklist protection: {len(blacklisted_chats)} chats blocked")
    print(f"[Gcast] Blacklisted IDs: {list(blacklisted_chats)}")
    
    # Double check PV REVERIES specifically
    pv_reveries_id = -1002785371546
    if pv_reveries_id in blacklisted_chats:
        print(f"[Gcast] ✅ PV REVERIES ({pv_reveries_id}) CONFIRMED in blacklist")
    else:
        print(f"[Gcast] ❌ WARNING: PV REVERIES ({pv_reveries_id}) NOT in blacklist - adding now")
        blacklisted_chats.add(pv_reveries_id)
    
    channels = []
    blocked_count = 0
    invalid_count = 0
    
    try:
        # Get all dialogs dengan timeout protection
        dialogs = []
        async for dialog in client.iter_dialogs(limit=None):
            dialogs.append(dialog)
            
        print(f"[Gcast] Found {len(dialogs)} total dialogs")
        
        for dialog in dialogs:
            try:
                entity = dialog.entity
                
                # Skip users (PVs)
                if isinstance(entity, User):
                    continue
                
                # Validate entity has required attributes
                if not hasattr(entity, 'id') or not hasattr(entity, 'title'):
                    invalid_count += 1
                    continue
                
                entity_id = entity.id
                entity_title = getattr(entity, 'title', f'Unknown_{entity_id}')
                
                # Check blacklist protection - STRICT BLOCKING
                if entity_id in blacklisted_chats:
                    blocked_count += 1
                    print(f"[Gcast] BLOCKED: {entity_title} (ID: {entity_id}) - Tidak bisa kirim GCast, karena blacklist")
                    continue
                
                # Double check untuk ID spesifik PV REVERIES
                if entity_id == -1002785371546:
                    blocked_count += 1
                    print(f"[Gcast] PERMANENT BLOCK: PV REVERIES (ID: {entity_id}) - Vzoel Fox's private group")
                    continue
                
                # Filter valid channels dan groups
                if isinstance(entity, (Chat, Channel)):
                    # For broadcast channels, check permissions
                    if isinstance(entity, Channel) and getattr(entity, 'broadcast', False):
                        # Check if we have permission to post
                        if not (getattr(entity, 'creator', False) or 
                               (hasattr(entity, 'admin_rights') and entity.admin_rights and 
                                getattr(entity.admin_rights, 'post_messages', False))):
                            invalid_count += 1
                            continue
                    
                    # Check if channel/group is accessible
                    if hasattr(entity, 'left') and entity.left:
                        invalid_count += 1
                        continue
                        
                    # Check if we're banned atau restricted
                    if hasattr(entity, 'banned_rights') and entity.banned_rights:
                        if getattr(entity.banned_rights, 'send_messages', False):
                            invalid_count += 1
                            continue
                    
                    # Add valid channel
                    channel_info = {
                        'entity': entity,
                        'id': entity_id,
                        'title': entity_title,
                        'type': 'Channel' if (isinstance(entity, Channel) and getattr(entity, 'broadcast', False)) else 'Group'
                    }
                    
                    channels.append(channel_info)
                    
            except Exception as e:
                invalid_count += 1
                print(f"[Gcast] Error processing dialog: {str(e)[:50]}")
                continue
        
        print(f"[Gcast] Results: {len(channels)} valid, {blocked_count} protected, {invalid_count} invalid")
        return channels
        
    except Exception as e:
        print(f"[Gcast] Error getting channels: {e}")
        return []

async def execute_gcast(message_text, entities=None, progress_callback=None):
    """Execute gcast dengan enhanced error handling dan markdown preservation"""
    if not message_text or not message_text.strip():
        return {
            'success': False,
            'error': 'Empty message text',
            'channels_total': 0
        }
    
    # Force reload blacklist untuk ensure PV REVERIES diblok
    load_blacklist()
    pv_reveries_id = -1002785371546
    if pv_reveries_id not in blacklisted_chats:
        blacklisted_chats.add(pv_reveries_id)
        print(f"[Gcast] FORCE ADDED PV REVERIES ({pv_reveries_id}) to blacklist")
    
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
    
    # Validate dan prepare entities
    validated_entities = []
    if entities:
        for entity in entities:
            if (hasattr(entity, 'document_id') and 
                hasattr(entity, 'offset') and 
                hasattr(entity, 'length') and
                entity.document_id is not None):
                try:
                    # Create clean entity copy
                    clean_entity = MessageEntityCustomEmoji(
                        offset=int(entity.offset),
                        length=int(entity.length),
                        document_id=int(entity.document_id)
                    )
                    validated_entities.append(clean_entity)
                except (ValueError, TypeError):
                    continue
    else:
        # Create entities untuk UI premium emojis
        validated_entities = create_premium_entities(message_text)
    
    # Semaphore untuk limit concurrent sends
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def send_to_channel(channel_info):
        async with semaphore:
            channel_id = channel_info['id']
            channel_title = channel_info.get('title', 'Unknown')
            
            try:
                # Rate limiting delay
                await asyncio.sleep(GCAST_DELAY)
                
                # Send message dengan hybrid support: premium entities + markdown
                try:
                    # Always try to send with markdown enabled for text formatting
                    await client.send_message(
                        channel_id,
                        message_text,
                        formatting_entities=validated_entities if validated_entities else None,
                        parse_mode='md'  # Always enable markdown
                    )
                except Exception as markdown_error:
                    # Fallback: send with entities only (no markdown)
                    if validated_entities:
                        await client.send_message(
                            channel_id,
                            message_text,
                            formatting_entities=validated_entities,
                            parse_mode=None
                        )
                    else:
                        # Final fallback: plain text
                        await client.send_message(channel_id, message_text)
                
                results['channels_success'] += 1
                return True
                
            except FloodWaitError as e:
                # Handle flood wait
                wait_time = min(e.seconds, 60)  # Max 60 seconds wait
                await asyncio.sleep(wait_time)
                
                try:
                    # Retry send with hybrid support
                    try:
                        await client.send_message(
                            channel_id,
                            message_text,
                            formatting_entities=validated_entities if validated_entities else None,
                            parse_mode='md'
                        )
                    except Exception:
                        # Final retry without markdown
                        if validated_entities:
                            await client.send_message(
                                channel_id,
                                message_text,
                                formatting_entities=validated_entities,
                                parse_mode=None
                            )
                        else:
                            await client.send_message(channel_id, message_text)
                    results['channels_success'] += 1
                    return True
                    
                except Exception as retry_error:
                    results['channels_failed'] += 1
                    results['errors'].append(f"Retry failed for {channel_title}: {str(retry_error)}")
                    return False
                    
            except ChatWriteForbiddenError:
                results['channels_failed'] += 1
                results['errors'].append(f"Permission denied: {channel_title}")
                return False
                
            except Exception as e:
                results['channels_failed'] += 1
                error_msg = str(e)[:100]  # Limit error message length
                results['errors'].append(f"Error in {channel_title}: {error_msg}")
                return False
    
    # Execute all sends dengan progress tracking
    tasks = [send_to_channel(channel_info) for channel_info in channels]
    completed_count = 0
    
    for task in asyncio.as_completed(tasks):
        await task
        completed_count += 1
        
        # Progress callback every 3 completions atau major milestones
        if progress_callback and (completed_count % 3 == 0 or completed_count in [1, len(channels)]):
            await progress_callback(completed_count, len(channels))
    
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
                # Use additional text dari command dengan markdown support
                message_text = command_text.strip()
                message_entities = None  # Create new entities untuk command text
            else:
                # Use replied message dengan preserve entities dan markdown
                message_text = reply_message.text or reply_message.message or ""
                
                # Extract premium emoji entities dari reply
                message_entities = extract_all_premium_entities(reply_message)
                
                # Log entity extraction
                if message_entities:
                    print(f"[Gcast] Extracted {len(message_entities)} premium emoji entities from reply")
                else:
                    print("[Gcast] No premium emoji entities found, using markdown parsing")
                
            # Validate message text
            if not message_text or not message_text.strip():
                await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** No text found in message!")
                return
                
        else:
            if not event.pattern_match.group(2):
                usage_text = f"""{get_emoji('main')} **GCAST USAGE**

{get_emoji('check')} **Text Gcast:** `.gcast <your message>`
{get_emoji('adder1')} **Reply Gcast:** Reply to message + `.gcast`
{get_emoji('adder2')} **Reply with text:** Reply + `.gcast <additional text>`

{get_emoji('adder3')} **Premium Emoji:** Reply ke message dengan premium emoji untuk broadcast unlimited emojis
{get_emoji('adder4')} **Markdown Support:** _italic_, **bold**, `code`, [links](url)
{get_emoji('adder6')} **Blacklist:** `.gcastbl <refresh|list|status>`"""
                
                await safe_send_premium(event, usage_text)
                return
                
            # Get text dari command dengan markdown preservation
            raw_text = event.pattern_match.group(2)
            if raw_text:
                message_text = raw_text.strip()
                # Don't create entities untuk typed text - let markdown parsing handle it
                message_entities = None
            else:
                await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** Empty message text!")
                return
        
        # Show animated starting message
        emoji_info = ""
        if message_entities:
            emoji_info = f"\n{get_emoji('adder3')} Premium emojis: {len(message_entities)} entities preserved"
        
        # Animation frames untuk startup
        animation_frames = [
            f"{get_emoji('main')} Initializing GCAST {get_emoji('adder7')}",
            f"{get_emoji('check')} Loading channels {get_emoji('adder8')}",
            f"{get_emoji('adder1')} Processing blacklist {get_emoji('adder9')}",
            f"{get_emoji('adder4')} Preparing broadcast {get_emoji('adder10')}"
        ]
        
        progress_msg = await safe_send_premium(event, animation_frames[0])
        
        # Animate startup
        for i, frame in enumerate(animation_frames[1:], 1):
            await asyncio.sleep(0.8)
            try:
                frame_text = f"{frame}\n\n{get_emoji('main')} Step {i+1}/4 completed{emoji_info}"
                await progress_msg.edit(frame_text, formatting_entities=create_premium_entities(frame_text))
            except MessageNotModifiedError:
                pass
        
        await asyncio.sleep(1)
        
        # Enhanced progress callback dengan animasi
        progress_emojis = [get_emoji('adder7'), get_emoji('adder8'), get_emoji('adder9'), get_emoji('adder10')]
        
        async def progress_update(completed, total):
            try:
                # Rotating emoji berdasarkan progress
                emoji_idx = (completed // 5) % len(progress_emojis)
                progress_emoji = progress_emojis[emoji_idx]
                
                # Calculate percentage
                percentage = int((completed / total) * 100) if total > 0 else 0
                
                # Progress bar dengan emoji
                bar_length = 20
                filled_length = int((completed / total) * bar_length) if total > 0 else 0
                progress_bar = '▓' * filled_length + '░' * (bar_length - filled_length)
                
                progress_text = f"""{get_emoji('main')} GCAST Broadcasting {progress_emoji}

{get_emoji('check')} Progress: [{progress_bar}] {percentage}%
{get_emoji('adder2')} Sent: {completed}/{total} channels
{get_emoji('adder4')} Status: Broadcasting to groups..."""
                
                await progress_msg.edit(progress_text, formatting_entities=create_premium_entities(progress_text))
            except (MessageNotModifiedError, Exception):
                pass
        
        # Execute gcast dengan entities (unlimited support)
        result = await execute_gcast(message_text, message_entities, progress_update)
        
        # Animated completion dengan celebration
        if result['success']:
            # Success animation
            celebration_frames = [
                f"{get_emoji('adder7')} GCAST Finishing...",
                f"{get_emoji('adder8')} GCAST Complete!",
                f"{get_emoji('adder9')} Success!",
                f"{get_emoji('adder10')} Ready!"
            ]
            
            for frame in celebration_frames:
                await asyncio.sleep(0.5)
                try:
                    await progress_msg.edit(frame, formatting_entities=create_premium_entities(frame))
                except MessageNotModifiedError:
                    pass
            
            # Final success message
            emoji_sent = ""
            if message_entities:
                emoji_sent = f"\n{get_emoji('adder3')} Premium emojis: {len(message_entities)} entities broadcasted"
            
            success_rate = (result['channels_success'] / result['channels_total'] * 100) if result['channels_total'] > 0 else 0
            
            success_text = f"""{get_emoji('main')} GCAST COMPLETED {get_emoji('adder10')}

{get_emoji('adder2')} Successfully sent: {result['channels_success']} groups
{get_emoji('adder7')} Success rate: {success_rate:.1f}%
{get_emoji('check')} Failed: {result['channels_failed']} groups
{get_emoji('adder4')} Completed at: {datetime.now().strftime('%H:%M:%S')}{emoji_sent}

{get_emoji('main')} Ready for next broadcast {get_emoji('adder8')}"""
            
            await asyncio.sleep(1)
            await progress_msg.edit(success_text, formatting_entities=create_premium_entities(success_text))
        else:
            # Error animation
            error_frames = [
                f"{get_emoji('adder5')} GCAST Failed...",
                f"{get_emoji('adder5')} Error detected"
            ]
            
            for frame in error_frames:
                await asyncio.sleep(0.5)
                try:
                    await progress_msg.edit(frame, formatting_entities=create_premium_entities(frame))
                except MessageNotModifiedError:
                    pass
            
            error_text = f"""{get_emoji('adder5')} GCAST FAILED

{get_emoji('check')} Error: {result.get('error', 'Unknown error')}
{get_emoji('adder3')} Total channels: {result['channels_total']}
{get_emoji('adder4')} Time: {datetime.now().strftime('%H:%M:%S')}

{get_emoji('main')} Check blacklist and try again"""
            
            await asyncio.sleep(1)
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