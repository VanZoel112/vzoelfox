#!/usr/bin/env python3
"""
Vzoel Assistant Client Plugin Collection
Complete plugin collection with advanced animations and features
Author: Vzoel Fox's (Ltpn)
"""

import asyncio
import logging
import time
import random
import re
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest
from telethon.tl.types import InputPeerChannel, InputGroupCall
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")
OWNER_ID = int(os.getenv("OWNER_ID", "0")) if os.getenv("OWNER_ID") else None
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Global variables
start_time = datetime.now()

# ============= UTILITY FUNCTIONS =============

async def is_owner(user_id):
    """Check if user is owner"""
    try:
        if OWNER_ID:
            return user_id == OWNER_ID
        me = await client.get_me()
        return user_id == me.id
    except Exception:
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

# ============= PLUGIN 1: ALIVE =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Enhanced alive command with animation"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split('.')[0]
        
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
🔥 **Version:** v2.0 Enhanced

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
            """.strip()
        ]
        
        msg = await event.reply(alive_animations[0])
        await animate_text(msg, alive_animations, delay=2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Alive command error: {e}")

# ============= PLUGIN 2: GCAST ADVANCED =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}gcast\s+(.+)', flags=re.DOTALL))
async def gcast_handler(event):
    """Advanced Global Broadcast with animation"""
    if not await is_owner(event.sender_id):
        return
    
    message_to_send = event.pattern_match.group(1).strip()
    if not message_to_send:
        await event.reply("❌ **Usage:** `.gcast <message>`")
        return
    
    try:
        # Animation phases
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
        
        # Final animation
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
    """Join Voice Chat"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        if not hasattr(chat, 'id'):
            await event.reply("❌ **Cannot join VC in this chat!**")
            return
        
        msg = await event.reply("🔄 **Joining voice chat...**")
        
        # Try to join voice chat (simplified version)
        try:
            # This is a basic implementation - real VC joining needs pytgcalls
            await msg.edit("⚠️ **Voice Chat feature requires pytgcalls library**\n✅ **Command received and processed**")
            
        except Exception as vc_error:
            await msg.edit(f"❌ **Failed to join VC:** {str(vc_error)}")
            
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"JoinVC error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}leavevc'))
async def leavevc_handler(event):
    """Leave Voice Chat"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        msg = await event.reply("🔄 **Leaving voice chat...**")
        
        # Try to leave voice chat (simplified version)
        try:
            # This is a basic implementation - real VC leaving needs pytgcalls
            await msg.edit("⚠️ **Voice Chat feature requires pytgcalls library**\n✅ **Leave command processed**")
            
        except Exception as vc_error:
            await msg.edit(f"❌ **Failed to leave VC:** {str(vc_error)}")
            
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"LeaveVC error: {e}")

# ============= PLUGIN 4: VZL COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}vzl'))
async def vzl_handler(event):
    """Vzoel command with 12x animation"""
    if not await is_owner(event.sender_id):
        return
    
    try:
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

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
            """.strip()
        ]
        
        msg = await event.reply(vzl_animations[0])
        await animate_text(msg, vzl_animations, delay=1.2)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"VZL command error: {e}")

# ============= PLUGIN 5: INFO =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}info'))
async def info_handler(event):
    """System information"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split('.')[0]
        
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
🚀 **Version:** v2.0 Enhanced
🔧 **Framework:** Telethon
🐍 **Language:** Python 3.9+
💾 **Session:** Active
🌐 **Server:** Cloud Hosted

📊 **Available Commands:**
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}gcast` - Global broadcast
• `{COMMAND_PREFIX}joinvc` - Join voice chat
• `{COMMAND_PREFIX}leavevc` - Leave voice chat
• `{COMMAND_PREFIX}vzl` - Vzoel animation
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}sg` - Spam guard
• `{COMMAND_PREFIX}infofounder` - Founder info

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(info_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Info command error: {e}")

# ============= PLUGIN 6: HELP =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Help command with all available commands"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        help_text = f"""
🆘 **VZOEL ASSISTANT HELP**

╔══════════════════════════════╗
   📚 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗟𝗜𝗦𝗧 📚
╚══════════════════════════════╝

🔥 **MAIN COMMANDS:**
• `{COMMAND_PREFIX}alive` - Check bot status
• `{COMMAND_PREFIX}info` - System information
• `{COMMAND_PREFIX}vzl` - Vzoel animation
• `{COMMAND_PREFIX}help` - Show this help

📡 **BROADCAST:**
• `{COMMAND_PREFIX}gcast <message>` - Global broadcast

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
```

⚠️ **NOTE:** All commands are owner-only

⚡ **Support:** @VZLfx | @VZLfxs
🔥 **Created by Vzoel Fox's (LTPN)**
⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(help_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Help command error: {e}")

# ============= PLUGIN 7: SPAM GUARD =============

spam_guard_enabled = False
spam_users = {}

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}sg'))
async def spam_guard_handler(event):
    """Toggle spam guard"""
    if not await is_owner(event.sender_id):
        return
    
    global spam_guard_enabled
    
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

{'🟢 **Protection is now ACTIVE!**' if spam_guard_enabled else '🔴 **Protection is now INACTIVE!**'}

⚡ **Hak milik Vzoel Fox's ©2025 ~ LTPN** ⚡
        """.strip()
        
        await event.edit(sg_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Spam guard error: {e}")

@client.on(events.NewMessage)
async def spam_detection(event):
    """Auto spam detection"""
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
                    f"🔥 **Vzoel Protection Active**"
                )
                
                await asyncio.sleep(5)
                await warning_msg.delete()
                
                # Reset counter
                spam_users[user_id] = []
                
            except Exception as e:
                logger.error(f"Spam action error: {e}")
    
    except Exception as e:
        logger.error(f"Spam detection error: {e}")

# ============= PLUGIN 8: INFO FOUNDER =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}infofounder'))
async def infofounder_handler(event):
    """Founder information"""
    if not await is_owner(event.sender_id):
        return
    
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

# ============= PING COMMAND (BONUS) =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Ping command with response time"""
    if not await is_owner(event.sender_id):
        return
    
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

⚡ **Vzoel Assistant is running smoothly!**
        """.strip()
        
        await msg.edit(ping_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Ping error: {e}")

# ============= STARTUP MESSAGE =============

async def send_startup_message():
    """Send startup notification"""
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

🔌 **Loaded Plugins:**
• Alive System ✅
• Global Broadcast ✅
• Voice Chat Control ✅
• Vzoel Animation ✅
• Information System ✅
• Help Command ✅
• Spam Guard ✅
• Founder Info ✅

💡 **Quick Start:**
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}alive` - Check status
• `{COMMAND_PREFIX}info` - System info

🔥 **Vzoel Assistant is ready to serve!**
⚡ **Powered by Vzoel Fox's (LTPN)**
        """.strip()
        
        await client.send_message('me', startup_msg)
        logger.info("✅ Startup message sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

# ============= MAIN FUNCTION =============

async def main():
    """Main function to start the client"""
    logger.info("🚀 Starting Vzoel Assistant Client...")
    
    try:
        await client.start()
        logger.info("✅ Client started successfully")
        
        # Send startup message
        await send_startup_message()
        
        logger.info("🔄 Vzoel Assistant is now running...")
        logger.info("📝 Press Ctrl+C to stop")
        
        # Keep the client running
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("👋 Vzoel Assistant stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        logger.info("🔄 Disconnecting...")
        await client.disconnect()
        logger.info("✅ Vzoel Assistant stopped successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        exit(1)
