#!/usr/bin/env python3
"""
Tag All Plugin dengan Premium Emoji Support - Enhanced UTF-16 Edition
File: plugins/tagall.py
Founder : Vzoel Fox's Ltpn (Enhanced Premium Emoji Mapping)
Description:
    Plugin advanced untuk tag semua member group dan cek user ID dengan dukungan 
    premium emoji yang sudah diperbarui menggunakan mapping UTF-16 terbaru.
    Fitur utama: tagall members, cek ID user via username/reply.
"""

import re
import asyncio
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError, FloodWaitError

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "tagall_premium",
    "version": "1.0.0",
    "description": "Tag all members and user ID checker with premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".tagall", ".cekid"],
    "features": ["tag all members", "user ID checker", "premium emojis"]
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

# ===== Global Client Variable =====
client = None

# ===== Helper Functions =====
async def safe_send_message(event, text):
    """Send message with error handling"""
    try:
        return await event.reply(text)
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

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

def convert_font(text):
    """Convert text to bold font"""
    return f"**{text}**"

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
                        emoji_bytes = emoji.encode('utf-16le')
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
                char_bytes = char.encode('utf-16le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

# ===== Tag All Command =====
@events.register(events.NewMessage(pattern=r'^\.tagall(?:\s+(.*))?$', outgoing=True))
async def tagall_handler(event):
    """Tag all members in group with premium emoji support"""
    global client
    if client is None:
        client = event.client
    
    try:
        # Check if in group/channel
        chat = await event.get_chat()
        if not isinstance(chat, (Channel, Chat)):
            error_text = f"{get_emoji('adder5')} {convert_font('Perintah ini hanya bisa digunakan di grup!')}"
            await event.reply(error_text, formatting_entities=create_premium_entities(error_text))
            return
        
        # Get custom message or use default
        custom_message = event.pattern_match.group(1) or "Tag All Members by Vzoel Fox"
        
        # Progress message
        progress_text = f"""
{get_emoji('adder1')} {convert_font('Memuat daftar member...')}
{get_emoji('check')} {convert_font('Mohon tunggu sebentar...')}
        """.strip()
        progress_msg = await event.reply(progress_text, formatting_entities=create_premium_entities(progress_text))
        
        # Get all participants
        participants = await client.get_participants(event.chat_id)
        
        if not participants:
            no_members_text = f"{get_emoji('adder5')} {convert_font('Tidak ada member yang ditemukan!')}"
            await safe_edit_message(progress_msg, no_members_text, create_premium_entities(no_members_text))
            return
        
        # Create tag message
        tag_message = f"{get_emoji('main')} {convert_font(custom_message)}\n\n"
        
        # Split participants into chunks to avoid message length limit
        chunk_size = 50  # Tag 50 users per message
        participant_chunks = [participants[i:i + chunk_size] for i in range(0, len(participants), chunk_size)]
        
        for chunk_index, chunk in enumerate(participant_chunks):
            current_tags = ""
            
            for user in chunk:
                # Validate user object
                if not isinstance(user, User):
                    continue
                    
                if user.username:
                    current_tags += f"@{user.username} "
                elif user.first_name:
                    # Use mention for users without username
                    current_tags += f"[{user.first_name}](tg://user?id={user.id}) "
            
            if chunk_index == 0:
                # Update first message
                final_text = tag_message + current_tags
                await safe_edit_message(progress_msg, final_text, create_premium_entities(final_text))
            else:
                # Send additional messages for remaining chunks
                chunk_text = f"{get_emoji('adder3')} {convert_font(f'Tag All - Part {chunk_index + 1}')}\n\n" + current_tags
                await event.reply(chunk_text, formatting_entities=create_premium_entities(chunk_text))
            
            # Add delay between chunks to avoid flood
            if chunk_index < len(participant_chunks) - 1:
                await asyncio.sleep(2)
        
        # Final completion message
        completion_text = f"""
{get_emoji('adder2')} {convert_font('Tag All Selesai!')}
{get_emoji('adder4')} {convert_font(f'Total member: {len(participants)}')}
{get_emoji('main')} {convert_font('By Vzoel Fox Ltpn')}
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

print("🤩 Tag All Plugin dengan Premium Emoji Support berhasil dimuat!")
print("Commands: .tagall [pesan] | .cekid [@username atau reply]")