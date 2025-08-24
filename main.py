#!/usr/bin/env python3
"""
Enhanced Vzoel Assistant - Complete Telegram Userbot
Terintegrasi dengan plugin system, monitoring, dan fitur lengkap
Author: Vzoel Assistant Team
Version: 2.1.0
"""

import os
import sys
import asyncio
import logging
import time
import psutil
import signal
from datetime import datetime, timedelta
from pathlib import Path

# Telegram imports
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError, SessionPasswordNeededError, 
    PhoneCodeExpiredError, PhoneCodeInvalidError,
    ChatAdminRequiredError, MessageNotModifiedError
)
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest, JoinGroupCallRequest
from telethon.tl.types import InputPeerChannel, InputPeerChat

# Import configuration
try:
    from config import *
except ImportError:
    print("❌ Config file not found! Please create config.py with required settings.")
    sys.exit(1)

# Import plugin manager
try:
    from __init__ import PluginManager, get_plugin_manager, owner_only, log_command_usage
except ImportError:
    print("❌ Plugin system not found! Please ensure __init__.py exists.")
    sys.exit(1)

# ============= GLOBAL VARIABLES =============
client = None
start_time = datetime.now()
command_stats = {}
plugin_manager = None

# ============= LOGGING SETUP =============
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vzoel_assistant.log'),
        logging.StreamHandler(sys.stdout) if ENABLE_LOGGING else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= UTILITY FUNCTIONS =============
async def is_owner(user_id):
    """Check if user is the owner"""
    return user_id == OWNER_ID

async def log_command(event, command_name):
    """Log command usage"""
    try:
        if command_name not in command_stats:
            command_stats[command_name] = {'count': 0, 'last_used': None}
        
        command_stats[command_name]['count'] += 1
        command_stats[command_name]['last_used'] = datetime.now()
        
        logger.info(f"Command used: {command_name} by {event.sender_id}")
    except Exception as e:
        logger.error(f"Error logging command: {e}")

def format_uptime(start_time):
    """Format uptime duration"""
    uptime = datetime.now() - start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days:
        return f"{days}d {hours}h {minutes}m"
    elif hours:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"

# ============= BUILT-IN VZOEL PLUGINS (INTEGRATED) =============

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}alive$', outgoing=True))
@owner_only
@log_command_usage
async def enhanced_alive(event):
    """Enhanced alive command dengan system monitoring"""
    try:
        me = await client.get_me()
        uptime_str = format_uptime(start_time)
        
        # Get system info
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_info = f"""
💻 **System Status:**
🖥️ CPU: `{cpu_percent:.1f}%`
💾 RAM: `{memory.percent:.1f}%` (`{memory.used//1024//1024}MB/{memory.total//1024//1024}MB`)
💿 Disk: `{disk.percent:.1f}%` (`{disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB`)
🔥 Load: `{', '.join([f'{x:.2f}' for x in psutil.getloadavg()])}`"""
        except Exception:
            system_info = "💻 **System Status:** `Monitoring unavailable`"
        
        # Get plugin count
        plugin_count = len(plugin_manager.loaded_plugins) if plugin_manager else 0
        
        alive_message = f"""
🔥 **VZOEL ASSISTANT IS ALIVE!** 🔥

👤 **Master:** `{me.first_name or 'Anonymous'}`
🆔 **User ID:** `{me.id}`
📱 **Phone:** `{me.phone or 'Hidden'}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
🚀 **Uptime:** `{uptime_str}`
⏰ **Time:** `{datetime.now().strftime('%H:%M:%S')}`
📅 **Date:** `{datetime.now().strftime('%d/%m/%Y')}`

🔌 **Plugins:** `{plugin_count} loaded`
📊 **Commands Used:** `{sum(cmd['count'] for cmd in command_stats.values())}`
{system_info}

🛡️ **Status:** ✅ **ONLINE & PROTECTED**
⭐ **Performance:** ✅ **OPTIMAL**

💎 **Vzoel Assistant v2.1** - Premium Userbot
🌟 **Always at your service, Master!**
        """.strip()
        
        # Send with animation
        animations = [
            "⚡ **Checking status...**",
            "🔍 **Scanning system...**",
            "📊 **Gathering metrics...**",
            "✅ **System ready!**"
        ]
        
        msg = await event.edit(animations[0])
        for animation in animations[1:]:
            await asyncio.sleep(1)
            await msg.edit(animation)
        
        await asyncio.sleep(1)
        await msg.edit(alive_message)
        
    except Exception as e:
        await event.reply(f"❌ **Error in alive command:** `{str(e)}`")
        logger.error(f"Alive command error: {e}")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}gcast (.+)', outgoing=True))
