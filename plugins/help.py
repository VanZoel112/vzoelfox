#!/usr/bin/env python3
"""
Help Plugin dengan Premium Emoji Support
File: plugins/help.py
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
from telethon import events, Button
from telethon.tl.types import MessageEntityCustomEmoji
from datetime import datetime

# Premium emoji configuration (copy dari main.py)
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
}

# Unicode Fonts
FONTS = {
    'bold': {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
        'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
        's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
        'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
        'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    },
    'mono': {
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
        'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
        's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
        'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
        'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
        '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
    }
}

# Global premium status
premium_status = None

async def check_premium_status():
    """Check premium status in plugin"""
    global premium_status
    try:
        me = await client.get_me()
        premium_status = getattr(me, 'premium', False)
        return premium_status
    except Exception:
        premium_status = False
        return False

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def get_emoji(emoji_type):
    """Get premium emoji character"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    if not premium_status:
        return []
    
    entities = []
    current_offset = 0
    i = 0
    
    try:
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        # Calculate UTF-16 length
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        i += len(emoji_char)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

async def safe_send_with_entities(event, text, buttons=None):
    """Send message with premium entities and buttons if available"""
    try:
        # Check premium status first
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities, buttons=buttons)
                return
        
        # Fallback to normal reply with buttons
        await event.reply(text, buttons=buttons)
    except Exception:
        # Final fallback
        await event.reply(text, buttons=buttons)

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return True

def get_prefix():
    """Get command prefix"""
    try:
        import os
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

# HELP COMMAND HANDLER WITH PREMIUM EMOJI SUPPORT  
async def help_handler(event):
    """Enhanced help command with premium emoji support"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        category = command_arg.strip().lower() if command_arg else None
        
        LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
        
        if not category:
            # Main help menu dengan premium emoji dan buttons
            help_text = f"""
