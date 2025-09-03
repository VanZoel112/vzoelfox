#!/usr/bin/env python3
"""
Vzoel Assistant Client with Dynamic Plugin System (Fixed)
Compatible version with proper Telethon syntax
Author: Vzoel Fox's (Ltpn)
"""

import asyncio
import logging
import time
import random
import re
import os
import sys
import importlib
import inspect
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")
OWNER_ID = int(os.getenv("OWNER_ID", "0")) if os.getenv("OWNER_ID") else None
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
PLUGINS_DIR = os.getenv("PLUGINS_DIR", "plugins")

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
loaded_plugins = {}

# ============= PLUGIN SYSTEM =============

class PluginManager:
    """Enhanced Plugin Manager for dynamic loading"""
    
    def __init__(self, client, plugins_dir):
        self.client = client
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins = {}
        
    async def load_plugins(self):
        """Load all plugins from plugins directory"""
        if not self.plugins_dir.exists():
            logger.info(f"📁 Creating plugins directory: {self.plugins_dir}")
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            await self.create_sample_plugins()
            
        logger.info(f"🔍 Scanning plugins directory: {self.plugins_dir}")
        
        # Add plugins directory to Python path
        if str(self.plugins_dir.parent) not in sys.path:
            sys.path.insert(0, str(self.plugins_dir.parent))
            
        loaded_count = 0
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private files
                
            try:
                await self.load_plugin(plugin_file)
                loaded_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to load plugin {plugin_file.name}: {e}")
                
        logger.info(f"✅ Successfully loaded {loaded_count} plugins")
        return loaded_count
        
    async def load_plugin(self, plugin_file):
        """Load individual plugin file"""
        plugin_name = plugin_file.stem
        module_path = f"{self.plugins_dir.name}.{plugin_name}"
        
        try:
            # Import or reload module
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)
                
            # Initialize plugin if it has setup function
            if hasattr(module, 'setup'):
                await module.setup(self.client)
                logger.info(f"✅ Plugin '{plugin_name}' loaded and initialized")
            else:
                logger.info(f"✅ Plugin '{plugin_name}' loaded")
                
            # Store plugin info
            self.loaded_plugins[plugin_name] = {
                'module': module,
                'file': plugin_file,
                'loaded_at': datetime.now(),
                'commands': self.get_plugin_commands(module)
            }
            
        except Exception as e:
            logger.error(f"❌ Error loading plugin {plugin_name}: {e}")
            raise
            
    def get_plugin_commands(self, module):
        """Extract commands from plugin module"""
        commands = []
        
        for name, obj in inspect.getmembers(module):
            if hasattr(obj, '__telethon_handler__'):
                # Get pattern from event handler
                if hasattr(obj, 'pattern'):
                    commands.append(obj.pattern)
                    
        return commands
        
    async def reload_plugin(self, plugin_name):
        """Reload specific plugin"""
        if plugin_name not in self.loaded_plugins:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")
            
        plugin_file = self.loaded_plugins[plugin_name]['file']
        await self.load_plugin(plugin_file)
        logger.info(f"🔄 Plugin '{plugin_name}' reloaded successfully")
        
    async def unload_plugin(self, plugin_name):
        """Unload specific plugin"""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            logger.info(f"🗑️ Plugin '{plugin_name}' unloaded")
        
    async def create_sample_plugins(self):
        """Create sample plugins for demonstration"""
        
        # Sample alive plugin
        alive_plugin = '''
"""Sample Alive Plugin"""
import asyncio
from datetime import datetime
from telethon import events

start_time = datetime.now()

async def setup(client):
    """Plugin setup function"""
    
    @client.on(events.NewMessage(pattern=r\'\\.alive\'))
    async def alive_handler(event):
        """Enhanced alive command"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split('.')[0]
        
        animations = [
            "🔄 **Checking system...**",
            "⚡ **Loading components...**",
            """✅ **VZOEL ASSISTANT ALIVE!**

🚀 **Status:** Active & Running  
⏰ **Uptime:** `{}`
🔥 **Plugin System:** Enabled
⚡ **External Plugin Loaded!**""".format(uptime_str)
        ]
        
        msg = await event.edit(animations[0])
        for anim in animations[1:]:
            await asyncio.sleep(2)
            await msg.edit(anim)
'''

        # Sample ping plugin  
        ping_plugin = '''
"""Sample Ping Plugin"""
import time
from telethon import events

async def setup(client):
    """Plugin setup function"""
    
    @client.on(events.NewMessage(pattern=r\'\\.ping\'))
    async def ping_handler(event):
        """Ping command with response time"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        start = time.time()
        msg = await event.edit("🏓 **Pinging...**")
        end = time.time()
        
        ping_time = (end - start) * 1000
        
        await msg.edit("""🏓 **PONG!**

⚡ **Response:** `{:.2f}ms`
🚀 **Status:** Active
✅ **Plugin:** Loaded Externally""".format(ping_time))
'''

        # Sample gcast plugin (FIXED VERSION)
        gcast_plugin = '''
"""Sample GCast Plugin - FIXED VERSION"""
import asyncio
from telethon import events

async def setup(client):
    """Plugin setup function"""
    
    # FIXED: Proper pattern without flags parameter
    @client.on(events.NewMessage(pattern=r\'\\.gcast (.+)\'))
    async def gcast_handler(event):
        """Global broadcast command - FIXED"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
        
        # Get message from pattern match
        message_to_send = event.pattern_match.group(1).strip()
        
        if not message_to_send:
            await event.edit("❌ **Usage:** `.gcast <message>`")
            return
        
        try:
            msg = await event.edit("🔄 **Starting broadcast...**")
            
            # Get all chats
            chats = []
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    chats.append(dialog)
            
            if not chats:
                await msg.edit("❌ **No chats found for broadcast!**")
                return
            
            # Broadcast to all chats
            success = 0
            failed = 0
            
            for chat in chats:
                try:
                    await client.send_message(chat.entity, message_to_send)
                    success += 1
                except:
                    failed += 1
                
                # Rate limiting
                await asyncio.sleep(0.3)
            
            await msg.edit(f"""✅ **BROADCAST COMPLETED!**
            
📊 **Results:**
✅ **Success:** `{success}`
❌ **Failed:** `{failed}`
📈 **Total:** `{len(chats)}`

🔥 **External Plugin Working!**""")
            
        except Exception as e:
            await event.edit(f"❌ **Error:** {str(e)}")
'''

        # Sample vzl plugin
        vzl_plugin = '''
"""Sample VZL Plugin"""
import asyncio
from telethon import events

async def setup(client):
    """Plugin setup function"""
    
    @client.on(events.NewMessage(pattern=r\'\\.vzl\'))
    async def vzl_handler(event):
        """Vzoel animation command"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
        
        animations = [
            "🔥 **V**",
            "🔥 **VZ**", 
            "🔥 **VZO**",
            "🔥 **VZOE**",
            "🔥 **VZOEL**",
            "🚀 **VZOEL F**",
            "🚀 **VZOEL FO**",
            "🚀 **VZOEL FOX**",
            "⚡ **VZOEL FOX\\'S**",
            "✨ **VZOEL FOX\\'S A**",
            "🌟 **VZOEL FOX\\'S ASS**",
            """🔥 **VZOEL FOX\\'S ASSISTANT** 🔥

╔══════════════════════════════╗
   🚩 𝗩𝗭𝗢𝗘𝗟 𝗔𝗦𝗦𝗜𝗦𝗧𝗔𝗡𝗧 🚩
╚══════════════════════════════╝

⚡ **Dynamic Plugin System**
🔥 **External Plugins Working**
✨ **Created by Vzoel Fox\\'s**

⚡ **Hak milik Vzoel Fox\\'s -2025**"""
        ]
        
        msg = await event.edit(animations[0])
        for anim in animations[1:]:
            await asyncio.sleep(1.2)
            await msg.edit(anim)
'''

        # Sample info plugin
        info_plugin = '''
"""Sample Info Plugin"""
from datetime import datetime
from telethon import events

async def setup(client):
    """Plugin setup function"""
    
    @client.on(events.NewMessage(pattern=r\'\\.info\'))
    async def info_handler(event):
        """System information"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
        
        uptime = datetime.now() - datetime.now()  # This should be start_time
        uptime_str = "Active"
            
        await event.edit(f"""📊 **SYSTEM INFORMATION**

╔══════════════════════════════╗
   📊 𝗦𝗬𝗦𝗧𝗘𝗠 𝗜𝗡𝗙𝗢 📊
╚══════════════════════════════╝

👤 **Name:** {me.first_name}
🆔 **ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
⚡ **Status:** {uptime_str}
🔥 **Plugin System:** ✅ Active

⚡ **Loaded from External Plugin!**
🔥 **Vzoel Fox\\'s Assistant**""")
'''

        # Write sample plugins
        (self.plugins_dir / "alive.py").write_text(alive_plugin.strip())
        (self.plugins_dir / "ping.py").write_text(ping_plugin.strip())
        (self.plugins_dir / "gcast.py").write_text(gcast_plugin.strip())  # FIXED VERSION
        (self.plugins_dir / "vzl.py").write_text(vzl_plugin.strip())
        (self.plugins_dir / "info.py").write_text(info_plugin.strip())
        
        logger.info("📝 Sample plugins created in plugins directory")

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