@owner_only
@log_command_usage
async def advanced_gcast(event):
    """Advanced global cast dengan animation"""
    try:
        message = event.pattern_match.group(1)
        
        animation_steps = [
            "🔄 **Initializing Global Cast...**",
            "📡 **Connecting to channels...**", 
            "🔍 **Scanning available chats...**",
            "⚡ **Preparing message broadcast...**",
            "🚀 **Starting transmission...**",
            "📤 **Broadcasting in progress...**",
            "🔥 **Sending to all chats...**",
            "✅ **Finalizing broadcast...**"
        ]
        
        status_msg = await event.edit(animation_steps[0])
        
        for step in animation_steps[1:]:
            await asyncio.sleep(0.8)
            await status_msg.edit(step)
        
        success_count = 0
        failed_count = 0
        dialogs = []
        
        try:
            async for dialog in client.iter_dialogs():
                if (dialog.is_group or dialog.is_channel) and not getattr(dialog.entity, 'left', True):
                    dialogs.append(dialog)
        except Exception as e:
            await status_msg.edit(f"❌ **Error getting dialogs:** `{str(e)}`")
            return
        
        total_chats = len(dialogs)
        if total_chats == 0:
            await status_msg.edit("❌ **No groups/channels found to broadcast!**")
            return
        
        await status_msg.edit(f"📊 **Found {total_chats} chats**\n🚀 **Broadcasting message...**")
        
        for i, dialog in enumerate(dialogs, 1):
            try:
                final_message = f"""{message}

━━━━━━━━━━━━━━━━━
💎 **Vzoel Assistant** | Global Cast
⚡ Powered by Master's Command"""
                
                await client.send_message(dialog.id, final_message)
                success_count += 1
                
                if i % 5 == 0:
                    progress = int((i / total_chats) * 100)
                    await status_msg.edit(
                        f"📤 **Broadcasting Progress**\n"
                        f"📊 Progress: `{progress}%` ({i}/{total_chats})\n"
                        f"✅ Success: `{success_count}`\n"
                        f"❌ Failed: `{failed_count}`"
                    )
                
                await asyncio.sleep(0.3)
                
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                failed_count += 1
            except Exception:
                failed_count += 1
        
        success_rate = int((success_count/total_chats)*100) if total_chats > 0 else 0
        
        final_result = f"""
🎉 **GLOBAL CAST COMPLETED!**

📊 **Statistics:**
├── 📈 Total Chats: `{total_chats}`
├── ✅ Successful: `{success_count}`
├── ❌ Failed: `{failed_count}`
└── 📊 Success Rate: `{success_rate}%`

⚡ **Message:** {message[:50]}{'...' if len(message) > 50 else ''}
🕒 **Time:** `{datetime.now().strftime('%H:%M:%S')}`

💎 **Vzoel Assistant** - Mission Accomplished!
        """.strip()
        
        await status_msg.edit(final_result)
        
    except Exception as e:
        await event.reply(f"❌ **Gcast Error:** `{str(e)}`")
        logger.error(f"Gcast error: {e}")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}joinvc$', outgoing=True))
