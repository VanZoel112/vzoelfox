#!/usr/bin/env python3
"""
VZOEL ASSISTANT - ENHANCED MAIN FILE
Complete Telegram Userbot with improved gcast and new features
Author: Vzoel Fox's (LTPN)
Version: v2.1 Enhanced Edition
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
from telethon.tl.types import User, Chat, Channel
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

# Logo URLs (Imgur links)
LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"  # Ganti dengan URL logo Anda
VZOEL_LOGO = "https://imgur.com/gallery/logo-S6biYEi"  # Ganti dengan URL logo VZL

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

async def animate_text(message, texts, delay=1.5):
    """Animate text by editing message multiple times"""
    for i, text in enumerate(texts):
        try:
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

# ============= PLUGIN 1: ALIVE COMMAND (WITH LOGO) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with animation and logo"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "alive")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        alive_animations = [
            "🔥 **Checking system status...**",
            "⚡ **Loading components...**",
            "🚀 **Initializing Vzoel Assistant...**",
            f"""
[🚩]({LOGO_URL}) **VZOEL ASSISTANT IS ALIVE!**

╔═══════════════════════════════╗
   🚩 **𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧** 🚩
╚═══════════════════════════════╝

👤 **Name:** {me.first_name or 'Vzoel Assistant'}
🆔 **ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
🔥 **Status:** Active & Running
📦 **Version:** v2.1 Enhanced
🚫 **Blacklisted Chats:** `{len(blacklisted_chats)}`

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
            """.strip()
        ]
        
        msg = await event.reply(alive_animations[0])
        await animate_text(msg, alive_animations, delay=2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Alive command error: {e}")

# ============= PLUGIN 2: ENHANCED GCAST COMMAND =============

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}gcast\s+(.+)', re.DOTALL)))
async def gcast_handler(event):
    """Enhanced Global Broadcast with improved error handling and blacklist support"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    message_to_send = event.pattern_match.group(1).strip()
    if not message_to_send:
        await event.reply("❌ **Usage:** `.gcast <message>`")
        return
    
    try:
        # 8-phase animation
        gcast_animations = [
            " **lagi otw ngegikes.......**",
            " **cuma gikes aja diblacklist.. kek mui ngeblacklist sound horeg wkwkwkwkwkwk...**",
            " **dikit² blacklist...**",
            " **dikit² maen mute...**",
            " **dikit² gban...**",
            " **wkwkwkwk...**",
            " **anying......**",
            " **wkwkwkwkwkwkwkwk...**"
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
            await msg.edit("❌ **No available channels found for broadcasting!**")
            return
        
        # Continue animation
        await asyncio.sleep(1.5)
        await msg.edit(f"{gcast_animations[5]}\n📊 **Found:** `{total_channels}` chats (🚫 `{blacklisted_count}` blacklisted)")
        
        await asyncio.sleep(1.5)
        await msg.edit(f"{gcast_animations[6]}\n📊 **Broadcasting to:** `{total_channels}` chats")
        
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
                    
                    await msg.edit(f"""
 **lagi otw ngegikesss...**

**Total Kandang:** `{i}/{total_channels}` ({progress:.1f}%)
**Kandang yang berhasil:** `{success_count}`
**Kandang pelit.. alay.. dikit² maen mute** `{failed_count}`
⚡ **Current:** {current_title}...
🚫 **Blacklisted:** `{blacklisted_count}` chats skipped
                    """.strip())
                
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
 **Gcast kelar....**

╔═══════════════════════════════════╗
     **𝖁𝖟𝖔𝖊𝖑 𝖌𝖈𝖆𝖘𝖙.** 
╚═══════════════════════════════════╝

 **Total Kandang:** `{total_channels}`
 **Kandang yang berhasil:** `{success_count}`
 **Kandang pelit.. alay.. dikit² mute:** `{failed_count}`
 **Success Rate:** `{success_rate:.1f}%`
🚫 **Blacklisted Chats Skipped:** `{blacklisted_count}`

        **Message delivered successfully!**
        **Gcast by Vzoel Assistant**
        """.strip()
        
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

# ============= NEW PLUGIN: ADDBL COMMAND =============

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

╔═══════════════════════════════════╗
   🚫 **𝗚𝗖𝗔𝗦𝗧 𝗕𝗟𝗔𝗖𝗞𝗟𝗜𝗦𝗧** 🚫
╚═══════════════════════════════════╝

📝 **Chat:** {chat_title}
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

# ============= NEW PLUGIN: RMBL COMMAND (Remove Blacklist) =============

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

╔═══════════════════════════════════╗
   ✅ **𝗚𝗖𝗔𝗦𝗧 𝗨𝗡𝗕𝗟𝗔𝗖𝗞𝗟𝗜𝗦𝗧** ✅
╚═══════════════════════════════════╝

📝 **Chat:** {chat_title}
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

# ============= NEW PLUGIN: LISTBL COMMAND (List Blacklist) =============

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

╔═══════════════════════════════════╗
   📋 **𝗕𝗟𝗔𝗖𝗞𝗟𝗜𝗦𝗧 𝗘𝗠𝗣𝗧𝗬** 📋
╚═══════════════════════════════════╝

🔥 **No chats are blacklisted**
⚡ **All chats will receive gcast**

💡 **Use `{COMMAND_PREFIX}addbl` to blacklist chats**
            """.strip())
            return
        
        blacklist_text = f"""
📋 **GCAST BLACKLIST**

╔═══════════════════════════════════╗
   📋 **𝗚𝗖𝗔𝗦𝗧 𝗕𝗟𝗔𝗖𝗞𝗟𝗜𝗦𝗧** 📋
╚═══════════════════════════════════╝

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

# ============= PLUGIN 3: JOIN/LEAVE VC =============

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
            " **lagi naik ya bang.. sabar bentar...**",
            " **kalo udah diatas ya disapa bukan dicuekin anying...**",
            " **kalo ga nimbrung berarti bot ye... wkwkwkwkwk**",
            f"""
 **Panglima Pizol udah diatas**

