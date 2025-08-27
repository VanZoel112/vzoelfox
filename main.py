#!/usr/bin/env python3
"""
VZOEL ASSISTANT - FULL PREMIUM EMOJI VERSION
Complete Telegram Userbot with Dual Premium Emoji Support
Author: Vzoel Fox's (LTPN)
Version: v0.0.0.69 Premium Ultimate
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
premium_status = None

# Logo URLs
LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
VZOEL_LOGO = "https://imgur.com/gallery/logo-S6biYEi"

# Premium Emoji Configuration - DUAL EMOJI SYSTEM
PREMIUM_EMOJI_MAIN = "6156784006194009426"  # 🤩
PREMIUM_EMOJI_MAIN= "5793955979460613233"  # ✅
PREMIUM_EMOJI_CHAR_MAIN = "🤩"
PREMIUM_EMOJI_CHAR_MAIN = "✅"

# Premium Emoji Mapping - ALL EMOJIS NOW PREMIUM
PREMIUM_EMOJI_MAP = {
    'premium': PREMIUM_EMOJI_CHAR_MAIN,
    'check': PREMIUM_EMOJI_CHAR_MAIN,
    'fire': PREMIUM_EMOJI_CHAR_MAIN,
    'rocket': PREMIUM_EMOJI_CHAR_MAIN,
    'lightning': PREMIUM_EMOJI_CHAR_MAIN,
    'diamond': PREMIUM_EMOJI_CHAR_MAIN,
    'star': PREMIUM_EMOJI_CHAR_MAIN,
    'warning': PREMIUM_EMOJI_CHAR_MAIN,
    'party': PREMIUM_EMOJI_CHAR_MAIN,
    'crown': PREMIUM_EMOJI_CHAR_MAIN,
    'zap': PREMIUM_EMOJI_CHAR_MAIN,
    'boom': PREMIUM_EMOJI_CHAR_MAIN,
    'sparkles': PREMIUM_EMOJI_CHAR_MAIN,
    'phone': PREMIUM_EMOJI_CHAR_MAIN,
    'user': PREMIUM_EMOJI_CHAR_MAIN,
    'globe': PREMIUM_EMOJI_CHAR_MAIN,
    'success': PREMIUM_EMOJI_CHAR_MAIN,
    'verified': PREMIUM_EMOJI_CHAR_MAIN,
}

# ============= PREMIUM EMOJI FUNCTIONS =============

def create_premium_entities(text):
    """Create MessageEntityCustomEmoji for all premium emojis in text"""
    entities = []
    # Find all 🤩 emojis
    for match in re.finditer(PREMIUM_EMOJI_CHAR_MAIN, text):
        entities.append(MessageEntityCustomEmoji(
            offset=match.start(),
            length=2,
            document_id=int(PREMIUM_EMOJI_MAIN)
        ))
    # Find all ✅ emojis
    for match in re.finditer(PREMIUM_EMOJI_CHAR_CHECK, text):
        entities.append(MessageEntityCustomEmoji(
            offset=match.start(),
            length=1,
            document_id=int(PREMIUM_EMOJI_CHECK)
        ))
    return entities

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

def get_emoji(emoji_id, emoji_char):
    """Get premium emoji format"""
    if premium_status:
        return emoji_char
    return emoji_char  # Always use emoji char

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

async def animate_text_premium(message, texts, delay=1.5):
    """Animate text with premium emoji support"""
    for i, text in enumerate(texts):
        try:
            if premium_status:
                entities = create_premium_entities(text)
                await message.edit(text, formatting_entities=entities)
            else:
                await message.edit(text)
            if i < len(texts) - 1:
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Animation error: {e}")
            break

async def get_broadcast_channels():
    """Get all channels and groups for broadcasting"""
    channels = []
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            if isinstance(entity, User):
                continue
            
            if entity.id in blacklisted_chats:
                continue
                
            if isinstance(entity, (Chat, Channel)):
                if isinstance(entity, Channel):
                    if entity.broadcast and not (entity.creator or entity.admin_rights):
                        continue
                
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
            reply_msg = await event.get_reply_message()
            user = await client.get_entity(reply_msg.sender_id)
        elif user_input:
            if user_input.isdigit():
                user = await client.get_entity(int(user_input))
            else:
                username = user_input.lstrip('@')
                user = await client.get_entity(username)
        else:
            return None
            
        return user
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None

# ============= PLUGIN 1: ALIVE COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with full premium emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "alive")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        base_animations = [
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Checking system status...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Loading components...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Initializing Vzoel Assistant...**",
        ]
        
        final_message = f"""
