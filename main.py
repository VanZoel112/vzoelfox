#!/usr/bin/env python3
"""
VZOEL ASSISTANT - PREMIUM EMOJI ENHANCED VERSION
Complete Telegram Userbot with Custom Premium Emoji Support
Author: Vzoel Fox's (LTPN)
Version: v2.3.0 Premium Emoji Enhanced
File: main.py
"""

import asyncio
import logging
import time
import random
import re
import os
import sys
import json
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import User, Chat, Channel, MessageEntityCustomEmoji
from telethon.tl.functions.messages import SendMessageRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============= CONFIGURATION =============
try:
    API_ID = int(os.getenv("API_ID", "29919905"))
    API_HASH = os.getenv("API_HASH", "717957f0e3ae20a7db004d08b66bfd30")
    SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")
    OWNER_ID = int(os.getenv("OWNER_ID", "7847025168")) if os.getenv("OWNER_ID") else None
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
except ValueError as e:
    print(f"⚠️ Configuration error: {e}")
    print("Please check your .env file")
    sys.exit(1)

# Validation
if not API_ID or not API_HASH:
    print("❌ ERROR: API_ID and API_HASH must be set in .env file!")
    print("Please create a .env file with your Telegram API credentials")
    sys.exit(1)

# Setup logging
if ENABLE_LOGGING:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler('vzoel_enhanced.log'),
            logging.StreamHandler()
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

# Global variables
start_time = None
spam_guard_enabled = False
spam_users = {}
blacklist_file = "gcast_blacklist.json"
blacklisted_chats = set()
premium_status = None  # Will store premium status after login

# Logo URLs (Imgur links)
LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"  # Ganti dengan URL logo Anda
VZOEL_LOGO = "https://imgur.com/gallery/logo-S6biYEi"  # Ganti dengan URL logo VZL

# Premium Emoji Configuration
PREMIUM_EMOJI_ID = "6156784006194009426"  # ID untuk emoji 🤩
PREMIUM_EMOJI_CHAR = "🤩"

# Standard Emoji mapping (fallback)
PREMIUM_EMOJI_MAP = {
    'fire': '🔥',
    'rocket': '🚀',
    'lightning': '⚡',
    'diamond': '💎',
    'star': '⭐',
    'check': '✅',
    'warning': '⚠️',
    'party': '🎉',
    'crown': '👑',
    'zap': '⚡',
    'boom': '💥',
    'sparkles': '✨',
    'phone': '📱',
    'user': '👤',
    'globe': '🌍',
    'premium': '🤩',  # Premium emoji utama
}

# ============= PREMIUM EMOJI FUNCTIONS =============

def create_premium_emoji(text, offset=0):
    """Create MessageEntityCustomEmoji for premium emoji"""
    return MessageEntityCustomEmoji(
        offset=offset,
        length=2,  # Length of emoji character
        document_id=int(PREMIUM_EMOJI_ID)
    )

def add_premium_emoji(text):
    """Add premium emoji to text with proper entity"""
    # Tambahkan emoji premium di awal text
    new_text = f"{PREMIUM_EMOJI_CHAR} {text}"
    entities = [create_premium_emoji(new_text, 0)]
    return new_text, entities

async def check_premium_status():
    """Check if user has Telegram Premium"""
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

def get_emoji(emoji_name, fallback=''):
    """Get emoji with premium support"""
    if emoji_name == 'premium' and premium_status:
        return PREMIUM_EMOJI_CHAR
    return PREMIUM_EMOJI_MAP.get(emoji_name, fallback)

def format_with_premium_emoji(base_text):
    """Format text with premium emoji at beginning and end"""
    if premium_status:
        return f"{PREMIUM_EMOJI_CHAR} {base_text} {PREMIUM_EMOJI_CHAR}"
    return base_text

# ============= BLACKLIST MANAGEMENT FUNCTIONS =============

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
    except Exception as e:
        logger.error(f"Error loading blacklist: {e}")
        blacklisted_chats = set()

def save_blacklist():
    """Save blacklisted chat IDs to file"""
    try:
        with open(blacklist_file, 'w') as f:
            json.dump({'blacklisted_chats': list(blacklisted_chats)}, f, indent=2)
        logger.info(f"💾 Saved {len(blacklisted_chats)} blacklisted chats")
    except Exception as e:
        logger.error(f"Error saving blacklist: {e}")

# ============= UTILITY FUNCTIONS =============

async def is_owner(user_id):
    """Check if user is owner"""
    try:
        if OWNER_ID:
            return user_id == OWNER_ID
        me = await client.get_me()
        return user_id == me.id
    except Exception as e:
        logger.error(f"Error checking owner: {e}")
        return False

async def animate_text(message, texts, delay=1.5, use_premium=False):
    """Animate text by editing message multiple times"""
    for i, text in enumerate(texts):
        try:
            if use_premium and premium_status and i == len(texts) - 1:
                # Add premium emoji to final message
                formatted_text, entities = add_premium_emoji(text)
                await message.edit(formatted_text, formatting_entities=entities)
            else:
                await message.edit(text)
            if i < len(texts) - 1:  # Don't sleep on last iteration
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Animation error: {e}")
            break

async def get_broadcast_channels():
    """Get all channels and groups for broadcasting (improved with blacklist filter)"""
    channels = []
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Skip private chats
            if isinstance(entity, User):
                continue
            
            # Skip blacklisted chats
            if entity.id in blacklisted_chats:
                continue
                
            # Include groups and channels where we can send messages
            if isinstance(entity, (Chat, Channel)):
                # For channels, check if we have broadcast rights or it's a group
                if isinstance(entity, Channel):
                    if entity.broadcast and not (entity.creator or entity.admin_rights):
                        continue  # Skip channels where we can't post
                
                channels.append({
                    'entity': entity,
                    'id': entity.id,
                    'title': getattr(entity, 'title', 'Unknown'),
                    'type': 'Channel' if isinstance(entity, Channel) and entity.broadcast else 'Group'
                })
                
    except Exception as e:
        logger.error(f"Error getting broadcast channels: {e}")
    
    return channels

