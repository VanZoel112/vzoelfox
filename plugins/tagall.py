#!/usr/bin/env python3
"""
Enhanced TagAll Plugin for VzoelFox Userbot - Premium Batch System
Fitur: Smart batch processing, reply support, stop functionality, premium emoji per username
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 2.0.0 - Enhanced Batch TagAll System
"""

import re
import asyncio
import random
import time
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User, Message
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError, FloodWaitError, MessageNotModifiedError

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "tagall_enhanced",
    "version": "2.0.0",
    "description": "Enhanced TagAll dengan batch processing, reply support, stop functionality, premium emoji per username",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".tag all <text>", ".tag all (reply)", ".stop tagall"],
    "features": ["5-member batch processing", "reply message support", "stop functionality", "premium emoji per username", "random member selection", "no markdown bugs"]
}

# Premium Emoji Mapping - Updated with UTF-16 support (mapping dari formorgan.py)
PREMIUM_EMOJIS = {
    "main":    {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check":   {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1":  {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2":  {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3":  {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4":  {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5":  {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6":  {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

# Import from central font system
from utils.font_helper import convert_font

# ===== Global Variables =====
client = None
active_tagall = {}  # Track active tagall processes per chat
tagall_stop_flags = {}  # Stop flags for tagall processes

# ===== Helper Functions =====
async def safe_send_premium(event, text):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            return await event.reply(text, formatting_entities=entities)
        else:
            return await event.reply(text)
    except Exception as e:
        print(f"Error sending message: {e}")
        return await event.reply(text)

async def safe_edit_premium(message, text):
    """Edit message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
    except MessageNotModifiedError:
        pass
    except Exception as e:
        print(f"Error editing message: {e}")
        await message.edit(text)

async def safe_edit_message(message, text, entities=None):
    """Edit message safely with error handling"""
    try:
        if message and hasattr(message, 'edit'):
            return await message.edit(text, formatting_entities=entities)
        return None
    except Exception as e:
        print(f"Error editing message: {e}")
        return None

def get_emoji(emoji_name):
    """Get emoji from premium mapping"""
    return PREMIUM_EMOJIS.get(emoji_name, {}).get("emoji", "❓")

# Import from central font system
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.font_helper import convert_font, process_markdown_bold, process_all_markdown

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support (FIXED VERSION)"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
                emoji = emoji_data["emoji"]
                custom_emoji_id = int(emoji_data["custom_emoji_id"])
                
                if text[i:].startswith(emoji):
                    try:
                        # Calculate UTF-16 length properly
                        emoji_bytes = emoji.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=custom_emoji_id
                        ))
                        
                        i += len(emoji)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

# ===== Enhanced Tag All Command System =====
@events.register(events.NewMessage(pattern=r'^\.tag all(?:\s+(.*))?$', outgoing=True))
async def enhanced_tag_all_handler(event):
    """Enhanced tag all with 5-member batch processing, premium emoji per username, stop functionality"""
    global client, active_tagall, tagall_stop_flags
    
    if client is None:
        client = event.client
    
    chat_id = event.chat_id
    
    try:
        # Check if in group/channel
        chat = await event.get_chat()
        if not isinstance(chat, (Channel, Chat)):
            error_text = f"{get_emoji('adder5')} {convert_font('Perintah ini hanya bisa digunakan di grup!')}"
            await event.reply(error_text, formatting_entities=create_premium_entities(error_text))
            return
        
        # Check if tagall already running in this chat
        if chat_id in active_tagall:
            running_text = f"{get_emoji('adder5')} {convert_font('Tag All sedang berjalan! Gunakan .stop tagall untuk memberhentikan.')}"
            await event.reply(running_text, formatting_entities=create_premium_entities(running_text))
            return
        
        # Get message - either from command parameter or replied message
        custom_message = None
        if event.is_reply:
            # Reply to message - use replied message content
            reply_message = await event.get_reply_message()
            if reply_message and reply_message.text:
                custom_message = reply_message.text
            else:
                custom_message = "Tag All Members by Vzoel Fox"
        else:
            # Text from command parameter
            custom_message = event.pattern_match.group(1) or "Tag All Members by Vzoel Fox"
        
        # Initialize tagall process
        active_tagall[chat_id] = {
            'start_time': time.time(),
            'message': custom_message,
            'total_tagged': 0
        }
        tagall_stop_flags[chat_id] = False
        
        # Progress message
        progress_text = f"""
{get_emoji('adder1')} {convert_font('Memulai Enhanced Tag All System...')}
{get_emoji('check')} {convert_font('Menggunakan batch processing 5 member per waktu')}
{get_emoji('adder3')} {convert_font('Gunakan .stop tagall untuk memberhentikan')}
        """.strip()
        progress_msg = await event.reply(progress_text, formatting_entities=create_premium_entities(progress_text))
        
        await asyncio.sleep(2)
        
        # Get all participants
        participants = await client.get_participants(event.chat_id)
        
        if not participants:
            no_members_text = f"{get_emoji('adder5')} {convert_font('Tidak ada member yang ditemukan!')}"
            await safe_edit_message(progress_msg, no_members_text, create_premium_entities(no_members_text))
            # Clean up
            if chat_id in active_tagall:
                del active_tagall[chat_id]
            if chat_id in tagall_stop_flags:
                del tagall_stop_flags[chat_id]
            return
        
        # Filter valid users and shuffle for random selection
        valid_users = [user for user in participants if isinstance(user, User) and not getattr(user, 'bot', False)]
        random.shuffle(valid_users)  # Random selection optimization
        
        # Start batch processing with 5 members at a time
        batch_size = 5
        total_batches = (len(valid_users) + batch_size - 1) // batch_size
        
        # Update progress message with batch info
        batch_info_text = f"""
{get_emoji('main')} {convert_font(custom_message)}

{get_emoji('adder2')} {convert_font(f'Total member: {len(valid_users)}')}
{get_emoji('adder4')} {convert_font(f'Batch processing: {total_batches} batch')}
{get_emoji('check')} {convert_font('Memulai batch tagging...')}
        """.strip()
        await safe_edit_message(progress_msg, batch_info_text, create_premium_entities(batch_info_text))
        
        await asyncio.sleep(3)
        
        # Process in batches of 5 members
        for batch_num in range(0, len(valid_users), batch_size):
            # Check stop flag
            if tagall_stop_flags.get(chat_id, False):
                stop_text = f"""
{get_emoji('adder5')} {convert_font('Tag All diberhentikan oleh pengguna!')}
{get_emoji('adder3')} {convert_font(f'Total yang sudah ditag: {active_tagall[chat_id]["total_tagged"]}')}
{get_emoji('main')} {convert_font('By Vzoel Fox Ltpn')}
                """.strip()
                await event.reply(stop_text, formatting_entities=create_premium_entities(stop_text))
                # Clean up
                if chat_id in active_tagall:
                    del active_tagall[chat_id]
                if chat_id in tagall_stop_flags:
                    del tagall_stop_flags[chat_id]
                return
            
            # Get current batch
            batch_users = valid_users[batch_num:batch_num + batch_size]
            current_batch_number = (batch_num // batch_size) + 1
            
            # Build tag message for this batch with premium emoji after each username
            batch_tags = ""
            for user in batch_users:
                if user.username:
                    batch_tags += f"@{user.username} {get_emoji('main')} "
                elif user.first_name:
                    # Use mention for users without username + premium emoji
                    display_name = user.first_name[:20]  # Limit length
                    batch_tags += f"[{display_name}](tg://user?id={user.id}) {get_emoji('main')} "
            
            # Create batch message
            batch_message = f"""
{get_emoji('adder3')} {convert_font(f'Batch {current_batch_number}/{total_batches} - Enhanced Tag All')}

{batch_tags}

{get_emoji('adder4')} {convert_font(custom_message)}
{get_emoji('check')} {convert_font('By Vzoel Fox Ltpn')}
            """.strip()
            
            # Send batch message
            await event.reply(batch_message, formatting_entities=create_premium_entities(batch_message))
            
            # Update counter
            active_tagall[chat_id]['total_tagged'] += len(batch_users)
            
            # Wait between batches (avoid flood)
            if batch_num + batch_size < len(valid_users):
                await asyncio.sleep(4)  # 4 second delay between batches
        
        # Final completion message
        completion_text = f"""
{get_emoji('adder2')} {convert_font('Enhanced Tag All Selesai!')}
{get_emoji('main')} {convert_font(f'Total member ditag: {len(valid_users)}')}
{get_emoji('adder4')} {convert_font(f'Total batch: {total_batches}')}
{get_emoji('adder6')} {convert_font('Dengan premium emoji per username')}
{get_emoji('check')} {convert_font('By Vzoel Fox Ltpn')}
        """.strip()
        await event.reply(completion_text, formatting_entities=create_premium_entities(completion_text))
        
    except ChatAdminRequiredError:
        admin_error_text = f"{get_emoji('adder5')} {convert_font('Butuh izin admin untuk melihat member!')}"
        await event.reply(admin_error_text, formatting_entities=create_premium_entities(admin_error_text))
    except FloodWaitError as e:
        flood_text = f"{get_emoji('adder5')} {convert_font(f'Flood wait: tunggu {e.seconds} detik')}"
        await event.reply(flood_text, formatting_entities=create_premium_entities(flood_text))
    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Error: {str(e)}')}"
        await event.reply(error_text, formatting_entities=create_premium_entities(error_text))
    finally:
        # Clean up tracking variables
        if chat_id in active_tagall:
            del active_tagall[chat_id]
        if chat_id in tagall_stop_flags:
            del tagall_stop_flags[chat_id]

# ===== Stop Tag All Command =====
@events.register(events.NewMessage(pattern=r'^\.stop tagall$', outgoing=True))
async def stop_tagall_handler(event):
    """Stop active tagall process"""
    global tagall_stop_flags, active_tagall
    
    chat_id = event.chat_id
    
    try:
        if chat_id not in active_tagall:
            not_running_text = f"{get_emoji('adder5')} {convert_font('Tidak ada Tag All yang sedang berjalan di grup ini!')}"
            await event.reply(not_running_text, formatting_entities=create_premium_entities(not_running_text))
            return
        
        # Set stop flag
        tagall_stop_flags[chat_id] = True
        
        # Confirmation message
        stopping_text = f"""
{get_emoji('adder1')} {convert_font('Menghentikan Tag All...')}
{get_emoji('check')} {convert_font('Proses akan berhenti setelah batch saat ini selesai')}
        """.strip()
        await event.reply(stopping_text, formatting_entities=create_premium_entities(stopping_text))
        
    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Error menghentikan tagall: {str(e)}')}"
        await event.reply(error_text, formatting_entities=create_premium_entities(error_text))

# ===== Check User ID Command =====
@events.register(events.NewMessage(pattern=r'^\.cekid(?:\s+@?(\w+))?$', outgoing=True))
async def cekid_handler(event):
    """Check user ID by username or reply with premium emoji support"""
    global client
    if client is None:
        client = event.client
    
    try:
        target_user = None
        username = event.pattern_match.group(1)
        
        # Check if replying to a message
        if event.is_reply:
            reply_message = await event.get_reply_message()
            if reply_message and reply_message.sender:
                target_user = reply_message.sender
        
        # Check if username provided
        elif username:
            try:
                target_user = await client.get_entity(username)
            except Exception as e:
                not_found_text = f"{get_emoji('adder5')} {convert_font(f'User @{username} tidak ditemukan!')}"
                await event.reply(not_found_text, formatting_entities=create_premium_entities(not_found_text))
                return
        
        # No target found
        else:
            usage_text = f"""
{get_emoji('check')} {convert_font('Cara penggunaan:')}
{get_emoji('adder3')} `.cekid @username` - cek ID dari username
{get_emoji('adder3')} `.cekid` (reply pesan) - cek ID dari pengirim pesan
            """.strip()
            await event.reply(usage_text, formatting_entities=create_premium_entities(usage_text))
            return
        
        # Validate target user
        if not target_user:
            error_text = f"{get_emoji('adder5')} {convert_font('User tidak ditemukan!')}"
            await event.reply(error_text, formatting_entities=create_premium_entities(error_text))
            return
        
        # Display user info
        user_info_text = f"""
{get_emoji('main')} {convert_font('Informasi User')}

{get_emoji('adder2')} **ID:** `{target_user.id}`
{get_emoji('adder3')} **Nama:** {target_user.first_name or 'Tidak ada'}
{get_emoji('adder4')} **Username:** @{target_user.username or 'Tidak ada'}
{get_emoji('adder6')} **Bot:** {'Ya' if getattr(target_user, 'bot', False) else 'Tidak'}
{get_emoji('adder1')} **Premium:** {'Ya' if getattr(target_user, 'premium', False) else 'Tidak'}

{get_emoji('check')} {convert_font('By Vzoel Fox Ltpn')}
        """.strip()
        
        await event.reply(user_info_text, formatting_entities=create_premium_entities(user_info_text))
        
    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Error: {str(e)}')}"
        await event.reply(error_text, formatting_entities=create_premium_entities(error_text))

def setup(client):
    """Setup function to register event handlers with client"""
    if client:
        client.add_event_handler(enhanced_tag_all_handler)
        client.add_event_handler(stop_tagall_handler)
        client.add_event_handler(cekid_handler)
        print("⚙️ Enhanced Tagall handlers registered to client")

print("🤩 Enhanced Tag All Plugin v2.0 dengan Premium Emoji Support berhasil dimuat!")
print("Commands: .tag all [pesan] | .tag all (reply) | .stop tagall | .cekid [@username atau reply]")