#!/usr/bin/env python3
"""
Telegram Userbot dengan Telethon
Dibuat untuk AWS Ubuntu
"""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
import os
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============= KONFIGURASI =============
API_ID = int(os.getenv("API_ID", "29919905"))
API_HASH = os.getenv("API_HASH", "717957f0e3ae20a7db004d08b66bfd30")
SESSION_NAME = os.getenv("SESSION_NAME", "userbot_session")
OWNER_ID = int(os.getenv("OWNER_ID", "0")) if os.getenv("OWNER_ID") else None
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
MAX_SPAM_COUNT = int(os.getenv("MAX_SPAM_COUNT", "10"))
NOTIFICATION_CHAT = os.getenv("NOTIFICATION_CHAT", "me")

# Setup logging
if ENABLE_LOGGING:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handlers = [
        logging.FileHandler('userbot.log'),
        logging.StreamHandler()
    ]
    if LOG_LEVEL.upper() == "DEBUG":
        handlers.append(logging.FileHandler('debug.log'))
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=log_format,
        handlers=handlers
    )
else:
    logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)

# Initialize client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ============= UTILITY FUNCTIONS =============

async def is_owner(user_id):
    """Check if user is owner"""
    if OWNER_ID:
        return user_id == OWNER_ID
    return user_id == (await client.get_me()).id

async def log_command(event, command):
    """Log command usage"""
    user = await client.get_entity(event.sender_id)
    chat = await event.get_chat()
    logger.info(f"Command '{command}' used by {user.first_name} ({user.id}) in {getattr(chat, 'title', 'Private')}")

# ============= EVENT HANDLERS =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Perintah ping untuk test userbot"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "ping")
    start = time.time()
    msg = await event.reply("🏓 Pong!")
    end = time.time()
    await msg.edit(f"🏓 **Pong!**\n⚡ Response time: `{(end-start)*1000:.2f}ms`")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}info'))
async def info_handler(event):
    """Informasi userbot"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "info")
    me = await client.get_me()
    uptime = datetime.now() - start_time
    
    info_text = f"""
🤖 **Userbot Info**
👤 Name: {me.first_name or 'N/A'}
🆔 ID: `{me.id}`
📱 Phone: `{me.phone or 'Hidden'}`
⚡ Prefix: `{COMMAND_PREFIX}`
⏰ Uptime: `{str(uptime).split('.')[0]}`
🖥️ Server: AWS Ubuntu
📊 Log Level: `{LOG_LEVEL}`
    """.strip()
    
    await event.edit(info_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Status userbot"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "alive")
    uptime = datetime.now() - start_time
    await event.edit(f"✅ **Userbot is alive!**\n🚀 Uptime: `{str(uptime).split('.')[0]}`\n⚡ Prefix: `{COMMAND_PREFIX}`")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Daftar perintah"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "help")
    help_text = f"""
🔧 **Available Commands:**

`{COMMAND_PREFIX}ping` - Test response time
`{COMMAND_PREFIX}info` - Userbot information  
`{COMMAND_PREFIX}alive` - Check if userbot is running
`{COMMAND_PREFIX}help` - Show this help message
`{COMMAND_PREFIX}typing [duration]` - Show typing for X seconds
`{COMMAND_PREFIX}del` - Delete replied message
`{COMMAND_PREFIX}edit [text]` - Edit your last message
`{COMMAND_PREFIX}spam [count] [text]` - Send message X times (max: {MAX_SPAM_COUNT})
`{COMMAND_PREFIX}restart` - Restart userbot
`{COMMAND_PREFIX}logs` - Show recent logs

📝 **Usage Examples:**
`{COMMAND_PREFIX}typing 5` - Show typing for 5 seconds
`{COMMAND_PREFIX}spam 3 Hello` - Send "Hello" 3 times
`{COMMAND_PREFIX}edit New text` - Edit your last message

