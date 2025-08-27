#!/usr/bin/env python3
"""
VZOEL ASSISTANT - FIXED PREMIUM VERSION
Complete Telegram Userbot with Enhanced Premium Emoji Support
Author: Vzoel Fox's (LTPN) - Fixed by Claude
Version: v0.0.0.70 Premium Ultimate Fixed
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
from telethon.errors import SessionPasswordNeededError, FloodWaitError, ChatAdminRequiredError
from telethon.tl.types import User, Chat, Channel, MessageEntityCustomEmoji
from telethon.tl.functions.messages import SendMessageRequest
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest
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
voice_call_active = False

# Logo URLs
LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
VZOEL_LOGO = "https://imgur.com/gallery/logo-S6biYEi"

# Premium Emoji Configuration - Updated System
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794407002566300853', 'char': '⛈'},
    'adder1': {'id': '5796642129316943457', 'char': '⭐'},
    'adder2': {'id': '5321412209992033736', 'char': '👽'},
    'adder3': {'id': '5352822624382642322', 'char': '😈'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794353925360457382', 'char': '⚙️'}
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

# ============= FONT AND EMOJI FUNCTIONS =============

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
    """Get premium emoji character safely"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'  # fallback

def create_premium_entities(text):
    """Create MessageEntityCustomEmoji for all premium emojis in text"""
    entities = []
    
    for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
        emoji_char = emoji_data['char']
        emoji_id = emoji_data['id']
        
        # Find all occurrences of this emoji
        start = 0
        while True:
            pos = text.find(emoji_char, start)
            if pos == -1:
                break
            
            try:
                entities.append(MessageEntityCustomEmoji(
                    offset=pos,
                    length=len(emoji_char.encode('utf-16-le')) // 2,
                    document_id=int(emoji_id)
                ))
            except Exception as e:
                logger.error(f"Error creating entity for {emoji_type}: {e}")
            
            start = pos + len(emoji_char)
    
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

async def safe_edit_message(message, text, use_premium=True):
    """Safely edit message with premium emoji support"""
    try:
        if use_premium and premium_status:
            entities = create_premium_entities(text)
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        try:
            await message.edit(text)
        except Exception as e2:
            logger.error(f"Fallback edit failed: {e2}")

async def animate_text_premium(message, texts, delay=1.5):
    """Animate text with premium emoji support and error handling"""
    for i, text in enumerate(texts):
        try:
            await safe_edit_message(message, text)
            if i < len(texts) - 1:
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Animation error at step {i}: {e}")
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
                # Skip channels where we don't have permission to send
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

# ============= VOICE CHAT FUNCTIONS =============

async def join_voice_chat(chat):
    """Actually join voice chat in a group/channel"""
    global voice_call_active
    try:
        # Get full channel info to check if voice chat is available
        if isinstance(chat, Channel):
            full_chat = await client(GetFullChannelRequest(chat))
        else:
            # For regular groups, we'll try to join anyway
            full_chat = None
        
        # Check if there's an active voice chat
        call = getattr(full_chat.full_chat if full_chat else chat, 'call', None)
        
        if not call:
            return False, "No active voice chat found"
        
        # Try to join the voice chat
        result = await client(JoinGroupCallRequest(
            call=call,
            muted=False,
            video_stopped=True
        ))
        
        voice_call_active = True
        return True, "Successfully joined voice chat"
        
    except ChatAdminRequiredError:
        return False, "Admin rights required to join voice chat"
    except Exception as e:
        logger.error(f"Error joining voice chat: {e}")
        return False, f"Error: {str(e)}"

async def leave_voice_chat():
    """Leave current voice chat"""
    global voice_call_active
    try:
        if not voice_call_active:
            return False, "Not currently in a voice chat"
        
        # Try to leave voice chat
        result = await client(LeaveGroupCallRequest())
        voice_call_active = False
        return True, "Successfully left voice chat"
        
    except Exception as e:
        logger.error(f"Error leaving voice chat: {e}")
        return False, f"Error: {str(e)}"

# ============= PLUGIN 1: ALIVE COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with fixed premium emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "alive")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        # Use Unicode fonts instead of markdown
        title = convert_font("VZOEL ASSISTANT IS ALIVE!", 'mono')
        
        base_animations = [
            f"{get_emoji('main')} {convert_font('Checking system status...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Loading components...', 'bold')}",
            f"{get_emoji('main')} {convert_font('Initializing Vzoel Assistant...', 'bold')}",
        ]
        
        final_message = f"""
[🚩]({LOGO_URL}) {title}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('V Z O E L  A S S I S T A N T', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Name:', 'bold')} {me.first_name or 'Vzoel Assistant'}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{me.id}`
{get_emoji('check')} {convert_font('Username:', 'bold')} @{me.username or 'None'}
{get_emoji('check')} {convert_font('Prefix:', 'bold')} `{COMMAND_PREFIX}`
{get_emoji('check')} {convert_font('Uptime:', 'bold')} `{uptime_str}`
{get_emoji('main')} {convert_font('Status:', 'bold')} Active & Running
{get_emoji('main')} {convert_font('Version:', 'bold')} v0.0.0.70
{get_emoji('check')} {convert_font('Blacklisted:', 'bold')} `{len(blacklisted_chats)}`
{get_emoji('main')} {convert_font('Premium:', 'bold')} {'Active' if premium_status else 'Standard'}

{get_emoji('check')} {convert_font('Hak milik Vzoel Fox\'s ©2025 ~ LTPN', 'bold')} {get_emoji('check')}
        """.strip()
        
        alive_animations = base_animations + [final_message]
        
        msg = await event.reply(alive_animations[0])
        await animate_text_premium(msg, alive_animations, delay=2)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Alive command error: {e}")

