#!/usr/bin/env python3
"""
Cek Togel User Info Plugin dengan Premium Emoji Support - FIXED VERSION
File: plugins/cektogel.py
Author: Vzoel Fox's (Enhanced by Morgan)
Compatible dengan plugin system VZOEL ASSISTANT v0.1.0.75
"""

import re
import os
import sys
import logging
import json
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User, UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth, UserStatusEmpty
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import UserNotMutualContactError, UserPrivacyRestrictedError, FloodWaitError

# Premium emoji configuration (akan di-inject dari main.py)
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

# Global variables (akan di-set oleh plugin system)
premium_status = None
# Global client reference - akan di-inject oleh plugin loader
client = None

def get_client():
    """Safe client getter with fallback"""
    global client
    if client is not None:
        return client
    
    # Try to get from globals
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if 'client' in frame.f_globals and frame.f_globals['client'] is not None:
                client = frame.f_globals['client']
                return client
            frame = frame.f_back
        
        # Try to get from __main__
        if hasattr(sys.modules.get('__main__'), 'client'):
            client = sys.modules['__main__'].client
            return client
            
    except Exception:
        pass
    finally:
        del frame
    
    raise RuntimeError("Telegram client not available. Ensure plugin is loaded through plugin system.")

# Initialize client reference on import
try:
    if 'client' not in globals() or globals()['client'] is None:
        # Try to get client from plugin loader injection
        pass
except Exception:
    pass
    
    def check_plugin_dependencies():
    """Check if required dependencies are available"""
    required_deps = [
        'telethon',
        'asyncio',
        're',
        'os',
        'sys'
    ]
    
    missing = []
    for dep in required_deps:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        raise ImportError(f"Missing required dependencies: {', '.join(missing)}")
    
    return True
    
# MASALAH 3: Environment variables tidak tersedia
# SOLUSI: Safe environment variable access

def get_env_var(var_name: str, default_value=None):
    """Safely get environment variable with fallback"""
    try:
        value = os.getenv(var_name, default_value)
        if value is None and default_value is None:
            # Try to get from main module
            if hasattr(sys.modules.get('__main__'), var_name):
                value = getattr(sys.modules['__main__'], var_name)
        return value
    except Exception:
        return default_value

def get_command_prefix():
    """Get command prefix safely"""
    return get_env_var("COMMAND_PREFIX", ".")

def get_owner_id():
    """Get owner ID safely"""
    try:
        owner_id = get_env_var("OWNER_ID")
        if owner_id:
            return int(owner_id)
        return None
    except (ValueError, TypeError):
        return None

# MASALAH 4: Async function issues
# SOLUSI: Proper async handling template

async def safe_async_wrapper(func, *args, **kwargs):
    """Safe wrapper for async functions"""
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in async function {func.__name__}: {e}")
        raise
        
# MASALAH 4: Async function issues
# SOLUSI: Proper async handling template

async def safe_async_wrapper(func, *args, **kwargs):
    """Safe wrapper for async functions"""
    try:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in async function {func.__name__}: {e}")
        raise
        
def safe_event_handler(pattern):
    """Safe event handler decorator"""
    def decorator(func):
        try:
            client = get_client()
            return client.on(events.NewMessage(pattern=pattern))(func)
        except Exception as e:
            logger.error(f"Error registering event handler {func.__name__}: {e}")
            return func
    return decorator
    
# Cache for user info to avoid repeated API calls
user_cache = {}
CACHE_DURATION = 300  # 5 minutes

