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
from datetime import datetime

# ============= KONFIGURASI =============
API_ID = 29919905
API_HASH = "717957f0e3ae20a7db004d08b66bfd30"
SESSION_NAME = "userbot_session"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('userbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ============= EVENT HANDLERS =============

@client.on(events.NewMessage(pattern=r'\.ping'))
async def ping_handler(event):
    """Perintah ping untuk test userbot"""
    if event.sender_id == (await client.get_me()).id:
        start = time.time()
        msg = await event.reply("🏓 Pong!")
        end = time.time()
        await msg.edit(f"🏓 **Pong!**\n⚡ Response time: `{(end-start)*1000:.2f}ms`")

@client.on(events.NewMessage(pattern=r'\.info'))
async def info_handler(event):
    """Informasi userbot"""
    if event.sender_id == (await client.get_me()).id:
        me = await client.get_me()
        uptime = datetime.now() - start_time
        
        info_text = f"""
🤖 **Userbot Info**
👤 Name: {me.first_name or 'N/A'}
🆔 ID: `{me.id}`
📱 Phone: `{me.phone or 'Hidden'}`
⏰ Uptime: `{str(uptime).split('.')[0]}`
🖥️ Server: AWS Ubuntu
        """.strip()
        
        await event.edit(info_text)

@client.on(events.NewMessage(pattern=r'\.alive'))
async def alive_handler(event):
    """Status userbot"""
    if event.sender_id == (await client.get_me()).id:
        await event.edit("✅ **Userbot is alive and running!**\n🚀 Ready to serve you!")

@client.on(events.NewMessage(pattern=r'\.help'))
async def help_handler(event):
    """Daftar perintah"""
    if event.sender_id == (await client.get_me()).id:
        help_text = """
🔧 **Available Commands:**

`.ping` - Test response time
`.info` - Userbot information  
`.alive` - Check if userbot is running
`.help` - Show this help message
`.typing [duration]` - Show typing for X seconds
`.del` - Delete replied message
`.edit [text]` - Edit your last message
`.spam [count] [text]` - Send message X times (use carefully!)

📝 **Usage Examples:**
`.typing 5` - Show typing for 5 seconds
`.spam 3 Hello` - Send "Hello" 3 times
`.edit New text` - Edit your last message

⚠️ **Note:** Only works for your own messages!
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

@client.on(events.NewMessage(pattern=r'\.spam (\d+) (.+)'))
async def spam_handler(event):
    """Send message multiple times"""
    if event.sender_id == (await client.get_me()).id:
        count = int(event.pattern_match.group(1))
        text = event.pattern_match.group(2)
        
        # Limit spam count
        if count > 10:
            await event.edit("❌ Spam limit: max 10 messages!")
            return
            
        await event.delete()
        
        for i in range(count):
            await client.send_message(event.chat_id, f"{text}")
            await asyncio.sleep(0.5)  # Delay to avoid flood

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