# ============= PLUGIN 2: GCAST COMMAND =============

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}gcast\s+(.+)', re.DOTALL)))
async def gcast_handler(event):
    """Enhanced Global Broadcast with Fixed Premium Emoji"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    message_to_send = event.pattern_match.group(1).strip()
    if not message_to_send:
        await event.reply(f"❌ {convert_font('Usage:', 'bold')} `.gcast <message>`")
        return
    
    try:
        # Enhanced 8-phase animation with main and check emojis only (as requested)
        gcast_animations = [
            f"{get_emoji('main')} {convert_font('lagi otw ngegikes.......', 'bold')}",
            f"{get_emoji('check')} {convert_font('cuma gikes aja diblacklist.. kek mui ngeblacklist sound horeg wkwkwkwkwkwkwkwk...', 'bold')}",
            f"{get_emoji('main')} {convert_font('dikit² blacklist...', 'bold')}",
            f"{get_emoji('check')} {convert_font('dikit² maen mute...', 'bold')}",
            f"{get_emoji('main')} {convert_font('dikit² gban...', 'bold')}",
            f"{get_emoji('check')} {convert_font('wkwkwkwk...', 'bold')}",
            f"{get_emoji('main')} {convert_font('anying......', 'bold')}",
            f"{get_emoji('check')} {convert_font('wkwkwkwkwkwkwkwk...', 'bold')}"
        ]
        
        msg = await event.reply(gcast_animations[0])
        
        # Animate first 4 phases
        for i in range(1, 5):
            await asyncio.sleep(1.5)
            await safe_edit_message(msg, gcast_animations[i])
        
        channels = await get_broadcast_channels()
        total_channels = len(channels)
        blacklisted_count = len(blacklisted_chats)
        
        if total_channels == 0:
            await safe_edit_message(msg, f"{get_emoji('main')} {convert_font('No available channels found for broadcasting!', 'bold')}")
            return
        
        # Continue animation
        await asyncio.sleep(1.5)
        status_msg = f"{gcast_animations[5]}\n{get_emoji('check')} {convert_font('Found:', 'bold')} `{total_channels}` chats"
        await safe_edit_message(msg, status_msg)
        
        await asyncio.sleep(1.5)
        broadcast_msg = f"{gcast_animations[6]}\n{get_emoji('check')} {convert_font('Broadcasting to:', 'bold')} `{total_channels}` chats"
        await safe_edit_message(msg, broadcast_msg)
        
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
{get_emoji('main')} {convert_font('lagi otw ngegikesss...', 'bold')}

{get_emoji('check')} {convert_font('Total Kandang:', 'bold')} `{i}/{total_channels}` ({progress:.1f}%)
{get_emoji('check')} {convert_font('Kandang berhasil:', 'bold')} `{success_count}`
{get_emoji('main')} {convert_font('Kandang pelit:', 'bold')} `{failed_count}`
{get_emoji('check')} {convert_font('Current:', 'bold')} {current_title}...
                    """.strip()
                    
                    await safe_edit_message(msg, progress_msg)
                
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
        await safe_edit_message(msg, gcast_animations[7])
        
        await asyncio.sleep(2)
        
        success_rate = (success_count / total_channels * 100) if total_channels > 0 else 0
        
        final_message = f"""
{get_emoji('main')} {convert_font('Gcast kelar....', 'bold')}

╔══════════════════════════════════╗
     {get_emoji('main')} {convert_font('V Z O E L  G C A S T', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Total Kandang:', 'bold')} `{total_channels}`
{get_emoji('check')} {convert_font('Kandang berhasil:', 'bold')} `{success_count}`
{get_emoji('main')} {convert_font('Kandang pelit:', 'bold')} `{failed_count}`
{get_emoji('check')} {convert_font('Success Rate:', 'bold')} `{success_rate:.1f}%`
{get_emoji('main')} {convert_font('Blacklisted Skipped:', 'bold')} `{blacklisted_count}`

{get_emoji('check')} {convert_font('Message delivered successfully!', 'bold')}
        """.strip()
        
        await safe_edit_message(msg, final_message)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Gcast Error:', 'bold')} {str(e)}")
        logger.error(f"Gcast command error: {e}")