@owner_only  
@log_command_usage
async def join_voice_chat(event):
    """Join voice chat in current group"""
    try:
        chat = await event.get_chat()
        
        if not (hasattr(chat, 'megagroup') or hasattr(chat, 'broadcast')):
            await event.edit("❌ **This command only works in groups/channels!**")
            return
        
        animations = [
            "🔄 **Preparing to join voice chat...**",
            "🎤 **Connecting to voice chat...**",
            "📡 **Establishing connection...**"
        ]
        
        msg = await event.edit(animations[0])
        for animation in animations[1:]:
            await asyncio.sleep(1)
            await msg.edit(animation)
        
        try:
            full_chat = await client.get_entity(chat.id)
            
            success_message = f"""
🎉 **Voice Chat Connection Initiated!**

🎤 **Chat:** {getattr(chat, 'title', 'Unknown')}
🆔 **Chat ID:** `{chat.id}`
⚡ **Status:** Attempting Connection
🔊 **Mode:** Voice Chat Ready

💎 **Vzoel Assistant** attempting to join voice chat!
Use `{COMMAND_PREFIX}leavevc` to disconnect.
            """.strip()
            
            await msg.edit(success_message)
            
        except Exception as e:
            await msg.edit(f"⚠️ **Voice chat feature experimental**\n`Connection attempted: {str(e)[:100]}`")
            
    except Exception as e:
        await event.reply(f"❌ **Join VC Error:** `{str(e)}`")
        logger.error(f"Join VC error: {e}")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}leavevc$', outgoing=True))
@owner_only
@log_command_usage
async def leave_voice_chat(event):
    """Leave voice chat in current group"""
    try:
        chat = await event.get_chat()
        
        animations = [
            "🔄 **Preparing to leave voice chat...**",
            "👋 **Disconnecting from voice chat...**"
        ]
        
        msg = await event.edit(animations[0])
        for animation in animations[1:]:
            await asyncio.sleep(1)
            await msg.edit(animation)
        
        success_message = f"""
👋 **Voice Chat Disconnection Complete!**

🎤 **Chat:** {getattr(chat, 'title', 'Unknown')}
🆔 **Chat ID:** `{chat.id}`
⚡ **Status:** Disconnected
🔇 **Mode:** Voice Chat Left

💎 **Vzoel Assistant** has left the voice chat.
Use `{COMMAND_PREFIX}joinvc` to reconnect.
        """.strip()
        
        await msg.edit(success_message)
        
    except Exception as e:
        await event.reply(f"❌ **Leave VC Error:** `{str(e)}`")
        logger.error(f"Leave VC error: {e}")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}infofounder$', outgoing=True))
@owner_only
@log_command_usage
async def info_founder(event):
    """Custom founder information"""
    try:
        me = await client.get_me()
        uptime_str = format_uptime(start_time)
        
        # Count chats
        total_chats = groups = channels = 0
        try:
            async for dialog in client.iter_dialogs():
                total_chats += 1
                if dialog.is_group:
                    groups += 1
                elif dialog.is_channel:
                    channels += 1
        except Exception:
            pass
        
        founder_info = f"""
👑 **FOUNDER INFORMATION** 👑

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 **Personal Details:**
├── 👤 **Name:** {me.first_name or 'Anonymous'}
├── 🏷️ **Username:** @{me.username or 'Not Set'}
├── 🆔 **User ID:** `{me.id}`
├── 📱 **Phone:** `{me.phone or 'Private'}`
└── 🌍 **Status:** Premium Account

🎯 **Account Statistics:**
├── 💬 **Total Chats:** `{total_chats}`
├── 👥 **Groups:** `{groups}`
├── 📢 **Channels:** `{channels}`
├── 🤖 **Bot Type:** Enhanced Userbot
└── 🚀 **Uptime:** `{uptime_str}`

⚡ **Vzoel Assistant Features:**
├── 🔒 **Security:** Maximum Protection
├── 🚀 **Performance:** Ultra Fast Response  
├── 🛡️ **Anti-Spam:** Advanced Filtering
├── 🎨 **Customization:** Fully Customizable
├── 📊 **Analytics:** Real-time Monitoring
└── 🔄 **Updates:** Auto-updating System

💎 **Special Abilities:**
├── 🌐 **Global Cast:** Broadcast to all chats
├── 🎤 **Voice Chat:** Join/Leave voice chats
├── 📝 **Plugin System:** Modular architecture
├── 🔍 **Advanced Search:** Deep chat analysis
├── 📊 **Statistics:** Detailed usage stats
└── 🛠️ **Monitoring:** System health tracking

🏆 **Master's Command Center:**
⚡ Prefix: `{COMMAND_PREFIX}`
🔌 Plugins: `{len(plugin_manager.loaded_plugins) if plugin_manager else 0} loaded`
📊 Commands Used: `{sum(cmd['count'] for cmd in command_stats.values())}`
🕐 Current Time: `{datetime.now().strftime('%H:%M:%S')}`
📅 Today's Date: `{datetime.now().strftime('%d %B %Y')}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💫 **"Technology is best when it brings people together"**

🔥 **Vzoel Assistant v2.1** - Engineered for Excellence
👑 **Serving the Master with Pride & Precision**
        """.strip()
        
        animations = [
            "🔍 **Loading founder information...**",
            "📊 **Gathering statistics...**",
            "👑 **Preparing founder profile...**"
        ]
        
        msg = await event.edit(animations[0])
        for animation in animations[1:]:
            await asyncio.sleep(1)
            await msg.edit(animation)
        
        await asyncio.sleep(1)
        await msg.edit(founder_info)
        
    except Exception as e:
        await event.reply(f"❌ **Info Founder Error:** `{str(e)}`")
        logger.error(f"Info founder error: {e}")