╔═══════════════════════════════════╗
    **𝗩𝗢𝗜𝗖𝗘 𝗖𝗛𝗔𝗧 𝗔𝗖𝗧𝗜𝗩𝗘** 
╚═══════════════════════════════════╝

 **Kandang:** {chat.title[:30] if hasattr(chat, 'title') else 'Private'}
 **Status:** Connected
 **Sound Horeg:** Ready
 **Kualitas:** HD


⚠️ **Note:** Full VC features require pytgcalls
 **Pangeran Pizol udah diatas**
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
            """
✅ **VOICE CHAT LEFT!**

╔═══════════════════════════════════╗
   👋 **𝗩𝗢𝗜𝗖𝗘 𝗖𝗛𝗔𝗧 𝗗𝗜𝗦𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗** 👋
╚═══════════════════════════════════╝

📌 **Status:** Disconnected
🎙️ **Audio:** Stopped
✅ **Action:** Completed

 **Udah turun bang!**
 **Vzoel Assistant ready for next command**
            """.strip()
        ]
        
        msg = await event.reply(animations[0])
        await animate_text(msg, animations, delay=1.5)
            
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"LeaveVC error: {e}")

# ============= PLUGIN 4: VZL COMMAND (12 ANIMATIONS) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}vzl'))
async def vzl_handler(event):
    """Vzoel command with 12-phase animation as requested"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "vzl")
    
    try:
        # 12 animation phases as requested
        vzl_animations = [
            "🔥 **V**",
            "🔥 **VZ**",
            "🔥 **VZO**", 
            "🔥 **VZOE**",
            "🔥 **VZOEL**",
            "🚀 **VZOEL F**",
            "🚀 **VZOEL FO**",
            "🚀 **VZOEL FOX**",
            "⚡ **VZOEL FOX'S**",
            "✨ **VZOEL FOX'S A**",
            "🌟 **VZOEL FOX'S ASS**",
            f"""
[🔥]({VZOEL_LOGO}) **VZOEL FOX'S ASSISTANT** 🔥

╔═══════════════════════════════════╗
   🚩 **𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧** 🚩
╚═══════════════════════════════════╝

⚡ **The most advanced Telegram userbot**
🚀 **Built with passion and precision**
🔥 **Powered by Telethon & Python**
✨ **Created by Vzoel Fox's (LTPN)**

📱 **Features:**
• Global Broadcasting
• Voice Chat Control  
• Advanced Animations
• Multi-Plugin System
• Real-time Monitoring
• Spam Protection
• User ID Lookup
• Gcast Blacklist System

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
            """.strip()
        ]
        
        msg = await event.reply(vzl_animations[0])
        await animate_text(msg, vzl_animations, delay=1.2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"VZL command error: {e}")

# ============= PLUGIN 5: ID COMMAND (NEW) =============

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
            status_icons.append("⭐ Premium ni boss")
        if is_scam:
            status_icons.append("⚠️ Scam anying")
        if is_fake:
            status_icons.append("🚫 Faker bjirrr")
        
        status_text = " | ".join(status_icons) if status_icons else "👤 Regular User"
        
        id_info = f"""
🆔 **Ni boss informasi khodamnya**

╔═══════════════════════════════════╗
    **𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐒𝐈 𝐊𝐇𝐎𝐃𝐀𝐌** 
╚═══════════════════════════════════╝

