#!/usr/bin/env python3
"""
Toggle Bot Integration Plugin for VzoelFox Userbot
Fitur: Integration with Node.js toggle bot untuk remote control
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0 - Toggle Bot Integration
"""

import asyncio
import json
import os
import sys
import subprocess
import requests
from datetime import datetime
from telethon import events

# Premium emoji helper
sys.path.append('utils')
try:
    from premium_emoji_helper import get_emoji, safe_send_premium, safe_edit_premium, get_vzoel_signature
except ImportError:
    def get_emoji(emoji_type): return '🤩'
    async def safe_send_premium(event, text, **kwargs): await event.reply(text, **kwargs)
    async def safe_edit_premium(message, text, **kwargs): await message.edit(text, **kwargs)
    def get_vzoel_signature(): return '🤩 VzoelFox Premium System'

# Plugin Info
PLUGIN_INFO = {
    "name": "toggle_bot_integration",
    "version": "1.0.0",
    "description": "Integration dengan Node.js toggle bot untuk remote control userbot",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".togglebot", ".togglebot status", ".togglebot start", ".togglebot stop", ".togglebot install"],
    "features": ["remote control integration", "toggle bot management", "automatic setup", "status monitoring"]
}

# Configuration
TOGGLE_BOT_SCRIPT = "vzoel_toggle_bot.js"
TOGGLE_STARTUP_SCRIPT = "start_toggle_bot.sh"
TOGGLE_CONFIG_FILE = "toggle_bot_config.json"
BOT_TOKEN = "8380293227:AAHYbOVl5Mou_yJmqKO890lwNqvDyLMM_lE"

def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_toggle_bot_running():
    """Check if toggle bot is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'node.*vzoel_toggle_bot.js'], capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def get_toggle_bot_pid():
    """Get toggle bot process ID"""
    try:
        result = subprocess.run(['pgrep', '-f', 'node.*vzoel_toggle_bot.js'], capture_output=True, text=True)
        pid = result.stdout.strip()
        return int(pid) if pid else None
    except:
        return None

async def start_toggle_bot():
    """Start the toggle bot"""
    try:
        # Check if startup script exists
        if not os.path.exists(TOGGLE_STARTUP_SCRIPT):
            return False, "Startup script not found"
        
        # Run startup script
        process = await asyncio.create_subprocess_exec(
            'bash', TOGGLE_STARTUP_SCRIPT, 'start',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True, stdout.decode()
        else:
            return False, stderr.decode() or stdout.decode()
    except Exception as e:
        return False, str(e)

async def stop_toggle_bot():
    """Stop the toggle bot"""
    try:
        if not os.path.exists(TOGGLE_STARTUP_SCRIPT):
            # Try direct kill
            result = subprocess.run(['pkill', '-f', 'node.*vzoel_toggle_bot.js'], capture_output=True)
            return result.returncode == 0, "Direct kill attempted"
        
        # Use startup script
        process = await asyncio.create_subprocess_exec(
            'bash', TOGGLE_STARTUP_SCRIPT, 'stop',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return process.returncode == 0, stdout.decode() or stderr.decode()
    except Exception as e:
        return False, str(e)

async def get_toggle_bot_status():
    """Get toggle bot detailed status"""
    try:
        is_running = check_toggle_bot_running()
        pid = get_toggle_bot_pid()
        node_installed = check_node_installed()
        
        status = {
            'running': is_running,
            'pid': pid,
            'node_installed': node_installed,
            'bot_script_exists': os.path.exists(TOGGLE_BOT_SCRIPT),
            'startup_script_exists': os.path.exists(TOGGLE_STARTUP_SCRIPT),
            'config_exists': os.path.exists(TOGGLE_CONFIG_FILE),
            'npm_installed': os.path.exists('node_modules')
        }
        
        if is_running and pid:
            # Get process info
            try:
                ps_result = subprocess.run(['ps', '-o', 'lstart,rss,%cpu', '-p', str(pid)], 
                                         capture_output=True, text=True)
                if ps_result.returncode == 0:
                    lines = ps_result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        info = lines[1].strip().split()
                        if len(info) >= 6:
                            status['start_time'] = ' '.join(info[:-2])
                            status['memory_mb'] = f"{float(info[-2]) / 1024:.1f}"
                            status['cpu_percent'] = info[-1]
            except:
                pass
        
        return status
    except Exception as e:
        return {'error': str(e)}

async def install_toggle_bot():
    """Install toggle bot dependencies"""
    try:
        # Check if files exist
        if not os.path.exists(TOGGLE_BOT_SCRIPT):
            return False, "Toggle bot script tidak ditemukan"
        
        if not os.path.exists(TOGGLE_STARTUP_SCRIPT):
            return False, "Startup script tidak ditemukan"
        
        # Run installation
        process = await asyncio.create_subprocess_exec(
            'bash', TOGGLE_STARTUP_SCRIPT, 'install',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return process.returncode == 0, stdout.decode() or stderr.decode()
    except Exception as e:
        return False, str(e)

# Event Handlers
async def togglebot_handler(event):
    """Handle .togglebot commands"""
    args = event.text.split()
    
    if len(args) == 1:
        # Show main menu
        status = await get_toggle_bot_status()
        
        status_text = f"""{get_emoji('main')} **Toggle Bot Integration**