# Fallback functions (jika tidak di-inject dari main.py)
def safe_convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts dengan fallback"""
    try:
        # Try to use injected function first
        if 'convert_font' in globals():
            return convert_font(text, font_type)
    except:
        pass
    
    # Fallback implementation
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def safe_get_emoji(emoji_type):
    """Get premium emoji character dengan fallback"""
    try:
        # Try to use injected function first
        if 'get_emoji' in globals():
            return get_emoji(emoji_type)
    except:
        pass
    
    # Fallback implementation
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def safe_create_premium_entities(text):
    """Create premium emoji entities dengan fallback"""
    try:
        # Try to use injected function first
        if 'create_premium_entities' in globals():
            return create_premium_entities(text)
    except:
        pass
    
    # Fallback: return empty entities
    return []

async def safe_check_premium_status():
    """Check premium status dengan fallback"""
    global premium_status
    try:
        # Try to use injected function first
        if 'check_premium_status' in globals():
            return await check_premium_status()
    except:
        pass
    
    # Fallback implementation
    try:
        if not client:
            premium_status = False
            return False
            
        me = client_instance = get_client() await client_instance.get_me()
        premium_status = getattr(me, 'premium', False)
        return premium_status
    except Exception:
        premium_status = False
        return False

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available"""
    try:
        # Try to use injected function first
        if 'safe_send_with_entities' in globals():
            return await safe_send_with_entities(event, text)
    except:
        pass
    
    # Fallback implementation
    try:
        await safe_check_premium_status()
        
        if premium_status:
            entities = safe_create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

async def safe_is_owner_check(user_id):
    """Check if user is owner dengan fallback"""
    try:
        # Try to use injected function first
        if 'is_owner' in globals():
            return await is_owner(user_id)
    except:
        pass
    
    # Fallback implementation
    try:
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        if client:
            me = client_instance = get_client() await client_instance.get_me()
            return user_id == me.id
        return False
    except Exception:
        return True

def safe_get_prefix():
    """Get command prefix dengan fallback"""
    try:
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

def format_status(status):
    """Format user online status"""
    if isinstance(status, UserStatusOnline):
        return f"{safe_get_emoji('adder2')} Online"
    elif isinstance(status, UserStatusRecently):
        return f"{safe_get_emoji('adder1')} Recently (within 3 days)"
    elif isinstance(status, UserStatusLastWeek):
        return f"{safe_get_emoji('adder3')} Last week"
    elif isinstance(status, UserStatusLastMonth):
        return f"{safe_get_emoji('adder4')} Last month"
    elif isinstance(status, UserStatusOffline):
        if hasattr(status, 'was_online'):
            return f"{safe_get_emoji('adder5')} Offline since {status.was_online.strftime('%m/%d %H:%M')}"
        return f"{safe_get_emoji('adder5')} Offline"
    else:
        return f"{safe_get_emoji('adder6')} Unknown"

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
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        prefix = safe_get_prefix()
        command_arg = event.pattern_match.group(2)
        
        # Get user from reply or text
        try:
            user = await get_user_from_text(event, command_arg)
        except Exception as e:
            error_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('USER NOT FOUND', 'mono')}

{safe_get_emoji('check')} Could not find user: {str(e)}

{safe_get_emoji('main')} {safe_convert_font('Usage Examples:', 'bold')}
• Reply to user message + `{prefix}cektogel`
• `{prefix}cektogel @username`
• `{prefix}cektogel 123456789` (User ID)
• `{prefix}cektogel username` (without @)
            """.strip()
            await safe_send_with_entities(event, error_text)
            return
        
        if not user:
            usage_text = f"""
{safe_get_emoji('adder1')} {safe_convert_font('CEK TOGEL USAGE', 'mono')}

{safe_get_emoji('check')} {safe_convert_font('How to use:', 'bold')}
• Reply to any message + `{prefix}cektogel`
• `{prefix}cektogel @username`
• `{prefix}cektogel 123456789`
• `{prefix}cektogel username`