async def log_command(event, command):
    """Log command usage"""
    try:
        user = await client.get_entity(event.sender_id)
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Private Chat')
        user_name = getattr(user, 'first_name', 'Unknown') or 'Unknown'
        logger.info(f"Command '{command}' used by {user_name} ({user.id}) in {chat_title}")
    except Exception as e:
        logger.error(f"Error logging command: {e}")

async def get_user_info(event, user_input=None):
    """Get user information from reply or username/id"""
    user = None
    
    try:
        if event.is_reply and not user_input:
            # Get from reply
            reply_msg = await event.get_reply_message()
            user = await client.get_entity(reply_msg.sender_id)
        elif user_input:
            # Get from username or ID
            if user_input.isdigit():
                user = await client.get_entity(int(user_input))
            else:
                # Remove @ if present
                username = user_input.lstrip('@')
                user = await client.get_entity(username)
        else:
            return None
            
        return user
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None

# ============= PLUGIN 1: ALIVE COMMAND (WITH PREMIUM EMOJI) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with premium emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "alive")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        # Base animations
        base_animations = [
            f"{get_emoji('fire', '🔥')} **Checking system status...**",
            f"{get_emoji('lightning', '⚡')} **Loading components...**",
            f"{get_emoji('rocket', '🚀')} **Initializing Vzoel Assistant...**",
        ]
        
        # Final message with premium emoji
        final_message = f"""
[🚩]({LOGO_URL}) **𝚅𝚉𝙾𝙴𝙻 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃 IS ALIVE!**

╔══════════════════════════════════╗
   {get_emoji('premium')} **𝚅 𝚉 𝙾 𝙴 𝙻  𝙰 𝚂 𝚂 𝙸 𝚂 𝚃 𝙰 𝙽 𝚃** {get_emoji('premium')}
╚══════════════════════════════════╝

{get_emoji('user', '👤')} **Name:** {me.first_name or 'Vzoel Assistant'}
🆔 **ID:** `{me.id}`
{get_emoji('phone', '📱')} **Username:** @{me.username or 'None'}
{get_emoji('lightning', '⚡')} **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
{get_emoji('fire', '🔥')} **Status:** Active & Running
📦 **Version:** v2.3.0 Premium Enhanced
🚫 **Blacklisted Chats:** `{len(blacklisted_chats)}`
{get_emoji('diamond', '💎')} **Premium:** {'Active ✓' if premium_status else 'Standard'}

{get_emoji('zap', '⚡')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji('zap', '⚡')}
        """.strip()
        
        # Add final message to animations
        alive_animations = base_animations + [final_message]
        
        msg = await event.reply(alive_animations[0])
        
        # Animate through messages
        for i in range(1, len(alive_animations)):
            await asyncio.sleep(2 if i < len(alive_animations) - 1 else 1)
            
            if i == len(alive_animations) - 1 and premium_status:
                # For final message, add premium emoji entities
                text_with_emoji, entities = add_premium_emoji(alive_animations[i])
                await msg.edit(text_with_emoji, formatting_entities=entities)
            else:
                await msg.edit(alive_animations[i])
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Alive command error: {e}")

# ============= PLUGIN 2: ENHANCED GCAST COMMAND (WITH PREMIUM EMOJI) =============

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}gcast\s+(.+)', re.DOTALL)))
async def gcast_handler(event):
    """Enhanced Global Broadcast with Premium Emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    message_to_send = event.pattern_match.group(1).strip()
    if not message_to_send:
        await event.reply("❌ **Usage:** `.gcast <message>`")
        return
    
    try:
        # Enhanced 8-phase animation with premium emoji
        gcast_animations = [
            f"{get_emoji('fire', '🔥')} **lagi otw ngegikes.......**",
            f"{get_emoji('warning', '⚠️')} **cuma gikes aja diblacklist.. kek mui ngeblacklist sound horeg wkwkwkwkwkwkwkwk...**",
            f"{get_emoji('zap', '⚡')} **dikit² blacklist...**",
            f"{get_emoji('warning', '🚫')} **dikit² maen mute...**",
            f"{get_emoji('boom', '💥')} **dikit² gban...**",
            f"{get_emoji('party', '😂')} **wkwkwkwk...**",
            f"{get_emoji('fire', '🔥')} **anying......**",
            f"{get_emoji('sparkles', '✨')} **wkwkwkwkwkwkwkwk...**"
        ]
        
        msg = await event.reply(gcast_animations[0])
        
        # Animate first 4 phases
        for i in range(1, 5):
            await asyncio.sleep(1.5)
            await msg.edit(gcast_animations[i])
        
        # Get channels (now with blacklist filtering)
        channels = await get_broadcast_channels()
        total_channels = len(channels)
        blacklisted_count = len(blacklisted_chats)
        
        if total_channels == 0:
            await msg.edit(f"{get_emoji('warning', '❌')} **No available channels found for broadcasting!**")
            return
        
        # Continue animation
        await asyncio.sleep(1.5)
        status_msg = f"{gcast_animations[5]}\n📊 **Found:** `{total_channels}` chats (🚫 `{blacklisted_count}` blacklisted)"
        await msg.edit(status_msg)
        
        await asyncio.sleep(1.5)
        broadcast_msg = f"{gcast_animations[6]}\n📊 **Broadcasting to:** `{total_channels}` chats"
        await msg.edit(broadcast_msg)
        
        # Start broadcasting
        success_count = 0
        failed_count = 0
        failed_chats = []
        
        for i, channel_info in enumerate(channels, 1):
            try:
                entity = channel_info['entity']
                
                # Send message
                await client.send_message(entity, message_to_send)
                success_count += 1
                
                # Update progress every 3 messages or on last message
                if i % 3 == 0 or i == total_channels:
                    progress = (i / total_channels) * 100
                    current_title = channel_info['title'][:20]
                    
                    progress_msg = f"""
{get_emoji('rocket', '🚀')} **lagi otw ngegikesss...**