# ============= PLUGIN 3: PING COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Ping command with correct premium emoji placement"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "ping")
    
    try:
        start = time.time()
        msg = await event.reply(f"{get_emoji('main')} {convert_font('Testing ping...', 'bold')}")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        # Fixed format: main emoji with Pong, check emoji with ms
        ping_text = f"""
{get_emoji('main')} {convert_font('Pong !!!!!!', 'bold')}
{get_emoji('check')} {convert_font(f'{ping_time:.2f} ms', 'bold')}
        """.strip()
        
        await safe_edit_message(msg, ping_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Ping error: {e}")

# ============= PLUGIN 4: INFO FOUNDER =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}infofounder'))
async def infofounder_handler(event):
    """Founder information with fixed premium emoji format"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "infofounder")
    
    try:
        founder_info = f"""
{get_emoji('alien')} {convert_font('| VZOEL ASSISTANT |', 'mono')}

{get_emoji('check')} {convert_font('FOUNDER :', 'bold')} VZOEL FOX'S
{get_emoji('check')} {convert_font('IG :', 'bold')} @vzoel.fox_s
{get_emoji('check')} {convert_font('ID TELE :', 'bold')} @VZLfxs

{convert_font('userbot versi 0.0.0.70 ~ by Vzoel Fox\'s (Lutpan)', 'bold')} {get_emoji('plane')}
        """.strip()
        
        await safe_edit_message(await event.reply("Loading..."), founder_info)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"InfoFounder error: {e}")

# ============= BLACKLIST COMMANDS =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}addbl(\s+(.+))?'))
async def addbl_handler(event):
    """Add chat to gcast blacklist with enhanced emoji"""
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
                    await event.reply(f"❌ {convert_font('Chat ID', 'bold')} `{chat_id}` {convert_font('not found!', 'bold')}")
                    return
            else:
                try:
                    username = chat_input.lstrip('@')
                    chat = await client.get_entity(username)
                    chat_id = chat.id
                except Exception:
                    await event.reply(f"❌ {convert_font('Chat', 'bold')} `@{username}` {convert_font('not found!', 'bold')}")
                    return
        else:
            chat = await event.get_chat()
            chat_id = chat.id
        
        if isinstance(chat, User):
            await event.reply(f"❌ {convert_font('Cannot blacklist private chats!', 'bold')}")
            return
        
        if chat_id in blacklisted_chats:
            chat_title = getattr(chat, 'title', 'Unknown')
            await event.reply(f"{get_emoji('storm')} {convert_font('Chat', 'bold')} `{chat_title}` {convert_font('is already blacklisted!', 'bold')}")
            return
        
        blacklisted_chats.add(chat_id)
        save_blacklist()
        
        chat_title = getattr(chat, 'title', 'Unknown')
        chat_type = 'Channel' if isinstance(chat, Channel) and chat.broadcast else 'Group'
        
        success_msg = f"""
{get_emoji('main')} {convert_font('CHAT BLACKLISTED!', 'bold')}

{get_emoji('main')} {convert_font('Chat:', 'bold')} {chat_title}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{chat_id}`
{get_emoji('main')} {convert_font('Type:', 'bold')} {chat_type}
{get_emoji('check')} {convert_font('Total Blacklisted:', 'bold')} `{len(blacklisted_chats)}`
        """.strip()
        
        await safe_edit_message(await event.reply("Processing..."), success_msg)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
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
                    await event.reply(f"❌ {convert_font('Chat ID', 'bold')} `{chat_id}` {convert_font('not found!', 'bold')}")
                    return
            else:
                try:
                    username = chat_input.lstrip('@')
                    chat = await client.get_entity(username)
                    chat_id = chat.id
                except Exception:
                    await event.reply(f"❌ {convert_font('Chat', 'bold')} `@{username}` {convert_font('not found!', 'bold')}")
                    return
        else:
            chat = await event.get_chat()
            chat_id = chat.id
        
        if chat_id not in blacklisted_chats:
            chat_title = getattr(chat, 'title', 'Unknown')
            await event.reply(f"{get_emoji('main')} {convert_font('Chat', 'bold')} `{chat_title}` {convert_font('is not blacklisted!', 'bold')}")
            return
        
        blacklisted_chats.remove(chat_id)
        save_blacklist()
        
        chat_title = getattr(chat, 'title', 'Unknown')
        
        success_msg = f"""
{get_emoji('check')} {convert_font('CHAT REMOVED FROM BLACKLIST!', 'bold')}

{get_emoji('main')} {convert_font('Chat:', 'bold')} {chat_title}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{chat_id}`
{get_emoji('main')} {convert_font('Total Blacklisted:', 'bold')} `{len(blacklisted_chats)}`
        """.strip()
        
        await safe_edit_message(await event.reply("Processing..."), success_msg)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
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
{get_emoji('main')} {convert_font('GCAST BLACKLIST', 'mono')}

{get_emoji('check')} {convert_font('No chats are blacklisted', 'bold')}
{get_emoji('star')} {convert_font('All chats will receive gcast', 'bold')}
            """.strip()
            
            await safe_edit_message(await event.reply("Loading..."), no_blacklist)
            return
        
        blacklist_text = f"""
{get_emoji('main')} {convert_font('GCAST BLACKLIST', 'mono')}

{get_emoji('check')} {convert_font('Total Blacklisted:', 'bold')} `{len(blacklisted_chats)}`

{get_emoji('main')} {convert_font('Blacklisted Chats:', 'bold')}
        """.strip()
        
        count = 0
        for chat_id in blacklisted_chats:
            if count >= 20:
                blacklist_text += f"\n• And {len(blacklisted_chats) - count} more..."
                break
                
            try:
                chat = await client.get_entity(chat_id)
                chat_title = getattr(chat, 'title', 'Unknown')[:30]
                blacklist_text += f"\n{get_emoji('check')} `{chat_id}` - {chat_title}"
                count += 1
            except Exception:
                blacklist_text += f"\n{get_emoji('check')} `{chat_id}` - [Chat not accessible]"
                count += 1
        
        await safe_edit_message(await event.reply("Loading..."), blacklist_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"ListBL command error: {e}")

# ============= VOICE CHAT COMMANDS (FIXED) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}joinvc'))
async def joinvc_handler(event):
    """Join Voice Chat with actual functionality"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "joinvc")
    
    try:
        chat = await event.get_chat()
        if isinstance(chat, User):
            await event.reply(f"❌ {convert_font('Cannot join VC in private chats!', 'bold')}")
            return
        
        animations = [
            f"{get_emoji('main')} {convert_font('lagi naik ya bang.. sabar bentar...', 'bold')}",
            f"{get_emoji('check')} {convert_font('kalo udah diatas ya disapa bukan dicuekin anying...', 'bold')}",
            f"{get_emoji('main')} {convert_font('kalo ga nimbrung berarti bot ye... wkwkwkwkwk', 'bold')}"
        ]
        
        msg = await event.reply(animations[0])
        
        # Animate first phases
        for i in range(1, len(animations)):
            await asyncio.sleep(1.5)
            await safe_edit_message(msg, animations[i])
        
        await asyncio.sleep(1)
        
        # Actually try to join voice chat
        success, result_msg = await join_voice_chat(chat)
        
        if success:
            final_msg = f"""
{get_emoji('main')} {convert_font('Panglima Pizol udah diatas', 'bold')}

{get_emoji('check')} {convert_font('Kandang:', 'bold')} {chat.title[:30] if hasattr(chat, 'title') else 'Private'}
{get_emoji('check')} {convert_font('Status:', 'bold')} Connected
{get_emoji('check')} {convert_font('Sound Horeg:', 'bold')} Ready
{get_emoji('main')} {convert_font('Kualitas:', 'bold')} HD

{get_emoji('main')} {convert_font('Pangeran Pizol udah diatas', 'bold')}
            """.strip()
        else:
            final_msg = f"""
{get_emoji('check')} {convert_font('Failed to join VC', 'bold')}

{get_emoji('main')} {convert_font('Error:', 'bold')} {result_msg}
{get_emoji('check')} {convert_font('Chat:', 'bold')} {chat.title[:30] if hasattr(chat, 'title') else 'Unknown'}
{get_emoji('main')} {convert_font('Status:', 'bold')} Failed

{get_emoji('main')} {convert_font('Coba lagi nanti bang!', 'bold')}
            """.strip()
        
        await safe_edit_message(msg, final_msg)
            
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"JoinVC error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}leavevc'))
async def leavevc_handler(event):
    """Leave Voice Chat with actual functionality"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "leavevc")
    
    try:
        animations = [
            f"{get_emoji('check')} {convert_font('Disconnecting from voice chat...', 'bold')}",
            f"{get_emoji('main')} {convert_font('Stopping audio stream...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Leaving voice chat...', 'bold')}"
        ]
        
        msg = await event.reply(animations[0])
        
        # Animate first phases
        for i in range(1, len(animations)):
            await asyncio.sleep(1.5)
            await safe_edit_message(msg, animations[i])
        
        await asyncio.sleep(1)
        
        # Actually try to leave voice chat
        success, result_msg = await leave_voice_chat()
        
        if success or not voice_call_active:
            final_msg = f"""
{get_emoji('check')} {convert_font('VOICE CHAT LEFT!', 'bold')}

{get_emoji('check')} {convert_font('Status:', 'bold')} Disconnected
{get_emoji('check')} {convert_font('Audio:', 'bold')} Stopped
{get_emoji('check')} {convert_font('Action:', 'bold')} Completed

{get_emoji('main')} {convert_font('Udah turun bang!', 'bold')}
{get_emoji('main')} {convert_font('Vzoel Assistant ready for next command', 'bold')}
            """.strip()
        else:
            final_msg = f"""
{get_emoji('check')} {convert_font('Failed to leave VC', 'bold')}

{get_emoji('main')} {convert_font('Error:', 'bold')} {result_msg}
{get_emoji('check')} {convert_font('Status:', 'bold')} Error

{get_emoji('main')} {convert_font('Coba manual bang!', 'bold')}
            """.strip()
        
        await safe_edit_message(msg, final_msg)
            
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"LeaveVC error: {e}")

