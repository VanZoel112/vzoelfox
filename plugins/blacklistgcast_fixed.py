#!/usr/bin/env python3
"""
Blacklist GCast Plugin dengan Premium Emoji Support
File: plugins/blacklistgcast.py
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
import json
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError

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

# Blacklist file path
BLACKLIST_FILE = "gcast_blacklist.json"

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

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available"""
    try:
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

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

def load_blacklist():
    """Load blacklist from JSON file"""
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                # Convert blacklisted_chats list to set for compatibility
                if isinstance(data, dict) and 'blacklisted_chats' in data:
                    blacklist_data = {}
                    for chat_id in data['blacklisted_chats']:
                        blacklist_data[int(chat_id)] = {
                            'title': f'Chat {chat_id}',
                            'type': 'Unknown',
                            'added_date': datetime.now().isoformat(),
                            'added_by': 'legacy'
                        }
                    return blacklist_data
                # New format - dict with chat info
                elif isinstance(data, dict):
                    return {int(k): v for k, v in data.items() if k.lstrip('-').isdigit()}
        return {}
    except Exception as e:
        print(f"Error loading blacklist: {e}")
        return {}

def save_blacklist(blacklist):
    """Save blacklist to JSON file"""
    try:
        # Convert keys to string for JSON compatibility
        data = {str(k): v for k, v in blacklist.items()}
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving blacklist: {e}")
        return False

async def get_chat_info(chat_id):
    """Get chat title and type"""
    try:
        entity = await client.get_entity(chat_id)
        
        if isinstance(entity, Channel):
            chat_type = "Channel" if entity.broadcast else "Supergroup"
            title = entity.title
        elif isinstance(entity, Chat):
            chat_type = "Group"
            title = entity.title
        else:
            chat_type = "Unknown"
            title = str(chat_id)
            
        return {
            'title': title,
            'type': chat_type,
            'id': chat_id
        }
    except Exception:
        return {
            'title': f"Chat {chat_id}",
            'type': "Unknown",
            'id': chat_id
        }

def is_valid_chat_id(chat_id_str):
    """Validate chat ID format"""
    try:
        chat_id = int(chat_id_str)
        return True
    except ValueError:
        return False

# ADD BLACKLIST COMMAND
@client.on(events.NewMessage(pattern=r'\.addbl(\s+(.+))?'))
async def add_blacklist_handler(event):
    """Add chat to gcast blacklist"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        blacklist = load_blacklist()
        
        # If no argument provided, use current chat
        if not command_arg or not command_arg.strip():
            chat_id = event.chat_id
            source = "current chat"
        else:
            # Validate and parse chat ID
            chat_id_str = command_arg.strip()
            if not is_valid_chat_id(chat_id_str):
                error_text = f"""
{get_emoji('adder3')} {convert_font('INVALID CHAT ID', 'mono')}

{get_emoji('check')} Use valid chat ID format:
• Negative number for groups/channels
• Example: -1001234567890

{get_emoji('main')} Or use `{prefix}addbl` in target chat directly
                """.strip()
                await safe_send_with_entities(event, error_text)
                return
            
            chat_id = int(chat_id_str)
            source = "manual ID"
        
        # Check if already blacklisted
        if chat_id in blacklist:
            already_text = f"""
{get_emoji('adder1')} {convert_font('ALREADY BLACKLISTED', 'mono')}

{get_emoji('check')} Chat is already in gcast blacklist
{get_emoji('main')} Use `{prefix}listbl` to view all blacklisted chats
            """.strip()
            await safe_send_with_entities(event, already_text)
            return
        
        # Get chat information
        chat_info = await get_chat_info(chat_id)
        
        # Add to blacklist
        blacklist[chat_id] = {
            'title': chat_info['title'],
            'type': chat_info['type'],
            'added_date': datetime.now().isoformat(),
            'added_by': source
        }
        
        # Save to file
        if save_blacklist(blacklist):
            success_text = f"""
{get_emoji('adder2')} {convert_font('BLACKLIST ADDED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('GCAST PROTECTION ACTIVE', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Chat:', 'bold')} {convert_font(chat_info['title'], 'mono')}
{get_emoji('adder1')} {convert_font('Type:', 'bold')} {chat_info['type']}
{get_emoji('adder4')} {convert_font('ID:', 'bold')} {chat_id}
{get_emoji('adder5')} {convert_font('Added:', 'bold')} {datetime.now().strftime('%H:%M:%S')}