**Total Kandang:** `{i}/{total_channels}` ({progress:.1f}%)
**Kandang yang berhasil:** `{success_count}` {get_emoji('check', '✅')}
**Kandang pelit.. alay.. dikit² maen mute** `{failed_count}` {get_emoji('warning', '⚠️')}
{get_emoji('zap', '⚡')} **Current:** {current_title}...
🚫 **Blacklisted:** `{blacklisted_count}` chats skipped
                    """.strip()
                    
                    await msg.edit(progress_msg)
                
                # Rate limiting - important!
                await asyncio.sleep(0.5)
                
            except FloodWaitError as e:
                # Handle flood wait
                wait_time = e.seconds
                if wait_time > 300:  # Skip if wait is too long
                    failed_count += 1
                    failed_chats.append(f"{channel_info['title']} (Flood: {wait_time}s)")
                    continue
                    
                await asyncio.sleep(wait_time)
                try:
                    await client.send_message(entity, message_to_send)
                    success_count += 1
                except Exception:
                    failed_count += 1
                    failed_chats.append(f"{channel_info['title']} (Flood retry failed)")
                    
            except Exception as e:
                failed_count += 1
                error_msg = str(e)[:50]
                failed_chats.append(f"{channel_info['title']} ({error_msg})")
                logger.error(f"Gcast error for {channel_info['title']}: {e}")
                continue
        
        # Final animation phase
        await asyncio.sleep(2)
        await msg.edit(gcast_animations[7])
        
        await asyncio.sleep(2)
        
        # Calculate success rate
        success_rate = (success_count / total_channels * 100) if total_channels > 0 else 0
        
        final_message = f"""
{get_emoji('sparkles', '✨')} **Gcast kelar....**

╔══════════════════════════════════╗
     **{get_emoji('premium')} 𝚅 𝚉 𝙾 𝙴 𝙻  𝙶 𝙲 𝙰 𝚂 𝚃 {get_emoji('premium')}**
╚══════════════════════════════════╝

{get_emoji('globe', '🌍')} **Total Kandang:** `{total_channels}`
{get_emoji('check', '✅')} **Kandang yang berhasil:** `{success_count}`
{get_emoji('warning', '⚠️')} **Kandang pelit.. alay.. dikit² mute:** `{failed_count}`
{get_emoji('star', '⭐')} **Success Rate:** `{success_rate:.1f}%`
🚫 **Blacklisted Chats Skipped:** `{blacklisted_count}`

{get_emoji('diamond', '💎')} **Message delivered successfully!**
{get_emoji('fire', '🔥')} **Gcast by Vzoel Assistant**
        """.strip()
        
        if premium_status:
            # Add premium emoji to final message
            final_with_emoji, entities = add_premium_emoji(final_message)
            await msg.edit(final_with_emoji, formatting_entities=entities)
        else:
            await msg.edit(final_message)
        
        # Send error log if there are failures
        if failed_chats and len(failed_chats) <= 10:  # Only show first 10 errors
            error_log = "**Failed Chats:**\n"
            for chat in failed_chats[:10]:
                error_log += f"• {chat}\n"
            if len(failed_chats) > 10:
                error_log += f"• And {len(failed_chats) - 10} more..."
                
            await event.reply(error_log)
        
    except Exception as e:
        await event.reply(f"❌ **Gcast Error:** {str(e)}")
        logger.error(f"Gcast command error: {e}")

# ============= PLUGIN 3: INFO FOUNDER (WITH PREMIUM EMOJI) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}infofounder'))
async def infofounder_handler(event):
    """Founder information with premium emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "infofounder")
    
    try:
        founder_info_base = f"""
{get_emoji('fire', '🔥')} **apa woy** {get_emoji('fire', '🔥')}
[╔══════════════════════════════════╗]({VZOEL_LOGO})
    **𝚅 𝚉 𝙾 𝙴 𝙻  𝙰 𝚂 𝚂 𝙸 𝚂 𝚃 𝙰 𝙽 𝚃** {get_emoji('crown', '👑')}
╚══════════════════════════════════╝

⟢ Founder    : **𝚅𝚣𝚘𝚎𝚕 𝙵𝚘𝚡'𝚜 (Ltpn)** {get_emoji('user', '👤')}
⟢ Instagram  : @vzoel.fox_s {get_emoji('phone', '📱')}
⟢ Telegram   : @VZLfx | @VZLfxs {get_emoji('globe', '🌍')}
⟢ Channel    : t.me/damnitvzoel {get_emoji('sparkles', '✨')}

{get_emoji('diamond', '💎')} Premium: {'Active ✓' if premium_status else 'Standard'}

{get_emoji('zap', '⚡')} Hak milik **𝚅𝚣𝚘𝚎𝚕 𝙵𝚘𝚡'𝚜** ©2025 ~ LTPN. {get_emoji('zap', '⚡')}
        """.strip()
        
        if premium_status:
            # Add premium emoji decoration
            formatted_info = format_with_premium_emoji(founder_info_base)
            info_with_emoji, entities = add_premium_emoji(formatted_info)
            await event.edit(info_with_emoji, formatting_entities=entities)
        else:
            await event.edit(founder_info_base)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"InfoFounder error: {e}")

