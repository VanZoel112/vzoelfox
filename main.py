#!/usr/bin/env python3
"""
Telegram Vzoel Assistant dengan Telethon
Enhanced version dengan plugin loader
Dibuat untuk AWS Ubuntu
"""

import asyncio
import logging
import glob
import importlib.util
import os
import time
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============= KONFIGURASI =============
API_ID = int(os.getenv("API_ID", "29919905"))
API_HASH = os.getenv("API_HASH", "717957f0e3ae20a7db004d08b66bfd30")
SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")
OWNER_ID = int(os.getenv("OWNER_ID", "0")) if os.getenv("OWNER_ID") else None
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
MAX_SPAM_COUNT = int(os.getenv("MAX_SPAM_COUNT", "10"))
NOTIFICATION_CHAT = os.getenv("NOTIFICATION_CHAT", "me")

# Validation
if not API_ID or not API_HASH:
    print("❌ ERROR: API_ID and API_HASH must be set in .env file!")
    exit(1)

# Setup logging
if ENABLE_LOGGING:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handlers = [
        logging.FileHandler('vzoel_assistant.log'),
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

# Global variables
start_time = None
loaded_plugins = []

# ============= PLUGIN LOADER =============

def load_plugins():
    """Load all plugin files automatically"""
    global loaded_plugins
    plugin_files = glob.glob("*.py")
    loaded_plugins = []
    
    # Skip main files
    skip_files = ['main.py', 'config.py', '__init__.py']
    
    for file in plugin_files:
        if file in skip_files:
            continue
            
        try:
            plugin_name = file[:-3]  # Remove .py extension
            spec = importlib.util.spec_from_file_location(plugin_name, file)
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Register event handlers from plugin if they exist
                handlers_found = 0
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if hasattr(attr, '_telethon_event'):
                        client.add_event_handler(attr)
                        handlers_found += 1
                
                if handlers_found > 0:
                    loaded_plugins.append(f"{plugin_name}({handlers_found})")
                    logger.info(f"✅ Plugin loaded: {plugin_name} - {handlers_found} handlers")
                else:
                    loaded_plugins.append(plugin_name)
                    logger.info(f"✅ Plugin loaded: {plugin_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {file}: {e}")
    
    return loaded_plugins

# ============= UTILITY FUNCTIONS =============

async def is_owner(user_id):
    """Check if user is owner"""
    if OWNER_ID:
        return user_id == OWNER_ID
    return user_id == (await client.get_me()).id

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

# ============= BUILT-IN EVENT HANDLERS =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}ping'))
async def ping_handler(event):
    """Perintah ping untuk test Vzoel Assistant"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "ping")
    start = time.time()
    msg = await event.reply("🏓 Pong!")
    end = time.time()
    await msg.edit(f"🏓 **Pong!**\n⚡ Response time: `{(end-start)*1000:.2f}ms`")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}info'))
async def info_handler(event):
    """Informasi Vzoel Assistant"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "info")
    me = await client.get_me()
    uptime = datetime.now() - start_time
    
    plugin_text = ""
    if loaded_plugins:
        plugin_text = f"\n🔌 Plugins: `{len(loaded_plugins)}` loaded"
    
    info_text = f"""
🤖 **Vzoel Assistant Info**
👤 Name: {me.first_name or 'N/A'}
🆔 ID: `{me.id}`
📱 Phone: `{me.phone or 'Hidden'}`
⚡ Prefix: `{COMMAND_PREFIX}`
⏰ Uptime: `{str(uptime).split('.')[0]}`
🖥️ Server: AWS Ubuntu
📊 Log Level: `{LOG_LEVEL}`{plugin_text}
    """.strip()
    
    await event.edit(info_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Status Vzoel Assistant"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "alive")
    uptime = datetime.now() - start_time
    plugin_count = len(loaded_plugins)
    
    alive_text = f"""
✅ **Vzoel Assistant is alive!**
🚀 Uptime: `{str(uptime).split('.')[0]}`
⚡ Prefix: `{COMMAND_PREFIX}`
🔌 Plugins: `{plugin_count}` active
    """.strip()
    
    await event.edit(alive_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Daftar perintah"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "help")
    
    # Built-in commands
    builtin_commands = [
        f"`{COMMAND_PREFIX}ping` - Test response time",
        f"`{COMMAND_PREFIX}info` - Vzoel Assistant information",
        f"`{COMMAND_PREFIX}alive` - Check if Vzoel Assistant is running",
        f"`{COMMAND_PREFIX}help` - Show this help message",
        f"`{COMMAND_PREFIX}plugins` - List loaded plugins",
        f"`{COMMAND_PREFIX}reload` - Reload all plugins",
        f"`{COMMAND_PREFIX}typing [duration]` - Show typing for X seconds",
        f"`{COMMAND_PREFIX}del` - Delete replied message",
        f"`{COMMAND_PREFIX}edit [text]` - Edit your last message",
        f"`{COMMAND_PREFIX}spam [count] [text]` - Send message X times (max: {MAX_SPAM_COUNT})",
        f"`{COMMAND_PREFIX}restart` - Restart Vzoel Assistant",
        f"`{COMMAND_PREFIX}logs` - Show recent logs",
        f"`{COMMAND_PREFIX}env` - Show environment info"
    ]
    
    help_text = f"""
🔧 **Available Commands:**

**📋 Built-in Commands:**
{chr(10).join(builtin_commands)}

**📝 Usage Examples:**
`{COMMAND_PREFIX}typing 5` - Show typing for 5 seconds
`{COMMAND_PREFIX}spam 3 Hello` - Send "Hello" 3 times
`{COMMAND_PREFIX}edit New text` - Edit your last message

**🔌 Plugin Commands:**
Type `{COMMAND_PREFIX}plugins` to see loaded plugins

⚠️ **Note:** Only responds to owner commands!
    """.strip()
    
    await event.edit(help_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugins'))
async def plugins_handler(event):
    """List loaded plugins"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "plugins")
    
    if not loaded_plugins:
        await event.edit("❌ No external plugins loaded")
        return
    
    plugin_text = f"""
🔌 **Loaded Plugins ({len(loaded_plugins)}):**

{chr(10).join([f"• `{plugin}`" for plugin in loaded_plugins])}

💡 **Tips:**
- Add .py files to auto-load plugins
- Use `{COMMAND_PREFIX}reload` to reload plugins
- Check logs for plugin errors
    """.strip()
    
    await event.edit(plugin_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}reload'))
async def reload_handler(event):
    """Reload all plugins"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "reload")
    msg = await event.reply("🔄 Reloading plugins...")
    
    try:
        # Clear existing plugin handlers (if any way to do this)
        new_plugins = load_plugins()
        
        if new_plugins:
            await msg.edit(f"✅ **Plugins Reloaded!**\n\n🔌 Loaded {len(new_plugins)} plugins:\n{chr(10).join([f'• `{p}`' for p in new_plugins])}")
        else:
            await msg.edit("⚠️ No external plugins found to reload")
            
    except Exception as e:
        await msg.edit(f"❌ Error reloading plugins: {str(e)}")

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

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}restart'))
async def restart_handler(event):
    """Restart Vzoel Assistant"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "restart")
    await event.edit("🔄 **Restarting Vzoel Assistant...**")
    logger.info("Vzoel Assistant restart requested by user")
    
    # Send notification
    try:
        await client.send_message(NOTIFICATION_CHAT, "🔄 **Vzoel Assistant is restarting...**")
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
        with open('vzoel_assistant.log', 'r') as f:
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
🔌 Plugins: `{len(loaded_plugins)}` loaded
    """.strip()
    
    await event.edit(env_info)

# ============= STARTUP FUNCTIONS =============

async def startup():
    """Enhanced startup function with plugin loading"""
    global start_time
    start_time = datetime.now()
    
    logger.info("🚀 Starting enhanced Vzoel Assistant...")
    
    try:
        await client.start()
        me = await client.get_me()
        
        # Load external plugins
        logger.info("🔌 Loading plugins...")
        loaded = load_plugins()
        
        logger.info(f"✅ Vzoel Assistant started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"🔌 Loaded {len(loaded)} external plugins")
        
        if loaded:
            logger.info(f"📋 Plugin list: {', '.join(loaded)}")
        
        # Enhanced startup message
        plugin_text = ""
        if loaded:
            plugin_text = f"""
**🔌 External Plugins ({len(loaded)}):**
{chr(10).join([f'• `{p}`' for p in loaded])}
"""
        
        startup_message = f"""
🚀 **Enhanced Vzoel Assistant Started!**

✅ All systems operational
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
🔌 **Built-in Commands:** Ready
{plugin_text}
**💡 Quick Start:**
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}info` - Vzoel Assistant information
• `{COMMAND_PREFIX}plugins` - List plugins

**🎯 Ready to receive commands!**
        """.strip()
        
        try:
            await client.send_message('me', startup_message)
        except Exception as e:
            logger.warning(f"Could not send startup message: {e}")
            
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor authentication enabled. Please login manually first.")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting Vzoel Assistant: {e}")
        return False
    
    return True

async def main():
    """Enhanced main function"""
    logger.info("🔄 Initializing enhanced Vzoel Assistant...")
    
    # Validate configuration
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"📁 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    
    # Start Vzoel Assistant
    if await startup():
        logger.info("🔄 Enhanced Vzoel Assistant is now running...")
        logger.info("📝 Press Ctrl+C to stop")
        
        try:
            await client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("👋 Vzoel Assistant stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            logger.info("🔄 Disconnecting...")
            await client.disconnect()
            logger.info("✅ Enhanced Vzoel Assistant stopped successfully!")
    else:
        logger.error("❌ Failed to start enhanced Vzoel Assistant!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
