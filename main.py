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
            info_text += f"• Commands: {cmd_list}\n"
        
        info_text += "\n"
    
    await event.edit(info_text)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}structure'))
async def structure_handler(event):
    """Show plugins directory structure"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "structure")
    structure_text = list_plugins_structure()
    await event.edit(f"```\n{structure_text}\n```")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}reload'))
async def reload_handler(event):
    """Reload all plugins"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "reload")
    msg = await event.reply("🔄 Reloading plugins...")
    
    try:
        # Clear existing handlers (we'll need to restart for full clean reload)
        global plugin_manager
        
        # Load plugins again
        results = load_plugins()
        
        if results['loaded']:
            location_info = ""
            if results['by_location']['root']:
                location_info += f"\n📁 Root: {len(results['by_location']['root'])} plugins"
            if results['by_location']['plugins']:
                location_info += f"\n📂 Plugins dir: {len(results['by_location']['plugins'])} plugins"
            if results['by_location']['subdirs']:
                location_info += f"\n📁 Subdirs: {len(results['by_location']['subdirs'])} plugins"
            
            await msg.edit(f"✅ **Plugins Reloaded!**\n\n🔌 Loaded {len(results['loaded'])} plugins with {results['total_handlers']} handlers{location_info}")
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
    
    plugin_info = plugin_manager.get_plugin_info() if plugin_manager else {'count': 0}
    
    env_info = f"""
🔧 **Environment Info:**
📁 Session: `{SESSION_NAME}`
⚡ Prefix: `{COMMAND_PREFIX}`
📊 Log Level: `{LOG_LEVEL}`
📝 Logging: `{'Enabled' if ENABLE_LOGGING else 'Disabled'}`
🚫 Spam Limit: `{MAX_SPAM_COUNT}`
💬 Notifications: `{NOTIFICATION_CHAT}`
🆔 Owner ID: `{OWNER_ID or 'Auto-detect'}`
🔌 Plugins: `{plugin_info['count']}` loaded
📂 Plugins Dir: `{'Available' if os.path.exists('plugins') else 'Not found'}`
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
        
        # Load external plugins using enhanced system
        logger.info("🔌 Loading plugins...")
        results = load_plugins()
        
        logger.info(f"✅ Vzoel Assistant started successfully!")
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username or 'No username'})")
        logger.info(f"🆔 User ID: {me.id}")
        logger.info(f"🔌 Loaded {len(results['loaded'])} plugins with {results['total_handlers']} handlers")
        
        # Log plugin locations
        if results['by_location']['root']:
            logger.info(f"📁 Root directory: {len(results['by_location']['root'])} plugins")
        if results['by_location']['plugins']:
            logger.info(f"📂 Plugins directory: {len(results['by_location']['plugins'])} plugins")
        if results['by_location']['subdirs']:
            logger.info(f"📁 Subdirectories: {len(results['by_location']['subdirs'])} plugins")
        
        # Enhanced startup message
        plugin_text = ""
        if results['loaded']:
            location_details = []
            if results['by_location']['root']:
                location_details.append(f"📁 Root: {len(results['by_location']['root'])}")
            if results['by_location']['plugins']:
                location_details.append(f"📂 Plugins: {len(results['by_location']['plugins'])}")
            if results['by_location']['subdirs']:
                location_details.append(f"📁 Subdirs: {len(results['by_location']['subdirs'])}")
            
            plugin_text = f"""
**🔌 External Plugins ({len(results['loaded'])}):**
{' | '.join(location_details)}
**Total Handlers:** `{results['total_handlers']}`
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
• `{COMMAND_PREFIX}structure` - Show directory layout

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
    logger.info(f"