# ============= PLUGIN 4: PING COMMAND (WITH PREMIUM EMOJI) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Ping command with premium emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "ping")
    
    try:
        start = time.time()
        msg = await event.reply(f"{get_emoji('rocket', '📡')} **Lagi ngetest ping dulu om.......**")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        # Determine latency level
        if ping_time < 100:
            latency = f"{get_emoji('lightning', '⚡')} Low"
            status_emoji = get_emoji('check', '✅')
        elif ping_time < 300:
            latency = f"{get_emoji('star', '⭐')} Normal"
            status_emoji = get_emoji('check', '✅')
        else:
            latency = f"{get_emoji('warning', '⚠️')} High"
            status_emoji = get_emoji('warning', '⚠️')
        
        ping_text_base = f"""
{get_emoji('rocket', '📡')} **Tch....**

╔══════════════════════════════════╗
   {get_emoji('premium')} **𝙿 𝙸 𝙽 𝙶  𝚁 𝙴 𝚂 𝚄 𝙻 𝚃** {get_emoji('premium')}
╚══════════════════════════════════╝

{get_emoji('lightning', '⚡')} **Response Time:** `{ping_time:.2f}ms`
{get_emoji('rocket', '🚀')} **Status:** Active
{get_emoji('fire', '🔥')} **Server:** Online
{status_emoji} **Connection:** Stable
{get_emoji('globe', '📡')} **Latency:** {latency}
{get_emoji('diamond', '💎')} **Premium:** {'Active ✓' if premium_status else 'Standard'}

{get_emoji('zap', '⚡')} **pasti aman anti delay**
        """.strip()
        
        if premium_status:
            # Add premium emoji
            ping_with_emoji, entities = add_premium_emoji(ping_text_base)
            await msg.edit(ping_with_emoji, formatting_entities=entities)
        else:
            await msg.edit(ping_text_base)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Ping error: {e}")

# ============= OTHER PLUGINS (UNCHANGED BUT KEPT FOR COMPLETENESS) =============

# [Include all other plugin handlers here - addbl, rmbl, listbl, joinvc, leavevc, vzl, id, info, help, sg, etc.]
# They remain the same as in your original code, but I'll add the premium emoji to key ones

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}addbl(\s+(.+))?'))
async def addbl_handler(event):
    """Add chat to gcast blacklist"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "addbl")
    
    try:
        # Get current chat if no argument provided
        chat_input = event.pattern_match.group(2)
        
        if chat_input:
            # Try to get chat by username/ID
            if chat_input.isdigit() or chat_input.lstrip('-').isdigit():
                chat_id = int(chat_input)
                try:
                    chat = await client.get_entity(chat_id)
                except Exception:
                    await event.reply(f"❌ **Chat ID `{chat_id}` not found!**")
                    return
            else:
                # Try by username
                try:
                    username = chat_input.lstrip('@')
                    chat = await client.get_entity(username)
                    chat_id = chat.id
                except Exception:
                    await event.reply(f"❌ **Chat `@{username}` not found!**")
                    return
        else:
            # Use current chat
            chat = await event.get_chat()
            chat_id = chat.id
        
        # Check if it's a private chat
        if isinstance(chat, User):
            await event.reply("❌ **Cannot blacklist private chats!**")
            return
        
        # Check if already blacklisted
        if chat_id in blacklisted_chats:
            chat_title = getattr(chat, 'title', 'Unknown')
            await event.reply(f"⚠️ **Chat `{chat_title}` is already blacklisted!**")
            return
        
        # Add to blacklist
        blacklisted_chats.add(chat_id)
        save_blacklist()
        
        chat_title = getattr(chat, 'title', 'Unknown')
        chat_type = 'Channel' if isinstance(chat, Channel) and chat.broadcast else 'Group'
        
        success_msg = f"""
🚫 **CHAT BLACKLISTED!**

╔══════════════════════════════════╗
   🚫 **𝙶 𝙲 𝙰 𝚂 𝚃  𝙱 𝙻 𝙰 𝙲 𝙺 𝙻 𝙸 𝚂 𝚃** 🚫
╚══════════════════════════════════╝

📍 **Chat:** {chat_title}
🆔 **ID:** `{chat_id}`
📊 **Type:** {chat_type}
✅ **Status:** Added to blacklist

📋 **Total Blacklisted:** `{len(blacklisted_chats)}`
🔥 **Action:** This chat will be skipped in gcast

⚡ **Note:** Use `{COMMAND_PREFIX}rmbl` to remove from blacklist
        """.strip()
        
        await event.edit(success_msg)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"AddBL command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}rmbl(\s+(.+))?'))
async def rmbl_handler(event):
    """Remove chat from gcast blacklist"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "rmbl")
    
    try:
        # Get current chat if no argument provided
        chat_input = event.pattern_match.group(2)
        
        if chat_input:
            # Try to get chat by username/ID
            if chat_input.isdigit() or chat_input.lstrip('-').isdigit():
                chat_id = int(chat_input)
                try:
                    chat = await client.get_entity(chat_id)
                except Exception:
                    await event.reply(f"❌ **Chat ID `{chat_id}` not found!**")
                    return
            else:
                # Try by username
                try:
                    username = chat_input.lstrip('@')
                    chat = await client.get_entity(username)
                    chat_id = chat.id
                except Exception:
                    await event.reply(f"❌ **Chat `@{username}` not found!**")
                    return
        else:
            # Use current chat
            chat = await event.get_chat()
            chat_id = chat.id
        
        # Check if blacklisted
        if chat_id not in blacklisted_chats:
            chat_title = getattr(chat, 'title', 'Unknown')
            await event.reply(f"⚠️ **Chat `{chat_title}` is not blacklisted!**")
            return
        
        # Remove from blacklist
        blacklisted_chats.remove(chat_id)
        save_blacklist()
        
        chat_title = getattr(chat, 'title', 'Unknown')
        chat_type = 'Channel' if isinstance(chat, Channel) and chat.broadcast else 'Group'
        
        success_msg = f"""
✅ **CHAT REMOVED FROM BLACKLIST!**

╔══════════════════════════════════╗
   ✅ **𝙶 𝙲 𝙰 𝚂 𝚃  𝚄 𝙽 𝙱 𝙻 𝙰 𝙲 𝙺 𝙻 𝙸 𝚂 𝚃** ✅
╚══════════════════════════════════╝

📍 **Chat:** {chat_title}
🆔 **ID:** `{chat_id}`
📊 **Type:** {chat_type}
✅ **Status:** Removed from blacklist

📋 **Total Blacklisted:** `{len(blacklisted_chats)}`
🔥 **Action:** This chat will receive gcast messages

⚡ **Note:** Use `{COMMAND_PREFIX}addbl` to add back to blacklist
        """.strip()
        
        await event.edit(success_msg)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"RmBL command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}listbl'))