[🚩]({LOGO_URL}) {convert_font('VZOEL ASSISTANT v0.1.0.76 HELP', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('COMMAND CATEGORIES', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Quick Usage:', 'bold')}
{get_emoji('check')} `{prefix}alive` - Bot status
{get_emoji('check')} `{prefix}gcast <text>` - Broadcast message
{get_emoji('check')} `{prefix}sgcast <text>` - Slow broadcast (anti-spam)
{get_emoji('check')} Reply + `{prefix}gcast` - Enhanced gcast
{get_emoji('check')} Reply + `{prefix}setemoji` - Auto extract emojis

{convert_font('Click buttons below for detailed help:', 'bold')}
{get_emoji('check')} {convert_font('Total Commands Available: 30+', 'bold')}
            """.strip()
            
            # Create inline buttons
            buttons = [
                [Button.inline(f"{get_emoji('check')} Basic", b"help_basic"),
                 Button.inline(f"{get_emoji('adder1')} Broadcast", b"help_gcast")],
                [Button.inline(f"{get_emoji('adder2')} Emoji", b"help_emoji"),
                 Button.inline(f"{get_emoji('adder3')} User", b"help_user")],
                [Button.inline(f"{get_emoji('adder4')} Voice", b"help_voice"),
                 Button.inline(f"{get_emoji('adder5')} Manage", b"help_manage")],
                [Button.inline(f"{get_emoji('adder6')} System", b"help_system"),
                 Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]
            ]
            
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
        
        # Send with premium entities and buttons
        if not category:
            await safe_send_with_entities(event, help_text, buttons)
        else:
            # Add back button for category pages
            back_button = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            await safe_send_with_entities(event, help_text, back_button)
        
    except Exception as e:
        error_text = f"""
{get_emoji('adder3')} {convert_font('Help Error:', 'bold')} {str(e)}

{get_emoji('check')} Try: `{get_prefix()}help` for main menu
        """.strip()
        await safe_send_with_entities(event, error_text)

# Button callback handler
async def help_callback_handler(event):
    """Handle inline button callbacks for help menu"""
    if not await is_owner_check(event.sender_id):
        await event.answer("❌ Only owner can use this!", alert=True)
        return
    
    try:
        category = event.data.decode('utf-8').split('_', 1)[1]
        prefix = get_prefix()
        
        LOGO_URL = "https://imgur.com/gallery/logo-S6biYEi"
        
        if category == "main":
            # Main help menu
            help_text = f"""
[🚩]({LOGO_URL}) {convert_font('VZOEL ASSISTANT v0.1.0.76 HELP', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('COMMAND CATEGORIES', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Quick Usage:', 'bold')}
{get_emoji('check')} `{prefix}alive` - Bot status
{get_emoji('check')} `{prefix}gcast <text>` - Broadcast message
{get_emoji('check')} `{prefix}sgcast <text>` - Slow broadcast (anti-spam)
{get_emoji('check')} Reply + `{prefix}gcast` - Enhanced gcast
{get_emoji('check')} Reply + `{prefix}setemoji` - Auto extract emojis

{convert_font('Click buttons below for detailed help:', 'bold')}
{get_emoji('check')} {convert_font('Total Commands Available: 30+', 'bold')}
            """.strip()
            
            buttons = [
                [Button.inline(f"{get_emoji('check')} Basic", b"help_basic"),
                 Button.inline(f"{get_emoji('adder1')} Broadcast", b"help_gcast")],
                [Button.inline(f"{get_emoji('adder2')} Emoji", b"help_emoji"),
                 Button.inline(f"{get_emoji('adder3')} User", b"help_user")],
                [Button.inline(f"{get_emoji('adder4')} Voice", b"help_voice"),
                 Button.inline(f"{get_emoji('adder5')} Manage", b"help_manage")],
                [Button.inline(f"{get_emoji('adder6')} System", b"help_system"),
                 Button.inline("🔄 Refresh", b"help_main")]
            ]
            
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
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            
        elif category == "gcast":
            help_text = f"""
{get_emoji('adder1')} {convert_font('BROADCAST COMMANDS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('GLOBAL CASTING ENHANCED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('adder2')} `{prefix}gcast <message>`
Standard broadcast to all groups/channels

{get_emoji('main')} `{prefix}sgcast <message>`
NEW: Slow broadcast with 15s delay (anti-spam)

{get_emoji('check')} Reply to message + `{prefix}gcast`
Enhanced gcast with entity preservation

{get_emoji('adder3')} Reply to message + `{prefix}sgcast`
Forward message with slow broadcast

{get_emoji('adder4')} {convert_font('Enhanced Features:', 'bold')}
{get_emoji('check')} Premium emoji preservation
{get_emoji('check')} Concurrent broadcasting (gcast)
{get_emoji('check')} Anti-spam delays (sgcast)
{get_emoji('check')} Advanced error handling
{get_emoji('check')} Blacklist filtering
{get_emoji('check')} Real-time progress updates
{get_emoji('check')} Animated progress (sgcast)

{get_emoji('adder5')} {convert_font('Usage Examples:', 'bold')}
• `{prefix}gcast Hello everyone!`
• `{prefix}sgcast Important announcement`
• Reply to emoji message + `{prefix}gcast`
• Reply to any message + `{prefix}sgcast`
            """.strip()
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            
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
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            
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
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            
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

{get_emoji('adder2')} `{prefix}vcstatus`
Check voice chat monitoring status

{get_emoji('adder3')} {convert_font('Requirements:', 'bold')}
{get_emoji('check')} Active voice chat in the group
{get_emoji('check')} Proper permissions (admin rights may be needed)
{get_emoji('check')} Group/channel must support voice chats

{get_emoji('adder5')} {convert_font('Features:', 'bold')}
{get_emoji('check')} Auto-detect voice chat availability
{get_emoji('check')} Enhanced error handling
{get_emoji('check')} Duration tracking
{get_emoji('check')} Auto-disconnect notifications
{get_emoji('check')} Database logging

{get_emoji('adder6')} {convert_font('Usage:', 'bold')}
• Use in group/channel with active voice chat
• Bot will join muted by default
• Check permissions if join fails
            """.strip()
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            
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
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
            
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
            buttons = [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
        
        # Check premium status
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(help_text)
            if entities:
                await event.edit(help_text, formatting_entities=entities, buttons=buttons)
                await event.answer()
                return
        
        # Fallback
        await event.edit(help_text, buttons=buttons)
        await event.answer()
        
    except Exception as e:
        await event.answer(f"Error: {str(e)}", alert=True)

# Plugin info
PLUGIN_INFO = {
    'name': 'help',
    'version': '1.0.2',
    'description': 'Comprehensive help system with premium emoji support',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['help'],
    'categories': ['basic', 'gcast', 'emoji', 'user', 'voice', 'manage', 'system']
}

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    """Setup function untuk register event handlers"""
    client.add_event_handler(help_handler, events.NewMessage(pattern=rf'\.help(\s+(.+))?'))
    client.add_event_handler(help_callback_handler, events.CallbackQuery(pattern=rb"help_(.+)"))
    
    # Set global client untuk functions yang membutuhkan
    globals()['client'] = client