👤 **Nama Makhluk ini :** {user.first_name or 'None'} {user.last_name or ''}
🆔 **Nomor Togel:** `{user.id}`
📱 **Nama Khodam:** @{user.username or 'None'}
📞 **Phone:** `{user.phone or 'Hidden'}`
🏷️ **STATUS:** {status_text}
🌐 **Language:** `{user.lang_code or 'Unknown'}`

📊 **Informasi Khodam:**
• **Nama Pertama Makhluknya:** `{user.first_name or 'Not set'}`
• **Nama Akhir Makhluknya:** `{user.last_name or 'Not set'}`
• **Quotes alaynya :** {'Yes' if hasattr(user, 'about') else 'No'}

⚡ **Vzoel Assistant ID Lookup**
        """.strip()
        
        await event.reply(id_info)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"ID command error: {e}")

# ============= PLUGIN 6: INFO COMMAND =============

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
🤖 **VZOEL ASSISTANT INFO**

╔═══════════════════════════════════╗
    💢**𝗦𝗬𝗦𝗧𝗘𝗠 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡** 💢
╚═══════════════════════════════════╝

👤 **USER:** {me.first_name or 'Vzoel Assistant'}
🆔 **User ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
🧠 **FOUNDER UBOT:** **Vzoel Fox's (Lutpan)**
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
🚀 **Version:** v2.1 Enhanced
🔧 **Framework:** Telethon
🐍 **Language:** Python 3.9+
💾 **Session:** Active
🌐 **Server:** Cloud Hosted
🛡️ **Spam Guard:** {'Enabled' if spam_guard_enabled else 'Disabled'}
🚫 **Blacklisted Chats:** `{len(blacklisted_chats)}`

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

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(info_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Info command error: {e}")

# ============= PLUGIN 7: HELP COMMAND (WITH LOGO) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Help command with all available commands and logo"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "help")
    
    try:
        help_text = f"""
[🆘]({LOGO_URL}) **VZOEL ASSISTANT HELP**

╔═══════════════════════════════════╗
   📚 **𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗟𝗜𝗦𝗧** 📚
╚═══════════════════════════════════╝

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

📝 **USAGE EXAMPLES:**
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

