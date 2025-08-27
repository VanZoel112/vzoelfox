#!/usr/bin/env python3
"""
ID Checker Plugin for VZOEL ASSISTANT v0.1.0.75
Compatible plugin untuk cek user/chat information
Author: Enhanced by Morgan
File: plugins/id_checker.py
"""

import asyncio
import logging
import time
import re
from datetime import datetime
from telethon import events
from telethon.errors import (
    PeerIdInvalidError, UsernameInvalidError, UsernameNotOccupiedError,
    ChatAdminRequiredError, ChannelPrivateError, UserNotParticipantError
)
from telethon.tl.types import User, Chat, Channel, ChatFull, ChannelFull

# Import dari main.py
try:
    from main import (
        client, COMMAND_PREFIX, get_emoji, convert_font, 
        is_owner, log_command, safe_edit_message, stats, premium_status
    )
except ImportError:
    # Fallback jika import gagal
    print("❌ Error: Cannot import from main.py - Make sure this plugin is in plugins/ directory")
    exit(1)

logger = logging.getLogger(__name__)

# ============= ID CHECKER FUNCTIONS =============

async def get_user_or_chat_info(target):
    """
    Enhanced function untuk mendapatkan informasi user atau chat
    Supports: User ID, Username, Chat ID, atau entity object
    """
    try:
        if isinstance(target, (User, Chat, Channel)):
            return target
        
        # Handle string input (username atau ID)
        if isinstance(target, str):
            target = target.strip()
            
            # Remove @ dari username
            if target.startswith('@'):
                target = target[1:]
            
            # Cek apakah itu ID (angka)
            if target.isdigit() or (target.startswith('-') and target[1:].isdigit()):
                target = int(target)
        
        # Get entity dari Telegram
        entity = await client.get_entity(target)
        return entity
        
    except PeerIdInvalidError:
        return None, "Invalid user ID or username"
    except UsernameInvalidError:
        return None, "Invalid username format"
    except UsernameNotOccupiedError:
        return None, "Username not found or doesn't exist"
    except ValueError as e:
        if "No user has" in str(e):
            return None, "User not found or never interacted"
        return None, f"Value error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

async def get_detailed_info(entity):
    """Get detailed information tentang user/chat"""
    info = {}
    
    try:
        if isinstance(entity, User):
            info.update({
                'type': 'User',
                'id': entity.id,
                'first_name': getattr(entity, 'first_name', None),
                'last_name': getattr(entity, 'last_name', None),
                'username': getattr(entity, 'username', None),
                'phone': getattr(entity, 'phone', None),
                'is_bot': getattr(entity, 'bot', False),
                'is_verified': getattr(entity, 'verified', False),
                'is_premium': getattr(entity, 'premium', False),
                'is_scam': getattr(entity, 'scam', False),
                'is_fake': getattr(entity, 'fake', False),
                'is_deleted': getattr(entity, 'deleted', False),
                'is_contact': getattr(entity, 'contact', False),
                'is_mutual_contact': getattr(entity, 'mutual_contact', False),
                'lang_code': getattr(entity, 'lang_code', None),
                'dc_id': getattr(entity, 'dc_id', None)
            })
            
        elif isinstance(entity, (Chat, Channel)):
            info.update({
                'type': 'Channel' if isinstance(entity, Channel) and getattr(entity, 'broadcast', False) else 'Group',
                'id': entity.id,
                'title': getattr(entity, 'title', None),
                'username': getattr(entity, 'username', None),
                'participants_count': getattr(entity, 'participants_count', None),
                'date': getattr(entity, 'date', None),
                'creator': getattr(entity, 'creator', False),
                'admin_rights': getattr(entity, 'admin_rights', None),
                'banned_rights': getattr(entity, 'banned_rights', None),
                'is_verified': getattr(entity, 'verified', False),
                'is_scam': getattr(entity, 'scam', False),
                'is_fake': getattr(entity, 'fake', False),
                'dc_id': getattr(entity, 'dc_id', None)
            })
            
            # Get additional info jika memungkinkan
            try:
                if isinstance(entity, Channel):
                    full_info = await client.get_entity(entity.id)
                    if hasattr(full_info, 'participants_count'):
                        info['participants_count'] = full_info.participants_count
            except:
                pass
        
        return info
        
    except Exception as e:
        logger.error(f"Error getting detailed info: {e}")
        return info

