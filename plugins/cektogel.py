#!/usr/bin/env python3
"""
Cek Togel User Info Plugin dengan Premium Emoji Support
File: plugins/cektogel.py
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
import json
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User, UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth, UserStatusEmpty
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import UserNotMutualContactError, UserPrivacyRestrictedError, FloodWaitError

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

# Cache for user info to avoid repeated API calls
user_cache = {}
CACHE_DURATION = 300  # 5 minutes

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

def format_status(status):
    """Format user online status"""
    if isinstance(status, UserStatusOnline):
        return f"{get_emoji('adder2')} Online"
    elif isinstance(status, UserStatusRecently):
        return f"{get_emoji('adder1')} Recently (within 3 days)"
    elif isinstance(status, UserStatusLastWeek):
        return f"{get_emoji('adder3')} Last week"
    elif isinstance(status, UserStatusLastMonth):
        return f"{get_emoji('adder4')} Last month"
    elif isinstance(status, UserStatusOffline):
        if hasattr(status, 'was_online'):
            return f"{get_emoji('adder5')} Offline since {status.was_online.strftime('%m/%d %H:%M')}"
        return f"{get_emoji('adder5')} Offline"
    else:
        return f"{get_emoji('adder6')} Unknown"

def mask_phone(phone):
    """Mask phone number for privacy"""
    if not phone:
        return "Not visible"
    
    # Mask middle digits: +1234***89
    if len(phone) > 6:
        return f"{phone[:4]}***{phone[-2:]}"
    return phone

async def get_user_from_text(event, text):
    """Extract user from reply or text input"""
    try:
        # Check if replying to a message
        if event.reply_to_msg_id:
            reply_msg = await event.get_reply_message()
            if reply_msg and reply_msg.sender_id:
                return await client.get_entity(reply_msg.sender_id)
        
        # Check if text contains username or user ID
        if text:
            text = text.strip()
            
            # Username format (@username)
            if text.startswith('@'):
                username = text[1:]  # Remove @
                return await client.get_entity(username)
            
            # User ID format (numbers)
            elif text.isdigit():
                user_id = int(text)
                return await client.get_entity(user_id)
            
            # Plain username (without @)
            else:
                return await client.get_entity(text)
        
        return None
    except Exception as e:
        raise e

async def get_detailed_user_info(user):
    """Get detailed user information"""
    try:
        # Check cache first
        cache_key = f"user_{user.id}"
        current_time = datetime.now().timestamp()
        
        if cache_key in user_cache:
            cached_data, cache_time = user_cache[cache_key]
            if current_time - cache_time < CACHE_DURATION:
                return cached_data
        
        # Get full user info
        try:
            full_user = await client(GetFullUserRequest(user))
            user_full = full_user.full_user
            user_data = full_user.users[0]
        except Exception:
            # Fallback to basic user info
            user_full = None
            user_data = user
        
        # Compile user information
        info = {
            'id': user.id,
            'first_name': getattr(user, 'first_name', None),
            'last_name': getattr(user, 'last_name', None),
            'username': getattr(user, 'username', None),
            'phone': getattr(user, 'phone', None),
            'is_premium': getattr(user, 'premium', False),
            'is_verified': getattr(user, 'verified', False),
            'is_bot': getattr(user, 'bot', False),
            'is_scam': getattr(user, 'scam', False),
            'is_fake': getattr(user, 'fake', False),
            'is_restricted': getattr(user, 'restricted', False),
            'status': getattr(user, 'status', None),
            'lang_code': getattr(user, 'lang_code', None),
        }
        
        # Additional info from full user if available
        if user_full:
            info.update({
                'about': getattr(user_full, 'about', None),
                'common_chats_count': getattr(user_full, 'common_chats_count', 0),
                'blocked': getattr(user_full, 'blocked', False),
                'can_pin_message': getattr(user_full, 'can_pin_message', False),
            })
        
        # Cache the result
        user_cache[cache_key] = (info, current_time)
        
        return info
        
    except Exception as e:
        raise e

def generate_login_suggestion(user_info):
    """Generate login information suggestion"""
    suggestions = []
    
    # Phone number
    if user_info.get('phone'):
        suggestions.append(f"Phone: +{user_info['phone']}")
    
    # Username
    if user_info.get('username'):
        suggestions.append(f"Username: @{user_info['username']}")
    
    # Email suggestion based on name/username
    if user_info.get('first_name') or user_info.get('username'):
        base_name = user_info.get('username') or user_info.get('first_name', '').lower()
        if base_name:
            suggestions.append(f"Possible Email: {base_name}@gmail.com")
            suggestions.append(f"Possible Email: {base_name}@yahoo.com")
    
    return suggestions

# MAIN CEK TOGEL COMMAND
@client.on(events.NewMessage(pattern=r'\.cektogel(\s+(.+))?'))
async def cek_togel_handler(event):
    """Cek informasi user untuk keperluan togel/login"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        
        # Get user from reply or text
        try:
            user = await get_user_from_text(event, command_arg)
        except Exception as e:
            error_text = f"""
{get_emoji('adder3')} {convert_font('USER NOT FOUND', 'mono')}

{get_emoji('check')} Could not find user: {str(e)}

{get_emoji('main')} {convert_font('Usage Examples:', 'bold')}
• Reply to user message + `{prefix}cektogel`
• `{prefix}cektogel @username`
• `{prefix}cektogel 123456789` (User ID)
• `{prefix}cektogel username` (without @)
            """.strip()
            await safe_send_with_entities(event, error_text)
            return
        
        if not user:
            usage_text = f"""
{get_emoji('adder1')} {convert_font('CEK TOGEL USAGE', 'mono')}

{get_emoji('check')} {convert_font('How to use:', 'bold')}
• Reply to any message + `{prefix}cektogel`
• `{prefix}cektogel @username`
• `{prefix}cektogel 123456789`
• `{prefix}cektogel username`

{get_emoji('main')} {convert_font('This will show:', 'bold')}
{get_emoji('adder2')} User ID & Name
{get_emoji('adder4')} Username & Phone
{get_emoji('adder5')} Login suggestions
            """.strip()
            await safe_send_with_entities(event, usage_text)
            return
        
        # Show loading message
        loading_msg = await event.reply(f"{get_emoji('main')} {convert_font('Loading user information...', 'mono')}")
        
        try:
            # Get detailed user info
            user_info = await get_detailed_user_info(user)
            
            # Delete loading message
            await loading_msg.delete()
            
            # Format full name
            full_name = ""
            if user_info.get('first_name'):
                full_name += user_info['first_name']
            if user_info.get('last_name'):
                full_name += f" {user_info['last_name']}"
            if not full_name:
                full_name = "No name set"
            
            # Format username
            username_display = f"@{user_info['username']}" if user_info.get('username') else "No username"
            
            # Format phone
            phone_display = f"+{user_info['phone']}" if user_info.get('phone') else "Not visible/Private"
            phone_masked = mask_phone(user_info.get('phone'))
            
            # Generate login suggestions
            login_suggestions = generate_login_suggestion(user_info)
            
            # Account flags
            flags = []
            if user_info.get('is_premium'):
                flags.append(f"{get_emoji('main')} Premium")
            if user_info.get('is_verified'):
                flags.append(f"{get_emoji('adder2')} Verified")
            if user_info.get('is_bot'):
                flags.append(f"{get_emoji('adder6')} Bot")
            if user_info.get('is_scam'):
                flags.append(f"{get_emoji('adder3')} Scam")
            if user_info.get('is_fake'):
                flags.append(f"{get_emoji('adder5')} Fake")
            
            # Build main info
            info_text = f"""
{get_emoji('main')} {convert_font('CEK TOGEL RESULT', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder1')} {convert_font('USER INFORMATION', 'mono')} {get_emoji('adder1')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Full Name:', 'bold')} {convert_font(full_name, 'mono')}
{get_emoji('adder2')} {convert_font('User ID:', 'bold')} {convert_font(str(user_info['id']), 'mono')}
{get_emoji('adder4')} {convert_font('Username:', 'bold')} {convert_font(username_display, 'mono')}
{get_emoji('adder5')} {convert_font('Phone Number:', 'bold')} {convert_font(phone_masked, 'mono')}

{get_emoji('adder6')} {convert_font('Account Status:', 'bold')}
""" + (f"{format_status(user_info.get('status'))}\n" if user_info.get('status') else f"{get_emoji('adder3')} Status unknown\n")

            # Add flags if any
            if flags:
                info_text += f"""
{get_emoji('adder3')} {convert_font('Account Flags:', 'bold')}
""" + "\n".join(flags) + "\n"
            
            # Add login suggestions
            info_text += f"""
╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('LOGIN SUGGESTIONS', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

"""
            
            if login_suggestions:
                for i, suggestion in enumerate(login_suggestions, 1):
                    info_text += f"{get_emoji('adder' + str(min(i, 6)))} {convert_font(suggestion, 'mono')}\n"
            else:
                info_text += f"{get_emoji('adder3')} {convert_font('Limited login information available', 'mono')}\n"
            
            # Add additional info if available
            if user_info.get('about'):
                info_text += f"""
{get_emoji('adder6')} {convert_font('Bio:', 'bold')} {user_info['about'][:50]}{'...' if len(user_info.get('about', '')) > 50 else ''}
"""
            
            if user_info.get('common_chats_count', 0) > 0:
                info_text += f"{get_emoji('adder2')} {convert_font('Common Groups:', 'bold')} {user_info['common_chats_count']}\n"
            
            # Privacy warning
            info_text += f"""
╔══════════════════════════════════╗
   {get_emoji('adder3')} {convert_font('PRIVACY NOTE', 'mono')} {get_emoji('adder3')}
╚══════════════════════════════════╝

{get_emoji('check')} Phone numbers are masked for privacy
{get_emoji('adder1')} Only public information is shown
{get_emoji('adder5')} Use responsibly and ethically

{get_emoji('main')} {convert_font('Checked at:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            await safe_send_with_entities(event, info_text)
            
        except FloodWaitError as e:
            await loading_msg.delete()
            flood_text = f"""
{get_emoji('adder3')} {convert_font('RATE LIMIT', 'mono')}

