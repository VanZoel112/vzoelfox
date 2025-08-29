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

# ===== Plugin Info (Untuk plugin loader) =====
PLUGIN_INFO = {
    "name": "blacklistgcast_fixed",
    "version": "1.1.0",
    "description": "GCast blacklist management with assetjson environment integration",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".addbl", ".rmbl", ".listbl", ".clearbl"],
    "features": ["blacklist management", "gcast protection", "premium emojis", "env integration"]
}

# Import assetjson environment
try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None
client = None

# Blacklist file path
BLACKLIST_FILE = "gcast_blacklist.json"

# Helper functions with assetjson environment integration
async def safe_send_message(event, text, use_env=True):
    """Helper function to safely send messages with or without env"""
    if use_env and env and 'safe_send_with_entities' in env:
        await env['safe_send_with_entities'](event, text)
    else:
        await event.reply(text)

def safe_safe_get_emoji(emoji_type):
    """Helper function to safely get emoji with fallback"""
    if env and 'get_emoji' in env:
        return env['get_emoji'](emoji_type)
    emoji_fallbacks = {
        'main': '🤩', 'check': '⚙️', 'adder1': '⛈', 'adder2': '✅', 
        'adder3': '👽', 'adder4': '✈️', 'adder5': '😈', 'adder6': '🎚️'
    }
    return emoji_fallbacks.get(emoji_type, '🤩')

def safe_safe_convert_font(text, font_type='bold'):
    """Helper function to safely convert fonts with fallback"""
    if env and 'convert_font' in env:
        return env['convert_font'](text, font_type)
    return text

async def is_owner_check(user_id):
    """Check if user is owner with env integration"""
    # Check if env is properly initialized and has is_owner function
    if env and 'is_owner' in env:
        try:
            return await env['is_owner'](user_id)
        except Exception:
            pass
    
    # Fallback to manual check
    try:
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

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
{safe_safe_get_emoji('adder3')} {safe_safe_convert_font('INVALID CHAT ID', 'mono')}

{safe_safe_get_emoji('check')} Use valid chat ID format:
• Negative number for groups/channels
• Example: -1001234567890

{safe_safe_get_emoji('main')} Or use `{prefix}addbl` in target chat directly
                """.strip()
                await safe_send_message(event, error_text)
                return
            
            chat_id = int(chat_id_str)
            source = "manual ID"
        
        # Check if already blacklisted
        if chat_id in blacklist:
            already_text = f"""
{safe_get_emoji('adder1')} {safe_convert_font('ALREADY BLACKLISTED', 'mono')}

{safe_get_emoji('check')} Chat is already in gcast blacklist
{safe_get_emoji('main')} Use `{prefix}listbl` to view all blacklisted chats
            """.strip()
            await safe_send_message(event, already_text)
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
{safe_get_emoji('adder2')} {safe_convert_font('BLACKLIST ADDED', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('GCAST PROTECTION ACTIVE', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Chat:', 'bold')} {safe_convert_font(chat_info['title'], 'mono')}
{safe_get_emoji('adder1')} {safe_convert_font('Type:', 'bold')} {chat_info['type']}
{safe_get_emoji('adder4')} {safe_convert_font('ID:', 'bold')} {chat_id}
{safe_get_emoji('adder5')} {safe_convert_font('Added:', 'bold')} {datetime.now().strftime('%H:%M:%S')}

{safe_get_emoji('adder6')} {safe_convert_font('Protection Status:', 'bold')}
{safe_get_emoji('check')} GCast messages will be blocked
{safe_get_emoji('check')} Automatic filtering enabled
{safe_get_emoji('check')} Persistent across bot restarts

{safe_get_emoji('main')} Total blacklisted chats: {safe_convert_font(str(len(blacklist)), 'bold')}
            """.strip()
            await safe_send_message(event, success_text)
        else:
            error_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('SAVE ERROR', 'mono')}

