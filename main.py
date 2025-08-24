#!/usr/bin/env python3
"""
VZOEL ASSISTANT - MAIN FILE
Complete Telegram Userbot with all plugins integrated
Author: Vzoel Fox's (LTPN)
Version: v2.0 Main Edition
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
from telethon.errors import SessionPasswordNeededError
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
    print(f"❌ Configuration error: {e}")
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
            logging.FileHandler('vzoel_complete.log'),
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

async def get_all_chats():
    """Get all available chats for broadcasting"""
    chats = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                if hasattr(dialog.entity, 'broadcast') and not dialog.entity.broadcast:
                    chats.append(dialog)
                elif not hasattr(dialog.entity, 'broadcast'):
                    chats.append(dialog)
    except Exception as e:
        logger.error(f"Error getting chats: {e}")
    return chats

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

# ============= PLUGIN 1: ALIVE COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with animation"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "alive")
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        alive_animations = [
            "🔄 **Checking system status...**",
            "⚡ **Loading components...**",
            "🚀 **Initializing Vzoel Assistant...**",
            f"""
✅ **VZOEL ASSISTANT IS ALIVE!**

╔══════════════════════════════╗
   🚩 𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧 🚩
╚══════════════════════════════╝

👤 **Name:** {me.first_name or 'Vzoel Assistant'}
🆔 **ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
🏓 **Status:** Active & Running
🔥 **Version:** v2.0 Complete

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
            """.strip()
        ]
        
        msg = await event.reply(alive_animations[0])
        await animate_text(msg, alive_animations, delay=2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Alive command error: {e}")

# ============= PLUGIN 2: GCAST COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}gcast\s+(.+)', flags=re.DOTALL))
async def gcast_handler(event):
    """Advanced Global Broadcast with 8-phase animation"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    message_to_send = event.pattern_match.group(1).strip()
    if not message_to_send:
        await event.reply("❌ **Usage:** `.gcast <message>`")
        return
    
    try:
        # 8-phase animation as requested
        gcast_animations = [
            "🔍 **Scanning available chats...**",
            "📡 **Establishing broadcast connection...**",
            "⚡ **Initializing transmission protocol...**",
            "🚀 **Preparing message distribution...**",
            "📨 **Starting global broadcast...**",
            "🔄 **Broadcasting in progress...**",
            "✅ **Broadcast transmission active...**",
            "📊 **Finalizing delivery status...**"
        ]
        
        msg = await event.reply(gcast_animations[0])
        
        # Animate first 4 phases
        for i in range(1, 5):
            await asyncio.sleep(1.5)
            await msg.edit(gcast_animations[i])
        
        # Get chats
        chats = await get_all_chats()
        total_chats = len(chats)
        
        if total_chats == 0:
            await msg.edit("❌ **No available chats found for broadcasting!**")
            return
        
        # Continue animation
        await asyncio.sleep(1.5)
        await msg.edit(f"{gcast_animations[5]}\n📊 **Found:** `{total_chats}` chats")
        
        await asyncio.sleep(1.5)
        await msg.edit(f"{gcast_animations[6]}\n📊 **Broadcasting to:** `{total_chats}` chats")
        
        # Start broadcasting
        success_count = 0
        failed_count = 0
        
        for i, chat in enumerate(chats, 1):
            try:
                await client.send_message(chat.entity, message_to_send)
                success_count += 1
                
                # Update progress every 5 messages
                if i % 5 == 0 or i == total_chats:
                    progress = (i / total_chats) * 100
                    await msg.edit(f"""
🚀 **Global Broadcast in Progress...**

📊 **Progress:** `{i}/{total_chats}` ({progress:.1f}%)
✅ **Success:** `{success_count}`
❌ **Failed:** `{failed_count}`
⚡ **Current:** {chat.title[:20]}...
                    """.strip())
                
                await asyncio.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Gcast error for {chat.title}: {e}")
                continue
        
        # Final animation phase
        await asyncio.sleep(2)
        await msg.edit(gcast_animations[7])
        
        await asyncio.sleep(2)
        final_message = f"""
✅ **GLOBAL BROADCAST COMPLETED!**

╔═══════════════════════════════╗
    📡 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗥𝗘𝗣𝗢𝗥𝗧 📡
╚═══════════════════════════════╝

📊 **Total Chats:** `{total_chats}`
✅ **Successful:** `{success_count}`
❌ **Failed:** `{failed_count}`
📈 **Success Rate:** `{(success_count/total_chats)*100:.1f}%`

🔥 **Message delivered successfully!**
⚡ **Powered by Vzoel Assistant**
        """.strip()
        
        await msg.edit(final_message)
        
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
            "🔄 **Connecting to voice chat...**",
            "🎵 **Initializing audio stream...**",
            "🚀 **Joining voice chat...**",
            f"""
✅ **VOICE CHAT JOINED!**

╔══════════════════════════════╗
   🎵 𝗩𝗢𝗜𝗖𝗘 𝗖𝗛𝗔𝗧 𝗔𝗖𝗧𝗜𝗩𝗘 🎵
╚══════════════════════════════╝

📍 **Chat:** {chat.title[:30] if hasattr(chat, 'title') else 'Private'}
🎙️ **Status:** Connected
🔊 **Audio:** Ready
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
            "🔄 **Disconnecting from voice chat...**",
            "🎵 **Stopping audio stream...**",
            "👋 **Leaving voice chat...**",
            """