# ============= CORE MANAGEMENT COMMANDS =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}plugins'))
async def plugins_handler(event):
    """Show loaded plugins"""
    if not await is_owner(event.sender_id):
        return
        
    try:
        if not plugin_manager.loaded_plugins:
            await event.edit("❌ **No plugins loaded**")
            return
            
        plugins_text = "🔌 **LOADED PLUGINS**\n\n"
        
        for i, (name, info) in enumerate(plugin_manager.loaded_plugins.items(), 1):
            loaded_at = info['loaded_at'].strftime("%H:%M:%S")
            commands_count = len(info['commands'])
            
            plugins_text += f"`{i:02d}.` **{name.upper()}**\n"
            plugins_text += f"     ⏰ Loaded: `{loaded_at}`\n"
            plugins_text += f"     📝 Commands: `{commands_count}`\n\n"
            
        plugins_text += f"📊 **Total:** `{len(plugin_manager.loaded_plugins)}` plugins loaded"
        
        await event.edit(plugins_text)
        
    except Exception as e:
        await event.edit(f"❌ **Error:** {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}reload\s+(.+)'))
async def reload_handler(event):
    """Reload specific plugin"""
    if not await is_owner(event.sender_id):
        return
        
    plugin_name = event.pattern_match.group(1).strip()
    
    try:
        msg = await event.edit(f"🔄 **Reloading plugin:** `{plugin_name}`...")
        await plugin_manager.reload_plugin(plugin_name)
        await msg.edit(f"✅ **Plugin `{plugin_name}` reloaded successfully!**")
        
    except Exception as e:
        await event.edit(f"❌ **Error reloading plugin:** {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}loadall'))
async def loadall_handler(event):
    """Reload all plugins"""
    if not await is_owner(event.sender_id):
        return
        
    try:
        msg = await event.edit("🔄 **Reloading all plugins...**")
        count = await plugin_manager.load_plugins()
        await msg.edit(f"✅ **Successfully reloaded `{count}` plugins!**")
        
    except Exception as e:
        await event.edit(f"❌ **Error loading plugins:** {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def help_handler(event):
    """Enhanced help with plugin system info"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        help_text = f"""
🆘 **VZOEL ASSISTANT HELP**

╔══════════════════════════════╗
   📚 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗟𝗜𝗦𝗧 📚
╚══════════════════════════════╝

🔧 **PLUGIN MANAGEMENT:**
• `{COMMAND_PREFIX}plugins` - Show loaded plugins
• `{COMMAND_PREFIX}reload <name>` - Reload plugin
• `{COMMAND_PREFIX}loadall` - Reload all plugins

📊 **SYSTEM:**
• `{COMMAND_PREFIX}help` - Show this help

🔌 **EXTERNAL PLUGINS:**
Place your plugins in `{PLUGINS_DIR}/` directory
Each plugin must have a `setup(client)` function

📝 **PLUGIN STRUCTURE:**
```python
async def setup(client):
    @client.on(events.NewMessage(pattern=r'\\.command'))
    async def handler(event):
        await event.edit("Response")
```

📊 **SAMPLE PLUGINS INCLUDED:**
• alive.py - System status
• ping.py - Response time
• gcast.py - Global broadcast
• vzl.py - Vzoel animation  
• info.py - System info

⚡ **Plugin Count:** `{len(plugin_manager.loaded_plugins) if 'plugin_manager' in globals() else 0}`
🔥 **Created by Vzoel Fox's (LTPN)**
        """.strip()
        
        await event.edit(help_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")

# ============= STARTUP MESSAGE =============

async def send_startup_message():
    """Send startup notification with plugin info"""
    try:
        me = await client.get_me()
        plugin_count = len(plugin_manager.loaded_plugins)
        
        startup_msg = f"""
🚀 **VZOEL ASSISTANT STARTED!**

╔══════════════════════════════╗
   🔥 𝗘𝗡𝗛𝗔𝗡𝗖𝗘𝗗 𝗦𝗬𝗦𝗧𝗘𝗠 🔥
╚══════════════════════════════╝

✅ **Core System:** Online
👤 **User:** {me.first_name}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
🔌 **Plugins:** `{plugin_count}` loaded
⏰ **Started:** `{start_time.strftime("%Y-%m-%d %H:%M:%S")}`

🔥 **Features:**
• Dynamic Plugin System ✅
• External Plugin Loading ✅
• Plugin Management Commands ✅
• Hot-Reload Support ✅
• Sample Plugins Included ✅

💡 **Quick Start:**
• `{COMMAND_PREFIX}help` - Show commands
• `{COMMAND_PREFIX}plugins` - Show plugins
• `{COMMAND_PREFIX}loadall` - Reload plugins

🧪 **Try Sample Commands:**
• `{COMMAND_PREFIX}alive` - System status
• `{COMMAND_PREFIX}ping` - Response time
• `{COMMAND_PREFIX}gcast Hello!` - Broadcast
• `{COMMAND_PREFIX}vzl` - Animation
• `{COMMAND_PREFIX}info` - System info

🔌 **Plugin Directory:** `{PLUGINS_DIR}/`
🔥 **Enhanced by Vzoel Fox's (LTPN)**
        """.strip()
        
        await client.send_message('me', startup_msg)
        logger.info("✅ Enhanced startup message sent")
        
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")

# ============= MAIN FUNCTION =============

async def main():
    """Main function with plugin system initialization"""
    global plugin_manager
    
    logger.info("🚀 Starting Enhanced Vzoel Assistant...")
    
    try:
        await client.start()
        logger.info("✅ Client connected successfully")
        
        # Initialize plugin manager
        plugin_manager = PluginManager(client, PLUGINS_DIR)
        
        # Load all plugins
        logger.info("🔌 Initializing plugin system...")
        plugin_count = await plugin_manager.load_plugins()
        
        # Send startup message
        await send_startup_message()
        
        logger.info(f"🔄 Enhanced Vzoel Assistant running with {plugin_count} plugins...")
        logger.info("📝 Press Ctrl+C to stop")
        
        # Keep running
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("👋 Enhanced Vzoel Assistant stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        logger.info("🔄 Disconnecting...")
        await client.disconnect()
        logger.info("✅ Enhanced Vzoel Assistant stopped!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        exit(1)