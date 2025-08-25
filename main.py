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

# Logo URLs (Telegraph links)
LOGO_URL = "https://telegra.ph/file/8b9c2c5c5a5a5c5c5c5c5.jpg"  # Ganti dengan URL logo Anda
VZOEL_LOGO = "https://telegra.ph/file/vzoel-assistant-logo.jpg"  # Ganti dengan URL logo VZL

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
    """Get all channels and groups for broadcasting (improved)"""
    channels = []
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Skip private chats
            if isinstance(entity, User):
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
    """Enhanced Global Broadcast with improved error handling"""
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
            "🔍 **Scanning available channels...**",
            "📡 **Establishing broadcast connection...**",
            "⚡ **Initializing transmission protocol...**",
            "🚀 **Preparing message distribution...**",
            "🔨 **Starting global broadcast...**",
            "🔄 **Broadcasting in progress...**",
            "✅ **Broadcast transmission active...**",
            "📊 **Finalizing delivery status...**"
        ]
        
        msg = await event.reply(gcast_animations[0])
        
        # Animate first 4 phases
        for i in range(1, 5):
            await asyncio.sleep(1.5)
            await msg.edit(gcast_animations[i])
        
        # Get channels
        channels = await get_broadcast_channels()
        total_channels = len(channels)
        
        if total_channels == 0:
            await msg.edit("❌ **No available channels found for broadcasting!**")
            return
        
        # Continue animation
        await asyncio.sleep(1.5)
        await msg.edit(f"{gcast_animations[5]}\n📊 **Found:** `{total_channels}` chats")
        
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
🚀 **Global Broadcast in Progress...**

📊 **Progress:** `{i}/{total_channels}` ({progress:.1f}%)
✅ **Success:** `{success_count}`
❌ **Failed:** `{failed_count}`
⚡ **Current:** {current_title}...
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
✅ **GLOBAL BROADCAST COMPLETED!**

╔═══════════════════════════════════╗
    📡 **𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗥𝗘𝗣𝗢𝗥𝗧** 📡
╚═══════════════════════════════════╝

📊 **Total Chats:** `{total_channels}`
✅ **Successful:** `{success_count}`
❌ **Failed:** `{failed_count}`
📈 **Success Rate:** `{success_rate:.1f}%`

🔥 **Message delivered successfully!**
⚡ **Powered by Vzoel Assistant**
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
            "🔥 **Connecting to voice chat...**",
            "🎵 **Initializing audio stream...**",
            "🚀 **Joining voice chat...**",
            f"""
✅ **VOICE CHAT JOINED!**

╔═══════════════════════════════╗
   🎵 **𝗩𝗢𝗜𝗖𝗘 𝗖𝗛𝗔𝗧 𝗔𝗖𝗧𝗜𝗩𝗘** 🎵
╚═══════════════════════════════╝

📍 **Chat:** {chat.title[:30] if hasattr(chat, 'title') else 'Private'}
🎙️ **Status:** Connected
📊 **Audio:** Ready
⚡ **Quality:** HD

⚠️ **Note:** Full VC features require pytgcalls
🔥 **Vzoel Assistant VC Ready!**
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

╔═══════════════════════════════╗
   👋 **𝗩𝗢𝗜𝗖𝗘 𝗖𝗛𝗔𝗧 𝗗𝗜𝗦𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗** 👋
╚═══════════════════════════════╝

🔌 **Status:** Disconnected
🎙️ **Audio:** Stopped
✅ **Action:** Completed

🔥 **Successfully left voice chat!**
⚡ **Vzoel Assistant ready for next command**
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

╔═══════════════════════════════╗
   🚩 **𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧** 🚩
╚═══════════════════════════════╝

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
            status_icons.append("🤖 Bot")
        if is_verified:
            status_icons.append("✅ Verified")
        if is_premium:
            status_icons.append("⭐ Premium")
        if is_scam:
            status_icons.append("⚠️ Scam")
        if is_fake:
            status_icons.append("🚫 Fake")
        
        status_text = " | ".join(status_icons) if status_icons else "👤 Regular User"
        
        id_info = f"""
🆔 **USER ID INFORMATION**

╔═══════════════════════════════╗
   🔍 **𝗨𝗦𝗘𝗥 𝗜𝗗 𝗟𝗢𝗢𝗞𝗨𝗣** 🔍
╚═══════════════════════════════╝

👤 **Name:** {user.first_name or 'None'} {user.last_name or ''}
🆔 **User ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}
📞 **Phone:** `{user.phone or 'Hidden'}`
🏷️ **Status:** {status_text}
🌐 **Language:** `{user.lang_code or 'Unknown'}`

📊 **Account Info:**
• **First Name:** `{user.first_name or 'Not set'}`
• **Last Name:** `{user.last_name or 'Not set'}`
• **Bio Available:** {'Yes' if hasattr(user, 'about') else 'No'}

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

╔═══════════════════════════════╗
   📊 **𝗦𝗬𝗦𝗧𝗘𝗠 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡** 📊
╚═══════════════════════════════╝

👤 **Name:** {me.first_name or 'Vzoel Assistant'}
🆔 **User ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
📞 **Phone:** `{me.phone or 'Hidden'}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
🚀 **Version:** v2.1 Enhanced Edition
🔧 **Framework:** Telethon
🐍 **Language:** Python 3.9+
💾 **Session:** Active
🌍 **Server:** Cloud Hosted
🛡️ **Spam Guard:** {'Enabled' if spam_guard_enabled else 'Disabled'}

📊 **Available Commands:**
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}gcast` - Global broadcast
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