async def listbl_handler(event):
    """Show all blacklisted chats"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "listbl")
    
    try:
        if not blacklisted_chats:
            await event.edit(f"""
📋 **GCAST BLACKLIST**

╔══════════════════════════════════╗
   📋 **𝙱 𝙻 𝙰 𝙲 𝙺 𝙻 𝙸 𝚂 𝚃  𝙴 𝙼 𝙿 𝚃 𝚈** 📋
╚══════════════════════════════════╝

🔥 **No chats are blacklisted**
⚡ **All chats will receive gcast**

💡 **Use `{COMMAND_PREFIX}addbl` to blacklist chats**
            """.strip())
            return
        
        blacklist_text = f"""
📋 **GCAST BLACKLIST**

╔══════════════════════════════════╗
   📋 **𝙶 𝙲 𝙰 𝚂 𝚃  𝙱 𝙻 𝙰 𝙲 𝙺 𝙻 𝙸 𝚂 𝚃** 📋
╚══════════════════════════════════╝

📊 **Total Blacklisted:** `{len(blacklisted_chats)}`

🚫 **Blacklisted Chats:**
        """.strip()
        
        count = 0
        for chat_id in blacklisted_chats:
            if count >= 20:  # Limit to prevent message too long
                blacklist_text += f"\n• And {len(blacklisted_chats) - count} more..."
                break
                
            try:
                chat = await client.get_entity(chat_id)
                chat_title = getattr(chat, 'title', 'Unknown')[:30]
                blacklist_text += f"\n• `{chat_id}` - {chat_title}"
                count += 1
            except Exception:
                blacklist_text += f"\n• `{chat_id}` - [Chat not accessible]"
                count += 1
        
        blacklist_text += f"""

💡 **Commands:**
• `{COMMAND_PREFIX}addbl [chat]` - Add to blacklist
• `{COMMAND_PREFIX}rmbl [chat]` - Remove from blacklist
• `{COMMAND_PREFIX}listbl` - Show this list
        """
        
        await event.edit(blacklist_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"ListBL command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}joinvc'))
async def joinvc_handler(event):
    """Join Voice Chat with animation"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "joinvc")
    
    try:
        chat = await event.get_chat()
        if not hasattr(chat, 'id'):
            await event.reply("❌ **Cannot join VC in this chat!**")
            return
        
        animations = [
            f"{get_emoji('rocket', '🚀')} **lagi naik ya bang.. sabar bentar...**",
            f"{get_emoji('fire', '🔥')} **kalo udah diatas ya disapa bukan dicuekin anying...**",
            f"{get_emoji('party', '🎉')} **kalo ga nimbrung berarti bot ye... wkwkwkwkwk**",
            f"""
{get_emoji('crown', '👑')} **Panglima Pizol udah diatas**

╔══════════════════════════════════╗
    **𝚅 𝙾 𝙸 𝙲 𝙴  𝙲 𝙷 𝙰 𝚃  𝙰 𝙲 𝚃 𝙸 𝚅 𝙴** {get_emoji('phone', '📞')}
╚══════════════════════════════════╝

{get_emoji('globe', '🌍')} **Kandang:** {chat.title[:30] if hasattr(chat, 'title') else 'Private'}
{get_emoji('check', '✅')} **Status:** Connected
{get_emoji('sparkles', '✨')} **Sound Horeg:** Ready
{get_emoji('diamond', '💎')} **Kualitas:** HD

⚠️ **Note:** Full VC features require pytgcalls
{get_emoji('crown', '👑')} **Pangeran Pizol udah diatas**
            """.strip()
        ]
        
        msg = await event.reply(animations[0])
        await animate_text(msg, animations, delay=1.5)
            
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"JoinVC error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}leavevc'))
async def leavevc_handler(event):
    """Leave Voice Chat with animation"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "leavevc")
    
    try:
        animations = [
            "🔥 **Disconnecting from voice chat...**",
            "🎵 **Stopping audio stream...**",
            "👋 **Leaving voice chat...**",
            f"""
✅ **VOICE CHAT LEFT!**

╔══════════════════════════════════╗
   👋 **𝚅 𝙾 𝙸 𝙲 𝙴  𝙲 𝙷 𝙰 𝚃  𝙳 𝙸 𝚂 𝙲 𝙾 𝙽 𝙽 𝙴 𝙲 𝚃 𝙴 𝙳** 👋
╚══════════════════════════════════╝

📌 **Status:** Disconnected
🎙️ **Audio:** Stopped
✅ **Action:** Completed

