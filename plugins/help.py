#!/usr/bin/env python3
"""
Help Plugin untuk VZOEL ASSISTANT v0.1.0.75
File: plugins/help.py
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
from telethon import events
from datetime import datetime

# Plugin akan mengakses client dan COMMAND_PREFIX dari main.py
# Pastikan variabel ini tersedia dari main module

async def is_owner_check(user_id):
    """Check if user is owner - import from main module"""
    try:
        # Akses fungsi is_owner dari main module
        import __main__
        return await __main__.is_owner(user_id)
    except:
        # Fallback check
        me = await client.get_me()
        return user_id == me.id

def get_prefix():
    """Get command prefix from main module"""
    try:
        import __main__
        return getattr(__main__, 'COMMAND_PREFIX', '.')
    except:
        return '.'

def get_emoji(emoji_type):
    """Get premium emoji from main module"""
    try:
        import __main__
        return __main__.get_emoji(emoji_type)
    except:
        # Fallback emojis
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
    """Convert text to Unicode fonts - import from main module"""
    try:
        import __main__
        return __main__.convert_font(text, font_type)
    except:
        return text  # Fallback to original text

async def log_command_plugin(event, command):
    """Log command execution - import from main module"""
    try:
        import __main__
        await __main__.log_command(event, command)
    except:
        pass

# HELP COMMAND - PLUGIN VERSION
@client.on(events.NewMessage(pattern=rf'{re.escape(get_prefix())}help(\s+(.+))?'))
async def help_handler(event):
    """
    Comprehensive help command dengan kategorisasi
    Usage: .help atau .help <category>
    """
    if not await is_owner_check(event.sender_id):
        return
    
    await log_command_plugin(event, "help")
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        category = command_arg.strip().lower() if command_arg else None
        
        # Logo dan header
        LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
        
        if not category:
            # Main help menu
            help_text = f"""