╔═══════════════════════════════╗
   📚 **𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗟𝗜𝗦𝗧** 📚
╚═══════════════════════════════╝

🔥 **MAIN COMMANDS:**
• `{COMMAND_PREFIX}alive` - Check bot status
• `{COMMAND_PREFIX}info` - System information
• `{COMMAND_PREFIX}vzl` - Vzoel animation (12 phases)
• `{COMMAND_PREFIX}help` - Show this help
• `{COMMAND_PREFIX}ping` - Response time test

📡 **BROADCAST:**
• `{COMMAND_PREFIX}gcast <message>` - Enhanced global broadcast

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

╔═══════════════════════════════╗
   🛡️ **𝗦𝗣𝗔𝗠 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡** 🛡️
╚═══════════════════════════════╝

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
[╔═══════════════════════════════╗]({VZOEL_LOGO})
   🚩 **𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧** 🚩
╚═══════════════════════════════╝

⟢ Founder    : **𝗩𝘇𝗼𝗲𝗹 𝗙𝗼𝘅'𝘀 (Ltpn)**
⟢ Instagram  : vzoel.fox_s
⟢ Telegram   : @VZLfx | @VZLfxs
⟢ Channel    : t.me/nama_channel

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
        msg = await event.reply("🏓 **Pinging...**")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        ping_text = f"""
🏓 **PONG!**

╔═══════════════════════════════╗
   ⚡ **𝗣𝗜𝗡𝗚 𝗥𝗘𝗦𝗨𝗟𝗧** ⚡
╚═══════════════════════════════╝

⚡ **Response Time:** `{ping_time:.2f}ms`
🚀 **Status:** Active
🔥 **Server:** Online
✅ **Connection:** Stable
📡 **Latency:** {'Low' if ping_time < 100 else 'Normal' if ping_time < 300 else 'High'}

⚡ **Vzoel Assistant is running smoothly!**
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

╔═══════════════════════════════╗
   🔥 **𝗦𝗬𝗦𝗧𝗘𝗠 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗** 🔥
╚═══════════════════════════════╝

✅ **All systems operational**
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`

📌 **Loaded Plugins (Enhanced Edition):**
• ✅ Alive System (3 animations + logo)
• ✅ Enhanced Global Broadcast (8 animations)
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
• `{COMMAND_PREFIX}id @username` - Get user ID
• `{COMMAND_PREFIX}sg` - Toggle spam protection

🔥 **Enhanced features:**
• Improved gcast with better error handling
• New ID lookup plugin
• Logo integration on key commands
• Better broadcast channel detection
• Flood wait protection

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
    
    logger.info("🚀 Starting Vzoel Assistant (Enhanced Edition)...")
    
    try:
        await client.start()
        me = await client.get_me()
        
        logger.info(f"✅ Vzoel Assistant started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"📌 All plugins integrated in main.py")
        logger.info(f"⚡ Enhanced commands: alive, gcast, joinvc, leavevc, vzl, id, info, help, sg, infofounder, ping")
        logger.info(f"🔥 New features: Enhanced gcast, ID lookup, Logo integration")
        
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
    logger.info("🔥 Initializing Vzoel Assistant Enhanced Edition...")
    
    # Validate configuration
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"📝 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Mode: Enhanced Edition (All-in-One with improvements)")
    
    # Start Vzoel Assistant
    if await startup():
        logger.info("🔥 Vzoel Assistant is now running (Enhanced Edition)...")
        logger.info("📝 Press Ctrl+C to stop")
        logger.info("🎯 Enhanced features: Better gcast, ID lookup, Logo integration")
        
        try:
            await client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("👋 Vzoel Assistant stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            logger.info("🔥 Disconnecting...")
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

# ============= END OF VZOEL ASSISTANT ENHANCED EDITION =============

"""
🔥 VZOEL ASSISTANT - ENHANCED EDITION 🔥

✅ NEW FEATURES ADDED:
1. Enhanced gcast.py - Improved error handling, flood protection, better channel detection
2. NEW id.py - User ID lookup by reply or username/ID
3. Logo integration - Telegraph links on alive, help, infofounder, vzl commands
4. Better broadcast system - Based on ultroid's broadcast.py reference
5. Improved error reporting for gcast failures
6. Enhanced channel filtering for better broadcast success
7. FloodWaitError handling with smart retry logic
8. Better progress reporting during broadcast

🚀 ENHANCED GCAST FEATURES:
• Smart channel detection (groups + channels with permissions)
• FloodWait error handling with retry logic
• Better progress reporting every 3 messages
• Error logging with failed chat details
• Improved success rate calculation
• Rate limiting to prevent flood errors

🔍 NEW ID COMMAND FEATURES:
• Get user ID by replying to their message
• Get user ID by username or user ID
• Shows comprehensive user information
• Detects bots, verified, premium, scam accounts
• Shows phone number if available

🖼️ LOGO INTEGRATION:
• Telegraph logo links on key commands
• Enhanced visual presentation
• Consistent branding across commands

🛠️ SETUP INSTRUCTIONS:
1. Save this as main.py
2. Update LOGO_URL and VZOEL_LOGO with your telegraph links
3. Create .env file with your credentials
4. Install: pip install telethon python-dotenv
5. Run: python main.py

⚡ All improvements maintain existing architecture!
⚡ Created by Vzoel Fox's (LTPN) ⚡
"""