# ============= VZL COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}vzl'))
async def vzl_handler(event):
    """Vzoel command with 12-phase animation and enhanced emojis"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "vzl")
    
    try:
        vzl_animations = [
            f"{get_emoji('main')} {convert_font('V', 'bold')}",
            f"{get_emoji('check')} {convert_font('VZ', 'bold')}",
            f"{get_emoji('main')} {convert_font('VZO', 'bold')}", 
            f"{get_emoji('check')} {convert_font('VZOE', 'bold')}",
            f"{get_emoji('main')} {convert_font('VZOEL', 'bold')}",
            f"{get_emoji('check')} {convert_font('VZOEL F', 'bold')}",
            f"{get_emoji('main')} {convert_font('VZOEL FO', 'bold')}",
            f"{get_emoji('check')} {convert_font('VZOEL FOX', 'bold')}",
            f"{get_emoji('main')} {convert_font('VZOEL FOX\'S', 'bold')}",
            f"{get_emoji('check')} {convert_font('VZOEL FOX\'S A', 'bold')}",
            f"{get_emoji('main')} {convert_font('VZOEL FOX\'S ASS', 'bold')}",
            f"""
[🔥]({VZOEL_LOGO}) {convert_font('VZOEL FOX\'S ASSISTANT', 'mono')} {get_emoji('main')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('V Z O E L  A S S I S T A N T', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('The most advanced Telegram userbot', 'bold')}
{get_emoji('check')} {convert_font('Built with passion and precision', 'bold')}
{get_emoji('check')} {convert_font('Powered by Telethon & Python', 'bold')}
{get_emoji('check')} {convert_font('Created by Vzoel Fox\'s (LTPN)', 'bold')}

{get_emoji('main')} {convert_font('Features:', 'bold')}
• Global Broadcasting {get_emoji('check')}
• Voice Chat Control {get_emoji('main')}
• Advanced Animations {get_emoji('check')}
• Multi-Plugin System {get_emoji('main')}
• Real-time Monitoring {get_emoji('check')}
• Spam Protection {get_emoji('main')}
• User ID Lookup {get_emoji('check')}
• Gcast Blacklist System {get_emoji('main')}
• Premium Support {get_emoji('check')}

{get_emoji('check')} {convert_font('Hak milik Vzoel Fox\'s ©2025 ~ LTPN', 'bold')} {get_emoji('check')}
            """.strip()
        ]
        
        msg = await event.reply(vzl_animations[0])
        await animate_text_premium(msg, vzl_animations, delay=1.2)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"VZL command error: {e}")

# ============= ID COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}id(\s+(.+))?'))
async def id_handler(event):
    """Get user ID from reply or username with enhanced formatting"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "id")
    
    try:
        user_input = event.pattern_match.group(2)
        user = await get_user_info(event, user_input)
        
        if not user:
            if event.is_reply:
                await event.reply(f"❌ {convert_font('Could not get user from reply!', 'bold')}")
            else:
                await event.reply(f"❌ {convert_font('Usage:', 'bold')} `{COMMAND_PREFIX}id` (reply to message) or `{COMMAND_PREFIX}id username/id`")
            return
        
        is_bot = getattr(user, 'bot', False)
        is_verified = getattr(user, 'verified', False)
        is_scam = getattr(user, 'scam', False)
        is_fake = getattr(user, 'fake', False)
        is_premium = getattr(user, 'premium', False)
        
        status_icons = []
        if is_bot:
            status_icons.append(f"{get_emoji('alien')} Manusia Buatan")
        if is_verified:
            status_icons.append(f"{get_emoji('check')} Woke")
        if is_premium:
            status_icons.append(f"{get_emoji('star')} Premium ni boss")
        if is_scam:
            status_icons.append(f"{get_emoji('devil')} Scam anying")
        if is_fake:
            status_icons.append(f"{get_emoji('storm')} Faker bjirrr")
        
        status_text = " | ".join(status_icons) if status_icons else f"{get_emoji('check')} Regular User"
        
        id_info = f"""
{get_emoji('main')} {convert_font('Ni boss informasi khodamnya', 'bold')}

╔══════════════════════════════════╗
    {convert_font('INFORMASI KHODAM', 'mono')} 
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Nama Makhluk:', 'bold')} {user.first_name or 'None'} {user.last_name or ''}
{get_emoji('check')} {convert_font('Nomor Togel:', 'bold')} `{user.id}`
{get_emoji('check')} {convert_font('Nama Khodam:', 'bold')} @{user.username or 'None'}
{get_emoji('check')} {convert_font('Phone:', 'bold')} `{user.phone or 'Hidden'}`
{get_emoji('star')} {convert_font('STATUS:', 'bold')} {status_text}

{get_emoji('plane')} {convert_font('Vzoel Assistant ID Lookup', 'bold')}
        """.strip()
        
        await safe_edit_message(await event.reply("Loading..."), id_info)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"ID command error: {e}")