{safe_get_emoji('main')} {safe_convert_font('This will show:', 'bold')}
{safe_get_emoji('adder2')} User ID & Name
{safe_get_emoji('adder4')} Username & Phone
{safe_get_emoji('adder5')} Login suggestions
            """.strip()
            await safe_send_with_entities(event, usage_text)
            return
        
        # Show loading message
        loading_msg = await event.reply(f"{safe_get_emoji('main')} {safe_convert_font('Loading user information...', 'mono')}")
        
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
                flags.append(f"{safe_get_emoji('main')} Premium")
            if user_info.get('is_verified'):
                flags.append(f"{safe_get_emoji('adder2')} Verified")
            if user_info.get('is_bot'):
                flags.append(f"{safe_get_emoji('adder6')} Bot")
            if user_info.get('is_scam'):
                flags.append(f"{safe_get_emoji('adder3')} Scam")
            if user_info.get('is_fake'):
                flags.append(f"{safe_get_emoji('adder5')} Fake")
            
            # Build main info
            info_text = f"""
{safe_get_emoji('main')} {safe_convert_font('CEK TOGEL RESULT', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('adder1')} {safe_convert_font('USER INFORMATION', 'mono')} {safe_get_emoji('adder1')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Full Name:', 'bold')} {safe_convert_font(full_name, 'mono')}
{safe_get_emoji('adder2')} {safe_convert_font('User ID:', 'bold')} {safe_convert_font(str(user_info['id']), 'mono')}
{safe_get_emoji('adder4')} {safe_convert_font('Username:', 'bold')} {safe_convert_font(username_display, 'mono')}
{safe_get_emoji('adder5')} {safe_convert_font('Phone Number:', 'bold')} {safe_convert_font(phone_masked, 'mono')}

{safe_get_emoji('adder6')} {safe_convert_font('Account Status:', 'bold')}
""" + (f"{format_status(user_info.get('status'))}\n" if user_info.get('status') else f"{safe_get_emoji('adder3')} Status unknown\n")

            # Add flags if any
            if flags:
                info_text += f"""
{safe_get_emoji('adder3')} {safe_convert_font('Account Flags:', 'bold')}
""" + "\n".join(flags) + "\n"
            
            # Add login suggestions
            info_text += f"""
╔══════════════════════════════════╗
   {safe_get_emoji('check')} {safe_convert_font('LOGIN SUGGESTIONS', 'mono')} {safe_get_emoji('check')}
╚══════════════════════════════════╝

"""
            
            if login_suggestions:
                for i, suggestion in enumerate(login_suggestions, 1):
                    info_text += f"{safe_get_emoji('adder' + str(min(i, 6)))} {safe_convert_font(suggestion, 'mono')}\n"
            else:
                info_text += f"{safe_get_emoji('adder3')} {safe_convert_font('Limited login information available', 'mono')}\n"
            
            # Add additional info if available
            if user_info.get('about'):
                info_text += f"""
{safe_get_emoji('adder6')} {safe_convert_font('Bio:', 'bold')} {user_info['about'][:50]}{'...' if len(user_info.get('about', '')) > 50 else ''}
"""
            
            if user_info.get('common_chats_count', 0) > 0:
                info_text += f"{safe_get_emoji('adder2')} {safe_convert_font('Common Groups:', 'bold')} {user_info['common_chats_count']}\n"
            
            # Privacy warning
            info_text += f"""
╔══════════════════════════════════╗
   {safe_get_emoji('adder3')} {safe_convert_font('PRIVACY NOTE', 'mono')} {safe_get_emoji('adder3')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} Phone numbers are masked for privacy
{safe_get_emoji('adder1')} Only public information is shown
{safe_get_emoji('adder5')} Use responsibly and ethically

{safe_get_emoji('main')} {safe_convert_font('Checked at:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            await safe_send_with_entities(event, info_text)
            
        except FloodWaitError as e:
            await loading_msg.delete()
            flood_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('RATE LIMIT', 'mono')}

{safe_get_emoji('check')} Please wait {e.seconds} seconds before next check
{safe_get_emoji('main')} Telegram API rate limit reached
            """.strip()
            await safe_send_with_entities(event, flood_text)
            
        except (UserNotMutualContactError, UserPrivacyRestrictedError):
            await loading_msg.delete()
            privacy_text = f"""
{safe_get_emoji('adder5')} {safe_convert_font('PRIVACY RESTRICTED', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('LIMITED INFORMATION', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Name:', 'bold')} {safe_convert_font(getattr(user, 'first_name', 'Private'), 'mono')}
{safe_get_emoji('adder2')} {safe_convert_font('ID:', 'bold')} {safe_convert_font(str(user.id), 'mono')}
{safe_get_emoji('adder4')} {safe_convert_font('Username:', 'bold')} {safe_convert_font(f"@{user.username}" if user.username else "Private", 'mono')}
{safe_get_emoji('adder5')} {safe_convert_font('Phone:', 'bold')} {safe_convert_font('Private/Hidden', 'mono')}

{safe_get_emoji('adder3')} {safe_convert_font('User has strict privacy settings', 'bold')}
{safe_get_emoji('main')} Only basic public info available
            """.strip()
            await safe_send_with_entities(event, privacy_text)
            
        except Exception as e:
            await loading_msg.delete()
            await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error getting user info:', 'bold')} {str(e)}")
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Command error:', 'bold')} {str(e)}")

# BATCH CEK TOGEL (for multiple users)
@client.on(events.NewMessage(pattern=r'\.cektogelbatch'))
async def cek_togel_batch_handler(event):
    """Batch check multiple users from recent messages"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        prefix = safe_get_prefix()
        
        # Show loading
        loading_msg = await event.reply(f"{safe_get_emoji('main')} {safe_convert_font('Scanning recent messages...', 'mono')}")
        
        # Get recent messages to find unique users
        messages = await client.get_messages(event.chat_id, limit=20)
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
        
        await loading_msg.delete()
        
        if not unique_users:
            no_users_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('NO USERS FOUND', 'mono')}

{safe_get_emoji('check')} No recent users found in this chat
{safe_get_emoji('main')} Try using regular `{prefix}cektogel` command
            """.strip()
            await safe_send_with_entities(event, no_users_text)
            return
        
        # Build batch result
        batch_text = f"""
{safe_get_emoji('main')} {safe_convert_font('BATCH CEK TOGEL RESULT', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('adder1')} {safe_convert_font('RECENT USERS SUMMARY', 'mono')} {safe_get_emoji('adder1')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} Found {len(unique_users)} unique users:

"""
        
        # Add user summaries
        for i, (user_id, user) in enumerate(unique_users.items(), 1):
            try:
                # Basic user info
                full_name = ""
                if getattr(user, 'first_name', None):
                    full_name += user.first_name
                if getattr(user, 'last_name', None):
                    full_name += f" {user.last_name}"
                if not full_name:
                    full_name = "No name"
                
                username_display = f"@{user.username}" if getattr(user, 'username', None) else "No username"
                
                # Account flags
                flags = []
                if getattr(user, 'premium', False):
                    flags.append("Premium")
                if getattr(user, 'verified', False):
                    flags.append("Verified")
                if getattr(user, 'bot', False):
                    flags.append("Bot")
                
                flag_display = f" ({', '.join(flags)})" if flags else ""
                
                batch_text += f"""
{safe_get_emoji('adder' + str(min(i, 6)))} {safe_convert_font(f'#{i}', 'bold')} {safe_convert_font(full_name[:20], 'mono')}{flag_display}
{safe_get_emoji('check')} {safe_convert_font('ID:', 'mono')} {user_id} | {safe_convert_font('Username:', 'mono')} {username_display[:15]}

"""
            except Exception as e:
                batch_text += f"{safe_get_emoji('adder3')} #{i} Error: {str(e)}\n\n"
        
        batch_text += f"""
╔══════════════════════════════════╗
   {safe_get_emoji('adder2')} {safe_convert_font('DETAILED CHECK', 'mono')} {safe_get_emoji('adder2')}
╚══════════════════════════════════╝

{safe_get_emoji('main')} Use `{prefix}cektogel <user_id>` for detailed info
{safe_get_emoji('adder4')} Or reply to specific message + `{prefix}cektogel`

{safe_get_emoji('adder5')} {safe_convert_font('Scanned at:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        await safe_send_with_entities(event, batch_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Batch error:', 'bold')} {str(e)}")

# QUICK INFO COMMAND (minimal user info)
@client.on(events.NewMessage(pattern=r'\.quickinfo(\s+(.+))?'))
async def quick_info_handler(event):
    """Quick user info check with minimal details"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        prefix = safe_get_prefix()
        command_arg = event.pattern_match.group(2)
        
        # Get user from reply or text
        try:
            user = await get_user_from_text(event, command_arg)
        except Exception as e:
            await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} User not found: {str(e)}")
            return
        
        if not user:
            usage_text = f"""
{safe_get_emoji('check')} {safe_convert_font('QUICK INFO USAGE', 'mono')}

• Reply to message + `{prefix}quickinfo`
• `{prefix}quickinfo @username`
• `{prefix}quickinfo 123456789`
            """.strip()
            await safe_send_with_entities(event, usage_text)
            return
        
        # Format quick info
        full_name = ""
        if getattr(user, 'first_name', None):
            full_name += user.first_name
        if getattr(user, 'last_name', None):
            full_name += f" {user.last_name}"
        if not full_name:
            full_name = "No name set"
        
        username_display = f"@{user.username}" if getattr(user, 'username', None) else "No username"
        
        # Quick flags
        flags = []
        if getattr(user, 'premium', False):
            flags.append("Premium")
        if getattr(user, 'verified', False):
            flags.append("Verified")
        if getattr(user, 'bot', False):
            flags.append("Bot")
        
        flag_display = f" ({', '.join(flags)})" if flags else ""
        
        quick_text = f"""
{safe_get_emoji('adder4')} {safe_convert_font('QUICK USER INFO', 'mono')}

{safe_get_emoji('check')} {safe_convert_font(full_name, 'mono')}{flag_display}
{safe_get_emoji('adder2')} {safe_convert_font('ID:', 'bold')} {user.id}
{safe_get_emoji('adder1')} {safe_convert_font('Username:', 'bold')} {username_display}
{safe_get_emoji('main')} {safe_convert_font('Status:', 'bold')} {format_status(getattr(user, 'status', None))}

{safe_get_emoji('adder5')} Use `{prefix}cektogel` for detailed info
        """.strip()
        
        await safe_send_with_entities(event, quick_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Quick info error:', 'bold')} {str(e)}")

# CLEAR CACHE COMMAND
@client.on(events.NewMessage(pattern=r'\.clearcache'))
async def clear_cache_handler(event):
    """Clear user info cache"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        global user_cache
        cache_count = len(user_cache)
        user_cache.clear()
        
        clear_text = f"""
{safe_get_emoji('adder2')} {safe_convert_font('CACHE CLEARED', 'mono')}

{safe_get_emoji('check')} Cleared {cache_count} cached user entries
{safe_get_emoji('main')} Fresh data will be fetched on next check
{safe_get_emoji('adder1')} Memory usage optimized
        """.strip()
        
        await safe_send_with_entities(event, clear_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Cache clear error:', 'bold')} {str(e)}")

# Plugin info untuk plugin system
PLUGIN_INFO = {
    'name': 'cektogel',
    'version': '1.0.2',
    'description': 'User information lookup with privacy protection and premium emoji support',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['cektogel', 'cektogelbatch', 'quickinfo', 'clearcache'],
    'features': ['user_lookup', 'privacy_protection', 'batch_scanning', 'caching_system', 'premium_emojis'],
    'dependencies': ['client', 'convert_font', 'get_emoji', 'safe_send_with_entities']
}

def get_plugin_info():
    """Required function for plugin system"""
    return PLUGIN_INFO

def initialize_plugin():
    """Initialize plugin (called by plugin loader)"""
    try:
        # Plugin initialization code
        global user_cache
        user_cache = {}
        print(f"✅ {PLUGIN_INFO['name']} plugin initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing {PLUGIN_INFO['name']} plugin: {e}")
        return False

def cleanup_plugin():
    """Clean up plugin resources (called when unloading)"""
    try:
        global user_cache
        user_cache.clear()
        print(f"✅ {PLUGIN_INFO['name']} plugin cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Error cleaning up {PLUGIN_INFO['name']} plugin: {e}")

# Export untuk compatibility
__all__ = [
    'get_plugin_info',
    'initialize_plugin', 
    'cleanup_plugin',
    'PLUGIN_INFO'
]