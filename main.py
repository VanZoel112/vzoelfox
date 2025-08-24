#!/usr/bin/env python3
"""
Telegram Vzoel Assistant dengan Telethon
Enhanced version dengan plugin loader yang lebih baik untuk folder plugins
Dibuat untuk AWS Ubuntu
"""

import asyncio
import logging
import os
import time
import re
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import enhanced plugin manager
from __init__ import get_plugin_manager, list_plugins_structure

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
plugin_manager = None
plugin_stats = {}

# ============= ENHANCED PLUGIN LOADER =============

def load_plugins():
    """Load all plugin files using enhanced plugin manager"""
    global plugin_manager, plugin_stats
    
    plugin_manager = get_plugin_manager()
    results = plugin_manager.load_all_plugins()
    
    # Register event handlers with client
    for plugin_name, plugin_info in plugin_manager.loaded_plugins.items():
        module = plugin_info['module']
        
        # Find and register event handlers
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if hasattr(attr, '_telethon_event'):
                try:
                    client.add_event_handler(attr)
                    logger.debug(f"Registered handler {attr_name} from {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to register handler {attr_name} from {plugin_name}: {e}")
    
    plugin_stats = results
    return results

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
    
    # Get plugin information
    plugin_info = plugin_manager.get_plugin_info() if plugin_manager else {'count': 0, 'total_handlers': 0}
    by_location = plugin_info.get('by_location', {})
    
    location_text = ""
    if by_location.get('root'):
        location_text += f"\n  📁 Root: `{len(by_location['root'])}` plugins"
    if by_location.get('plugins'):
        location_text += f"\n  📂 Plugins dir: `{len(by_location['plugins'])}` plugins"
    if by_location.get('subdirs'):
        location_text += f"\n  📁 Subdirs: `{len(by_location['subdirs'])}` plugins"
    
    info_text = f"""
🤖 **Vzoel Assistant Info**
👤 Name: {me.first_name or 'N/A'}
🆔 ID: `{me.id}`
📱 Phone: `{me.phone or 'Hidden'}`
⚡ Prefix: `{COMMAND_PREFIX}`
⏰ Uptime: `{str(uptime).split('.')[0]}`
🖥️ Server: AWS Ubuntu
📊 Log Level: `{LOG_LEVEL}`
🔌 Plugins: `{plugin_info['count']}` loaded (`{plugin_info['total_handlers']}` handlers){location_text}
    """.strip()
    
    await event.edit(info_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Status Vzoel Assistant"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "alive")
    uptime = datetime.now() - start_time
    plugin_count = plugin_manager.get_plugin_info()['count'] if plugin_manager else 0
    
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
        f"`{COMMAND_PREFIX}plugininfo` - Detailed plugin information",
        f"`{COMMAND_PREFIX}structure` - Show plugins directory structure",
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
Use `{COMMAND_PREFIX}plugins` for loaded plugins
Use `{COMMAND_PREFIX}plugininfo` for detailed info

⚠️ **Note:** Only responds to owner commands!
    """.strip()
    
    await event.edit(help_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugins'))
async def plugins_handler(event):
    """List loaded plugins"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "plugins")
    
    if not plugin_manager or not plugin_manager.loaded_plugins:
        await event.edit("❌ No external plugins loaded")
        return
    
    plugin_info = plugin_manager.get_plugin_info()
    by_location = plugin_info.get('by_location', {})
    
    plugin_text = f"🔌 **Loaded Plugins ({plugin_info['count']}):**\n\n"
    
    if by_location.get('root'):
        plugin_text += f"**📁 Root Directory ({len(by_location['root'])}):**\n"
        plugin_text += "\n".join([f"• `{plugin}`" for plugin in by_location['root']]) + "\n\n"
    
    if by_location.get('plugins'):
        plugin_text += f"**📂 Plugins Directory ({len(by_location['plugins'])}):**\n"
        plugin_text += "\n".join([f"• `{plugin}`" for plugin in by_location['plugins']]) + "\n\n"
    
    if by_location.get('subdirs'):
        plugin_text += f"**📁 Subdirectories ({len(by_location['subdirs'])}):**\n"
        plugin_text += "\n".join([f"• `{plugin}`" for plugin in by_location['subdirs']]) + "\n\n"
    
    plugin_text += f"""💡 **Tips:**
- Add .py files to root or plugins/ directory
- Use `{COMMAND_PREFIX}plugininfo` for detailed information
- Use `{COMMAND_PREFIX}structure` to see directory layout
- Use `{COMMAND_PREFIX}reload` to reload plugins"""
    
    await event.edit(plugin_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugininfo'))
async def plugininfo_handler(event):
    """Detailed plugin information"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "plugininfo")
    
    if not plugin_manager or not plugin_manager.loaded_plugins:
        await event.edit("❌ No plugins loaded")
        return
    
    info_text = f"🔌 **Detailed Plugin Information:**\n\n"
    
    for name, info in plugin_manager.loaded_plugins.items():
        handlers = info['handlers']
        location = info['location']
        commands = info.get('commands', [])
        
        info_text += f"**📦 {name}**\n"
        info_text += f"• Location: `{location}`\n"
        info_text += f"• Handlers: `{handlers}`\n"
        
        if commands:
            cmd_list = ', '.join([f"`{cmd}`" for cmd in commands[:3]])
            if len(commands) > 3:
                cmd_list += f" and {len(commands)-3} more"
            info_text