{get_emoji('check', '✅')} **Udah turun bang!**
{get_emoji('fire', '🔥')} **Vzoel Assistant ready for next command**
            """.strip()
        ]
        
        msg = await event.reply(animations[0])
        await animate_text(msg, animations, delay=1.5)
            
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"LeaveVC error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}vzl'))
async def vzl_handler(event):
    """Vzoel command with 12-phase animation as requested"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "vzl")
    
    try:
        # 12 animation phases as requested
        vzl_animations = [
            f"{get_emoji('fire', '🔥')} **V**",
            f"{get_emoji('fire', '🔥')} **VZ**",
            f"{get_emoji('fire', '🔥')} **VZO**", 
            f"{get_emoji('fire', '🔥')} **VZOE**",
            f"{get_emoji('fire', '🔥')} **VZOEL**",
            f"{get_emoji('rocket', '🚀')} **VZOEL F**",
            f"{get_emoji('rocket', '🚀')} **VZOEL FO**",
            f"{get_emoji('rocket', '🚀')} **VZOEL FOX**",
            f"{get_emoji('lightning', '⚡')} **VZOEL FOX'S**",
            f"{get_emoji('sparkles', '✨')} **VZOEL FOX'S A**",
            f"{get_emoji('star', '🌟')} **VZOEL FOX'S ASS**",
            f"""
[🔥]({VZOEL_LOGO}) **𝚅𝚉𝙾𝙴𝙻 𝙵𝙾𝚇'𝚂 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃** {get_emoji('fire', '🔥')}

╔══════════════════════════════════╗
   {get_emoji('fire', '🚩')} **𝚅 𝚉 𝙾 𝙴 𝙻  𝙰 𝚂 𝚂 𝙸 𝚂 𝚃 𝙰 𝙽 𝚃** {get_emoji('fire', '🚩')}
╚══════════════════════════════════╝

{get_emoji('lightning', '⚡')} **The most advanced Telegram userbot**
{get_emoji('rocket', '🚀')} **Built with passion and precision**
{get_emoji('fire', '🔥')} **Powered by Telethon & Python**
{get_emoji('sparkles', '✨')} **Created by Vzoel Fox's (LTPN)**

{get_emoji('phone', '📱')} **Features:**
• Global Broadcasting
• Voice Chat Control  
• Advanced Animations
• Multi-Plugin System
• Real-time Monitoring
• Spam Protection
• User ID Lookup
• Gcast Blacklist System
• Premium Support {get_emoji('diamond', '💎')}

{get_emoji('zap', '⚡')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji('zap', '⚡')}
            """.strip()
        ]
        
        msg = await event.reply(vzl_animations[0])
        await animate_text(msg, vzl_animations, delay=1.2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"VZL command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}id(\s+(.+))?'))
async def id_handler(event):
    """Get user ID from reply or username"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "id")
    
    try:
        user_input = event.pattern_match.group(2)
        user = await get_user_info(event, user_input)
        
        if not user:
            if event.is_reply:
                await event.reply("❌ **Could not get user from reply!**")
            else:
                await event.reply(f"❌ **Usage:** `{COMMAND_PREFIX}id` (reply to message) or `{COMMAND_PREFIX}id username/id`")
            return
        
        # Get additional info
        is_bot = getattr(user, 'bot', False)
        is_verified = getattr(user, 'verified', False)
        is_scam = getattr(user, 'scam', False)
        is_fake = getattr(user, 'fake', False)
        is_premium = getattr(user, 'premium', False)
        
        # Format status
        status_icons = []
        if is_bot:
            status_icons.append("🤖 Manusia Buatan")
        if is_verified:
            status_icons.append("✅ Woke")
        if is_premium:
            status_icons.append(f"{get_emoji('diamond', '💎')} Premium ni boss")
        if is_scam:
            status_icons.append("⚠️ Scam anying")
        if is_fake:
            status_icons.append("🚫 Faker bjirrr")
        
        status_text = " | ".join(status_icons) if status_icons else "👤 Regular User"
        
        id_info = f"""
🆔 **Ni boss informasi khodamnya**

╔══════════════════════════════════╗
    **𝙸 𝙽 𝙵 𝙾 𝚁 𝙼 𝙰 𝚂 𝙸  𝙺 𝙷 𝙾 𝙳 𝙰 𝙼** 
╚══════════════════════════════════╝

👤 **Nama Makhluk ini :** {user.first_name or 'None'} {user.last_name or ''}
🆔 **Nomor Togel:** `{user.id}`
📱 **Nama Khodam:** @{user.username or 'None'}
📞 **Phone:** `{user.phone or 'Hidden'}`
🏷️ **STATUS:** {status_text}
🌍 **Language:** `{user.lang_code or 'Unknown'}`

📊 **Informasi Khodam:**
• **Nama Pertama Makhluknya:** `{user.first_name or 'Not set'}`
• **Nama Akhir Makhluknya:** `{user.last_name or 'Not set'}`
• **Quotes alaynya :** {'Yes' if hasattr(user, 'about') else 'No'}

{get_emoji('zap', '⚡')} **Vzoel Assistant ID Lookup**
        """.strip()
        
        await event.reply(id_info)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"ID command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}info'))
async def info_handler(event):
    """System information command"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "info")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        info_text = f"""
{get_emoji('user', '🤖')} **VZOEL ASSISTANT INFO**

╔══════════════════════════════════╗
    💢**𝚂 𝚈 𝚂 𝚃 𝙴 𝙼  𝙸 𝙽 𝙵 𝙾 𝚁 𝙼 𝙰 𝚃 𝙸 𝙾 𝙽** 💢
╚══════════════════════════════════╝

👤 **USER:** {me.first_name or 'Vzoel Assistant'}
🆔 **User ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
🧠 **FOUNDER UBOT:** **Vzoel Fox's (Lutpan)**
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
🚀 **Version:** v2.3.0 Premium Enhanced
🔧 **Framework:** Telethon
🐍 **Language:** Python 3.9+
💾 **Session:** Active
🌍 **Server:** Cloud Hosted
🛡️ **Spam Guard:** {'Enabled' if spam_guard_enabled else 'Disabled'}
🚫 **Blacklisted Chats:** `{len(blacklisted_chats)}`
{get_emoji('diamond', '💎')} **Premium:** {'Active ✓' if premium_status else 'Standard'}

📊 **Available Commands:**
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}gcast` - Global broadcast
• `{COMMAND_PREFIX}addbl` - Add chat to blacklist
• `{COMMAND_PREFIX}rmbl` - Remove from blacklist
• `{COMMAND_PREFIX}listbl` - Show blacklisted chats
• `{COMMAND_PREFIX}joinvc` - Join voice chat
• `{COMMAND_PREFIX}leavevc` - Leave voice chat
• `{COMMAND_PREFIX}vzl` - Vzoel animation
• `{COMMAND_PREFIX}id` - Get user ID
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}sg` - Spam guard toggle
• `{COMMAND_PREFIX}infofounder` - Founder info
• `{COMMAND_PREFIX}ping` - Response time