⚠️ **Note:** Only responds to owner commands!
    """.strip()
    
    await event.edit(help_text)

@client.on(events.NewMessage(pattern=r'\.typing (\d+)'))
async def typing_handler(event):
    """Show typing indicator"""
    if event.sender_id == (await client.get_me()).id:
        duration = int(event.pattern_match.group(1))
        if duration > 60:  # Max 60 seconds
            duration = 60
            
        await event.delete()
        async with client.action(event.chat_id, 'typing'):
            await asyncio.sleep(duration)

@client.on(events.NewMessage(pattern=r'\.del'))
async def delete_handler(event):
    """Delete replied message"""
    if event.sender_id == (await client.get_me()).id:
        if event.reply_to_msg_id:
            try:
                await client.delete_messages(event.chat_id, event.reply_to_msg_id)
                await event.delete()
            except Exception as e:
                await event.edit(f"❌ Error: {str(e)}")
        else:
            await event.edit("❌ Reply to a message to delete it!")

@client.on(events.NewMessage(pattern=r'\.edit (.+)'))
async def edit_handler(event):
    """Edit your last message"""
    if event.sender_id == (await client.get_me()).id:
        new_text = event.pattern_match.group(1)
        
        # Get last message from user
        messages = await client.get_messages(event.chat_id, limit=10, from_user='me')
        for msg in messages:
            if msg.id != event.id and not msg.text.startswith('.edit'):
                try:
                    await msg.edit(new_text)
                    await event.delete()
                    return
                except Exception as e:
                    await event.edit(f"❌ Error: {str(e)}")
                    return
        
        await event.edit("❌ No recent message found to edit!")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}spam (\d+) (.+)'))
async def spam_handler(event):
    """Send message multiple times"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "spam")
    count = int(event.pattern_match.group(1))
    text = event.pattern_match.group(2)
    
    # Limit spam count
    if count > MAX_SPAM_COUNT:
        await event.edit(f"❌ Spam limit: max {MAX_SPAM_COUNT} messages!")
        return
        
    await event.delete()
    
    for i in range(count):
        await client.send_message(event.chat_id, f"{text}")
        await asyncio.sleep(0.5)  # Delay to avoid flood

# New commands
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}restart'))
async def restart_handler(event):
    """Restart userbot"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "restart")
    await event.edit("🔄 **Restarting userbot...**")
    logger.info("Userbot restart requested by user")
    
    # Send notification
    try:
        await client.send_message(NOTIFICATION_CHAT, "🔄 **Userbot is restarting...**")
    except:
        pass
    
    await client.disconnect()
    os._exit(0)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}logs'))
async def logs_handler(event):
    """Show recent logs"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "logs")
    
    try:
        with open('userbot.log', 'r') as f:
            logs = f.readlines()
            recent_logs = ''.join(logs[-20:])  # Last 20 lines
            
        if len(recent_logs) > 4000:
            recent_logs = recent_logs[-4000:]
            
        await event.edit(f"📋 **Recent Logs:**\n```\n{recent_logs}\n```")
    except FileNotFoundError:
        await event.edit("❌ Log file not found!")
    except Exception as e:
        await event.edit(f"❌ Error reading logs: {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}env'))
async def env_handler(event):
    """Show environment info"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "env")
    
    env_info = f"""
🔧 **Environment Info:**
📁 Session: `{SESSION_NAME}`
⚡ Prefix: `{COMMAND_PREFIX}`
📊 Log Level: `{LOG_LEVEL}`
📝 Logging: `{'Enabled' if ENABLE_LOGGING else 'Disabled'}`
🚫 Spam Limit: `{MAX_SPAM_COUNT}`
💬 Notifications: `{NOTIFICATION_CHAT}`
🆔 Owner ID: `{OWNER_ID or 'Auto-detect'}`
    """.strip()
    
    await event.edit(env_info)

# ============= STARTUP FUNCTIONS =============

async def startup():
    """Startup function"""
    global start_time
    start_time = datetime.now()
    
    logger.info("🚀 Starting userbot...")
    
    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Userbot started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        
        # Send startup message to Saved Messages
        try:
            await client.send_message('me', """
🚀 **Userbot Started Successfully!**

✅ All systems operational
📱 Ready to receive commands
⏰ Started at: `{}`

Type `.help` for available commands!
            """.format(start_time.strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            logger.warning(f"Could not send startup message: {e}")
            
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor authentication enabled. Please login manually first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting userbot: {e}")
        return False
    
    return True

async def main():
    """Main function"""
    logger.info("🔄 Initializing userbot...")
    
    # Start userbot
    if await startup():
        logger.info("🔄 Userbot is now running...")
        logger.info("📝 Press Ctrl+C to stop")
        
        try:
            await client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("👋 Userbot stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            logger.info("🔄 Disconnecting...")
            await client.disconnect()
            logger.info("✅ Userbot stopped successfully!")
    else:
        logger.error("❌ Failed to start userbot!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