{safe_get_emoji('check')} Failed to save blacklist to file
{safe_get_emoji('main')} Check bot permissions and try again
            """.strip()
            await safe_send_message(event, error_text)
        
    except Exception as e:
        await safe_send_message(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# REMOVE BLACKLIST COMMAND
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
{safe_get_emoji('adder3')} {safe_convert_font('INVALID CHAT ID', 'mono')}

{safe_get_emoji('check')} Use valid chat ID format or use in target chat
{safe_get_emoji('main')} Example: `{prefix}rmbl -1001234567890`
                """.strip()
                await safe_send_message(event, error_text)
                return
            
            chat_id = int(chat_id_str)
        
        # Check if in blacklist
        if chat_id not in blacklist:
            not_found_text = f"""
{safe_get_emoji('adder1')} {safe_convert_font('NOT IN BLACKLIST', 'mono')}

{safe_get_emoji('check')} Chat is not currently blacklisted
{safe_get_emoji('main')} Use `{prefix}listbl` to view blacklisted chats
            """.strip()
            await safe_send_message(event, not_found_text)
            return
        
        # Get chat info before removal
        chat_data = blacklist[chat_id]
        
        # Remove from blacklist
        del blacklist[chat_id]
        
        # Save to file
        if save_blacklist(blacklist):
            removed_text = f"""
{safe_get_emoji('adder4')} {safe_convert_font('BLACKLIST REMOVED', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('GCAST ACCESS RESTORED', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Chat:', 'bold')} {safe_convert_font(chat_data['title'], 'mono')}
{safe_get_emoji('adder2')} {safe_convert_font('Type:', 'bold')} {chat_data['type']}
{safe_get_emoji('adder3')} {safe_convert_font('ID:', 'bold')} {chat_id}
{safe_get_emoji('adder5')} {safe_convert_font('Removed:', 'bold')} {datetime.now().strftime('%H:%M:%S')}

{safe_get_emoji('adder6')} {safe_convert_font('Access Status:', 'bold')}
{safe_get_emoji('check')} GCast messages will be delivered
{safe_get_emoji('check')} Chat unprotected from broadcasts
{safe_get_emoji('check')} Changes saved permanently

{safe_get_emoji('main')} Remaining blacklisted chats: {safe_convert_font(str(len(blacklist)), 'bold')}
            """.strip()
            await safe_send_message(event, removed_text)
        else:
            error_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('SAVE ERROR', 'mono')}