def format_user_info(info):
    """Format user information dengan style VZOEL"""
    if not info:
        return "No information available"
    
    # Header
    user_type = info.get('type', 'Unknown')
    type_emoji = get_emoji('main') if user_type == 'User' else get_emoji('adder1')
    
    formatted = f"""
{type_emoji} {convert_font(f'{user_type.upper()} INFORMATION', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('DETAILED INFO', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Basic Info:', 'bold')}
"""
    
    # ID (selalu ada)
    formatted += f"{get_emoji('check')} {convert_font('ID:', 'bold')} `{info['id']}`\n"
    
    if user_type == 'User':
        # User specific info
        name_parts = []
        if info.get('first_name'):
            name_parts.append(info['first_name'])
        if info.get('last_name'):
            name_parts.append(info['last_name'])
        
        full_name = ' '.join(name_parts) if name_parts else 'No Name'
        formatted += f"{get_emoji('check')} {convert_font('Name:', 'bold')} {full_name}\n"
        
        if info.get('username'):
            formatted += f"{get_emoji('check')} {convert_font('Username:', 'bold')} @{info['username']}\n"
        
        if info.get('phone'):
            formatted += f"{get_emoji('adder2')} {convert_font('Phone:', 'bold')} +{info['phone']}\n"
        
        # Status flags
        status_flags = []
        if info.get('is_bot'):
            status_flags.append('Bot')
        if info.get('is_verified'):
            status_flags.append('Verified')
        if info.get('is_premium'):
            status_flags.append('Premium')
        if info.get('is_scam'):
            status_flags.append('Scam')
        if info.get('is_fake'):
            status_flags.append('Fake')
        if info.get('is_deleted'):
            status_flags.append('Deleted')
        
        if status_flags:
            formatted += f"{get_emoji('adder3')} {convert_font('Status:', 'bold')} {', '.join(status_flags)}\n"
        
        # Contact info
        contact_flags = []
        if info.get('is_contact'):
            contact_flags.append('In Contacts')
        if info.get('is_mutual_contact'):
            contact_flags.append('Mutual Contact')
        
        if contact_flags:
            formatted += f"{get_emoji('adder4')} {convert_font('Contact:', 'bold')} {', '.join(contact_flags)}\n"
        
        # Technical info
        formatted += f"\n{get_emoji('adder5')} {convert_font('Technical Info:', 'bold')}\n"
        if info.get('dc_id'):
            formatted += f"{get_emoji('check')} {convert_font('DC ID:', 'bold')} `{info['dc_id']}`\n"
        if info.get('lang_code'):
            formatted += f"{get_emoji('check')} {convert_font('Language:', 'bold')} `{info['lang_code']}`\n"
    
    else:
        # Group/Channel specific info
        if info.get('title'):
            formatted += f"{get_emoji('check')} {convert_font('Title:', 'bold')} {info['title']}\n"
        
        if info.get('username'):
            formatted += f"{get_emoji('check')} {convert_font('Username:', 'bold')} @{info['username']}\n"
        
        if info.get('participants_count'):
            formatted += f"{get_emoji('adder2')} {convert_font('Members:', 'bold')} `{info['participants_count']:,}`\n"
        
        if info.get('date'):
            try:
                date_str = info['date'].strftime('%Y-%m-%d')
                formatted += f"{get_emoji('adder3')} {convert_font('Created:', 'bold')} `{date_str}`\n"
            except:
                pass
        
        # Status flags untuk group/channel
        status_flags = []
        if info.get('creator'):
            status_flags.append('Creator')
        if info.get('is_verified'):
            status_flags.append('Verified')
        if info.get('is_scam'):
            status_flags.append('Scam')
        if info.get('is_fake'):
            status_flags.append('Fake')
        
        if status_flags:
            formatted += f"{get_emoji('adder4')} {convert_font('Status:', 'bold')} {', '.join(status_flags)}\n"
        
        # Admin rights
        if info.get('admin_rights'):
            formatted += f"{get_emoji('adder5')} {convert_font('Admin Rights:', 'bold')} Yes\n"
        
        # Technical info
        formatted += f"\n{get_emoji('adder6')} {convert_font('Technical Info:', 'bold')}\n"
        if info.get('dc_id'):
            formatted += f"{get_emoji('check')} {convert_font('DC ID:', 'bold')} `{info['dc_id']}`\n"
    
    return formatted.strip()

