#!/usr/bin/env python3
"""
Bot Manager Plugin for VzoelFox Userbot - Permanent Bot Creation & Log Integration
Fitur: Auto create bot via BotFather, permanent token storage, log group integration
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Complete Bot Management System
"""

import os
import json
import asyncio
import random
import string
from datetime import datetime
from telethon import events, TelegramClient
from telethon.errors import FloodWaitError, UserIsBlockedError

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('bot_manager')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

PLUGIN_INFO = {
    "name": "bot_manager",
    "version": "1.0.0",
    "description": "Permanent bot creation & management dengan BotFather integration untuk log system",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".createbot", ".botinfo", ".bottest", ".logbot", ".botstatus"],
    "features": ["botfather integration", "permanent token storage", "log group integration", "auto bot management", "centralized database"]
}

# Premium Emoji Mapping
PREMIUM_EMOJIS = {
    "main": {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6": {"emoji": "🎚️", "custom_emoji_id": "5794323465452394551"}
}

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('emoji', '🤩')

# Bot storage configuration
BOT_CONFIG_DIR = os.path.expanduser("~/.vzoelfox_bots")
BOT_CONFIG_FILE = os.path.join(BOT_CONFIG_DIR, "bot_config.json")
BOT_ENV_FILE = os.path.join(BOT_CONFIG_DIR, ".bot_env")

def ensure_bot_directory():
    """Ensure bot config directory exists"""
    if not os.path.exists(BOT_CONFIG_DIR):
        os.makedirs(BOT_CONFIG_DIR, mode=0o700)
    return BOT_CONFIG_DIR

def save_bot_config(config):
    """Save bot configuration to file"""
    ensure_bot_directory()
    with open(BOT_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also save to environment file for easy access
    with open(BOT_ENV_FILE, 'w') as f:
        f.write(f"VZOEL_BOT_TOKEN={config.get('bot_token', '')}\n")
        f.write(f"VZOEL_BOT_USERNAME={config.get('bot_username', '')}\n")
        f.write(f"VZOEL_LOG_GROUP_ID={config.get('log_group_id', '')}\n")
        f.write(f"VZOEL_BOT_CREATED={config.get('created_date', '')}\n")

def load_bot_config():
    """Load bot configuration from file"""
    if os.path.exists(BOT_CONFIG_FILE):
        try:
            with open(BOT_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def generate_bot_name():
    """Generate unique bot name"""
    prefix = "VzoelLog"
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}{suffix}_bot"

def generate_bot_description():
    """Generate bot description"""
    return "VzoelFox Userbot Log Manager - Permanent logging system created by Vzoel Fox's"

async def create_bot_via_botfather(client, bot_name, description):
    """Create bot via BotFather interaction"""
    try:
        botfather = "@BotFather"
        
        # Start conversation with BotFather
        await client.send_message(botfather, "/start")
        await asyncio.sleep(2)
        
        # Create new bot
        await client.send_message(botfather, "/newbot")
        await asyncio.sleep(2)
        
        # Send bot display name
        display_name = f"Vzoel Log Manager {bot_name.replace('_bot', '')}"
        await client.send_message(botfather, display_name)
        await asyncio.sleep(2)
        
        # Send bot username
        await client.send_message(botfather, bot_name)
        await asyncio.sleep(3)
        
        # Get bot token from BotFather's response
        async for message in client.iter_messages(botfather, limit=5):
            if "token" in message.text.lower() and ":" in message.text:
                # Extract token from message
                lines = message.text.split('\n')
                for line in lines:
                    if ":" in line and len(line.split(':')[0]) > 8:
                        token = line.strip()
                        if token.count(':') == 1:
                            return token
        
        return None
        
    except Exception as e:
        print(f"Error creating bot: {e}")
        return None

async def setup_bot_commands(bot_token):
    """Setup bot commands via BotFather"""
    try:
        client_temp = TelegramClient('temp_bot', api_id=os.getenv('API_ID'), api_hash=os.getenv('API_HASH'))
        await client_temp.start(bot_token=bot_token)
        
        botfather = "@BotFather"
        
        # Set bot commands
        await client_temp.send_message(botfather, "/setcommands")
        await asyncio.sleep(2)
        
        # Select our bot
        bot_info = await client_temp.get_me()
        await client_temp.send_message(botfather, f"@{bot_info.username}")
        await asyncio.sleep(2)
        
        # Set command list
        commands = """start - Start the log bot
help - Show available commands
status - Check bot status
logs - Get recent logs"""
        
        await client_temp.send_message(botfather, commands)
        await asyncio.sleep(2)
        
        # Set bot description
        await client_temp.send_message(botfather, "/setdescription")
        await asyncio.sleep(2)
        await client_temp.send_message(botfather, f"@{bot_info.username}")
        await asyncio.sleep(2)
        await client_temp.send_message(botfather, generate_bot_description())
        
        await client_temp.disconnect()
        return bot_info.username
        
    except Exception as e:
        print(f"Error setting up bot commands: {e}")
        return None

async def create_log_group(client, bot_username):
    """Create permanent log group"""
    try:
        # Create group
        group_title = f"Vzoel Log Group - {datetime.now().strftime('%Y%m%d')}"
        group_description = f"Permanent log group for VzoelFox Userbot\nManaged by @{bot_username}\nCreated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create the group
        result = await client(functions.messages.CreateChatRequest(
            title=group_title,
            users=[]  # Empty initially
        ))
        
        group_id = result.chats[0].id
        
        # Add bot to group
        try:
            await client(functions.messages.AddChatUserRequest(
                chat_id=group_id,
                user_id=bot_username,
                fwd_limit=0
            ))
        except:
            # Alternative method using invite
            try:
                await client(functions.messages.CreateChatRequest(
                    title=group_title,
                    users=[bot_username]
                ))
            except:
                pass
        
        # Set group description
        try:
            await client(functions.messages.EditChatAboutRequest(
                peer=group_id,
                about=group_description
            ))
        except:
            pass
        
        return -int(str(group_id))  # Convert to supergroup format
        
    except Exception as e:
        print(f"Error creating log group: {e}")
        return None

async def test_bot_functionality(bot_token, log_group_id):
    """Test bot functionality"""
    try:
        # Create temporary bot client
        bot_client = TelegramClient('test_bot', api_id=os.getenv('API_ID'), api_hash=os.getenv('API_HASH'))
        await bot_client.start(bot_token=bot_token)
        
        # Test message sending
        test_message = f"{get_emoji('check')} Bot Test - {datetime.now().strftime('%H:%M:%S')}\n"
        test_message += f"{get_emoji('main')} VzoelFox Userbot Log Bot is working!\n"
        test_message += f"{get_emoji('adder2')} Ready to receive logs"
        
        await bot_client.send_message(log_group_id, test_message)
        
        await bot_client.disconnect()
        return True
        
    except Exception as e:
        print(f"Bot test error: {e}")
        return False

# Global client reference
client = None

async def createbot_handler(event):
    """Create permanent bot for logging"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        # Check if bot already exists
        config = load_bot_config()
        if config.get('bot_token') and config.get('log_group_id'):
            await event.reply(f"""
{get_emoji('check')} {convert_font('Bot sudah ada!', 'bold')}

{get_emoji('main')} Bot: @{config.get('bot_username', 'N/A')}
{get_emoji('adder4')} Token: {config.get('bot_token', 'N/A')[:20]}...
{get_emoji('adder6')} Log Group: {config.get('log_group_id', 'N/A')}
{get_emoji('adder2')} Created: {config.get('created_date', 'N/A')}

Use {convert_font('.bottest', 'mono')} to test functionality
            """.strip())
            return
        
        status_msg = await event.reply(f"{get_emoji('adder1')} Creating permanent bot...")
        
        # Generate bot details
        bot_name = generate_bot_name()
        description = generate_bot_description()
        
        await status_msg.edit(f"{get_emoji('adder1')} Creating bot: {bot_name}...")
        
        # Create bot via BotFather
        bot_token = await create_bot_via_botfather(client, bot_name, description)
        
        if not bot_token:
            await status_msg.edit(f"{get_emoji('adder5')} Failed to create bot. Try again.")
            return
        
        await status_msg.edit(f"{get_emoji('check')} Bot created! Setting up commands...")
        
        # Setup bot commands
        bot_username = await setup_bot_commands(bot_token)
        
        if not bot_username:
            await status_msg.edit(f"{get_emoji('adder5')} Bot created but command setup failed.")
            return
        
        await status_msg.edit(f"{get_emoji('adder4')} Creating log group...")
        
        # Create log group
        log_group_id = await create_log_group(client, bot_username)
        
        if not log_group_id:
            await status_msg.edit(f"{get_emoji('adder5')} Bot created but log group creation failed.")
            return
        
        # Save configuration
        config = {
            'bot_token': bot_token,
            'bot_username': bot_username,
            'log_group_id': log_group_id,
            'created_date': datetime.now().isoformat(),
            'status': 'active'
        }
        
        save_bot_config(config)
        
        await status_msg.edit(f"{get_emoji('adder6')} Testing bot functionality...")
        
        # Test bot
        test_result = await test_bot_functionality(bot_token, log_group_id)
        
        if test_result:
            await status_msg.edit(f"""
{get_emoji('adder2')} {convert_font('Bot berhasil dibuat!', 'bold')}

{get_emoji('main')} Bot: @{bot_username}
{get_emoji('check')} Token: {bot_token[:20]}...
{get_emoji('adder4')} Log Group ID: {log_group_id}
{get_emoji('adder6')} Status: Active & Ready

{get_emoji('adder3')} Bot siap menerima logs!
Use {convert_font('.logbot <message>', 'mono')} untuk test
            """.strip())
        else:
            await status_msg.edit(f"{get_emoji('adder5')} Bot created but functionality test failed.")
    
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Error: {str(e)}")

async def botinfo_handler(event):
    """Show bot information"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        config = load_bot_config()
        
        if not config.get('bot_token'):
            await event.reply(f"""
{get_emoji('adder5')} {convert_font('No bot found!', 'bold')}

Use {convert_font('.createbot', 'mono')} to create permanent bot
            """.strip())
            return
        
        await event.reply(f"""
{get_emoji('main')} {convert_font('BOT INFORMATION', 'bold')}

{get_emoji('check')} {convert_font('Bot Username', 'mono')}: @{config.get('bot_username', 'N/A')}
{get_emoji('adder4')} {convert_font('Bot Token', 'mono')}: {config.get('bot_token', 'N/A')[:20]}...
{get_emoji('adder6')} {convert_font('Log Group ID', 'mono')}: {config.get('log_group_id', 'N/A')}
{get_emoji('adder2')} {convert_font('Created Date', 'mono')}: {config.get('created_date', 'N/A')[:19]}
{get_emoji('adder1')} {convert_font('Status', 'mono')}: {config.get('status', 'Unknown')}

{get_emoji('adder3')} {convert_font('Available Commands:', 'bold')}
• {convert_font('.bottest', 'mono')} - Test bot functionality
• {convert_font('.logbot <msg>', 'mono')} - Send test log
• {convert_font('.botstatus', 'mono')} - Check bot status
        """.strip())
    
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Error: {str(e)}")

async def bottest_handler(event):
    """Test bot functionality"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        config = load_bot_config()
        
        if not config.get('bot_token'):
            await event.reply(f"{get_emoji('adder5')} No bot found. Use .createbot first.")
            return
        
        test_result = await test_bot_functionality(
            config.get('bot_token'), 
            config.get('log_group_id')
        )
        
        if test_result:
            await event.reply(f"""
{get_emoji('adder2')} {convert_font('Bot Test Successful!', 'bold')}

{get_emoji('check')} Bot is working properly
{get_emoji('adder4')} Log group accessible
{get_emoji('adder6')} Message sending functional

{get_emoji('main')} Bot ready for logging!
            """.strip())
        else:
            await event.reply(f"""
{get_emoji('adder5')} {convert_font('Bot Test Failed!', 'bold')}

{get_emoji('adder1')} Check bot token validity
{get_emoji('adder3')} Verify log group permissions
{get_emoji('adder4')} Consider recreating bot
            """.strip())
    
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Error: {str(e)}")

async def logbot_handler(event):
    """Send test log via bot"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split(maxsplit=1)
        message = args[1] if len(args) > 1 else "Test log message"
        
        config = load_bot_config()
        
        if not config.get('bot_token'):
            await event.reply(f"{get_emoji('adder5')} No bot found. Use .createbot first.")
            return
        
        # Send log via bot
        bot_client = TelegramClient('log_bot', api_id=os.getenv('API_ID'), api_hash=os.getenv('API_HASH'))
        await bot_client.start(bot_token=config.get('bot_token'))
        
        log_message = f"""
{get_emoji('adder6')} {convert_font('VZOEL LOG ENTRY', 'bold')}

{get_emoji('check')} {convert_font('Timestamp', 'mono')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{get_emoji('main')} {convert_font('Message', 'mono')}: {message}
{get_emoji('adder4')} {convert_font('Source', 'mono')}: VzoelFox Userbot
{get_emoji('adder2')} {convert_font('Status', 'mono')}: Delivered

{get_emoji('adder3')} Logged by @{config.get('bot_username', 'VzoelBot')}
        """.strip()
        
        await bot_client.send_message(config.get('log_group_id'), log_message)
        await bot_client.disconnect()
        
        await event.reply(f"{get_emoji('adder2')} Log sent successfully!")
    
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Error sending log: {str(e)}")

async def botstatus_handler(event):
    """Check bot status"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        config = load_bot_config()
        
        if not config.get('bot_token'):
            await event.reply(f"{get_emoji('adder5')} No bot configured.")
            return
        
        # Check bot status
        try:
            bot_client = TelegramClient('status_bot', api_id=os.getenv('API_ID'), api_hash=os.getenv('API_HASH'))
            await bot_client.start(bot_token=config.get('bot_token'))
            
            bot_info = await bot_client.get_me()
            await bot_client.disconnect()
            
            status = "🟢 Online"
            details = f"Bot is active and responsive"
            
        except Exception as e:
            status = "🔴 Offline"
            details = f"Error: {str(e)}"
        
        await event.reply(f"""
{get_emoji('main')} {convert_font('BOT STATUS CHECK', 'bold')}

{get_emoji('check')} {convert_font('Bot', 'mono')}: @{config.get('bot_username', 'N/A')}
{get_emoji('adder4')} {convert_font('Status', 'mono')}: {status}
{get_emoji('adder6')} {convert_font('Log Group', 'mono')}: {config.get('log_group_id', 'N/A')}
{get_emoji('adder2')} {convert_font('Created', 'mono')}: {config.get('created_date', 'N/A')[:10]}

{get_emoji('adder1')} {convert_font('Details', 'mono')}: {details}

{get_emoji('adder3')} Config stored at: {BOT_CONFIG_FILE}
        """.strip())
    
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Error: {str(e)}")

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
        }
        return ''.join([bold_map.get(c, c) for c in text])
    elif font_type == 'mono':
        mono_map = {
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
            'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
            's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
            'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
            'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉'
        }
        return ''.join([mono_map.get(c, c) for c in text])
    return text

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    client.add_event_handler(createbot_handler, events.NewMessage(pattern=r'\.createbot$'))
    client.add_event_handler(botinfo_handler, events.NewMessage(pattern=r'\.botinfo$'))
    client.add_event_handler(bottest_handler, events.NewMessage(pattern=r'\.bottest$'))
    client.add_event_handler(logbot_handler, events.NewMessage(pattern=r'\.logbot(?:\s+(.+))?$'))
    client.add_event_handler(botstatus_handler, events.NewMessage(pattern=r'\.botstatus$'))
    
    print(f"✅ [BotManager] Permanent bot management system loaded v{PLUGIN_INFO['version']}")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[BotManager] Plugin cleanup initiated")
        client = None
        print("[BotManager] Plugin cleanup completed")
    except Exception as e:
        print(f"[BotManager] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'save_bot_config', 'load_bot_config']