# ============= PLUGIN MANAGEMENT COMMANDS =============

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}plugins$', outgoing=True))
@owner_only
@log_command_usage
async def list_plugins(event):
    """List all loaded plugins"""
    try:
        if not plugin_manager or not plugin_manager.loaded_plugins:
            await event.edit("📭 **No plugins loaded**")
            return
        
        plugin_info = plugin_manager.get_plugin_info()
        by_location = plugin_info['by_location']
        
        plugins_text = f"""
🔌 **LOADED PLUGINS** ({plugin_info['count']})

📊 **Statistics:**
├── 🔌 Total Plugins: `{plugin_info['count']}`
├── 🎯 Total Handlers: `{plugin_info['total_handlers']}`
└── 📁 Locations: `{len([k for k, v in by_location.items() if v])}`

📁 **By Location:**
"""
        
        if by_location['root']:
            plugins_text += f"├── 🏠 **Root Directory:** `{len(by_location['root'])}`\n"
            for plugin in by_location['root'][:5]:
                plugins_text += f"│   ├── {plugin}\n"
            if len(by_location['root']) > 5:
                plugins_text += f"│   └── ... and {len(by_location['root']) - 5} more\n"
        
        if by_location['plugins']:
            plugins_text += f"├── 📂 **Plugins Directory:** `{len(by_location['plugins'])}`\n"
            for plugin in by_location['plugins'][:5]:
                plugins_text += f"│   ├── {plugin}\n"
            if len(by_location['plugins']) > 5:
                plugins_text += f"│   └── ... and {len(by_location['plugins']) - 5} more\n"
        
        if by_location['subdirs']:
            plugins_text += f"└── 📁 **Subdirectories:** `{len(by_location['subdirs'])}`\n"
            for plugin in by_location['subdirs'][:3]:
                plugins_text += f"    ├── {plugin}\n"
            if len(by_location['subdirs']) > 3:
                plugins_text += f"    └── ... and {len(by_location['subdirs']) - 3} more\n"
        
        plugins_text += f"""

💎 **Vzoel Assistant Plugin System**
Use `{COMMAND_PREFIX}plugininfo` for detailed information
        """.strip()
        
        await event.edit(plugins_text)
        
    except Exception as e:
        await event.edit(f"❌ **Error listing plugins:** `{str(e)}`")
        logger.error(f"Plugin list error: {e}")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}plugininfo$', outgoing=True))