# ============= COMMAND HANDLERS =============

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}id(\s+(.+))?', re.DOTALL)))
async def id_command_handler(event):
    """
    Enhanced ID command dengan support untuk:
    - Reply ke message: .id
    - Username/ID target: .id @username atau .id 123456789
    - Current chat info: .id (di group/channel tanpa reply)
    """
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "id")
    
    try:
        target = None
        target_source = ""
        
        # Cek apakah ada reply message
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg:
                target = reply_msg.sender_id
                target_source = "replied message sender"
        
        # Cek apakah ada argument (username/ID)
        elif event.pattern_match.group(2):
            target_arg = event.pattern_match.group(2).strip()
            target = target_arg
            target_source = f"specified target: {target_arg}"
        
        # Jika tidak ada target, tampilkan current chat info
        else:
            target = await event.get_chat()
            target_source = "current chat"
        
        # Show loading message
        loading_msg = await event.reply(f"{get_emoji('main')} {convert_font('Fetching information...', 'bold')}")
        
        # Get entity information
        if isinstance(target, (User, Chat, Channel)):
            entity = target
            error = None
        else:
            result = await get_user_or_chat_info(target)
            if isinstance(result, tuple):
                entity, error = result
            else:
                entity, error = result, None
        
        if error:
            error_msg = f"""
{get_emoji('adder3')} {convert_font('ID CHECK FAILED', 'mono')}

{get_emoji('check')} {convert_font('Target:', 'bold')} {target_source}
{get_emoji('adder3')} {convert_font('Error:', 'bold')} {error}

{get_emoji('main')} {convert_font('Tips:', 'bold')}
{get_emoji('check')} Reply ke message + `{COMMAND_PREFIX}id`
{get_emoji('check')} `{COMMAND_PREFIX}id @username`
{get_emoji('check')} `{COMMAND_PREFIX}id 123456789`
{get_emoji('check')} `{COMMAND_PREFIX}id` (current chat info)
            """.strip()
            
            await safe_edit_message(loading_msg, error_msg)
            return
        
        # Get detailed information
        detailed_info = await get_detailed_info(entity)
        
        # Format output
        info_text = format_user_info(detailed_info)
        
        # Add metadata
        final_text = f"""
{info_text}

{get_emoji('adder6')} {convert_font('Query Info:', 'bold')}
{get_emoji('check')} {convert_font('Source:', 'bold')} {target_source}
{get_emoji('check')} {convert_font('Timestamp:', 'bold')} `{datetime.now().strftime('%H:%M:%S')}`
{get_emoji('main')} {convert_font('Requested by:', 'bold')} User ID `{event.sender_id}`

{get_emoji('check')} {convert_font('Information retrieved successfully!', 'bold')}
        """.strip()
        
        await safe_edit_message(loading_msg, final_text)
        
        # Update statistics
        stats['commands_executed'] += 1
        
    except Exception as e:
        stats['errors_handled'] += 1
        error_text = f"""
{get_emoji('adder3')} {convert_font('UNEXPECTED ERROR', 'mono')}

{get_emoji('check')} {convert_font('Error:', 'bold')} {str(e)}
{get_emoji('main')} {convert_font('Please try again or contact support', 'bold')}
        """.strip()
        
        try:
            await safe_edit_message(loading_msg, error_text)
        except:
            await event.reply(error_text)
        
        logger.error(f"ID command error: {e}")

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}info(\s+(.+))?', re.DOTALL)))
async def info_command_handler(event):
    """
    Enhanced info command sebagai alias untuk id command dengan tampilan berbeda
    """
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "info")
    
    try:
        target = None
        target_source = ""
        
        # Logic sama seperti id command
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg:
                target = reply_msg.sender_id
                target_source = "replied message sender"
        elif event.pattern_match.group(2):
            target_arg = event.pattern_match.group(2).strip()
            target = target_arg
            target_source = f"specified target: {target_arg}"
        else:
            # Show help untuk info command
            help_text = f"""
{get_emoji('main')} {convert_font('INFO COMMAND USAGE', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder1')} {convert_font('GET DETAILED INFORMATION', 'mono')} {get_emoji('adder1')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Usage Methods:', 'bold')}
{get_emoji('adder2')} Reply ke message + `{COMMAND_PREFIX}info`
{get_emoji('adder2')} `{COMMAND_PREFIX}info @username`
{get_emoji('adder2')} `{COMMAND_PREFIX}info 123456789`

{get_emoji('adder3')} {convert_font('Information Provided:', 'bold')}
{get_emoji('check')} Full name dan username
{get_emoji('check')} User ID dan phone number
{get_emoji('check')} Account status (Bot, Premium, Verified, etc)
{get_emoji('check')} Contact relationship
{get_emoji('check')} Technical details (DC ID, Language)
{get_emoji('check')} Group/Channel information

{get_emoji('adder4')} {convert_font('Examples:', 'bold')}
Reply ke user message + `{COMMAND_PREFIX}info`
`{COMMAND_PREFIX}info @telegram`
`{COMMAND_PREFIX}info 777000`

{get_emoji('main')} {convert_font('Also try:', 'bold')} `{COMMAND_PREFIX}id` for quick ID check
            """.strip()
            
            await event.reply(help_text)
            return
        
        # Loading animation
        loading_animations = [
            f"{get_emoji('main')} {convert_font('Initializing info request...', 'bold')}",
            f"{get_emoji('adder1')} {convert_font('Fetching user data...', 'bold')}",
            f"{get_emoji('adder2')} {convert_font('Processing information...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Finalizing report...', 'bold')}"
        ]
        
        loading_msg = await event.reply(loading_animations[0])
        
        # Animate loading
        for i, animation in enumerate(loading_animations[1:], 1):
            await asyncio.sleep(0.8)
            await safe_edit_message(loading_msg, animation)
        
        # Get information (sama seperti id command)
        if isinstance(target, (User, Chat, Channel)):
            entity = target
            error = None
        else:
            result = await get_user_or_chat_info(target)
            if isinstance(result, tuple):
                entity, error = result
            else:
                entity, error = result, None
        
        if error:
            error_msg = f"""
{get_emoji('adder3')} {convert_font('INFO REQUEST FAILED', 'mono')}

{get_emoji('check')} {convert_font('Target:', 'bold')} {target_source}
{get_emoji('adder3')} {convert_font('Error:', 'bold')} {error}

{get_emoji('main')} {convert_font('Troubleshooting:', 'bold')}
{get_emoji('check')} Ensure username is correct
{get_emoji('check')} Check if user exists
{get_emoji('check')} Try with User ID instead
{get_emoji('check')} Make sure you've interacted with user before
            """.strip()
            
            await safe_edit_message(loading_msg, error_msg)
            return
        
        # Get detailed info
        detailed_info = await get_detailed_info(entity)
        info_text = format_user_info(detailed_info)
        
        # Enhanced final message untuk info command
        final_text = f"""
{info_text}

{get_emoji('adder5')} {convert_font('Query Details:', 'bold')}
{get_emoji('check')} {convert_font('Source:', 'bold')} {target_source}
{get_emoji('check')} {convert_font('Query Time:', 'bold')} `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
{get_emoji('check')} {convert_font('Requested by:', 'bold')} `{event.sender_id}`
{get_emoji('main')} {convert_font('Command:', 'bold')} info (detailed mode)

{get_emoji('adder6')} {convert_font('Data retrieved from Telegram API', 'bold')}
        """.strip()
        
        await safe_edit_message(loading_msg, final_text)
        stats['commands_executed'] += 1
        
    except Exception as e:
        stats['errors_handled'] += 1
        await event.reply(f"❌ {convert_font('Info Error:', 'bold')} {str(e)}")
        logger.error(f"Info command error: {e}")