[🚩]({LOGO_URL}) {convert_font('VZOEL ASSISTANT v0.1.0.75 HELP', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('COMMAND CATEGORIES', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Basic Commands:', 'bold')}
`{prefix}help basic` - Status, ping, alive commands

{get_emoji('adder1')} {convert_font('Broadcast Commands:', 'bold')}
`{prefix}help gcast` - Global broadcasting features

{get_emoji('adder2')} {convert_font('Emoji Commands:', 'bold')}
`{prefix}help emoji` - Premium emoji management

{get_emoji('adder3')} {convert_font('User Commands:', 'bold')}
`{prefix}help user` - User info, ID commands

{get_emoji('adder4')} {convert_font('Voice Chat Commands:', 'bold')}
`{prefix}help voice` - Voice chat controls

{get_emoji('adder5')} {convert_font('Management Commands:', 'bold')}
`{prefix}help manage` - Blacklist, settings

{get_emoji('adder6')} {convert_font('System Commands:', 'bold')}
`{prefix}help system` - Restart, founder info

{get_emoji('main')} {convert_font('Quick Usage:', 'bold')}
{get_emoji('check')} `{prefix}alive` - Bot status
{get_emoji('check')} `{prefix}gcast <text>` - Broadcast message
{get_emoji('check')} Reply + `{prefix}gcast` - Enhanced gcast
{get_emoji('check')} Reply + `{prefix}setemoji` - Auto extract emojis

{convert_font('Type', 'bold')} `{prefix}help <category>` {convert_font('for detailed commands', 'bold')}
{get_emoji('check')} {convert_font('Total Commands Available: 25+', 'bold')}
            """.strip()
            
        elif category == "basic":
            help_text = f"""
{get_emoji('check')} {convert_font('BASIC COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('STATUS & DIAGNOSTICS', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} `{prefix}alive`
Show comprehensive bot status with statistics

{get_emoji('check')} `{prefix}ping` 
Test response time and latency analysis

{get_emoji('adder1')} `{prefix}help [category]`
Show command help (this menu)

{get_emoji('adder2')} `{prefix}plugins`
Show loaded plugins status

{get_emoji('main')} {convert_font('Example Usage:', 'bold')}
• `{prefix}alive` - Full system status
• `{prefix}ping` - Response time test
• `{prefix}help gcast` - Gcast commands help
            """.strip()
            
        elif category == "gcast":
            help_text = f"""
{get_emoji('adder1')} {convert_font('BROADCAST COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('GLOBAL CASTING ENHANCED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('adder2')} `{prefix}gcast <message>`
Standard broadcast to all groups/channels

{get_emoji('main')} Reply to message + `{prefix}gcast`
NEW: Enhanced gcast with entity preservation

{get_emoji('check')} Reply + `{prefix}gcast <additional text>`
Combine replied content with new text

{get_emoji('adder3')} {convert_font('Enhanced Features:', 'bold')}
{get_emoji('check')} Premium emoji preservation
{get_emoji('check')} Concurrent broadcasting (faster)
{get_emoji('check')} Advanced error handling
{get_emoji('check')} Blacklist filtering
{get_emoji('check')} Real-time progress updates
{get_emoji('check')} Detailed success/failure reports

{get_emoji('adder4')} {convert_font('Usage Examples:', 'bold')}
• `{prefix}gcast Hello everyone!`
• Reply to emoji message + `{prefix}gcast`
• `{prefix}gcast Check out this update!`
            """.strip()
            
        elif category == "emoji":
            help_text = f"""
{get_emoji('adder2')} {convert_font('EMOJI COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('PREMIUM EMOJI SYSTEM', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('main')} Reply to message + `{prefix}setemoji`
NEW: Auto-extract ALL premium emojis from message

{get_emoji('check')} `{prefix}setemoji <type> <emoji_id>`
Manually set premium emoji by ID

{get_emoji('adder3')} {convert_font('Available Types:', 'bold')}
• main, check, adder1, adder2, adder3, adder4, adder5, adder6

{get_emoji('adder4')} {convert_font('How to Get Emoji ID:', 'bold')}
1. Send premium emoji in any chat
2. Forward to @userinfobot
3. Copy document_id from response

{get_emoji('adder5')} {convert_font('Auto-Extract Features:', 'bold')}
{get_emoji('check')} Extracts all premium emojis automatically
{get_emoji('check')} Validates emoji IDs
{get_emoji('check')} Maps to available slots
{get_emoji('check')} Saves to database
{get_emoji('check')} Shows detailed extraction report

{get_emoji('adder6')} {convert_font('Usage Examples:', 'bold')}
• Reply to emoji message + `{prefix}setemoji`
• `{prefix}setemoji main 6156784006194009426`
            """.strip()
            
        elif category == "user":
            help_text = f"""
{get_emoji('adder3')} {convert_font('USER COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('USER INFORMATION TOOLS', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} `{prefix}info [user]`
Get detailed user information

{get_emoji('check')} `{prefix}id`
Get current chat and user IDs

{get_emoji('adder1')} `{prefix}vzl <user> <custom_text>`
Create stylized user mention with custom text

{get_emoji('adder2')} {convert_font('User Input Methods:', 'bold')}
• Reply to message (auto-detect user)
• Username: @username
• User ID: 123456789
• No parameter (gets your own info)

{get_emoji('adder4')} {convert_font('Usage Examples:', 'bold')}
• `{prefix}info` - Your own info
• Reply to message + `{prefix}info` - Target user info
• `{prefix}info @username` - Specific user info
• `{prefix}id` - Chat and user IDs
• `{prefix}vzl @user Thanks for help!`
            """.strip()
            
        elif category == "voice":
            help_text = f"""
{get_emoji('adder4')} {convert_font('VOICE CHAT COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('VOICE CHAT CONTROLS', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} `{prefix}joinvc`
Join voice chat in current group/channel

{get_emoji('adder1')} `{prefix}leavevc`
Leave current voice chat

{get_emoji('adder2')} {convert_font('Requirements:', 'bold')}
{get_emoji('check')} Active voice chat in the group
{get_emoji('check')} Proper permissions (admin rights may be needed)
{get_emoji('check')} Group/channel must support voice chats

{get_emoji('adder3')} {convert_font('Features:', 'bold')}
{get_emoji('check')} Auto-detect voice chat availability
{get_emoji('check')} Enhanced error handling
{get_emoji('check')} Status tracking
{get_emoji('check')} Permission validation

{get_emoji('adder5')} {convert_font('Usage:', 'bold')}
• Use in group/channel with active voice chat
• Bot will join muted by default
• Check permissions if join fails
            """.strip()
            
        elif category == "manage":
            help_text = f"""
{get_emoji('adder5')} {convert_font('MANAGEMENT COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('BLACKLIST & SETTINGS', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} `{prefix}addbl [chat_id]`
Add chat to gcast blacklist

{get_emoji('adder1')} `{prefix}rmbl <chat_id>`
Remove chat from blacklist

{get_emoji('adder2')} `{prefix}listbl`
Show all blacklisted chats

{get_emoji('adder3')} `{prefix}sg`
Toggle spam guard on/off

{get_emoji('adder4')} {convert_font('Blacklist Features:', 'bold')}
{get_emoji('check')} Auto-saves to JSON file
{get_emoji('check')} Persistent across restarts
{get_emoji('check')} Shows chat titles when possible
{get_emoji('check')} Prevents accidental broadcasts

{get_emoji('adder6')} {convert_font('Usage Examples:', 'bold')}
• `{prefix}addbl` - Add current chat
• `{prefix}addbl -1001234567890` - Add specific chat
• `{prefix}rmbl -1001234567890` - Remove from blacklist
• `{prefix}listbl` - View all blacklisted
            """.strip()
            
        elif category == "system":
            help_text = f"""
{get_emoji('adder6')} {convert_font('SYSTEM COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('SYSTEM ADMINISTRATION', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} `{prefix}restart`
Restart the bot (with confirmation)

{get_emoji('adder1')} `{prefix}infofounder`
Show founder and bot information

{get_emoji('adder2')} {convert_font('System Information:', 'bold')}
{get_emoji('check')} Runtime statistics
{get_emoji('check')} Error handling status
{get_emoji('check')} Database connectivity
{get_emoji('check')} Plugin system status
{get_emoji('check')} Premium feature availability

{get_emoji('adder3')} {convert_font('Safety Features:', 'bold')}
{get_emoji('check')} Restart confirmation required
{get_emoji('check')} Graceful shutdown process
{get_emoji('check')} Configuration auto-save
{get_emoji('check')} Error logging maintained

{get_emoji('adder4')} {convert_font('Usage:', 'bold')}
• `{prefix}restart` - Restart with confirmation
• `{prefix}infofounder` - About the bot and creator
            """.strip()
            
        else:
            # Invalid category
            help_text = f"""
{get_emoji('adder3')} {convert_font('INVALID CATEGORY', 'mono')}

{get_emoji('check')} Available categories:
• basic - Status and diagnostic commands
• gcast - Broadcasting commands  
• emoji - Premium emoji management
• user - User information tools
• voice - Voice chat controls
• manage - Blacklist and settings
• system - System administration

{get_emoji('main')} Use `{prefix}help` for main menu
            """.strip()
        
        await event.reply(help_text)
        
    except Exception as e:
        error_text = f"""
{get_emoji('adder3')} {convert_font('Help Error:', 'bold')} {str(e)}

{get_emoji('check')} Try: `{get_prefix()}help` for main menu
        """.strip()
        await event.reply(error_text)

# Plugin info untuk debugging
PLUGIN_INFO = {
    'name': 'help',
    'version': '1.0.0',
    'description': 'Comprehensive help system for VZOEL ASSISTANT',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['help'],
    'categories': ['basic', 'gcast', 'emoji', 'user', 'voice', 'manage', 'system']
}

# Export plugin info
def get_plugin_info():
    return PLUGIN_INFO