{get_emoji('check')} Please wait {e.seconds} seconds before next check
{get_emoji('main')} Telegram API rate limit reached
            """.strip()
            await safe_send_with_entities(event, flood_text)
            
        except (UserNotMutualContactError, UserPrivacyRestrictedError):
            await loading_msg.delete()
            privacy_text = f"""
{get_emoji('adder5')} {convert_font('PRIVACY RESTRICTED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('LIMITED INFORMATION', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Name:', 'bold')} {convert_font(getattr(user, 'first_name', 'Private'), 'mono')}
{get_emoji('adder2')} {convert_font('ID:', 'bold')} {convert_font(str(user.id), 'mono')}
{get_emoji('adder4')} {convert_font('Username:', 'bold')} {convert_font(f"@{user.username}" if user.username else "Private", 'mono')}
{get_emoji('adder5')} {convert_font('Phone:', 'bold')} {convert_font('Private/Hidden', 'mono')}

{get_emoji('adder3')} {convert_font('User has strict privacy settings', 'bold')}
{get_emoji('main')} Only basic public info available
            """.strip()
            await safe_send_with_entities(event, privacy_text)
            
        except Exception as e:
            await loading_msg.delete()
            await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error getting user info:', 'bold')} {str(e)}")
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Command error:', 'bold')} {str(e)}")

# BATCH CEK TOGEL (for multiple users)
@client.on(events.NewMessage(pattern=r'\.cektogelbatch'))
async def cek_togel_batch_handler(event):
    """Batch check multiple users"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        # This would check last 5 messages in chat for different users
        messages = await client.get_messages(event.chat_id, limit=10)
        unique_users = {}
        
        for msg in messages:
            if msg.sender_id and msg.sender_id != event.sender_id:
                if msg.sender_id not in unique_users:
                    try:
                        user = await client.get_entity(msg.sender_id)
                        unique_users[msg.sender_id] = user
                        if len(unique_users) >= 5:  # Limit to 5 users
                            break
                    except Exception:
                        continue
        
        if not unique_users:
            no_users_text = f"""
{get_emoji('adder3')} {convert_font('NO USERS FOUND', 'mono')}

{get_emoji('check')} No recent users found in this chat
{get_emoji('main')} Try using regular `{get_prefix()}cektogel` c