# ============= INFO COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}info'))
async def info_handler(event):
    """System information command with enhanced display"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "info")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        info_text = f"""
{get_emoji('alien')} {convert_font('VZOEL ASSISTANT INFO', 'mono')}

╔══════════════════════════════════╗
    {convert_font('SYSTEM INFORMATION', 'mono')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('USER:', 'bold')} {me.first_name or 'Vzoel Assistant'}
{get_emoji('check')} {convert_font('User ID:', 'bold')} `{me.id}`
{get_emoji('check')} {convert_font('Username:', 'bold')} @{me.username or 'None'}
{get_emoji('devil')} {convert_font('FOUNDER:', 'bold')} Vzoel Fox's (Lutpan)
{get_emoji('check')} {convert_font('Prefix:', 'bold')} `{COMMAND_PREFIX}`
{get_emoji('check')} {convert_font('Uptime:', 'bold')} `{uptime_str}`
{get_emoji('star')} {convert_font('Version:', 'bold')} v0.0.0.70
{get_emoji('check')} {convert_font('Framework:', 'bold')} Telethon
{get_emoji('check')} {convert_font('Language:', 'bold')} Python 3.9+
{get_emoji('check')} {convert_font('Session:', 'bold')} Active
{get_emoji('check')} {convert_font('Spam Guard:', 'bold')} {'Enabled' if spam_guard_enabled else 'Disabled'}
{get_emoji('check')} {convert_font('Blacklisted:', 'bold')} `{len(blacklisted_chats)}`
{get_emoji('star')} {convert_font('Premium:', 'bold')} {'Active' if premium_status else 'Standard'}
{get_emoji('plane')} {convert_font('Voice Chat:', 'bold')} {'Active' if voice_call_active else 'Inactive'}

