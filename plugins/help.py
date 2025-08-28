#!/usr/bin/env python3
"""
Help Plugin untuk VZOEL ASSISTANT v0.1.0.75
File: plugins/help.py
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
from telethon import events
from datetime import datetime

# Client akan tersedia dari plugin loader
# client sudah di-inject oleh plugin loader

async def is_owner_check(user_id):
    """Check if user is owner - simplified version"""
    try:
        # Get owner ID from environment or main module
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        # Fallback: check if user is bot owner
        me = await client.get_me()
        return user_id == me.id
    except Exception as e:
        print(f"Owner check error: {e}")
        # Fallback: assume user is owner for testing
        return True

def get_prefix():
    """Get command prefix"""
    try:
        import os
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

def get_emoji(emoji_type):
    """Get emoji - simplified fallback"""
    emoji_map = {
        'main': '🤩',
        'check': '⚙️',
        'adder1': '⛈',
        'adder2': '✅',
        'adder3': '👽',
        'adder4': '✈️',
        'adder5': '😈',
        'adder6': '🎚️'
    }
    return emoji_map.get(emoji_type, '🤩')

def convert_font(text, font_type='bold'):
    """Simple font converter - fallback version"""
    if font_type == 'mono':
        return f"`{text}`"
    elif font_type == 'bold':
        return f"**{text}**"
    return text

# HELP COMMAND HANDLER
@client.on(events.NewMessage(pattern=rf'\.help(\s+(.+))?'))
async def help_handler(event):
    """Enhanced help command with categories"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        category = command_arg.strip().lower() if command_arg else None
        
        LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
        
        if not category:
            # Main help menu
            help_text = f"""
[🚩]({LOGO_URL}) **VZOEL ASSISTANT v0.1.0.75 HELP**

╔══════════════════════════════════╗
   🤩 **COMMAND CATEGORIES** 🤩
╚══════════════════════════════════╝

⚙️ **Basic Commands:**
`{prefix}help basic` - Status, ping, alive commands

⛈ **Broadcast Commands:**
`{prefix}help gcast` - Global broadcasting features

✅ **Emoji Commands:**
`{prefix}help emoji` - Premium emoji management

👽 **User Commands:**
`{prefix}help user` - User info, ID commands

✈️ **Voice Chat Commands:**
`{prefix}help voice` - Voice chat controls

😈 **Management Commands:**
`{prefix}help manage` - Blacklist, settings

🎚️ **System Commands:**
`{prefix}help system` - Restart, founder info

🤩 **Quick Usage:**
⚙️ `{prefix}alive` - Bot status
⚙️ `{prefix}gcast <text>` - Broadcast message
⚙️ Reply + `{prefix}gcast` - Enhanced gcast
⚙️ Reply + `{prefix}setemoji` - Auto extract emojis

**Type** `{prefix}help <category>` **for detailed commands**
⚙️ **Total Commands Available: 25+**
            """.strip()
            
        elif category == "basic":
            help_text = f"""
⚙️ **BASIC COMMANDS**

╔══════════════════════════════════╗
   🤩 **STATUS & DIAGNOSTICS** 🤩
╚══════════════════════════════════╝

⚙️ `{prefix}alive`
Show comprehensive bot status with statistics

⚙️ `{prefix}ping` 
Test response time and latency analysis

⛈ `{prefix}help [category]`
Show command help (this menu)

✅ `{prefix}plugins`
Show loaded plugins status

🤩 **Example Usage:**
• `{prefix}alive` - Full system status
• `{prefix}ping` - Response time test
• `{prefix}help gcast` - Gcast commands help
            """.strip()
            
        elif category == "gcast":
            help_text = f"""
⛈ **BROADCAST COMMANDS**

╔══════════════════════════════════╗
   🤩 **GLOBAL CASTING ENHANCED** 🤩
╚══════════════════════════════════╝

✅ `{prefix}gcast <message>`
Standard broadcast to all groups/channels

🤩 Reply to message + `{prefix}gcast`
NEW: Enhanced gcast with entity preservation

⚙️ Reply + `{prefix}gcast <additional text>`
Combine replied content with new text

👽 **Enhanced Features:**
⚙️ Premium emoji preservation
⚙️ Concurrent broadcasting (faster)
⚙️ Advanced error handling
⚙️ Blacklist filtering
⚙️ Real-time progress updates
⚙️ Detailed success/failure reports

✈️ **Usage Examples:**
• `{prefix}gcast Hello everyone!`
• Reply to emoji message + `{prefix}gcast`
• `{prefix}gcast Check out this update!`
            """.strip()
            
        elif category == "emoji":
            help_text = f"""
✅ **EMOJI COMMANDS**

╔══════════════════════════════════╗
   🤩 **PREMIUM EMOJI SYSTEM** 🤩
╚══════════════════════════════════╝

🤩 Reply to message + `{prefix}setemoji`
NEW: Auto-extract ALL premium emojis from message

⚙️ `{prefix}setemoji <type> <emoji_id>`
Manually set premium emoji by ID

👽 **Available Types:**
• main, check, adder1, adder2, adder3, adder4, adder5, adder6

✈️ **How to Get Emoji ID:**
1. Send premium emoji in any chat
2. Forward to @userinfobot
3. Copy document_id from response

😈 **Auto-Extract Features:**
⚙️ Extracts all premium emojis automatically
⚙️ Validates emoji IDs
⚙️ Maps to available slots
⚙️ Saves to database
⚙️ Shows detailed extraction report

🎚️ **Usage Examples:**
• Reply to emoji message + `{prefix}setemoji`
• `{prefix}setemoji main 6156784006194009426`
            """.strip()
            
        elif category == "user":
            help_text = f"""
👽 **USER COMMANDS**

╔══════════════════════════════════╗
   🤩 **USER INFORMATION TOOLS** 🤩
╚══════════════════════════════════╝

⚙️ `{prefix}info [user]`
Get detailed user information

⚙️ `{prefix}id`
Get current chat and user IDs

⛈ `{prefix}vzl <user> <custom_text>`
Create stylized user mention with custom text

✅ **User Input Methods:**
• Reply to message (auto-detect user)
• Username: @username
• User ID: 123456789
• No parameter (gets your own info)

✈️ **Usage Examples:**
• `{prefix}info` - Your own info
• Reply to message + `{prefix}info` - Target user info
• `{prefix}info @username` - Specific user info
• `{prefix}id` - Chat and user IDs
• `{prefix}vzl @user Thanks for help!`
            """.strip()
            
        elif category == "voice":
            help_text = f"""
✈️ **VOICE CHAT COMMANDS**

╔══════════════════════════════════╗
   🤩 **VOICE CHAT CONTROLS** 🤩
╚══════════════════════════════════╝

⚙️ `{prefix}joinvc`
Join voice chat in current group/channel

⛈ `{prefix}leavevc`
Leave current voice chat

✅ **Requirements:**
⚙️ Active voice chat in the group
⚙️ Proper permissions (admin rights may be needed)
⚙️ Group/channel must support voice chats

👽 **Features:**
⚙️ Auto-detect voice chat availability
⚙️ Enhanced error handling
⚙️ Status tracking
⚙️ Permission validation

😈 **Usage:**
• Use in group/channel with active voice chat
• Bot will join muted by default
• Check permissions if join fails
            """.strip()
            
        elif category == "manage":
            help_text = f"""
😈 **MANAGEMENT COMMANDS**

╔══════════════════════════════════╗
   🤩 **BLACKLIST & SETTINGS** 🤩
╚══════════════════════════════════╝

⚙️ `{prefix}addbl [chat_id]`
Add chat to gcast blacklist

⛈ `{prefix}rmbl <chat_id>`
Remove chat from blacklist

✅ `{prefix}listbl`
Show all blacklisted chats

👽 `{prefix}sg`
Toggle spam guard on/off

✈️ **Blacklist Features:**
⚙️ Auto-saves to JSON file
⚙️ Persistent across restarts
⚙️ Shows chat titles when possible
⚙️ Prevents accidental broadcasts

🎚️ **Usage Examples:**
• `{prefix}addbl` - Add current chat
• `{prefix}addbl -1001234567890` - Add specific chat
• `{prefix}rmbl -1001234567890` - Remove from blacklist
• `{prefix}listbl` - View all blacklisted
            """.strip()
            
        elif category == "system":
            help_text = f"""
🎚️ **SYSTEM COMMANDS**

╔══════════════════════════════════╗
   🤩 **SYSTEM ADMINISTRATION** 🤩
╚══════════════════════════════════╝

⚙️ `{prefix}restart`
Restart the bot (with confirmation)

⛈ `{prefix}infofounder`
Show founder and bot information

✅ **System Information:**
⚙️ Runtime statistics
⚙️ Error handling status
⚙️ Database connectivity
⚙️ Plugin system status
⚙️ Premium feature availability

👽 **Safety Features:**
⚙️ Restart confirmation required
⚙️ Graceful shutdown process
⚙️ Configuration auto-save
⚙️ Error logging maintained

✈️ **Usage:**
• `{prefix}restart` - Restart with confirmation
• `{prefix}infofounder` - About the bot and creator
            """.strip()
            
        else:
            # Invalid category
            help_text = f"""
👽 **INVALID CATEGORY**

⚙️ Available categories:
• basic - Status and diagnostic commands
• gcast - Broadcasting commands  
• emoji - Premium emoji management
• user - User information tools
• voice - Voice chat controls
• manage - Blacklist and settings
• system - System administration

🤩 Use `{prefix}help` for main menu
            """.strip()
        
        await event.reply(help_text)
        
    except Exception as e:
        error_text = f"""
👽 **Help Error:** {str(e)}

⚙️ Try: `{get_prefix()}help` for main menu
        """.strip()
        await event.reply(error_text)
        print(f"Help plugin error: {e}")

# Plugin info
PLUGIN_INFO = {
    'name': 'help',
    'version': '1.0.1',
    'description': 'Comprehensive help system for VZOEL ASSISTANT',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['help'],
    'categories': ['basic', 'gcast', 'emoji', 'user', 'voice', 'manage', 'system']
}

def get_plugin_info():
    return PLUGIN_INFO

print("✅ Help plugin loaded successfully!")