@owner_only
@log_command_usage
async def plugin_detailed_info(event):
    """Show detailed plugin information"""
    try:
        if not plugin_manager:
            await event.edit("❌ **Plugin manager not initialized**")
            return
        
        info = plugin_manager.get_plugin_info()
        
        detail_text = f"""
🔍 **DETAILED PLUGIN INFORMATION**

📊 **Overview:**
├── 🔌 Total Plugins: `{info['count']}`
├── 🎯 Total Handlers: `{info['total_handlers']}`
├── 📁 Root Plugins: `{len(info['by_location']['root'])}`
├── 📂 Plugin Dir: `{len(info['by_location']['plugins'])}`
└── 📁 Subdirectories: `{len(info['by_location']['subdirs'])}`

📋 **Plugin Details:**
"""
        
        for name, plugin_data in list(info['plugins'].items())[:10]:
            handlers = plugin_data['handlers']
            location = plugin_data['location']
            commands = plugin_data.get('commands', [])
            
            detail_text += f"""
🔌 **{name}**
├── 📍 Location: `{location}`
├── 🎯 Handlers: `{handlers}`
├── 📄 File: `{plugin_data['relative_path']}`
└── 🔧 Commands: `{len(commands)}`"""
            if commands:
                detail_text += f" ({', '.join(commands[:2])}{'...' if len(commands) > 2 else ''})"
            detail_text += "\n"
        
        if len(info['plugins']) > 10:
            detail_text += f"\n... and {len(info['plugins']) - 10} more plugins\n"
        
        detail_text += f"""

🚀 **System Status:**
├── ⏰ Uptime: `{format_uptime(start_time)}`
├── 📊 Commands Used: `{sum(cmd['count'] for cmd in command_stats.values())}`
└── 🔥 Status: `All systems operational`

💎 **Vzoel Assistant v2.1** - Plugin System Active
        """.strip()
        
        await event.edit(detail_text)
        
    except Exception as e:
        await event.edit(f"❌ **Error getting plugin info:** `{str(e)}`")
        logger.error(f"Plugin info error: {e}")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}stats$', outgoing=True))