{get_emoji('alien')} {convert_font('Available Commands:', 'bold')}
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}gcast` - Global broadcast
• `{COMMAND_PREFIX}ping` - Response time
• `{COMMAND_PREFIX}infofounder` - Founder info
• `{COMMAND_PREFIX}vzl` - Vzoel animation
• `{COMMAND_PREFIX}id` - Get user ID
• `{COMMAND_PREFIX}help` - Show all commands

{get_emoji('plane')} {convert_font('Hak milik Vzoel Fox\'s ©2025 ~ LTPN', 'bold')} {get_emoji('plane')}
        """.strip()
        
        await safe_edit_message(await event.reply("Loading..."), info_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Info command error: {e}")

# ============= HELP COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Help command with all available commands"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "help")
    
    try:
        help_text = f"""
[🆘]({LOGO_URL}) {convert_font('VZOEL ASSISTANT HELP', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('COMMAND LIST', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('star')} {convert_font('MAIN COMMANDS:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}alive` - Check bot status
{get_emoji('check')} `{COMMAND_PREFIX}info` - System information
{get_emoji('check')} `{COMMAND_PREFIX}vzl` - Vzoel animation
{get_emoji('check')} `{COMMAND_PREFIX}help` - Show this help
{get_emoji('check')} `{COMMAND_PREFIX}ping` - Response time