{get_emoji('zap', '⚡')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji('zap', '⚡')}
        """.strip()
        
        await event.edit(info_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Info command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Help command with all available commands and logo"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "help")
    
    try:
        help_text = f"""
[🆘]({LOGO_URL}) **𝚅𝚉𝙾𝙴𝙻 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃 HELP**

╔══════════════════════════════════╗
   📚 **𝙲 𝙾 𝙼 𝙼 𝙰 𝙽 𝙳  𝙻 𝙸 𝚂 𝚃** 📚
╚══════════════════════════════════╝

🔥 **MAIN COMMANDS:**
• `{COMMAND_PREFIX}alive` - Check bot status
• `{COMMAND_PREFIX}info` - System information
• `{COMMAND_PREFIX}vzl` - Vzoel animation (12 phases)
• `{COMMAND_PREFIX}help` - Show this help
• `{COMMAND_PREFIX}ping` - Response time test

📡 **BROADCAST:**
• `{COMMAND_PREFIX}gcast <message>` - Enhanced global broadcast
• `{COMMAND_PREFIX}addbl [chat]` - Add chat to blacklist
• `{COMMAND_PREFIX}rmbl [chat]` - Remove from blacklist
• `{COMMAND_PREFIX}listbl` - Show blacklisted chats

🎵 **VOICE CHAT:**
• `{COMMAND_PREFIX}joinvc` - Join voice chat
• `{COMMAND_PREFIX}leavevc` - Leave voice chat

🛡️ **SECURITY:**
• `{COMMAND_PREFIX}sg` - Spam guard toggle

🔍 **UTILITIES:**
• `{COMMAND_PREFIX}id` - Get user ID (reply/username)
• `{COMMAND_PREFIX}infofounder` - Founder information

📍 **USAGE EXAMPLES:**
```
{COMMAND_PREFIX}alive
{COMMAND_PREFIX}gcast Hello everyone!
{COMMAND_PREFIX}addbl @spamgroup
{COMMAND_PREFIX}addbl -1001234567890
{COMMAND_PREFIX}rmbl (remove current chat)
{COMMAND_PREFIX}listbl
{COMMAND_PREFIX}id @username
{COMMAND_PREFIX}id (reply to message)
{COMMAND_PREFIX}joinvc
{COMMAND_PREFIX}vzl
{COMMAND_PREFIX}sg
```

⚠️ **NOTE:** All commands are owner-only for security

{get_emoji('diamond', '💎')} **Premium Features:** {'Active ✓' if premium_status else 'Standard'}

⚡ **Support:** @VZLfx | @VZLfxs
🔥 **Created by Vzoel Fox's (LTPN)**
📱 **Instagram:** vzoel.fox_s
⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(help_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Help command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}sg'))
async def spam_guard_handler(event):
    """Toggle spam guard with status display"""
    if not await is_owner(event.sender_id):
        return
    
    global spam_guard_enabled
    await log_command(event, "sg")
    
    try:
        spam_guard_enabled = not spam_guard_enabled
        status = "**ENABLED** ✅" if spam_guard_enabled else "**DISABLED** ❌"
        
        sg_text = f"""
🛡️ **SPAM GUARD STATUS**

╔══════════════════════════════════╗
   🛡️ **𝚂 𝙿 𝙰 𝙼  𝙿 𝚁 𝙾 𝚃 𝙴 𝙲 𝚃 𝙸 𝙾 𝙽** 🛡️
╚══════════════════════════════════╝

🔥 **Status:** {status}
⚡ **Mode:** Auto-detection
🎯 **Action:** Delete & Warn
📊 **Threshold:** 5 messages/10s
⏰ **Detection Window:** 10 seconds
🚫 **Protected Users:** Owner only

{'🟢 **Protection is now ACTIVE!**' if spam_guard_enabled else '🔴 **Protection is now INACTIVE!**'}

💡 **How it works:**
- Monitors message frequency
- Auto-deletes spam messages
- Shows warning to spammers
- Protects all your chats

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(sg_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Spam guard error: {e}")

@client.on(events.NewMessage)
async def spam_detection(event):
    """Auto spam detection and prevention"""
    global spam_guard_enabled, spam_users
    
    if not spam_guard_enabled or await is_owner(event.sender_id):
        return
    
    try:
        user_id = event.sender_id
        current_time = time.time()
        
        if user_id not in spam_users:
            spam_users[user_id] = []
        
        # Remove old messages (older than 10 seconds)
        spam_users[user_id] = [msg_time for msg_time in spam_users[user_id] if current_time - msg_time < 10]
        
        # Add current message
        spam_users[user_id].append(current_time)
        
        # Check if spam (more than 5 messages in 10 seconds)
        if len(spam_users[user_id]) > 5:
            try:
                await event.delete()
                user = await client.get_entity(user_id)
                user_name = getattr(user, 'first_name', 'Unknown')
                
                warning_msg = await event.respond(
                    f"🛡️ **SPAM DETECTED!**\n"
                    f"👤 **User:** {user_name}\n"
                    f"⚠️ **Action:** Message deleted\n"
                    f"📊 **Messages:** {len(spam_users[user_id])} in 10s\n"
                    f"🔥 **Vzoel Protection Active**"
                )
                
                await asyncio.sleep(5)
                await warning_msg.delete()
                
                # Reset counter
                spam_users[user_id] = []
                
                logger.info(f"Spam detected and handled for user {user_name} ({user_id})")
                
            except Exception as e:
                logger.error(f"Spam action error: {e}")
    
    except Exception as e:
        logger.error(f"Spam detection error: {e}")

# ============= STARTUP AND MAIN FUNCTIONS =============

async def send_startup_message():
    """Send startup notification to saved messages with premium emoji"""
    try:
        me = await client.get_me()
        
        startup_msg_base = f"""
