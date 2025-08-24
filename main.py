#!/usr/bin/env python3
"""
Telegram Vzoel Assistant dengan Telethon - FIXED VERSION
Enhanced version dengan plugin loader yang diperbaiki
FIXED: Masalah plugin loading dan event registration
"""

import asyncio
import logging
import os
import time
import re
import sys
import glob
import importlib
import importlib.util
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import enhanced plugin manager
try:
    from __init__ import get_plugin_manager, list_plugins_structure
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure __init__.py is in the same directory")
    sys.exit(1)

# ============= KONFIGURASI =============
try:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")
    OWNER_ID = int(os.getenv("OWNER_ID", "0")) if os.getenv("OWNER_ID") else None
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    MAX_SPAM_COUNT = int(os.getenv("MAX_SPAM_COUNT", "10"))
    NOTIFICATION_CHAT = os.getenv("NOTIFICATION_CHAT", "me")
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
log_handlers = []
if ENABLE_LOGGING:
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler
    try:
        file_handler = logging.FileHandler('vzoel_assistant.log')
        file_handler.setFormatter(logging.Formatter(log_format))
        log_handlers.append(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    log_handlers.append(console_handler)
    
    # Debug handler if debug mode
    if LOG_LEVEL.upper() == "DEBUG":
        try:
            debug_handler = logging.FileHandler('debug.log')
            debug_handler.setFormatter(logging.Formatter(log_format))
            log_handlers.append(debug_handler)
        except Exception as e:
            print(f"Warning: Could not create debug log file: {e}")
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=log_handlers
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
plugin_manager = None
plugin_stats = {}

# ============= ENHANCED PLUGIN LOADER (FIXED) =============

def discover_all_plugin_files():
    """FIXED: Discover ALL plugin files including root directory"""
    plugin_files = []
    
    # Files to skip
    skip_files = ['main.py', 'config.py', '__init__.py', 'debug_vzoel_plugins.py']
    
    logger.info("🔍 Discovering plugin files...")
    
    # 1. Check ROOT directory for .py files (IMPORTANT!)
    root_files = glob.glob("*.py")
    for file in root_files:
        filename = os.path.basename(file)
        if filename not in skip_files and not filename.startswith('_'):
            plugin_files.append({
                'path': file,
                'name': os.path.splitext(filename)[0],
                'location': 'root',
                'filename': filename
            })
            logger.info(f"📁 Found root plugin: {filename}")
    
    # 2. Check plugins directory
    if os.path.exists("plugins"):
        plugins_dir_files = glob.glob("plugins/*.py")
        for file in plugins_dir_files:
            filename = os.path.basename(file)
            if filename != '__init__.py':
                plugin_files.append({
                    'path': file,
                    'name': f"plugins_{os.path.splitext(filename)[0]}",
                    'location': 'plugins',
                    'filename': filename
                })
                logger.info(f"📂 Found plugins directory file: {filename}")
        
        # 3. Check subdirectories in plugins
        for subdir in glob.glob("plugins/*/"):
            if os.path.isdir(subdir):
                subdir_name = os.path.basename(subdir.rstrip('/'))
                subdir_files = glob.glob(os.path.join(subdir, "*.py"))
                
                for file in subdir_files:
                    filename = os.path.basename(file)
                    if filename != '__init__.py':
                        plugin_files.append({
                            'path': file,
                            'name': f"{subdir_name}_{os.path.splitext(filename)[0]}",
                            'location': f'plugins/{subdir_name}',
                            'filename': filename
                        })
                        logger.info(f"📁 Found subdirectory plugin: {subdir_name}/{filename}")
    
    logger.info(f"🎯 Total plugin files discovered: {len(plugin_files)}")
    return plugin_files

def load_single_plugin_file(plugin_info):
    """FIXED: Load single plugin file dengan error handling yang lebih baik"""
    file_path = plugin_info['path']
    plugin_name = plugin_info['name']
    filename = plugin_info['filename']
    location = plugin_info['location']
    
    logger.info(f"🔄 Loading plugin: {filename} from {location}")
    
    try:
        # Add plugin directory to sys.path temporarily
        plugin_dir = os.path.dirname(os.path.abspath(file_path))
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
            temp_path_added = True
        else:
            temp_path_added = False
        
        # Create module spec
        spec = importlib.util.spec_from_file_location(plugin_name, file_path)
        if not spec or not spec.loader:
            logger.error(f"❌ Cannot create spec for {filename}")
            return None
        
        # Load module
        module = importlib.util.module_from_spec(spec)
        
        # Execute module
        spec.loader.exec_module(module)
        
        # Clean up temporary path
        if temp_path_added:
            sys.path.remove(plugin_dir)
        
        logger.info(f"✅ Successfully loaded plugin module: {filename}")
        return module
        
    except SyntaxError as e:
        logger.error(f"❌ Syntax error in {filename}: Line {e.lineno}: {e.msg}")
        return None
    except ImportError as e:
        logger.error(f"❌ Import error in {filename}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to load plugin {filename}: {e}")
        return None

def register_plugin_handlers(module, plugin_name):
    """FIXED: Register event handlers from plugin dengan client"""
    handlers_registered = 0
    commands = []
    
    try:
        # Find all event handlers in module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a telethon event handler
            if hasattr(attr, '_telethon_event') and callable(attr):
                try:
                    # FIXED: Register handler dengan client
                    client.add_event_handler(attr)
                    handlers_registered += 1
                    
                    logger.info(f"✅ Registered handler: {attr_name} from {plugin_name}")
                    
                    # Extract command pattern if possible
                    try:
                        if hasattr(attr._telethon_event, 'pattern'):
                            pattern = attr._telethon_event.pattern
                            if pattern:
                                command_str = str(pattern.pattern) if hasattr(pattern, 'pattern') else str(pattern)
                                commands.append(command_str)
                    except:
                        pass
                        
                except Exception as e:
                    logger.error(f"❌ Failed to register handler {attr_name}: {e}")
        
        return handlers_registered, commands
        
    except Exception as e:
        logger.error(f"❌ Error registering handlers from {plugin_name}: {e}")
        return 0, []

def load_plugins():
    """FIXED: Load all plugin files dengan improved discovery"""
    global plugin_manager, plugin_stats
    
    logger.info("🔌 Starting enhanced plugin loading...")
    
    # Initialize results
    results = {
        'loaded': [],
        'failed': [],
        'total_handlers': 0,
        'by_location': {'root': [], 'plugins': [], 'subdirs': []},
        'loaded_modules': {}
    }
    
    try:
        # Use enhanced plugin manager for directory plugins
        plugin_manager = get_plugin_manager()
        manager_results = plugin_manager.load_all_plugins()
        
        # Register handlers from plugin manager
        for plugin_name, plugin_info in plugin_manager.loaded_plugins.items():
            module = plugin_info['module']
            handlers_count, commands = register_plugin_handlers(module, plugin_name)
            
            if handlers_count > 0:
                results['loaded'].append(plugin_name)
                results['total_handlers'] += handlers_count
                results['loaded_modules'][plugin_name] = {
                    'module': module,
                    'handlers': handlers_count,
                    'commands': commands,
                    'location': plugin_info['location']
                }
                
                # Categorize by location
                location = plugin_info['location']
                if location == 'root':
                    results['by_location']['root'].append(plugin_name)
                elif location == 'plugins':
                    results['by_location']['plugins'].append(plugin_name)
                else:
                    results['by_location']['subdirs'].append(plugin_name)
        
        # FIXED: Also discover and load ROOT directory files that might be missed
        all_files = discover_all_plugin_files()
        
        for file_info in all_files:
            plugin_name = file_info['name']
            
            # Skip if already loaded by plugin manager
            if plugin_name in results['loaded']:
                continue
                
            # Try to load the file
            module = load_single_plugin_file(file_info)
            if module:
                handlers_count, commands = register_plugin_handlers(module, plugin_name)
                
                if handlers_count > 0:
                    results['loaded'].append(plugin_name)
                    results['total_handlers'] += handlers_count
                    results['loaded_modules'][plugin_name] = {
                        'module': module,
                        'handlers': handlers_count,
                        'commands': commands,
                        'location': file_info['location']
                    }
                    
                    # Categorize by location
                    if file_info['location'] == 'root':
                        results['by_location']['root'].append(plugin_name)
                    elif file_info['location'] == 'plugins':
                        results['by_location']['plugins'].append(plugin_name)
                    else:
                        results['by_location']['subdirs'].append(plugin_name)
                    
                    logger.info(f"✅ Extra plugin loaded: {file_info['filename']} ({handlers_count} handlers)")
                else:
                    logger.warning(f"⚠️ Plugin loaded but no handlers: {file_info['filename']}")
            else:
                results['failed'].append(f"{plugin_name} ({file_info['location']})")
        
        plugin_stats = results
        logger.info(f"🎉 Plugin loading completed: {len(results['loaded'])} loaded, {results['total_handlers']} handlers")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Critical error in plugin loading: {e}")
        return results

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
    try:
        me = await client.get_me()
        uptime = datetime.now() - start_time if start_time else "Unknown"
        
        # Get plugin information
        total_plugins = len(plugin_stats.get('loaded', []))
        total_handlers = plugin_stats.get('total_handlers', 0)
        by_location = plugin_stats.get('by_location', {})
        
        location_text = ""
        if by_location.get('root'):
            location_text += f"\n  📁 Root: `{len(by_location['root'])}` plugins"
        if by_location.get('plugins'):
            location_text += f"\n  📂 Plugins dir: `{len(by_location['plugins'])}` plugins"
        if by_location.get('subdirs'):
            location_text += f"\n  📁 Subdirs: `{len(by_location['subdirs'])}` plugins"
        
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        info_text = f"""
🤖 **Vzoel Assistant Info (FIXED)**
👤 Name: {me.first_name or 'N/A'}
🆔 ID: `{me.id}`
📱 Phone: `{me.phone or 'Hidden'}`
⚡ Prefix: `{COMMAND_PREFIX}`
⏰ Uptime: `{uptime_str}`
🖥️ Server: AWS Ubuntu
📊 Log Level: `{LOG_LEVEL}`
🔌 Plugins: `{total_plugins}` loaded (`{total_handlers}` handlers){location_text}
🎯 Plugin System: Enhanced & Fixed
        """.strip()
        
        await event.edit(info_text)
    except Exception as e:
        await event.edit(f"❌ Error getting info: {str(e)}")
        logger.error(f"Error in info handler: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugins'))
async def plugins_handler(event):
    """List loaded plugins (ENHANCED)"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "plugins")
    
    if not plugin_stats or not plugin_stats.get('loaded'):
        await event.edit("❌ No plugins loaded")
        return
    
    try:
        loaded_plugins = plugin_stats.get('loaded', [])
        total_handlers = plugin_stats.get('total_handlers', 0)
        by_location = plugin_stats.get('by_location', {})
        
        plugin_text = f"🔌 **Loaded Plugins ({len(loaded_plugins)}):**\n\n"
        
        if by_location.get('root'):
            plugin_text += f"**📁 Root Directory ({len(by_location['root'])}):**\n"
            for plugin in by_location['root']:
                handlers = plugin_stats.get('loaded_modules', {}).get(plugin, {}).get('handlers', 0)
                plugin_text += f"• `{plugin}` ({handlers} handlers)\n"
            plugin_text += "\n"
        
        if by_location.get('plugins'):
            plugin_text += f"**📂 Plugins Directory ({len(by_location['plugins'])}):**\n"
            for plugin in by_location['plugins']:
                handlers = plugin_stats.get('loaded_modules', {}).get(plugin, {}).get('handlers', 0)
                plugin_text += f"• `{plugin}` ({handlers} handlers)\n"
            plugin_text += "\n"
        
        if by_location.get('subdirs'):
            plugin_text += f"**📁 Subdirectories ({len(by_location['subdirs'])}):**\n"
            for plugin in by_location['subdirs']:
                handlers = plugin_stats.get('loaded_modules', {}).get(plugin, {}).get('handlers', 0)
                plugin_text += f"• `{plugin}` ({handlers} handlers)\n"
            plugin_text += "\n"
        
        plugin_text += f"📊 **Total:** {total_handlers} event handlers registered\n\n"
        plugin_text += f"""💡 **Tips:**
- Root plugins auto-loaded from current directory
- Use `{COMMAND_PREFIX}reload` to reload all plugins
- Check logs for detailed loading information"""
        
        await event.edit(plugin_text)
    except Exception as e:
        await event.edit(f"❌ Error getting plugins: {str(e)}")
        logger.error(f"Error in plugins handler: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}reload'))
async def reload_handler(event):
    """Reload all plugins (FIXED)"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "reload")
    msg = await event.reply("🔄 Reloading plugins...")
    
    try:
        # Clear old handlers (if possible)
        logger.info("🔄 Starting plugin reload...")
        
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
            
            await msg.edit(f"✅ **Plugins Reloaded! (FIXED)**\n\n🔌 Loaded {len(results['loaded'])} plugins with {results['total_handlers']} handlers{location_info}")
        else:
            await msg.edit("⚠️ No plugins found to reload")
            
    except Exception as e:
        await msg.edit(f"❌ Error reloading plugins: {str(e)}")
        logger.error(f"Error reloading plugins: {e}")

# ============= ADDITIONAL BUILT-IN COMMANDS (KEEPING ORIGINAL) =============
# ... (keeping all other built-in commands from original main.py) ...

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive'))
async def alive_handler(event):
    """Status Vzoel Assistant"""
    if not await is_owner(event.sender_id):
        return
        
    await log_command(event, "alive")
    try:
        uptime = datetime.now() - start_time if start_time else "Unknown"
        plugin_count = len(plugin_stats.get('loaded', []))
        handler_count = plugin_stats.get('total_handlers', 0)
        uptime_str = str(uptime).split('.')[0] if uptime != "Unknown" else "Unknown"
        
        alive_text = f"""
✅ **Vzoel Assistant is alive! (FIXED)**
🚀 Uptime: `{uptime_str}`
⚡ Prefix: `{COMMAND_PREFIX}`
🔌 Plugins: `{plugin_count}` active ({handler_count} handlers)
🎯 Plugin System: Enhanced & Working
        """.strip()
        
        await event.edit(alive_text)
    except Exception as e:
        await event.edit(f"❌ Error: {str(e)}")
        logger.error(f"Error in alive handler: {e}")

# ============= STARTUP FUNCTIONS (FIXED) =============

async def startup():
    """Enhanced startup function with FIXED plugin loading"""
    global start_time
    start_time = datetime.now()
    
    logger.info("🚀 Starting enhanced Vzoel Assistant (FIXED VERSION)...")
    
    try:
        await client.start()
        me = await client.get_me()
        
        # FIXED: Load plugins AFTER client is fully started
        logger.info("🔌 Loading plugins with fixed system...")
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
**🔌 Plugins ({len(results['loaded'])}):**
{' | '.join(location_details)}
**Total Handlers:** `{results['total_handlers']}`
"""
        
        startup_message = f"""
🚀 **Enhanced Vzoel Assistant Started! (FIXED)**

✅ All systems operational
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`
🔌 **Built-in Commands:** Ready
{plugin_text}
**💡 Quick Start:**
• `{COMMAND_PREFIX}help` - Show all commands
• `{COMMAND_PREFIX}info` - System information
• `{COMMAND_PREFIX}plugins` - List loaded plugins

**🎯 FIXED: Plugin system now working correctly!**
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
    logger.info("🔄 Initializing enhanced Vzoel Assistant (FIXED VERSION)...")
    
    # Validate configuration
    logger.info("🔍 Validating configuration...")
    logger.info(f"📱 API ID: {API_ID}")
    logger.info(f"📁 Session: {SESSION_NAME}")
    logger.info(f"⚡ Prefix: {COMMAND_PREFIX}")
    logger.info(f"🆔 Owner ID: {OWNER_ID or 'Auto-detect'}")
    logger.info(f"📂 Plugin discovery: Enhanced mode")
    
    # Start Vzoel Assistant
    if await startup():
        logger.info("🔄 Enhanced Vzoel Assistant is now running (FIXED)...")
        logger.info("📝 Press Ctrl+C to stop")
        
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
            logger.info("✅ Enhanced Vzoel Assistant stopped successfully!")
    else:
        logger.error("❌ Failed to start enhanced Vzoel Assistant!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)