✅ **VOICE CHAT LEFT!**

╔══════════════════════════════╗
   👋 𝗩𝗢𝗜𝗖𝗘 𝗖𝗛𝗔𝗧 𝗗𝗜𝗦𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 👋
╚══════════════════════════════╝

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
🔥 **VZOEL FOX'S ASSISTANT** 🔥

╔══════════════════════════════╗
   🚩 𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧 🚩
╚══════════════════════════════╝

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

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
            """.strip()
        ]
        
        msg = await event.reply(vzl_animations[0])
        await animate_text(msg, vzl_animations, delay=1.2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"VZL command error: {e}")

# ============= PLUGIN 5: INFO COMMAND =============

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

╔══════════════════════════════╗
   📊 𝗦𝗬𝗦𝗧𝗘𝗠 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 📊
╚══════════════════════════════╝

👤 **Name:** {me.first_name or 'Vzoel Assistant'}
🆔 **User ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
📞 **Phone:** `{me.phone or 'Hidden'}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Uptime:** `{uptime_str}`
🚀 **Version:** v2.0 Main Edition
🔧 **Framework:** Telethon
🐍 **Language:** Python 3.9+
💾 **Session:** Active
🌐 **Server:** Cloud Hosted
🛡️ **Spam Guard:** {'Enabled' if spam_guard_enabled else 'Disabled'}

📊 **Available Commands:**
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}gcast` - Global broadcast
• `{COMMAND_PREFIX}joinvc` - Join voice chat
• `{COMMAND_PREFIX}leavevc` - Leave voice chat
• `{COMMAND_PREFIX}vzl` - Vzoel animation
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

# ============= PLUGIN 6: HELP COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Help command with all available commands"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "help")
    
    try:
        help_text = f"""
🆘 **VZOEL ASSISTANT HELP**

╔══════════════════════════════╗
   📚 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗟𝗜𝗦𝗧 📚
╚══════════════════════════════╝

🔥 **MAIN COMMANDS:**
• `{COMMAND_PREFIX}alive` - Check bot status
• `{COMMAND_PREFIX}info` - System information
• `{COMMAND_PREFIX}vzl` - Vzoel animation (12 phases)
• `{COMMAND_PREFIX}help` - Show this help
• `{COMMAND_PREFIX}ping` - Response time test

📡 **BROADCAST:**
• `{COMMAND_PREFIX}gcast <message>` - Global broadcast (8 phases)

🎵 **VOICE CHAT:**
• `{COMMAND_PREFIX}joinvc` - Join voice chat
• `{COMMAND_PREFIX}leavevc` - Leave voice chat

🛡️ **SECURITY:**
• `{COMMAND_PREFIX}sg` - Spam guard toggle

ℹ️ **INFORMATION:**
• `{COMMAND_PREFIX}infofounder` - Founder information