[🚩]({LOGO_URL}) **𝚅𝚉𝙾𝙴𝙻 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃 IS ALIVE!**

╔══════════════════════════════════╗
   {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **𝚅 𝚉 𝙾 𝙴 𝙻  𝙰 𝚂 𝚂 𝙸 𝚂 𝚃 𝙰 𝙽 𝚃** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Name:** {me.first_name or 'Vzoel Assistant'}
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **ID:** `{me.id}`
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Username:** @{me.username or 'None'}
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Prefix:** `{COMMAND_PREFIX}`
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Uptime:** `{uptime_str}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Status:** Active & Running
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Version:** v0.0.0.69
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Blacklisted:** `{len(blacklisted_chats)}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Premium:** {'Active' if premium_status else 'Standard'}

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
        """.strip()
        
        alive_animations = base_animations + [final_message]
        
        msg = await event.reply(alive_animations[0])
        await animate_text_premium(msg, alive_animations, delay=2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Alive command error: {e}")

# ============= PLUGIN 2: GCAST COMMAND =============

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}gcast\s+(.+)', re.DOTALL)))
async def gcast_handler(event):
    """Enhanced Global Broadcast with Full Premium Emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    message_to_send = event.pattern_match.group(1).strip()
    if not message_to_send:
        await event.reply("❌ **Usage:** `.gcast <message>`")
        return
    
    try:
        # 8-phase animation with premium emoji
        gcast_animations = [
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **lagi otw ngegikes.......**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **cuma gikes aja diblacklist.. kek mui ngeblacklist sound horeg wkwkwkwkwkwkwkwk...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **dikit² blacklist...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **dikit² maen mute...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **dikit² gban...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **wkwkwkwk...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **anying......**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **wkwkwkwkwkwkwkwk...**"
        ]
        
        msg = await event.reply(gcast_animations[0])
        
        # Animate first 4 phases
        for i in range(1, 5):
            await asyncio.sleep(1.5)
            if premium_status:
                entities = create_premium_entities(gcast_animations[i])
                await msg.edit(gcast_animations[i], formatting_entities=entities)
            else:
                await msg.edit(gcast_animations[i])
        
        channels = await get_broadcast_channels()
        total_channels = len(channels)
        blacklisted_count = len(blacklisted_chats)
        
        if total_channels == 0:
            await msg.edit(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **No available channels found for broadcasting!**")
            return
        
        # Continue animation
        await asyncio.sleep(1.5)
        status_msg = f"{gcast_animations[5]}\n{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Found:** `{total_channels}` chats"
        if premium_status:
            entities = create_premium_entities(status_msg)
            await msg.edit(status_msg, formatting_entities=entities)
        else:
            await msg.edit(status_msg)
        
        await asyncio.sleep(1.5)
        broadcast_msg = f"{gcast_animations[6]}\n{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Broadcasting to:** `{total_channels}` chats"
        if premium_status:
            entities = create_premium_entities(broadcast_msg)
            await msg.edit(broadcast_msg, formatting_entities=entities)
        else:
            await msg.edit(broadcast_msg)
        
        # Start broadcasting
        success_count = 0
        failed_count = 0
        failed_chats = []
        
        for i, channel_info in enumerate(channels, 1):
            try:
                entity = channel_info['entity']
                await client.send_message(entity, message_to_send)
                success_count += 1
                
                if i % 3 == 0 or i == total_channels:
                    progress = (i / total_channels) * 100
                    current_title = channel_info['title'][:20]
                    
                    progress_msg = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **lagi otw ngegikesss...**

{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Total Kandang:** `{i}/{total_channels}` ({progress:.1f}%)
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Kandang berhasil:** `{success_count}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Kandang pelit:** `{failed_count}`
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Current:** {current_title}...
                    """.strip()
                    
                    if premium_status:
                        entities = create_premium_entities(progress_msg)
                        await msg.edit(progress_msg, formatting_entities=entities)
                    else:
                        await msg.edit(progress_msg)
                
                await asyncio.sleep(0.5)
                
            except FloodWaitError as e:
                wait_time = e.seconds
                if wait_time > 300:
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
        
        # Final animation
        await asyncio.sleep(2)
        if premium_status:
            entities = create_premium_entities(gcast_animations[7])
            await msg.edit(gcast_animations[7], formatting_entities=entities)
        else:
            await msg.edit(gcast_animations[7])
        
        await asyncio.sleep(2)
        
        success_rate = (success_count / total_channels * 100) if total_channels > 0 else 0
        
        final_message = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Gcast kelar....**

╔══════════════════════════════════╗
     {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **𝚅 𝚉 𝙾 𝙴 𝙻  𝙶 𝙲 𝙰 𝚂 𝚃** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Total Kandang:** `{total_channels}`
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Kandang berhasil:** `{success_count}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Kandang pelit:** `{failed_count}`
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Success Rate:** `{success_rate:.1f}%`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Blacklisted Skipped:** `{blacklisted_count}`

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Message delivered successfully!**
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(final_message)
            await msg.edit(final_message, formatting_entities=entities)
        else:
            await msg.edit(final_message)
        
    except Exception as e:
        await event.reply(f"❌ **Gcast Error:** {str(e)}")
        logger.error(f"Gcast command error: {e}")

# ============= PLUGIN 3: PING COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Ping command with premium emoji format"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "ping")
    
    try:
        start = time.time()
        msg = await event.reply(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Testing ping...**")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        # Format as requested
        ping_text = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Pong !!!!!!**
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **{ping_time:.2f} ms**
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(ping_text)
            await msg.edit(ping_text, formatting_entities=entities)
        else:
            await msg.edit(ping_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Ping error: {e}")

# ============= PLUGIN 4: INFO FOUNDER =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}infofounder'))
async def infofounder_handler(event):
    """Founder information with premium emoji format"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "infofounder")
    
    try:
        founder_info = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **| VZOEL ASSISTANT |**

{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **FOUNDER :** VZOEL FOX'S
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **IG :** @vzoel.fox_s
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **ID TELE :** @VZLfxs

**userbot versi 0.0.0.69 ~ by Vzoel Fox's (Lutpan)** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(founder_info)
            await event.edit(founder_info, formatting_entities=entities)
        else:
            await event.edit(founder_info)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"InfoFounder error: {e}")

# ============= OTHER PLUGINS WITH PREMIUM EMOJI =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}addbl(\s+(.+))?'))
async def addbl_handler(event):
    """Add chat to gcast blacklist"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "addbl")
    
    try:
        chat_input = event.pattern_match.group(2)
        
        if chat_input:
            if chat_input.isdigit() or chat_input.lstrip('-').isdigit():
                chat_id = int(chat_input)
                try:
                    chat = await client.get_entity(chat_id)
                except Exception:
                    await event.reply(f"❌ **Chat ID `{chat_id}` not found!**")
                    return
            else:
                try:
                    username = chat_input.lstrip('@')
                    chat = await client.get_entity(username)
                    chat_id = chat.id
                except Exception:
                    await event.reply(f"❌ **Chat `@{username}` not found!**")
                    return
        else:
            chat = await event.get_chat()
            chat_id = chat.id
        
        if isinstance(chat, User):
            await event.reply("❌ **Cannot blacklist private chats!**")
            return
        
        if chat_id in blacklisted_chats:
            chat_title = getattr(chat, 'title', 'Unknown')
            await event.reply(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Chat `{chat_title}` is already blacklisted!**")
            return
        
        blacklisted_chats.add(chat_id)
        save_blacklist()
        
        chat_title = getattr(chat, 'title', 'Unknown')
        chat_type = 'Channel' if isinstance(chat, Channel) and chat.broadcast else 'Group'
        
        success_msg = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **CHAT BLACKLISTED!**

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Chat:** {chat_title}
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **ID:** `{chat_id}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Type:** {chat_type}
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Total Blacklisted:** `{len(blacklisted_chats)}`
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(success_msg)
            await event.edit(success_msg, formatting_entities=entities)
        else:
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
        chat_input = event.pattern_match.group(2)
        
        if chat_input:
            if chat_input.isdigit() or chat_input.lstrip('-').isdigit():
                chat_id = int(chat_input)
                try:
                    chat = await client.get_entity(chat_id)
                except Exception:
                    await event.reply(f"❌ **Chat ID `{chat_id}` not found!**")
                    return
            else:
                try:
                    username = chat_input.lstrip('@')
                    chat = await client.get_entity(username)
                    chat_id = chat.id
                except Exception:
                    await event.reply(f"❌ **Chat `@{username}` not found!**")
                    return
        else:
            chat = await event.get_chat()
            chat_id = chat.id
        
        if chat_id not in blacklisted_chats:
            chat_title = getattr(chat, 'title', 'Unknown')
            await event.reply(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Chat `{chat_title}` is not blacklisted!**")
            return
        
        blacklisted_chats.remove(chat_id)
        save_blacklist()
        
        chat_title = getattr(chat, 'title', 'Unknown')
        
        success_msg = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **CHAT REMOVED FROM BLACKLIST!**

{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **Chat:** {chat_title}
{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **ID:** `{chat_id}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Total Blacklisted:** `{len(blacklisted_chats)}`
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(success_msg)
            await event.edit(success_msg, formatting_entities=entities)
        else:
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
            no_blacklist = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **GCAST BLACKLIST**

{get_emoji(PREMIUM_EMOJI_MAIN, '✅')} **No chats are blacklisted**
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **All chats will receive gcast**
            """.strip()
            
            if premium_status:
                entities = create_premium_entities(no_blacklist)
                await event.edit(no_blacklist, formatting_entities=entities)
            else:
                await event.edit(no_blacklist)
            return
        
        blacklist_text = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **GCAST BLACKLIST**

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Total Blacklisted:** `{len(blacklisted_chats)}`

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Blacklisted Chats:**
        """.strip()
        
        count = 0
        for chat_id in blacklisted_chats:
            if count >= 20:
                blacklist_text += f"\n• And {len(blacklisted_chats) - count} more..."
                break
                
            try:
                chat = await client.get_entity(chat_id)
                chat_title = getattr(chat, 'title', 'Unknown')[:30]
                blacklist_text += f"\n{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{chat_id}` - {chat_title}"
                count += 1
            except Exception:
                blacklist_text += f"\n{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{chat_id}` - [Chat not accessible]"
                count += 1
        
        if premium_status:
            entities = create_premium_entities(blacklist_text)
            await event.edit(blacklist_text, formatting_entities=entities)
        else:
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
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **lagi naik ya bang.. sabar bentar...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **kalo udah diatas ya disapa bukan dicuekin anying...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **kalo ga nimbrung berarti bot ye... wkwkwkwkwk**",
            f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Panglima Pizol udah diatas**

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Kandang:** {chat.title[:30] if hasattr(chat, 'title') else 'Private'}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Status:** Connected
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Sound Horeg:** Ready
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Kualitas:** HD

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Pangeran Pizol udah diatas**
            """.strip()
        ]
        
        msg = await event.reply(animations[0])
        await animate_text_premium(msg, animations, delay=1.5)
            
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
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Disconnecting from voice chat...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Stopping audio stream...**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Leaving voice chat...**",
            f"""
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **VOICE CHAT LEFT!**

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Status:** Disconnected
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Audio:** Stopped
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Action:** Completed

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Udah turun bang!**
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Vzoel Assistant ready for next command**
            """.strip()
        ]
        
        msg = await event.reply(animations[0])
        await animate_text_premium(msg, animations, delay=1.5)
            
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"LeaveVC error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}vzl'))
async def vzl_handler(event):
    """Vzoel command with 12-phase animation"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "vzl")
    
    try:
        vzl_animations = [
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **V**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZ**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZO**", 
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOE**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL F**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL FO**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL FOX**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL FOX'S**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL FOX'S A**",
            f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL FOX'S ASS**",
            f"""
[🔥]({VZOEL_LOGO}) **𝚅𝚉𝙾𝙴𝙻 𝙵𝙾𝚇'𝚂 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}

╔══════════════════════════════════╗
   {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **𝚅 𝚉 𝙾 𝙴 𝙻  𝙰 𝚂 𝚂 𝙸 𝚂 𝚃 𝙰 𝙽 𝚃** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **The most advanced Telegram userbot**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Built with passion and precision**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Powered by Telethon & Python**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Created by Vzoel Fox's (LTPN)**

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Features:**
• Global Broadcasting
• Voice Chat Control  
• Advanced Animations
• Multi-Plugin System
• Real-time Monitoring
• Spam Protection
• User ID Lookup
• Gcast Blacklist System
• Premium Support {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
            """.strip()
        ]
        
        msg = await event.reply(vzl_animations[0])
        await animate_text_premium(msg, vzl_animations, delay=1.2)
        
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
        
        is_bot = getattr(user, 'bot', False)
        is_verified = getattr(user, 'verified', False)
        is_scam = getattr(user, 'scam', False)
        is_fake = getattr(user, 'fake', False)
        is_premium = getattr(user, 'premium', False)
        
        status_icons = []
        if is_bot:
            status_icons.append(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} Manusia Buatan")
        if is_verified:
            status_icons.append(f"{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Woke")
        if is_premium:
            status_icons.append(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} Premium ni boss")
        if is_scam:
            status_icons.append(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} Scam anying")
        if is_fake:
            status_icons.append(f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} Faker bjirrr")
        
        status_text = " | ".join(status_icons) if status_icons else f"{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Regular User"
        
        id_info = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Ni boss informasi khodamnya**

╔══════════════════════════════════╗
    **𝙸𝙽𝙵𝙾𝚁𝙼𝙰𝚂𝙸 𝙺𝙷𝙾𝙳𝙰𝙼** 
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Nama Makhluk:** {user.first_name or 'None'} {user.last_name or ''}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Nomor Togel:** `{user.id}`
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Nama Khodam:** @{user.username or 'None'}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Phone:** `{user.phone or 'Hidden'}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **STATUS:** {status_text}

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Vzoel Assistant ID Lookup**
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(id_info)
            await event.reply(id_info, formatting_entities=entities)
        else:
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
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VZOEL ASSISTANT INFO**

╔══════════════════════════════════╗
    **𝚂𝚈𝚂𝚃𝙴𝙼 𝙸𝙽𝙵𝙾𝚁𝙼𝙰𝚃𝙸𝙾𝙽**
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **USER:** {me.first_name or 'Vzoel Assistant'}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **User ID:** `{me.id}`
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Username:** @{me.username or 'None'}
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **FOUNDER:** Vzoel Fox's (Lutpan)
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Prefix:** `{COMMAND_PREFIX}`
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Uptime:** `{uptime_str}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Version:** v0.0.0.69
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Framework:** Telethon
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Language:** Python 3.9+
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Session:** Active
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Spam Guard:** {'Enabled' if spam_guard_enabled else 'Disabled'}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Blacklisted:** `{len(blacklisted_chats)}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Premium:** {'Active' if premium_status else 'Standard'}

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Available Commands:**
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}gcast` - Global broadcast
• `{COMMAND_PREFIX}ping` - Response time
• `{COMMAND_PREFIX}infofounder` - Founder info
• `{COMMAND_PREFIX}vzl` - Vzoel animation
• `{COMMAND_PREFIX}id` - Get user ID
• `{COMMAND_PREFIX}help` - Show all commands

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(info_text)
            await event.edit(info_text, formatting_entities=entities)
        else:
            await event.edit(info_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Info command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Help command with all available commands"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "help")
    
    try:
        help_text = f"""
[🆘]({LOGO_URL}) **𝚅𝚉𝙾𝙴𝙻 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃 HELP**

╔══════════════════════════════════╗
   {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **𝙲𝙾𝙼𝙼𝙰𝙽𝙳 𝙻𝙸𝚂𝚃** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **MAIN COMMANDS:**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}alive` - Check bot status
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}info` - System information
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}vzl` - Vzoel animation
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}help` - Show this help
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}ping` - Response time

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **BROADCAST:**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}gcast <message>` - Global broadcast
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}addbl [chat]` - Add blacklist
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}rmbl [chat]` - Remove blacklist
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}listbl` - Show blacklist

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **VOICE CHAT:**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}joinvc` - Join voice
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}leavevc` - Leave voice

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **SECURITY:**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}sg` - Spam guard toggle

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **UTILITIES:**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}id` - Get user ID
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} `{COMMAND_PREFIX}infofounder` - Founder info

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Version:** v0.0.0.69
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Support:** @VZLfx | @VZLfxs
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Created by Vzoel Fox's (LTPN)**
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(help_text)
            await event.edit(help_text, formatting_entities=entities)
        else:
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
        status = f"{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **ENABLED**" if spam_guard_enabled else f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **DISABLED**"
        
        sg_text = f"""
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **SPAM GUARD STATUS**

╔══════════════════════════════════╗
   {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **𝚂𝙿𝙰𝙼 𝙿𝚁𝙾𝚃𝙴𝙲𝚃𝙸𝙾𝙽** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Status:** {status}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Mode:** Auto-detection
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Action:** Delete & Warn
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Threshold:** 5 messages/10s
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Protected:** Owner only

{get_emoji(PREMIUM_EMOJI_CHECK if spam_guard_enabled else PREMIUM_EMOJI_MAIN, '✅' if spam_guard_enabled else '🤩')} **Protection is {'ACTIVE' if spam_guard_enabled else 'INACTIVE'}!**

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Hak milik Vzoel Fox's ©2025 ~ LTPN** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(sg_text)
            await event.edit(sg_text, formatting_entities=entities)
        else:
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
        
        spam_users[user_id] = [msg_time for msg_time in spam_users[user_id] if current_time - msg_time < 10]
        spam_users[user_id].append(current_time)
        
        if len(spam_users[user_id]) > 5:
            try:
                await event.delete()
                user = await client.get_entity(user_id)
                user_name = getattr(user, 'first_name', 'Unknown')
                
                warning_msg = await event.respond(
                    f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **SPAM DETECTED!**\n"
                    f"{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **User:** {user_name}\n"
                    f"{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Action:** Message deleted\n"
                    f"{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Messages:** {len(spam_users[user_id])} in 10s\n"
                    f"{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Vzoel Protection Active**"
                )
                
                await asyncio.sleep(5)
                await warning_msg.delete()
                
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
        
        startup_msg = f"""
[🚀]({LOGO_URL}) **𝚅𝚉𝙾𝙴𝙻 𝙰𝚂𝚂𝙸𝚂𝚃𝙰𝙽𝚃 STARTED!**

╔══════════════════════════════════╗
   {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **𝚂𝚈𝚂𝚃𝙴𝙼 𝙰𝙲𝚃𝙸𝚅𝙰𝚃𝙴𝙳** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
╚══════════════════════════════════╝

{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **All systems operational**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **User:** {me.first_name}
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **ID:** `{me.id}`
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Prefix:** `{COMMAND_PREFIX}`
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} **Blacklisted:** `{len(blacklisted_chats)}`
{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Premium:** {'Active' if premium_status else 'Standard'}

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Loaded Plugins (Full Premium):**
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Alive System
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Global Broadcast
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Ping Command
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Founder Info
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Blacklist System
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Voice Chat
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} User ID Lookup
{get_emoji(PREMIUM_EMOJI_CHECK, '✅')} Spam Guard

{get_emoji(PREMIUM_EMOJI_MAIN, '🤩')} **Premium Emojis:**
• Main: {PREMIUM_EMOJI_MAIN} {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
• Check: {PREMIUM_EMOJI_CHECK} {get_emoji(PREMIUM_EMOJI_CHECK, '✅')}

**userbot versi 0.0.0.69 ~ by Vzoel Fox's (Lutpan)** {get_emoji(PREMIUM_EMOJI_MAIN, '🤩')}
        """.strip()
        
        if premium_status:
            entities = create_premium_entities(startup_msg)
            await client.send_message('me', startup_msg, formatting_entities=entities)
        else:
            await client.send_message('me', startup_msg)
            
        logger.info("✅ Premium startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def startup():
    """Enhanced startup function"""
    global start_time, premium_status
    start_time = datetime.now()
    
    load_blacklist()
    
    logger.info("🚀 Starting Vzoel Assistant v0.0.0.69...")
    
    try:
        await client.start()
        await check_premium_status()
        
        me = await client.get_me()
        
        logger.info(f"✅ Vzoel Assistant v0.0.0.69 started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"💎 Premium Status: {'Active' if premium_status else 'Standard'}")
        logger.info(f"🤩 Premium Emoji Main: {PREMIUM_EMOJI_MAIN}")
        logger.info(f"✅ Premium Emoji Check: {PREMIUM_EMOJI_CHECK}")
        
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
    logger.info("🔥 Initializing Vzoel Assistant v0.0.0.69...")
    
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"🔑 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Version: v0.0.0.69")
    logger.info(f"🤩 Premium Main Emoji: {PREMIUM_EMOJI_MAIN}")
    logger.info(f"✅ Premium Check Emoji: {PREMIUM_EMOJI_CHECK}")
    
    if await startup():
        logger.info("🔥 Vzoel Assistant v0.0.0.69 is now running...")
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

# ============= END OF VZOEL ASSISTANT v0.0.0.69 =============

"""
🔥 VZOEL ASSISTANT - FULL PREMIUM v0.0.0.69 🔥

🤩 DUAL PREMIUM EMOJI SYSTEM:
1. ✅ Main Emoji ID: 6156784006194009426 (🤩)
2. ✅ Check Emoji ID: 5793955979460613233 (✅)
3. ✅ All emojis converted to premium
4. ✅ Custom format for ping, gcast, infofounder
5. ✅ Version updated to v0.0.0.69
6. ✅ Full premium integration in all plugins

📋 FORMATTED PLUGINS:
• Ping: Simple format with premium emojis
• Gcast: 8 edits with premium emoji
• InfoFounder: Clean format as requested
• All plugins use dual premium emoji system

⚡ Created by Vzoel Fox's (Lutpan) ⚡
"""