{get_emoji('check')} **Node.js:** {'✅ Installed' if status.get('node_installed') else '❌ Not installed'}
{get_emoji('adder6')} **Bot Script:** {'✅ Found' if status.get('bot_script_exists') else '❌ Missing'}
{get_emoji('adder1')} **Dependencies:** {'✅ Installed' if status.get('npm_installed') else '❌ Missing'}
{get_emoji('adder4')} **Toggle Bot:** {'✅ Running' if status.get('running') else '❌ Stopped'}

{get_emoji('adder5')} **Bot Token:** `{BOT_TOKEN[:20]}...`
{get_emoji('adder2')} **Process ID:** {status.get('pid', 'N/A')}

**Commands:**
• `.togglebot status` - Detailed status
• `.togglebot start` - Start toggle bot
• `.togglebot stop` - Stop toggle bot  
• `.togglebot install` - Install dependencies

{get_vzoel_signature()}"""
        
        await safe_send_premium(event, status_text)
        return
    
    command = args[1].lower()
    
    if command == "status":
        # Show detailed status
        msg = await safe_send_premium(event, f"{get_emoji('main')} **Checking toggle bot status...**")
        
        status = await get_toggle_bot_status()
        
        if 'error' in status:
            await safe_edit_premium(msg, f"{get_emoji('adder3')} **Error:** {status['error']}\n\n{get_vzoel_signature()}")
            return
        
        # Build detailed status message
        status_items = []
        status_items.append(f"{get_emoji('check')} **Node.js:** {'✅ Installed' if status.get('node_installed') else '❌ Not installed'}")
        status_items.append(f"{get_emoji('adder6')} **Bot Script:** {'✅ Found' if status.get('bot_script_exists') else '❌ Missing'}")
        status_items.append(f"{get_emoji('adder1')} **Startup Script:** {'✅ Found' if status.get('startup_script_exists') else '❌ Missing'}")
        status_items.append(f"{get_emoji('adder2')} **Dependencies:** {'✅ Installed' if status.get('npm_installed') else '❌ Missing'}")
        status_items.append(f"{get_emoji('adder4')} **Config File:** {'✅ Exists' if status.get('config_exists') else '⚠️ Will be created'}")
        
        if status.get('running'):
            status_items.append(f"{get_emoji('check')} **Status:** ✅ Running (PID: {status.get('pid')})")
            if status.get('start_time'):
                status_items.append(f"{get_emoji('adder5')} **Started:** {status.get('start_time')}")
            if status.get('memory_mb'):
                status_items.append(f"{get_emoji('adder6')} **Memory:** {status.get('memory_mb')} MB")
            if status.get('cpu_percent'):
                status_items.append(f"{get_emoji('adder1')} **CPU:** {status.get('cpu_percent')}%")
        else:
            status_items.append(f"{get_emoji('adder3')} **Status:** ❌ Not running")
        
        detailed_status = f"""{get_emoji('main')} **Toggle Bot Detailed Status**

{chr(10).join(status_items)}

{get_emoji('adder2')} **Bot Information:**
• Token: `{BOT_TOKEN[:25]}...`
• Script: `{TOGGLE_BOT_SCRIPT}`
• Startup: `{TOGGLE_STARTUP_SCRIPT}`

{get_emoji('adder4')} **Quick Actions:**
• Use `.togglebot start` to start the bot
• Use `.togglebot stop` to stop the bot
• Use `.togglebot install` to setup dependencies

{get_vzoel_signature()}"""
        
        await safe_edit_premium(msg, detailed_status)
    
    elif command == "start":
        # Start toggle bot
        msg = await safe_send_premium(event, f"{get_emoji('main')} **Starting toggle bot...**")
        
        # Check if already running
        if check_toggle_bot_running():
            await safe_edit_premium(msg, f"{get_emoji('adder5')} **Toggle bot is already running!**\n\n{get_vzoel_signature()}")
            return
        
        # Check prerequisites
        if not check_node_installed():
            await safe_edit_premium(msg, f"{get_emoji('adder3')} **Node.js is not installed!**\n\nRun `.togglebot install` first.\n\n{get_vzoel_signature()}")
            return
        
        if not os.path.exists(TOGGLE_BOT_SCRIPT):
            await safe_edit_premium(msg, f"{get_emoji('adder3')} **Toggle bot script not found!**\n\nScript `{TOGGLE_BOT_SCRIPT}` is missing.\n\n{get_vzoel_signature()}")
            return
        
        # Start the bot
        success, output = await start_toggle_bot()
        
        if success:
            # Wait and check status
            await asyncio.sleep(3)
            is_running = check_toggle_bot_running()
            pid = get_toggle_bot_pid()
            
            if is_running:
                success_text = f"""{get_emoji('check')} **Toggle Bot Started Successfully!**