[🚀]({LOGO_URL}) **𝚅𝚉𝙾𝙴𝙻 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃 STARTED!**

╔══════════════════════════════════╗
   {get_emoji('fire', '🔥')} **𝚂 𝚈 𝚂 𝚃 𝙴 𝙼  𝙰 𝙲 𝚃 𝙸 𝚅 𝙰 𝚃 𝙴 𝙳** {get_emoji('fire', '🔥')}
╚══════════════════════════════════╝

✅ **All systems operational**
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
🚫 **Blacklisted Chats:** `{len(blacklisted_chats)}`
{get_emoji('diamond', '💎')} **Premium:** {'Active ✓' if premium_status else 'Standard'}

📌 **Loaded Plugins (Premium Enhanced):**
• ✅ Alive System (Premium Emoji Support)
• ✅ Enhanced Global Broadcast (Premium Emoji)
• ✅ Gcast Blacklist System (addbl/rmbl/listbl)
• ✅ Voice Chat Control
• ✅ Vzoel Animation (12 phases)
• ✅ User ID Lookup System
• ✅ Information System
• ✅ Help Command
• ✅ Spam Guard (Auto-detection)
• ✅ Founder Info (Premium Emoji)
• ✅ Ping System (Premium Emoji)

💡 **Quick Start:**
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}alive` - Check status
• `{COMMAND_PREFIX}vzl` - 12-phase animation
• `{COMMAND_PREFIX}gcast <message>` - Enhanced broadcast
• `{COMMAND_PREFIX}addbl @group` - Blacklist chat
• `{COMMAND_PREFIX}listbl` - Show blacklist
• `{COMMAND_PREFIX}id @username` - Get user ID
• `{COMMAND_PREFIX}sg` - Toggle spam protection

{get_emoji('sparkles', '✨')} **Premium Emoji: {get_emoji('premium')}**
• ID: {PREMIUM_EMOJI_ID}
• Status: {'Enabled' if premium_status else 'Fallback Mode'}

{get_emoji('zap', '⚡')} **Powered by Vzoel Fox's (LTPN)** {get_emoji('zap', '⚡')}
        """.strip()
        
        if premium_status:
            # Add premium emoji decoration
            startup_with_emoji, entities = add_premium_emoji(startup_msg_base)
            await client.send_message('me', startup_with_emoji, formatting_entities=entities)
        else:
            await client.send_message('me', startup_msg_base)
            
        logger.info("✅ Premium enhanced startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def startup():
    """Enhanced startup function"""
    global start_time, premium_status
    start_time = datetime.now()
    
    # Load blacklist on startup
    load_blacklist()
    
    logger.info("🚀 Starting Vzoel Assistant (Premium Enhanced Edition)...")
    
    try:
        await client.start()
        
        # Check premium status
        await check_premium_status()
        
        me = await client.get_me()
        
        logger.info(f"✅ Vzoel Assistant started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"💎 Premium Status: {'Active' if premium_status else 'Standard'}")
        logger.info(f"📌 All plugins loaded with premium emoji support")
        logger.info(f"⚡ Enhanced commands: alive, gcast, ping, infofounder with premium emoji")
        logger.info(f"🔥 Premium Emoji ID: {PREMIUM_EMOJI_ID}")
        
        # Send startup message
        await send_startup_message()
            
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor authentication enabled. Please login manually first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting Vzoel Assistant: {e}")
        return False
    
    return True

async def main():
    """Main function to run the enhanced userbot"""
    logger.info("🔥 Initializing Vzoel Assistant Premium Enhanced Edition...")
    
    # Validate configuration
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"🔑 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Mode: Premium Enhanced Edition")
    logger.info(f"🤩 Premium Emoji ID: {PREMIUM_EMOJI_ID}")
    
    # Start Vzoel Assistant
    if await startup():
        logger.info("🔥 Vzoel Assistant is now running (Premium Enhanced)...")
        logger.info("🔍 Press Ctrl+C to stop")
        logger.info(f"💎 Premium Features: {'Enabled' if premium_status else 'Standard Mode'}")
        
        try:
            await client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("👋 Vzoel Assistant stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            logger.info("🔥 Disconnecting...")
            # Save blacklist before exit
            save_blacklist()
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
            logger.info("✅ Vzoel Assistant stopped successfully!")
    else:
        logger.error("❌ Failed to start Vzoel Assistant!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

# ============= END OF VZOEL ASSISTANT PREMIUM ENHANCED =============

"""
🔥 VZOEL ASSISTANT - PREMIUM ENHANCED EDITION 🔥

🤩 PREMIUM EMOJI INTEGRATION:
1. ✅ Added premium emoji ID: 6156784006194009426
2. ✅ Integrated in alive, gcast, ping, infofounder commands
3. ✅ Created helper functions for premium emoji handling
4. ✅ Added MessageEntityCustomEmoji support
5. ✅ Fallback to standard emoji when premium not available
6. ✅ Version updated to v2.3.0 Premium Enhanced

📋 PREMIUM FEATURES:
• Premium emoji 🤩 appears in key commands
• Automatic detection of premium status
• Fallback support for non-premium users
• Enhanced visual appearance

⚡ Created by Vzoel Fox's (LTPN) ⚡
"""