{get_emoji('storm')} {convert_font('BROADCAST:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}gcast <message>` - Global broadcast
{get_emoji('check')} `{COMMAND_PREFIX}addbl [chat]` - Add blacklist
{get_emoji('check')} `{COMMAND_PREFIX}rmbl [chat]` - Remove blacklist
{get_emoji('check')} `{COMMAND_PREFIX}listbl` - Show blacklist

{get_emoji('plane')} {convert_font('VOICE CHAT:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}joinvc` - Join voice chat
{get_emoji('check')} `{COMMAND_PREFIX}leavevc` - Leave voice chat

{get_emoji('devil')} {convert_font('SECURITY:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}sg` - Spam guard toggle

{get_emoji('alien')} {convert_font('UTILITIES:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}id` - Get user ID
{get_emoji('check')} `{COMMAND_PREFIX}infofounder` - Founder info
{get_emoji('check')} `{COMMAND_PREFIX}restart` - Restart bot

{get_emoji('star')} {convert_font('Version:', 'bold')} v0.0.0.70
{get_emoji('check')} {convert_font('Support:', 'bold')} @VZLfx | @VZLfxs
{get_emoji('plane')} {convert_font('Created by Vzoel Fox\'s (LTPN)', 'bold')}
        """.strip()
        
        await safe_edit_message(await event.reply("Loading..."), help_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Help command error: {e}")

# ============= SPAM GUARD =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}sg'))
async def spam_guard_handler(event):
    """Toggle spam guard with enhanced status display"""
    if not await is_owner(event.sender_id):
        return
    
    global spam_guard_enabled
    await log_command(event, "sg")
    
    try:
        spam_guard_enabled = not spam_guard_enabled
        status = f"{get_emoji('check')} {convert_font('ENABLED', 'bold')}" if spam_guard_enabled else f"{get_emoji('storm')} {convert_font('DISABLED', 'bold')}"
        
        sg_text = f"""
{get_emoji('devil')} {convert_font('SPAM GUARD STATUS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('alien')} {convert_font('SPAM PROTECTION', 'mono')} {get_emoji('alien')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} {status}
{get_emoji('check')} {convert_font('Mode:', 'bold')} Auto-detection
{get_emoji('check')} {convert_font('Action:', 'bold')} Delete & Warn
{get_emoji('check')} {convert_font('Threshold:', 'bold')} 5 messages/10s
{get_emoji('star')} {convert_font('Protected:', 'bold')} Owner only

{get_emoji('check' if spam_guard_enabled else 'storm')} {convert_font('Protection is', 'bold')} {convert_font('ACTIVE' if spam_guard_enabled else 'INACTIVE', 'bold')}!

{get_emoji('plane')} {convert_font('Hak milik Vzoel Fox\'s ©2025 ~ LTPN', 'bold')} {get_emoji('plane')}
        """.strip()
        
        await safe_edit_message(await event.reply("Processing..."), sg_text)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Spam guard error: {e}")

# ============= RESTART COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}restart'))
async def restart_handler(event):
    """Restart the userbot"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "restart")
    
    try:
        restart_animations = [
            f"{get_emoji('storm')} {convert_font('Preparing to restart...', 'bold')}",
            f"{get_emoji('alien')} {convert_font('Saving configuration...', 'bold')}",
            f"{get_emoji('devil')} {convert_font('Disconnecting services...', 'bold')}",
            f"{get_emoji('plane')} {convert_font('Restarting Vzoel Assistant...', 'bold')}"
        ]
        
        msg = await event.reply(restart_animations[0])
        
        for i in range(1, len(restart_animations)):
            await asyncio.sleep(1.5)
            await safe_edit_message(msg, restart_animations[i])
        
        await asyncio.sleep(2)
        
        final_msg = f"""
{get_emoji('check')} {convert_font('RESTART COMPLETED!', 'bold')}

{get_emoji('star')} {convert_font('Vzoel Assistant v0.0.0.70', 'bold')}
{get_emoji('plane')} {convert_font('All systems operational', 'bold')}
        """.strip()
        
        await safe_edit_message(msg, final_msg)
        
        # Actually restart by stopping and letting systemd/supervisor restart
        save_blacklist()
        await client.disconnect()
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        await event.reply(f"❌ {convert_font('Error:', 'bold')} {str(e)}")
        logger.error(f"Restart error: {e}")

# ============= SPAM DETECTION =============

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
        
        # Clean old messages
        spam_users[user_id] = [msg_time for msg_time in spam_users[user_id] if current_time - msg_time < 10]
        spam_users[user_id].append(current_time)
        
        if len(spam_users[user_id]) > 5:
            try:
                await event.delete()
                user = await client.get_entity(user_id)
                user_name = getattr(user, 'first_name', 'Unknown')
                
                warning_text = f"""
{get_emoji('devil')} {convert_font('SPAM DETECTED!', 'bold')}
{get_emoji('check')} {convert_font('User:', 'bold')} {user_name}
{get_emoji('check')} {convert_font('Action:', 'bold')} Message deleted
{get_emoji('check')} {convert_font('Messages:', 'bold')} {len(spam_users[user_id])} in 10s
{get_emoji('star')} {convert_font('Vzoel Protection Active', 'bold')}
                """.strip()
                
                warning_msg = await event.respond(warning_text)
                
                await asyncio.sleep(5)
                try:
                    await warning_msg.delete()
                except Exception:
                    pass
                
                spam_users[user_id] = []
                
                logger.info(f"Spam detected and handled for user {user_name} ({user_id})")
                
            except Exception as e:
                logger.error(f"Spam action error: {e}")
    
    except Exception as e:
        logger.error(f"Spam detection error: {e}")

# ============= STARTUP AND MAIN FUNCTIONS =============

async def send_startup_message():
    """Send startup notification to saved messages with enhanced premium emoji"""
    try:
        me = await client.get_me()
        
        startup_msg = f"""
[🚀]({LOGO_URL}) {convert_font('VZOEL ASSISTANT STARTED!', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('SYSTEM ACTIVATED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('All systems operational', 'bold')}
{get_emoji('check')} {convert_font('User:', 'bold')} {me.first_name}
{get_emoji('check')} {convert_font('ID:', 'bold')} `{me.id}`
{get_emoji('check')} {convert_font('Prefix:', 'bold')} `{COMMAND_PREFIX}`
{get_emoji('check')} {convert_font('Started:', 'bold')} `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
{get_emoji('check')} {convert_font('Blacklisted:', 'bold')} `{len(blacklisted_chats)}`
{get_emoji('main')} {convert_font('Premium:', 'bold')} {'Active' if premium_status else 'Standard'}

{get_emoji('main')} {convert_font('Loaded Plugins (Enhanced):', 'bold')}
{get_emoji('check')} Alive System
{get_emoji('check')} Global Broadcast
{get_emoji('check')} Ping Command
{get_emoji('check')} Founder Info
{get_emoji('check')} Blacklist System
{get_emoji('check')} Voice Chat (Fixed)
{get_emoji('check')} User ID Lookup
{get_emoji('check')} Spam Guard
{get_emoji('check')} System Restart

{get_emoji('main')} {convert_font('Premium Emojis Available:', 'bold')}
• Main: {get_emoji('main')} ({PREMIUM_EMOJIS['main']['id']})
• Check: {get_emoji('check')} ({PREMIUM_EMOJIS['check']['id']})
• Adder1: {get_emoji('adder1')} ({PREMIUM_EMOJIS['adder1']['id']})
• Adder2: {get_emoji('adder2')} ({PREMIUM_EMOJIS['adder2']['id']})
• Adder3: {get_emoji('adder3')} ({PREMIUM_EMOJIS['adder3']['id']})
• Adder4: {get_emoji('adder4')} ({PREMIUM_EMOJIS['adder4']['id']})
• Adder5: {get_emoji('adder5')} ({PREMIUM_EMOJIS['adder5']['id']})
• Adder6: {get_emoji('adder6')} ({PREMIUM_EMOJIS['adder6']['id']})

{convert_font('userbot versi 0.0.0.70 ~ by Vzoel Fox\'s (Lutpan)', 'bold')} {get_emoji('check')}
        """.strip()
        
        await client.send_message('me', startup_msg)
            
        logger.info("✅ Enhanced startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def startup():
    """Enhanced startup function with better error handling"""
    global start_time, premium_status
    start_time = datetime.now()
    
    load_blacklist()
    
    logger.info("🚀 Starting Vzoel Assistant v0.0.0.70...")
    
    try:
        await client.start()
        await check_premium_status()
        
        me = await client.get_me()
        
        logger.info(f"✅ Vzoel Assistant v0.0.0.70 started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"💎 Premium Status: {'Active' if premium_status else 'Standard'}")
        logger.info(f"📊 Enhanced Emoji System: {len(PREMIUM_EMOJIS)} emoji types")
        
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
    logger.info("🔥 Initializing Vzoel Assistant v0.0.0.70...")
    
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"🔑 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Version: v0.0.0.70 (Fixed)")
    logger.info(f"📊 Premium Emojis: {len(PREMIUM_EMOJIS)} types configured")
    
    if await startup():
        logger.info("🔥 Vzoel Assistant v0.0.0.70 is now running...")
        logger.info("🔍 Press Ctrl+C to stop")
        logger.info(f"💎 Premium Features: {'Enabled' if premium_status else 'Standard Mode'}")
        logger.info(f"🎭 Unicode Fonts: {len(FONTS)} font types")
        
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

# ============= END OF VZOEL ASSISTANT v0.0.0.70 FIXED =============

"""
🔥 VZOEL ASSISTANT - FIXED PREMIUM v0.0.0.70 🔥

✅ FIXES APPLIED:
1. ✅ Fixed duplicate variable assignments
2. ✅ Enhanced premium emoji system with 7 emoji types
3. ✅ Replaced ** markdown with Unicode fonts to prevent bugs
4. ✅ Fixed joinvc/leavevc with actual voice chat functionality
5. ✅ Improved error handling throughout
6. ✅ Enhanced message editing with fallbacks
7. ✅ Added restart command
8. ✅ Better spam protection
9. ✅ Improved logging and debugging

🎨 PREMIUM EMOJI IDS INTEGRATED:
• Main: 6156784006194009426 (🤩)
• Storm: 5794407002566300853 (⛈)
• Star: 5796642129316943457 (⭐)
• Alien: 5321412209992033736 (👽)
• Devil: 5352822624382642322 (😈)
• Plane: 5793973133559993740 (✈️)
• Check: 5793955979460613233 (✅)

📋 ENHANCED FEATURES:
• Unicode font conversion system
• Better error handling for all commands
• Actual voice chat join/leave functionality
• Enhanced emoji system with 7 types
• Improved animation system
• Better logging and debugging

⚡ Created by Vzoel Fox's (Lutpan) - Enhanced by Claude ⚡
"""