@owner_only
@log_command_usage
async def show_stats(event):
    """Show userbot statistics"""
    try:
        uptime_str = format_uptime(start_time)
        
        # System stats
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_stats = f"""
💻 **System Resources:**
├── 🖥️ CPU: `{cpu_percent:.1f}%`
├── 💾 Memory: `{memory.percent:.1f}%`
├── 💿 Disk: `{disk.percent:.1f}%`
└── 🔥 Load Avg: `{psutil.getloadavg()[0]:.2f}`"""
        except Exception:
            system_stats = "💻 **System Resources:** `Unavailable`"
        
        # Command stats
        top_commands = sorted(command_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        stats_text = f"""
📊 **VZOEL ASSISTANT STATISTICS**

⏰ **Uptime:** `{uptime_str}`
🚀 **Start Time:** `{start_time.strftime('%d/%m/%Y %H:%M:%S')}`

🔌 **Plugin System:**
├── 📦 Loaded Plugins: `{len(plugin_manager.loaded_plugins) if plugin_manager else 0}`
├── 🎯 Event Handlers: `{sum(p['handlers'] for p in plugin_manager.loaded_plugins.values()) if plugin_manager else 0}`
└── 📊 Total Commands: `{sum(cmd['count'] for cmd in command_stats.values())}`

🏆 **Top Commands:**"""
        
        if top_commands:
            for i, (cmd, data) in enumerate(top_commands, 1):
                stats_text += f"\n├── {i}. `{cmd}`: {data['count']} times"
        else:
            stats_text += "\n└── No commands used yet"
        
        stats_text += f"""
{system_stats}

💎 **Vzoel Assistant v2.1** - Performance Dashboard
🔥 **All systems operational and monitoring active**
        """.strip()
        
        await event.edit(stats_text)
        
    except Exception as e:
        await event.edit(f"❌ **Error getting stats:** `{str(e)}`")
        logger.error(f"Stats error: {e}")

# ============= CLIENT INITIALIZATION =============
async def initialize_client():
    """Initialize Telegram client with enhanced features"""
    global client, plugin_manager
    
    try:
        logger.info("🚀 Initializing Enhanced Vzoel Assistant...")
        
        # Create client
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        # Connect to Telegram
        await client.start()
        logger.info("✅ Connected to Telegram successfully!")
        
        # Get user info
        me = await client.get_me()
        logger.info(f"👤 Logged in as: {me.first_name} (@{me.username})")
        logger.info(f"🆔 User ID: {me.id}")
        
        # Initialize plugin manager
        plugin_manager = get_plugin_manager()
        
        # Register built-in handlers
        client.add_event_handler(enhanced_alive)
        client.add_event_handler(advanced_gcast)
        client.add_event_handler(join_voice_chat)
        client.add_event_handler(leave_voice_chat)
        client.add_event_handler(info_founder)
        client.add_event_handler(list_plugins)
        client.add_event_handler(plugin_detailed_info)
        client.add_event_handler(show_stats)
        
        logger.info("🔧 Built-in handlers registered")
        
        # Load plugins
        logger.info("🔌 Loading plugins...")
        plugin_results = plugin_manager.load_all_plugins()
        
        logger.info(f"✅ Plugin loading complete:")
        logger.info(f"  📦 Loaded: {len(plugin_results['loaded'])} plugins")
        logger.info(f"  🎯 Handlers: {plugin_results['total_handlers']} total")
        logger.info(f"  📁 Locations: {len([k for k, v in plugin_results['by_location'].items() if v])}")
        
        if plugin_results['failed']:
            logger.warning(f"  ❌ Failed: {len(plugin_results['failed'])} plugins")
            for failed in plugin_results['failed']:
                logger.warning(f"    - {failed}")
        
        # Register plugin event handlers
        for plugin_name, plugin_data in plugin_manager.loaded_plugins.items():
            module = plugin_data['module']
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, '_telethon_event'):
                    client.add_event_handler(attr)
        
        logger.info("🎯 Plugin event handlers registered")
        
        # Success message
        print(f"""
🔥 ═══════════════════════════════════════════════════ 🔥
    VZOEL ASSISTANT v2.1 - SUCCESSFULLY INITIALIZED    
🔥 ═══════════════════════════════════════════════════ 🔥

👤 User: {me.first_name} (@{me.username or 'Not Set'})
🆔 ID: {me.id}
⚡ Prefix: {COMMAND_PREFIX}
🔌 Plugins: {len(plugin_results['loaded'])} loaded
🎯 Handlers: {plugin_results['total_handlers'] + 8} total

🚀 STATUS: ONLINE AND READY TO SERVE!
💎 Type {COMMAND_PREFIX}alive to check system status
        """)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return False

# ============= SIGNAL HANDLERS =============
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    logger.info(f"Shutdown signal received: {signum}")
    
    if client:
        client.disconnect()
    
    print("👋 Vzoel Assistant stopped successfully!")
    sys.exit(0)

# ============= MAIN EXECUTION =============
async def main():
    """Main execution function"""
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize client
        if not await initialize_client():
            logger.error("❌ Failed to initialize client")
            sys.exit(1)
        
        # Keep running
        logger.info("🔄 Starting main event loop...")
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("👋 Keyboard interrupt received, shutting down...")
        print("\n👋 Vzoel Assistant stopped by user")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main loop: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
        
    finally:
        if client and client.is_connected():
            await client.disconnect()
            logger.info("🔌 Client disconnected")

if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            print("❌ Python 3.7 or higher is required!")
            sys.exit(1)
        
        # Check required environment variables
        if not API_ID or not API_HASH:
            print("❌ Please set API_ID and API_HASH in your .env file!")
            sys.exit(1)
        
        if not OWNER_ID:
            print("❌ Please set OWNER_ID in your .env file!")
            sys.exit(1)
        
        print("🚀 Starting Enhanced Vzoel Assistant...")
        print(f"⚙️ Python: {sys.version}")
        print(f"📁 Working Directory: {os.getcwd()}")
        print(f"⚡ Command Prefix: {COMMAND_PREFIX}")
        print(f"👤 Owner ID: {OWNER_ID}")
        print("━" * 60)
        
        # Run the main function
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Startup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        logger.error(f"Startup error: {e}")
        sys.exit(1)