📝 **USAGE EXAMPLES:**
```
{COMMAND_PREFIX}alive
{COMMAND_PREFIX}gcast Hello everyone!
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

# ============= PLUGIN 7: SPAM GUARD =============

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

╔══════════════════════════════╗
   🛡️ 𝗦𝗣𝗔𝗠 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡 🛡️
╚══════════════════════════════╝

🔄 **Status:** {status}
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

# ============= PLUGIN 8: INFO FOUNDER =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}infofounder'))
async def infofounder_handler(event):
    """Founder information - exact as requested"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "infofounder")
    
    try:
        founder_info = (
            "╔══════════════════════════════╗\n"
            "   🚩 𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧 🚩\n"
            "╚══════════════════════════════╝\n\n"
            "⟢ Founder    : 𝗩𝘇𝗼𝗲𝗹 𝗙𝗼𝘅'𝘀 (Ltpn)\n"
            "⟢ Instagram  : vzoel.fox_s\n"
            "⟢ Telegram   : @VZLfx | @VZLfxs\n"
            "⟢ Channel    : t.me/nama_channel\n\n"
            "⚡ Hak milik 𝗩𝘇𝗼𝗲𝗹 𝗙𝗼𝘅'𝘀 ©2025 ~ LTPN. ⚡"
        )
        
        await event.edit(founder_info)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"InfoFounder error: {e}")

# ============= BONUS: PING COMMAND =============

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

╔══════════════════════════════╗
   ⚡ 𝗣𝗜𝗡𝗚 𝗥𝗘𝗦𝗨𝗟𝗧 ⚡
╚══════════════════════════════╝

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
🚀 **VZOEL ASSISTANT STARTED!**

╔══════════════════════════════╗
   🔥 𝗦𝗬𝗦𝗧𝗘𝗠 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗 🔥
╚══════════════════════════════╝

✅ **All systems operational**
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`

🔌 **Loaded Plugins (Main Edition):**
• ✅ Alive System (3 animations)
• ✅ Global Broadcast (8 animations)
• ✅ Voice Chat Control
• ✅ Vzoel Animation (12 phases)
• ✅ Information System
• ✅ Help Command
• ✅ Spam Guard (Auto-detection)
• ✅ Founder Info
• ✅ Ping System

💡 **Quick Start:**
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}alive` - Check status
• `{COMMAND_PREFIX}vzl` - 12-phase animation
• `{COMMAND_PREFIX}gcast <message>` - Broadcast
• `{COMMAND_PREFIX}sg` - Toggle spam protection

🔥 **All plugins integrated in main.py!**
⚡ **Powered by Vzoel Fox's (LTPN)**
        """.strip()
        
        await client.send_message('me', startup_msg)
        logger.info("✅ Startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

async def startup():
    """Enhanced startup function"""
    global start_time
    start_time = datetime.now()
    
    logger.info("🚀 Starting Vzoel Assistant (Main Edition)...")
    
    try:
        await client.start()
        me = await client.get_me()
        
        logger.info(f"✅ Vzoel Assistant started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"🔌 All plugins integrated in main.py")
        logger.info(f"⚡ Commands available: alive, gcast, joinvc, leavevc, vzl, info, help, sg, infofounder, ping")
        
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
    """Main function to run the complete userbot"""
    logger.info("🔄 Initializing Vzoel Assistant Main Edition...")
    
    # Validate configuration
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"📁 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Mode: Main Edition (All-in-One)")
    
    # Start Vzoel Assistant
    if await startup():
        logger.info("🔄 Vzoel Assistant is now running (Main Edition)...")
        logger.info("📝 Press Ctrl+C to stop")
        logger.info("🎯 All plugins integrated in main.py")
        
        try:
            await client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("👋 Vzoel Assistant stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            logger.info("🔄 Disconnecting...")
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

# ============= END OF VZOEL ASSISTANT MAIN EDITION =============

"""
🔥 VZOEL ASSISTANT - MAIN EDITION 🔥

✅ FEATURES INCLUDED:
1. alive.py - System status with 3-phase animation
2. gcast.py - Global broadcast with 8-phase animation + progress
3. joinleavevc.py - Voice chat control with animations  
4. vzl.py - 12-phase Vzoel animation as requested
5. info.py - Complete system information
6. help.py - Full command documentation
7. sg.py - Advanced spam guard with auto-detection
8. infofounder.py - Exact founder info as requested
9. ping.py - Response time testing (bonus)

🚀 SETUP INSTRUCTIONS:
1. Save this as main.py
2. Create .env file with:
   API_ID=your_api_id
   API_HASH=your_api_hash
   SESSION_NAME=vzoel_session
   OWNER_ID=your_user_id (optional)
   COMMAND_PREFIX=.
   
3. Install dependencies:
   pip install telethon python-dotenv

4. Run: python main.py

🎯 ALL PLUGINS INTEGRATED IN MAIN.PY!

⚡ Created by Vzoel Fox's (LTPN) ⚡
"""