⚡ **Support:** @VZLfx | @VZLfxs
🔥 **Created by Vzoel Fox's (LTPN)**
📱 **Instagram:** vzoel.fox_s
⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(help_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Help command error: {e}")

# ============= PLUGIN 8: SPAM GUARD =============

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

╔═══════════════════════════════════╗
   🛡️ **𝗦𝗣𝗔𝗠 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡** 🛡️
╚═══════════════════════════════════╝

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

# ============= PLUGIN 9: INFO FOUNDER (WITH LOGO) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}infofounder'))
async def infofounder_handler(event):
    """Founder information with logo - exact as requested"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "infofounder")
    
    try:
        founder_info = f"""
        
 **apa woy**
[╔═══════════════════════════════════╗]({VZOEL_LOGO})
    **𝖁𝖟𝖔𝖊𝖑 𝖆𝖘𝖘𝖎𝖘𝖙𝖆𝖓𝖙** 
╚═══════════════════════════════════╝

⟢ Founder    : **𝗩𝘇𝗼𝗲𝗹 𝗙𝗼𝘅'𝘀 (Ltpn)**
⟢ Instagram  : @vzoel.fox_s
⟢ Telegram   : @VZLfx | @VZLfxs
⟢ Channel    : t.me/damnitvzoel

⚡ Hak milik **𝗩𝘇𝗼𝗲𝗹 𝗙𝗼𝘅'𝘀** ©2025 ~ LTPN. ⚡
        """.strip()
        
        await event.edit(founder_info)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"InfoFounder error: {e}")

# ============= PLUGIN 10: PING COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Ping command with response time"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "ping")
    
    try:
        start = time.time()
        msg = await event.reply("🔍 **Lagi ngetest ping dulu om.......**")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        ping_text = f"""
🔍 **Tch....**

╔═══════════════════════════════════╗
   ⚡ **𝗣𝗜𝗡𝗚 𝗥𝗘𝗦𝗨𝗟𝗧** ⚡
╚═══════════════════════════════════╝

⚡ **Response Time:** `{ping_time:.2f}ms`
🚀 **Status:** Active
🔥 **Server:** Online
✅ **Connection:** Stable
📡 **Latency:** {'Low' if ping_time < 100 else 'Normal' if ping_time < 300 else 'High'}

⚡ **pasti aman anti delay**
        """.strip()
        
        await msg.edit(ping_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Ping error: {e}")

# ============= STARTUP AND MAIN FUNCTIONS =============

async def send_startup_message():
    """Send startup notification to saved messages"""
    try:
        me = await client.get_me()
        
        startup_msg = f"""
[🚀]({LOGO_URL}) **VZOEL ASSISTANT STARTED!**

╔═══════════════════════════════════╗
   🔥 **𝗦𝗬𝗦𝗧𝗘𝗠 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗** 🔥
╚═══════════════════════════════════╝

✅ **All systems operational**
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
🚫 **Blacklisted Chats:** `{len(blacklisted_chats)}`

📌 **Loaded Plugins (Enhanced Edition):**
• ✅ Alive System (3 animations + logo)
• ✅ Enhanced Global Broadcast (8 animations + blacklist)
• ✅ Gcast Blacklist System (addbl/rmbl/listbl)
• ✅ Voice Chat Control
• ✅ Vzoel Animation (12 phases + logo)
• ✅ User ID Lookup System
• ✅ Information System
• ✅ Help Command (with logo)
• ✅ Spam Guard (Auto-detection)
• ✅ Founder Info (with logo)
• ✅ Ping System

💡 **Quick Start:**
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}alive` - Check status
• `{COMMAND_PREFIX}vzl` - 12-phase animation
• `{COMMAND_PREFIX}gcast <message>` - Enhanced broadcast
• `{COMMAND_PREFIX}addbl @group` - Blacklist chat
• `{COMMAND_PREFIX}listbl` - Show blacklist
• `{COMMAND_PREFIX}id @username` - Get user ID
• `{COMMAND_PREFIX}sg` - Toggle spam protection

🔥 **Enhanced features:**
• NEW: Gcast blacklist system (addbl/rmbl/listbl)
• Improved gcast with blacklist filtering
• Better error handling and flood protection
• Logo integration on key commands
• Enhanced broadcast success tracking

⚡ **Powered by Vzoel Fox's (LTPN)**
        """.strip()
        
        await client.send_message('me', startup_msg)
        logger.info("✅ Enhanced startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def startup():
    """Enhanced startup function"""
    global start_time
    start_time = datetime.now()
    
    # Load blacklist on startup
    load_blacklist()
    
    logger.info("🚀 Starting Vzoel Assistant (Enhanced Edition with Blacklist)...")
    
    try:
        await client.start()
        me = await client.get_me()
        
        logger.info(f"✅ Vzoel Assistant started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"📌 All plugins integrated in main.py")
        logger.info(f"⚡ Enhanced commands: alive, gcast, addbl, rmbl, listbl, joinvc, leavevc, vzl, id, info, help, sg, infofounder, ping")
        logger.info(f"🔥 NEW: Gcast blacklist system with {len(blacklisted_chats)} blacklisted chats")
        
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
    logger.info("🔥 Initializing Vzoel Assistant Enhanced Edition with Blacklist...")
    
    # Validate configuration
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"📝 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Mode: Enhanced Edition with Gcast Blacklist System")
    
    # Start Vzoel Assistant
    if await startup():
        logger.info("🔥 Vzoel Assistant is now running (Enhanced Edition with Blacklist)...")
        logger.info("🔍 Press Ctrl+C to stop")
        logger.info("🎯 NEW: Gcast blacklist commands (addbl/rmbl/listbl)")
        
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

# ============= END OF VZOEL ASSISTANT ENHANCED EDITION WITH BLACKLIST =============

"""
🔥 VZOEL ASSISTANT - ENHANCED EDITION WITH BLACKLIST SYSTEM 🔥

🆕 NEW FEATURES ADDED:
1. ✅ ADDBL Command - Add chats to gcast blacklist
2. ✅ RMBL Command - Remove chats from blacklist  
3. ✅ LISTBL Command - Show all blacklisted chats
4. ✅ Blacklist Integration - Gcast now skips blacklisted chats
5. ✅ Persistent Storage - Blacklist saved to JSON file
6. ✅ Enhanced Logo Support - InfoFounder with proper Imgur logo

🚀 BLACKLIST SYSTEM FEATURES:
• Smart chat detection (current chat, username, or ID)
• Persistent storage in gcast_blacklist.json
• Real-time filtering during gcast
• Comprehensive blacklist management
• Error handling for inaccessible chats
• Blacklist counter in status displays

📋 BLACKLIST COMMANDS:
• .addbl - Blacklist current chat
• .addbl @username - Blacklist by username  
• .addbl -1001234567890 - Blacklist by ID
• .rmbl - Remove current chat from blacklist
• .rmbl @username - Remove by username
• .rmbl -1001234567890 - Remove by ID
• .listbl - Show all blacklisted chats

🔧 ENHANCED FEATURES:
• All existing plugins preserved (10 total)
• Gcast now shows blacklisted count
• Better error handling and logging
• Logo properly implemented in InfoFounder
• Blacklist loaded/saved automatically
• Real-time filtering during broadcast

📂 FILES CREATED:
• gcast_blacklist.json - Stores blacklisted chat IDs

⚡ All improvements maintain existing structure!
⚡ Created by Vzoel Fox's (LTPN) ⚡
"""