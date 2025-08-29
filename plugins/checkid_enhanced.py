"""
Enhanced Check ID Plugin - Standalone Premium Emoji
File: plugins/checkid_enhanced.py
Author: Morgan (Vzoel Fox's Assistant)
Version: 2.0.0
Fitur: Cek ID user dengan username/reply, premium emojis hardcoded
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User, Chat, Channel
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError
import re

# Import database helper
try:
    from database import create_table, insert, select, get_owner_id
except ImportError:
    print("[CheckID Enhanced] Database helper not found, using fallback")
    create_table = None
    insert = None
    select = None
    get_owner_id = lambda: 0

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "checkid_enhanced",
    "version": "2.0.0",
    "description": "Enhanced check ID with premium emojis and database logging",
    "author": "Morgan (Vzoel Fox's Assistant)",
    "commands": [".id", ".userid", ".checkid"],
    "features": ["check user id", "username lookup", "reply support", "premium emojis", "database logging"]
}

# ===== PREMIUM EMOJI CONFIGURATION (STANDALONE) =====
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

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
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

async def safe_send_premium(event, text):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception:
        await event.reply(text)

import os
async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        # Get owner ID from environment (primary method)
        OWNER_ID = os.getenv('OWNER_ID')
        if OWNER_ID:
            return user_id == int(OWNER_ID)
        
        # Fallback: check if user is the bot itself
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

# Global client reference
client = None

def init_checkid_database():
    """Initialize CheckID database table"""
    if create_table:
        schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL,
            requester_username TEXT,
            target_id INTEGER,
            target_username TEXT,
            target_first_name TEXT,
            target_last_name TEXT,
            lookup_type TEXT,
            lookup_value TEXT,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        create_table('checkid_logs', schema, 'main')
        return True
    return False

def save_checkid_log(requester_id, requester_username, target_data, lookup_type, lookup_value, success, error_msg=None):
    """Save checkid operation to database"""
    try:
        if not insert:
            return False
        
        log_data = {
            'requester_id': requester_id,
            'requester_username': requester_username,
            'target_id': target_data.get('id') if target_data else None,
            'target_username': target_data.get('username') if target_data else None,
            'target_first_name': target_data.get('first_name') if target_data else None,
            'target_last_name': target_data.get('last_name') if target_data else None,
            'lookup_type': lookup_type,
            'lookup_value': lookup_value,
            'success': success,
            'error_message': error_msg
        }
        
        result = insert('checkid_logs', log_data, 'main')
        return result is not None
    except Exception as e:
        print(f"[CheckID Enhanced] Log save error: {e}")
        return False

def format_user_info(user_data, lookup_type, lookup_value):
    """Format user information with premium emojis"""
    try:
        user_id = user_data.get('id', 'Unknown')
        first_name = user_data.get('first_name', 'Unknown')
        last_name = user_data.get('last_name', '')
        username = user_data.get('username', 'None')
        is_bot = user_data.get('is_bot', False)
        is_premium = user_data.get('is_premium', False)
        is_verified = user_data.get('is_verified', False)
        is_scam = user_data.get('is_scam', False)
        is_fake = user_data.get('is_fake', False)
        phone = user_data.get('phone', 'Hidden')
        
        # Build full name
        full_name = first_name
        if last_name:
            full_name += f" {last_name}"
        
        # Status indicators
        status_indicators = []
        if is_bot:
            status_indicators.append(f"{get_emoji('adder6')} Bot")
        if is_premium:
            status_indicators.append(f"{get_emoji('main')} Premium")
        if is_verified:
            status_indicators.append(f"{get_emoji('adder2')} Verified")
        if is_scam:
            status_indicators.append(f"{get_emoji('adder5')} Scam")
        if is_fake:
            status_indicators.append(f"{get_emoji('adder5')} Fake")
        
        status_text = " | ".join(status_indicators) if status_indicators else f"{get_emoji('adder4')} Regular User"
        
        # Format response
        report = f"""
{get_emoji('main')} **User Information Found!**

{get_emoji('check')} **Details:**
• **Name:** {full_name}
• **Username:** @{username}
• **User ID:** `{user_id}`
• **Phone:** {phone}

{get_emoji('adder3')} **Status:**
{status_text}

{get_emoji('adder1')} **Lookup Info:**
• **Method:** {lookup_type}
• **Query:** {lookup_value}
• **Time:** {datetime.now().strftime('%H:%M:%S')}

