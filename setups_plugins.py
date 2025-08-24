# ===== FILE: setups_plugins.py =====
#!/usr/bin/env python3
"""
Setup & System Plugins for Vzoel Assistant
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
import asyncio
import psutil
import os

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}restart$', outgoing=True))
@owner_only
@log_command_usage
async def restart_bot(event):
    """Restart the userbot"""
    await event.edit("🔄 **Restarting Vzoel Assistant...**")
    await asyncio.sleep(2)
    os.execl(sys.executable, sys.executable, *sys.argv)

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}shutdown$', outgoing=True))
@owner_only
@log_command_usage
async def shutdown_bot(event):
    """Shutdown the userbot"""
    await event.edit("⚡ **Shutting down Vzoel Assistant...**")
    await asyncio.sleep(2)
    exit()

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}system$', outgoing=True))
@owner_only
@log_command_usage
async def system_info(event):
    """Show detailed system information"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_text = f"""
🖥️ **SYSTEM INFORMATION**

**CPU Usage:** `{cpu}%`
**Memory:** `{memory.percent}%` ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)
**Disk:** `{disk.percent}%` ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)
**Load Average:** `{psutil.getloadavg()[0]:.2f}`

💎 **Vzoel Assistant System Monitor**
        """.strip()
        
        await event.edit(system_text)
    except Exception as e:
        await event.reply(f"❌ **System Error:** `{str(e)}`")

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}ping$', outgoing=True))
@owner_only
@log_command_usage
async def ping_command(event):
    """Check bot response time"""
    start_time = asyncio.get_event_loop().time()
    msg = await event.edit("🏓 **Pinging...**")
    end_time = asyncio.get_event_loop().time()
    ping_time = (end_time - start_time) * 1000
    
    await msg.edit(f"🏓 **Pong!**\n⚡ **Response Time:** `{ping_time:.2f}ms`")

# ===== FILE: vzoel_plugins.py =====
#!/usr/bin/env python3
"""
Main Vzoel Plugins Collection
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
import asyncio
from datetime import datetime

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}test$', outgoing=True))
@owner_only
@log_command_usage
async def test_command(event):
    """Test command to check plugin functionality"""
    animations = [
        "🔍 **Testing plugin system...**",
        "⚡ **Running diagnostics...**",
        "✅ **Plugin system operational!**"
    ]
    
    msg = await event.edit(animations[0])
    for animation in animations[1:]:
        await asyncio.sleep(1)
        await msg.edit(animation)

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}time$', outgoing=True))
@owner_only
@log_command_usage
async def current_time(event):
    """Show current date and time"""
    now = datetime.now()
    time_text = f"""
⏰ **CURRENT TIME**

📅 **Date:** `{now.strftime('%A, %d %B %Y')}`
🕐 **Time:** `{now.strftime('%H:%M:%S')}`
🌍 **Timezone:** `UTC`

💎 **Vzoel Assistant Time Service**
    """.strip()
    
    await event.edit(time_text)

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}echo (.+)', outgoing=True))
@owner_only
@log_command_usage
async def echo_command(event):
    """Echo back the message"""
    message = event.pattern_match.group(1)
    
    echo_text = f"""
🔊 **ECHO COMMAND**

**Original:** `{message}`
**Echoed:** {message}

💎 **Message successfully echoed!**
    """.strip()
    
    await event.edit(echo_text)

@events.register(events.NewMessage(pattern=rf'^{COMMAND_PREFIX}help$', outgoing=True))
@owner_only
@log_command_usage
async def help_command(event):
    """Show available commands"""
    help_text = f"""
🔥 **VZOEL ASSISTANT COMMANDS**

**🔧 System Commands:**
├── `{COMMAND_PREFIX}alive` - Check bot status
├── `{COMMAND_PREFIX}restart` - Restart bot
├── `{COMMAND_PREFIX}shutdown` - Shutdown bot
├── `{COMMAND_PREFIX}system` - System information
└── `{COMMAND_PREFIX}ping` - Check response time

**📊 Plugin Commands:**
├── `{COMMAND_PREFIX}plugins` - List loaded plugins
├── `{COMMAND_PREFIX}plugininfo` - Plugin details
└── `{COMMAND_PREFIX}stats` - Usage statistics

**🎯 Utility Commands:**
├── `{COMMAND_PREFIX}test` - Test plugin system
├── `{COMMAND_PREFIX}time` - Current time
├── `{COMMAND_PREFIX}echo <text>` - Echo message
├── `{COMMAND_PREFIX}help` - This help menu
└── `{COMMAND_PREFIX}gcast <text>` - Global broadcast

**💎 More commands coming soon!**
    """.strip()
    
    await event.edit(help_text)