{safe_get_emoji('check')} Failed to save changes to file
{safe_get_emoji('main')} Check bot permissions and try again
            """.strip()
            await safe_send_message(event, error_text)
        
    except Exception as e:
        await safe_send_message(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# LIST BLACKLIST COMMAND
async def list_blacklist_handler(event):
    """Show all blacklisted chats"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        blacklist = load_blacklist()
        prefix = get_prefix()
        
        if not blacklist:
            empty_text = f"""
{safe_get_emoji('check')} {safe_convert_font('GCAST BLACKLIST', 'mono')}

{safe_get_emoji('main')} No chats are currently blacklisted
{safe_get_emoji('adder1')} All groups/channels will receive gcast

{safe_get_emoji('adder2')} {safe_convert_font('Commands:', 'bold')}
• `{prefix}addbl` - Add current chat to blacklist
• `{prefix}addbl <chat_id>` - Add specific chat
            """.strip()
            await safe_send_message(event, empty_text)
            return
        
        # Create list with pagination if needed
        list_text = f"""
{safe_get_emoji('adder6')} {safe_convert_font('GCAST BLACKLIST', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('PROTECTED CHATS LIST', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Total Blacklisted:', 'bold')} {len(blacklist)} chats

"""
        
        # Show up to 15 chats to avoid message limit
        count = 0
        for chat_id, data in list(blacklist.items())[:15]:
            count += 1
            title = data.get('title', f'Chat {chat_id}')[:25]  # Limit title length
            chat_type = data.get('type', 'Unknown')
            added_date = datetime.fromisoformat(data.get('added_date', datetime.now().isoformat()))
            
            list_text += f"""
{safe_get_emoji('adder1')} {safe_convert_font(f'#{count}', 'bold')} {safe_convert_font(title, 'mono')}
{safe_get_emoji('adder2')} {safe_convert_font('Type:', 'mono')} {chat_type} | {safe_convert_font('ID:', 'mono')} {chat_id}
{safe_get_emoji('adder4')} {safe_convert_font('Added:', 'mono')} {added_date.strftime('%m/%d %H:%M')}

"""
        
        if len(blacklist) > 15:
            list_text += f"{safe_get_emoji('adder5')} ... and {len(blacklist) - 15} more chats\n\n"
        
        list_text += f"""
{safe_get_emoji('adder3')} {safe_convert_font('Management:', 'bold')}
• `{prefix}rmbl <chat_id>` - Remove from blacklist
• `{prefix}clearbl confirm` - Clear all blacklist
• `{prefix}addbl` - Add current chat
        """.strip()
        
        await safe_send_message(event, list_text)
        
    except Exception as e:
        await safe_send_message(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# CLEAR BLACKLIST COMMAND
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
{safe_get_emoji('check')} {safe_convert_font('BLACKLIST STATUS', 'mono')}

{safe_get_emoji('main')} Blacklist is already empty
{safe_get_emoji('adder1')} No chats to clear
            """.strip()
            await safe_send_message(event, empty_text)
            return
        
        # Check if confirmation provided
        if command_arg and 'confirm' in command_arg.lower():
            # Clear the blacklist
            empty_blacklist = {}
            
            if save_blacklist(empty_blacklist):
                cleared_text = f"""
{safe_get_emoji('adder4')} {safe_convert_font('BLACKLIST CLEARED', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('ALL RESTRICTIONS REMOVED', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Cleared:', 'bold')} {len(blacklist)} chats
{safe_get_emoji('adder2')} {safe_convert_font('Status:', 'bold')} All chats can receive gcast
{safe_get_emoji('adder6')} {safe_convert_font('Time:', 'bold')} {datetime.now().strftime('%H:%M:%S')}

{safe_get_emoji('main')} {safe_convert_font('Blacklist is now empty', 'bold')}
{safe_get_emoji('adder1')} Use `{prefix}addbl` to add protection again
                """.strip()
                await safe_send_message(event, cleared_text)
            else:
                error_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('CLEAR ERROR', 'mono')}

{safe_get_emoji('check')} Failed to save changes
{safe_get_emoji('main')} Check permissions and try again
                """.strip()
                await safe_send_message(event, error_text)
        else:
            # Show confirmation request
            confirmation_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('CLEAR CONFIRMATION REQUIRED', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('DANGER ZONE', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('adder1')} {safe_convert_font('This will remove ALL', 'bold')} {len(blacklist)} {safe_convert_font('blacklisted chats', 'bold')}
{safe_get_emoji('adder2')} {safe_convert_font('All chats will receive gcast again', 'bold')}
{safe_get_emoji('adder5')} {safe_convert_font('This action cannot be undone', 'bold')}

{safe_get_emoji('check')} Send `{prefix}clearbl confirm` to proceed
{safe_get_emoji('main')} Or use `{prefix}listbl` to review first
            """.strip()
            await safe_send_message(event, confirmation_text)
        
    except Exception as e:
        await safe_send_message(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client, env
    client = client_instance
    
    # Create plugin environment
    env = create_plugin_environment(client)
    
    # Register event handlers
    client.add_event_handler(add_blacklist_handler, events.NewMessage(pattern=r"\.addbl(\s+(.+))?"))
    client.add_event_handler(remove_blacklist_handler, events.NewMessage(pattern=r"\.rmbl(\s+(.+))?"))
    client.add_event_handler(list_blacklist_handler, events.NewMessage(pattern=r"\.listbl"))
    client.add_event_handler(clear_blacklist_handler, events.NewMessage(pattern=r"\.clearbl(\s+(.+))?"))
    
    print(f"✅ [GCast Blacklist] Plugin loaded with assetjson environment v{PLUGIN_INFO['version']}")