{get_emoji('adder6')} {convert_font('Protection Status:', 'bold')}
{get_emoji('check')} GCast messages will be blocked
{get_emoji('check')} Automatic filtering enabled
{get_emoji('check')} Persistent across bot restarts

{get_emoji('main')} Total blacklisted chats: {convert_font(str(len(blacklist)), 'bold')}
            """.strip()
            await safe_send_with_entities(event, success_text)
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('SAVE ERROR', 'mono')}

{get_emoji('check')} Failed to save blacklist to file
{get_emoji('main')} Check bot permissions and try again
            """.strip()
            await safe_send_with_entities(event, error_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# REMOVE BLACKLIST COMMAND
@client.on(events.NewMessage(pattern=r'\.rmbl(\s+(.+))?'))
async def remove_blacklist_handler(event):
    """Remove chat from gcast blacklist"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        blacklist = load_blacklist()
        
        # If no argument provided, use current chat
        if not command_arg or not command_arg.strip():
            chat_id = event.chat_id
        else:
            # Validate and parse chat ID
            chat_id_str = command_arg.strip()
            if not is_valid_chat_id(chat_id_str):
                error_text = f"""
{get_emoji('adder3')} {convert_font('INVALID CHAT ID', 'mono')}

{get_emoji('check')} Use valid chat ID format or use in target chat
{get_emoji('main')} Example: `{prefix}rmbl -1001234567890`
                """.strip()
                await safe_send_with_entities(event, error_text)
                return
            
            chat_id = int(chat_id_str)
        
        # Check if in blacklist
        if chat_id not in blacklist:
            not_found_text = f"""
{get_emoji('adder1')} {convert_font('NOT IN BLACKLIST', 'mono')}

{get_emoji('check')} Chat is not currently blacklisted
{get_emoji('main')} Use `{prefix}listbl` to view blacklisted chats
            """.strip()
            await safe_send_with_entities(event, not_found_text)
            return
        
        # Get chat info before removal
        chat_data = blacklist[chat_id]
        
        # Remove from blacklist
        del blacklist[chat_id]
        
        # Save to file
        if save_blacklist(blacklist):
            removed_text = f"""
{get_emoji('adder4')} {convert_font('BLACKLIST REMOVED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('GCAST ACCESS RESTORED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Chat:', 'bold')} {convert_font(chat_data['title'], 'mono')}
{get_emoji('adder2')} {convert_font('Type:', 'bold')} {chat_data['type']}
{get_emoji('adder3')} {convert_font('ID:', 'bold')} {chat_id}
{get_emoji('adder5')} {convert_font('Removed:', 'bold')} {datetime.now().strftime('%H:%M:%S')}

{get_emoji('adder6')} {convert_font('Access Status:', 'bold')}
{get_emoji('check')} GCast messages will be delivered
{get_emoji('check')} Chat unprotected from broadcasts
{get_emoji('check')} Changes saved permanently

{get_emoji('main')} Remaining blacklisted chats: {convert_font(str(len(blacklist)), 'bold')}
            """.strip()
            await safe_send_with_entities(event, removed_text)
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('SAVE ERROR', 'mono')}

{get_emoji('check')} Failed to save changes to file
{get_emoji('main')} Check bot permissions and try again
            """.strip()
            await safe_send_with_entities(event, error_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# LIST BLACKLIST COMMAND
@client.on(events.NewMessage(pattern=r'\.listbl'))
async def list_blacklist_handler(event):
    """Show all blacklisted chats"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        blacklist = load_blacklist()
        prefix = get_prefix()
        
        if not blacklist:
            empty_text = f"""
{get_emoji('check')} {convert_font('GCAST BLACKLIST', 'mono')}

{get_emoji('main')} No chats are currently blacklisted
{get_emoji('adder1')} All groups/channels will receive gcast

{get_emoji('adder2')} {convert_font('Commands:', 'bold')}
• `{prefix}addbl` - Add current chat to blacklist
• `{prefix}addbl <chat_id>` - Add specific chat
            """.strip()
            await safe_send_with_entities(event, empty_text)
            return
        
        # Create list with pagination if needed
        list_text = f"""
{get_emoji('adder6')} {convert_font('GCAST BLACKLIST', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('PROTECTED CHATS LIST', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Total Blacklisted:', 'bold')} {len(blacklist)} chats

"""
        
        # Show up to 15 chats to avoid message limit
        count = 0
        for chat_id, data in list(blacklist.items())[:15]:
            count += 1
            title = data.get('title', f'Chat {chat_id}')[:25]  # Limit title length
            chat_type = data.get('type', 'Unknown')
            added_date = datetime.fromisoformat(data.get('added_date', datetime.now().isoformat()))
            
            list_text += f"""
{get_emoji('adder1')} {convert_font(f'#{count}', 'bold')} {convert_font(title, 'mono')}
{get_emoji('adder2')} {convert_font('Type:', 'mono')} {chat_type} | {convert_font('ID:', 'mono')} {chat_id}
{get_emoji('adder4')} {convert_font('Added:', 'mono')} {added_date.strftime('%m/%d %H:%M')}

"""
        
        if len(blacklist) > 15:
            list_text += f"{get_emoji('adder5')} ... and {len(blacklist) - 15} more chats\n\n"
        
        list_text += f"""
{get_emoji('adder3')} {convert_font('Management:', 'bold')}
• `{prefix}rmbl <chat_id>` - Remove from blacklist
• `{prefix}clearbl confirm` - Clear all blacklist
• `{prefix}addbl` - Add current chat
        """.strip()
        
        await safe_send_with_entities(event, list_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# CLEAR BLACKLIST COMMAND
@client.on(events.NewMessage(pattern=r'\.clearbl(\s+(.+))?'))
async def clear_blacklist_handler(event):
    """Clear all blacklisted chats (with confirmation)"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        blacklist = load_blacklist()
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        
        if not blacklist:
            empty_text = f"""
{get_emoji('check')} {convert_font('BLACKLIST STATUS', 'mono')}

{get_emoji('main')} Blacklist is already empty
{get_emoji('adder1')} No chats to clear
            """.strip()
            await safe_send_with_entities(event, empty_text)
            return
        
        # Check if confirmation provided
        if command_arg and 'confirm' in command_arg.lower():
            # Clear the blacklist
            empty_blacklist = {}
            
            if save_blacklist(empty_blacklist):
                cleared_text = f"""
{get_emoji('adder4')} {convert_font('BLACKLIST CLEARED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('ALL RESTRICTIONS REMOVED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Cleared:', 'bold')} {len(blacklist)} chats
{get_emoji('adder2')} {convert_font('Status:', 'bold')} All chats can receive gcast
{get_emoji('adder6')} {convert_font('Time:', 'bold')} {datetime.now().strftime('%H:%M:%S')}

{get_emoji('main')} {convert_font('Blacklist is now empty', 'bold')}
{get_emoji('adder1')} Use `{prefix}addbl` to add protection again
                """.strip()
                await safe_send_with_entities(event, cleared_text)
            else:
                error_text = f"""
{get_emoji('adder3')} {convert_font('CLEAR ERROR', 'mono')}

{get_emoji('check')} Failed to save changes
{get_emoji('main')} Check permissions and try again
                """.strip()
                await safe_send_with_entities(event, error_text)
        else:
            # Show confirmation request
            confirmation_text = f"""
{get_emoji('adder3')} {convert_font('CLEAR CONFIRMATION REQUIRED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('DANGER ZONE', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('This will remove ALL', 'bold')} {len(blacklist)} {convert_font('blacklisted chats', 'bold')}
{get_emoji('adder2')} {convert_font('All chats will receive gcast again', 'bold')}
{get_emoji('adder5')} {convert_font('This action cannot be undone', 'bold')}

{get_emoji('check')} Send `{prefix}clearbl confirm` to proceed
{get_emoji('main')} Or use `{prefix}listbl` to review first
            """.strip()
            await safe_send_with_entities(event, confirmation_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# Plugin info
PLUGIN_INFO = {
    'name': 'blacklistgcast',
    'version': '1.0.1',
    'description': 'Gcast blacklist management with premium emoji support',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['addbl', 'rmbl', 'listbl', 'clearbl'],
    'features': ['blacklist_management', 'gcast_protection', 'premium_emojis']
}

def get_plugin_info():
    return PLUGIN_INFO