# ============= PLUGIN INITIALIZATION =============

def initialize_plugin():
    """Initialize plugin dengan logging"""
    try:
        logger.info("✅ ID Checker Plugin loaded successfully")
        logger.info(f"🔧 Commands registered: {COMMAND_PREFIX}id, {COMMAND_PREFIX}info")
        logger.info("🎯 Features: Reply support, Username/ID lookup, Current chat info")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing ID Checker Plugin: {e}")
        return False

# Auto-initialize saat plugin dimuat
if __name__ != "__main__":
    initialize_plugin()

"""
🔥 ID CHECKER PLUGIN for VZOEL ASSISTANT v0.1.0.75 🔥

✅ FEATURES:
1. ✅ Reply ke message untuk cek sender ID/info  
2. ✅ Ketik username (@username) atau User ID
3. ✅ Current chat info jika tanpa parameter
4. ✅ Detailed user information (Premium, Verified, Bot, etc)
5. ✅ Group/Channel information dengan member count
6. ✅ Technical details (DC ID, Language code)
7. ✅ Enhanced error handling dengan user-friendly messages
8. ✅ Loading animations dan progress indicators
9. ✅ Full integration dengan main.py styling dan functions

🎯 COMMANDS:
• .id - Quick ID check dengan basic info
• .id @username - Cek user berdasarkan username  
• .id 123456789 - Cek user berdasarkan User ID
• Reply + .id - Cek sender dari replied message
• .info - Detailed information dengan enhanced display
• .info @username - Detailed user info
• .info 123456789 - Detailed user info by ID

📋 COMPATIBILITY:
- ✅ Full compatibility dengan VZOEL ASSISTANT v0.1.0.75
- ✅ Menggunakan semua functions dari main.py
- ✅ Style consistency dengan font conversion dan emoji
- ✅ Error handling sesuai dengan main.py standards
- ✅ Statistics integration
- ✅ Logging integration

⚡ Ready untuk digunakan - Just save as plugins/id_checker.py ⚡
"""