{get_emoji('adder2')} **Enhanced CheckID v2.0**
        """.strip()
        
        return report
        
    except Exception as e:
        return f"{get_emoji('adder5')} **Error formatting user info:** {str(e)}"

async def get_user_from_username(client, username):
    """Get user entity from username"""
    try:
        # Clean username
        username = username.replace('@', '').replace('https://t.me/', '').replace('t.me/', '')
        
        # Get user entity
        user_entity = await client.get_entity(username)
        
        if isinstance(user_entity, User):
            return {
                'id': user_entity.id,
                'first_name': user_entity.first_name or 'Unknown',
                'last_name': user_entity.last_name or '',
                'username': user_entity.username or 'None',
                'is_bot': user_entity.bot,
                'is_premium': getattr(user_entity, 'premium', False),
                'is_verified': getattr(user_entity, 'verified', False),
                'is_scam': getattr(user_entity, 'scam', False),
                'is_fake': getattr(user_entity, 'fake', False),
                'phone': getattr(user_entity, 'phone', 'Hidden')
            }
        else:
            return None
            
    except (UsernameNotOccupiedError, UsernameInvalidError):
        return None
    except Exception as e:
        print(f"[CheckID Enhanced] Username lookup error: {e}")
        return None

async def get_user_from_reply(event):
    """Get user data from replied message"""
    try:
        if not event.is_reply:
            return None
            
        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.sender:
            return None
        
        sender = replied_msg.sender
        
        if isinstance(sender, User):
            return {
                'id': sender.id,
                'first_name': sender.first_name or 'Unknown',
                'last_name': sender.last_name or '',
                'username': sender.username or 'None',
                'is_bot': sender.bot,
                'is_premium': getattr(sender, 'premium', False),
                'is_verified': getattr(sender, 'verified', False),
                'is_scam': getattr(sender, 'scam', False),
                'is_fake': getattr(sender, 'fake', False),
                'phone': getattr(sender, 'phone', 'Hidden')
            }
        else:
            return None
            
    except Exception as e:
        print(f"[CheckID Enhanced] Reply lookup error: {e}")
        return None

async def checkid_handler(event):
    """Enhanced checkid handler - supports username, reply, and direct ID"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        # Get requester info
        requester = await client.get_me()  # Bot itself since only owner can use
        requester_username = getattr(requester, 'username', 'None')
        
        # Parse command and arguments
        message_text = event.message.text or ""
        parts = message_text.split()
        
        user_data = None
        lookup_type = "unknown"
        lookup_value = ""
        error_msg = None
        
        # Method 1: Check if it's a reply
        if event.is_reply:
            user_data = await get_user_from_reply(event)
            if user_data:
                lookup_type = "reply"
                lookup_value = "replied message"
        
        # Method 2: Check if username/ID provided in command
        elif len(parts) > 1:
            target = parts[1].strip()
            
            # Check if it's a user ID (numeric)
            if target.isdigit():
                try:
                    user_id = int(target)
                    user_entity = await client.get_entity(user_id)
                    
                    if isinstance(user_entity, User):
                        user_data = {
                            'id': user_entity.id,
                            'first_name': user_entity.first_name or 'Unknown',
                            'last_name': user_entity.last_name or '',
                            'username': user_entity.username or 'None',
                            'is_bot': user_entity.bot,
                            'is_premium': getattr(user_entity, 'premium', False),
                            'is_verified': getattr(user_entity, 'verified', False),
                            'is_scam': getattr(user_entity, 'scam', False),
                            'is_fake': getattr(user_entity, 'fake', False),
                            'phone': getattr(user_entity, 'phone', 'Hidden')
                        }
                        lookup_type = "user_id"
                        lookup_value = target
                        
                except Exception as e:
                    error_msg = f"Invalid user ID: {target}"
                    
            # Check if it's a username
            else:
                user_data = await get_user_from_username(client, target)
                if user_data:
                    lookup_type = "username"
                    lookup_value = target
                else:
                    error_msg = f"Username not found: {target}"
        
        # Method 3: No arguments - show current user (self)
        else:
            current_user = await client.get_me()
            user_data = {
                'id': current_user.id,
                'first_name': current_user.first_name or 'Unknown',
                'last_name': current_user.last_name or '',
                'username': current_user.username or 'None',
                'is_bot': current_user.bot,
                'is_premium': getattr(current_user, 'premium', False),
                'is_verified': getattr(current_user, 'verified', False),
                'is_scam': getattr(current_user, 'scam', False),
                'is_fake': getattr(current_user, 'fake', False),
                'phone': getattr(current_user, 'phone', 'Hidden')
            }
            lookup_type = "self"
            lookup_value = "current user"
        
        # Generate response
        if user_data:
            response = format_user_info(user_data, lookup_type, lookup_value)
            success = True
        else:
            response = f"""
{get_emoji('adder5')} **User Not Found**

{get_emoji('check')} **Error Details:**
• **Lookup:** {lookup_type}
• **Query:** {lookup_value}
• **Error:** {error_msg or "User not found or inaccessible"}

{get_emoji('adder4')} **Usage:**
• `.id` - Check your own ID
• `.id @username` - Check by username
• `.id 123456789` - Check by user ID
• `.id` (reply) - Check replied user

{get_emoji('main')} **Enhanced CheckID v2.0**
            """.strip()
            success = False
        
        # Send response
        await safe_send_premium(event, response)
        
        # Log to database
        save_checkid_log(
            event.sender_id, 
            requester_username, 
            user_data if success else None,
            lookup_type, 
            lookup_value, 
            success, 
            error_msg
        )
        
    except Exception as e:
        error_response = f"""
{get_emoji('adder5')} **CheckID Error**

{get_emoji('check')} **Error Details:**
• **Error:** {str(e)}
• **Time:** {datetime.now().strftime('%H:%M:%S')}

{get_emoji('adder4')} **Try:**
• Check username spelling
• Ensure user exists
• Try with user ID instead

{get_emoji('main')} **Enhanced CheckID v2.0**
        """.strip()
        
        await safe_send_premium(event, error_response)
        
        # Log error
        save_checkid_log(
            event.sender_id,
            getattr(await client.get_me(), 'username', 'None'),
            None,
            "error",
            message_text,
            False,
            str(e)
        )

def get_plugin_info():
    return PLUGIN_INFO

async def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Initialize database
    init_checkid_database()
    
    # Register handlers for multiple commands
    client.add_event_handler(checkid_handler, events.NewMessage(pattern=r"\.id(\s|$)"))
    client.add_event_handler(checkid_handler, events.NewMessage(pattern=r"\.userid(\s|$)"))
    client.add_event_handler(checkid_handler, events.NewMessage(pattern=r"\.checkid(\s|$)"))
    
    print(f"✅ [CheckID Enhanced] Plugin loaded - Premium emoji user ID checker v{PLUGIN_INFO['version']}")