{get_emoji('adder4')} **Status:** Running (PID: {pid})
{get_emoji('adder2')} **Bot Token:** `{BOT_TOKEN[:25]}...`

{get_emoji('main')} **Quick Start:**
1. Open Telegram
2. Search for your bot using the token
3. Send `/start` to the bot
4. Use buttons to control userbot

{get_emoji('adder5')} **Available Commands in Telegram:**
• `/start` - Show control panel
• `/toggle` - Start/Stop userbot
• `/restart` - Restart userbot
• `/status` - Check userbot status

{get_vzoel_signature()}"""
            else:
                success_text = f"""{get_emoji('adder5')} **Toggle bot started but may not be running properly**

{get_emoji('adder3')} **Output:** 
```
{output[:500]}
```

Check logs with: `tail -f toggle_bot_output.log`

{get_vzoel_signature()}"""
        else:
            success_text = f"""{get_emoji('adder3')} **Failed to start toggle bot**

{get_emoji('adder5')} **Error:** 
```
{output[:500]}
```

Try running `.togglebot install` first.

{get_vzoel_signature()}"""
        
        await safe_edit_premium(msg, success_text)
    
    elif command == "stop":
        # Stop toggle bot
        msg = await safe_send_premium(event, f"{get_emoji('main')} **Stopping toggle bot...**")
        
        if not check_toggle_bot_running():
            await safe_edit_premium(msg, f"{get_emoji('adder5')} **Toggle bot is not running**\n\n{get_vzoel_signature()}")
            return
        
        success, output = await stop_toggle_bot()
        
        if success:
            stop_text = f"""{get_emoji('check')} **Toggle Bot Stopped Successfully**

{get_emoji('adder2')} Remote control is now disabled
{get_emoji('adder4')} Use `.togglebot start` to restart

{get_vzoel_signature()}"""
        else:
            stop_text = f"""{get_emoji('adder3')} **Failed to stop toggle bot**

{get_emoji('adder5')} **Error:** 
```
{output[:500]}
```

{get_vzoel_signature()}"""
        
        await safe_edit_premium(msg, stop_text)
    
    elif command == "install":
        # Install dependencies
        msg = await safe_send_premium(event, f"{get_emoji('main')} **Installing toggle bot dependencies...**")
        
        success, output = await install_toggle_bot()
        
        if success:
            install_text = f"""{get_emoji('check')} **Installation Completed Successfully!**

{get_emoji('adder4')} **What was installed:**
• Node.js and npm
• Telegram bot API library
• Toggle bot scripts

{get_emoji('adder2')} **Next Steps:**
1. Run `.togglebot start` to start the bot
2. Open Telegram and find your bot
3. Send `/start` to begin remote control

{get_emoji('main')} **Bot Token:** `{BOT_TOKEN}`

{get_vzoel_signature()}"""
        else:
            install_text = f"""{get_emoji('adder3')} **Installation Failed**

{get_emoji('adder5')} **Error:** 
```
{output[:800]}
```

Try running manually:
```
pkg install nodejs
npm install node-telegram-bot-api
```

{get_vzoel_signature()}"""
        
        await safe_edit_premium(msg, install_text)
    
    else:
        help_text = f"""{get_emoji('main')} **Toggle Bot Commands**

{get_emoji('check')} **Available Commands:**
• `.togglebot` - Show main status
• `.togglebot status` - Detailed status check
• `.togglebot start` - Start the toggle bot
• `.togglebot stop` - Stop the toggle bot
• `.togglebot install` - Install dependencies

{get_emoji('adder4')} **What is Toggle Bot?**
Remote control system untuk manage userbot via Telegram bot. Bisa start/stop userbot dari HP lain.

{get_emoji('adder2')} **Features:**
• Remote start/stop userbot
• Real-time status monitoring
• Easy installation & setup
• Secure authorization system

{get_vzoel_signature()}"""
        
        await safe_send_premium(event, help_text)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    """Setup function untuk register event handlers"""
    client.add_event_handler(togglebot_handler, events.NewMessage(pattern=r'\.togglebot'))
    print(f"✅ [ToggleBotIntegration] Plugin loaded v{PLUGIN_INFO['version']}")

def cleanup_plugin():
    """Cleanup plugin resources"""
    try:
        print("[ToggleBotIntegration] Plugin cleanup completed")
    except Exception as e:
        print(f"[ToggleBotIntegration] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'togglebot_handler']