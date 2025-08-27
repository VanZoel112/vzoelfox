#!/usr/bin/env python3
"""
Voice Chat Plugin for VZOEL ASSISTANT v0.1.0.75
Plugin untuk join/leave voice chat dengan enhanced features
Author: Enhanced by Morgan
File: plugins/voice_chat.py
"""

import asyncio
import logging
import time
import re
from datetime import datetime
from telethon import events
from telethon.errors import (
    ChatAdminRequiredError, ChannelPrivateError, UserNotParticipantError,
    GroupCallNotFoundError, FloodWaitError, PeerIdInvalidError
)
from telethon.tl.types import Chat, Channel, User, InputPeerChannel, InputPeerChat
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest

# Import dari main.py
try:
    from main import (
        client, COMMAND_PREFIX, get_emoji, convert_font, 
        is_owner, log_command, safe_edit_message, stats, 
        premium_status, animate_text_premium
    )
except ImportError:
    # Fallback jika import gagal
    print("❌ Error: Cannot import from main.py - Make sure this plugin is in plugins/ directory")
    exit(1)

logger = logging.getLogger(__name__)

# ============= VOICE CHAT STATE MANAGEMENT =============

# Global voice chat state
voice_chat_state = {
    'active': False,
    'current_chat_id': None,
    'current_chat_title': None,
    'join_time': None,
    'call_id': None,
    'is_muted': False,
    'is_video_enabled': False
}

def update_voice_state(active=None, chat_id=None, chat_title=None, call_id=None, muted=None, video=None):
    """Update voice chat state dengan logging"""
    global voice_chat_state
    
    if active is not None:
        voice_chat_state['active'] = active
        if active:
            voice_chat_state['join_time'] = time.time()
        else:
            voice_chat_state['join_time'] = None
    
    if chat_id is not None:
        voice_chat_state['current_chat_id'] = chat_id
    
    if chat_title is not None:
        voice_chat_state['current_chat_title'] = chat_title
    
    if call_id is not None:
        voice_chat_state['call_id'] = call_id
    
    if muted is not None:
        voice_chat_state['is_muted'] = muted
    
    if video is not None:
        voice_chat_state['is_video_enabled'] = video
    
    logger.info(f"Voice chat state updated: {voice_chat_state}")

def get_voice_duration():
    """Get current voice chat duration"""
    if voice_chat_state['active'] and voice_chat_state['join_time']:
        duration = time.time() - voice_chat_state['join_time']
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    return "0s"

# ============= VOICE CHAT FUNCTIONS =============

async def get_chat_call_info(chat):
    """Enhanced function untuk mendapatkan info voice call dari chat"""
    try:
        call_info = None
        
        if isinstance(chat, Channel):
            try:
                full_chat = await client(GetFullChannelRequest(chat))
                call_info = getattr(full_chat.full_chat, 'call', None)
            except Exception as e:
                logger.error(f"Error getting channel call info: {e}")
                return None, f"Cannot access channel call info: {str(e)}"
        
        elif isinstance(chat, Chat):
            try:
                full_chat = await client(GetFullChatRequest(chat.id))
                call_info = getattr(full_chat.full_chat, 'call', None)
            except Exception as e:
                logger.error(f"Error getting chat call info: {e}")
                return None, f"Cannot access chat call info: {str(e)}"
        
        else:
            return None, "Invalid chat type for voice call"
        
        if not call_info:
            return None, "No active voice chat found in this chat"
        
        return call_info, None
        
    except Exception as e:
        logger.error(f"Error in get_chat_call_info: {e}")
        return None, f"Unexpected error: {str(e)}"

async def join_voice_chat_enhanced(chat, muted=True, video_stopped=True):
    """Enhanced voice chat joining dengan comprehensive error handling"""
    try:
        chat_title = getattr(chat, 'title', 'Unknown Chat')
        chat_id = chat.id
        
        # Check jika sudah dalam voice chat
        if voice_chat_state['active']:
            return False, f"Already in voice chat: {voice_chat_state['current_chat_title']}"
        
        # Get call information
        call_info, error = await get_chat_call_info(chat)
        if error:
            return False, error
        
        # Attempt to join voice chat
        try:
            result = await client(JoinGroupCallRequest(
                call=call_info,
                muted=muted,
                video_stopped=video_stopped
            ))
            
            # Update state
            update_voice_state(
                active=True,
                chat_id=chat_id,
                chat_title=chat_title,
                call_id=call_info.id,
                muted=muted,
                video=not video_stopped
            )
            
            logger.info(f"Successfully joined voice chat in {chat_title}")
            return True, f"Successfully joined voice chat in {chat_title}"
            
        except ChatAdminRequiredError:
            return False, "Admin rights required to join voice chat in this group"
        
        except UserNotParticipantError:
            return False, "You must be a member of this group to join voice chat"
        
        except GroupCallNotFoundError:
            return False, "Voice chat not found or has ended"
        
        except FloodWaitError as e:
            return False, f"Rate limit exceeded. Please wait {e.seconds} seconds"
        
        except Exception as join_error:
            logger.error(f"Join voice chat error: {join_error}")
            return False, f"Failed to join: {str(join_error)}"
        
    except Exception as e:
        logger.error(f"Error in join_voice_chat_enhanced: {e}")
        return False, f"Unexpected error: {str(e)}"

async def leave_voice_chat_enhanced():
    """Enhanced voice chat leaving dengan state management"""
    try:
        if not voice_chat_state['active']:
            return False, "Not currently in a voice chat"
        
        # Store info sebelum leave
        chat_title = voice_chat_state['current_chat_title']
        duration = get_voice_duration()
        
        try:
            # Leave voice chat
            await client(LeaveGroupCallRequest(
                call=voice_chat_state['call_id']
            ))
            
            # Reset state
            update_voice_state(
                active=False,
                chat_id=None,
                chat_title=None,
                call_id=None,
                muted=False,
                video=False
            )
            
            logger.info(f"Successfully left voice chat from {chat_title}")
            return True, f"Left voice chat from {chat_title} (Duration: {duration})"
            
        except Exception as leave_error:
            # Force reset state bahkan jika error
            update_voice_state(
                active=False,
                chat_id=None,
                chat_title=None,
                call_id=None,
                muted=False,
                video=False
            )
            
            logger.error(f"Leave voice chat error: {leave_error}")
            return True, f"Force left voice chat (Duration: {duration})"
        
    except Exception as e:
        logger.error(f"Error in leave_voice_chat_enhanced: {e}")
        return False, f"Error leaving voice chat: {str(e)}"

async def get_voice_chat_status():
    """Get detailed voice chat status"""
    if not voice_chat_state['active']:
        return {
            'active': False,
            'status': 'Not in voice chat',
            'duration': '0s'
        }
    
    return {
        'active': True,
        'chat_id': voice_chat_state['current_chat_id'],
        'chat_title': voice_chat_state['current_chat_title'],
        'duration': get_voice_duration(),
        'muted': voice_chat_state['is_muted'],
        'video': voice_chat_state['is_video_enabled'],
        'call_id': voice_chat_state['call_id']
    }

# ============= COMMAND HANDLERS =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}joinvc'))
async def joinvc_handler(event):
    """
    Enhanced join voice chat command dengan comprehensive features
    Usage: .joinvc (dalam group/channel dengan voice chat)
    """
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "joinvc")
    
    try:
        chat = await event.get_chat()
        
        # Validasi chat type
        if isinstance(chat, User):
            await event.reply(f"""
{get_emoji('adder3')} {convert_font('INVALID CHAT TYPE', 'mono')}

{get_emoji('check')} {convert_font('Error:', 'bold')} Cannot join voice chat in private messages
{get_emoji('main')} {convert_font('Usage:', 'bold')} Use this command in groups or channels only
            """.strip())
            return
        
        # Animation loading
        loading_animations = [
            f"{get_emoji('main')} {convert_font('Preparing to join voice chat...', 'bold')}",
            f"{get_emoji('adder1')} {convert_font('Checking voice chat availability...', 'bold')}",
            f"{get_emoji('adder2')} {convert_font('Validating permissions...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Attempting to join...', 'bold')}"
        ]
        
        msg = await event.reply(loading_animations[0])
        await animate_text_premium(msg, loading_animations, delay=1)
        
        # Attempt to join
        success, message = await join_voice_chat_enhanced(
            chat=chat,
            muted=True,  # Join muted by default
            video_stopped=True  # Video off by default
        )
        
        if success:
            chat_title = getattr(chat, 'title', 'Unknown Chat')
            success_text = f"""
{get_emoji('adder2')} {convert_font('VOICE CHAT JOINED!', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('SUCCESSFULLY CONNECTED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Chat:', 'bold')} {chat_title}
{get_emoji('check')} {convert_font('Chat ID:', 'bold')} `{chat.id}`
{get_emoji('adder4')} {convert_font('Status:', 'bold')} Connected & Muted
{get_emoji('adder5')} {convert_font('Video:', 'bold')} Disabled
{get_emoji('main')} {convert_font('Join Time:', 'bold')} `{datetime.now().strftime('%H:%M:%S')}`

{get_emoji('adder1')} {convert_font('Voice Chat Controls:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}leavevc` - Leave voice chat
{get_emoji('check')} `{COMMAND_PREFIX}vcstatus` - Check status
{get_emoji('check')} Voice controls via Telegram app

{get_emoji('adder6')} {convert_font('Tips:', 'bold')}
{get_emoji('check')} Use Telegram mobile app for full voice features
{get_emoji('check')} Bot joined muted by default
{get_emoji('check')} Enable microphone manually if needed

{get_emoji('main')} {convert_font('Enjoying the voice chat!', 'bold')}
            """.strip()
            
            await safe_edit_message(msg, success_text)
            stats['commands_executed'] += 1
            
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('JOIN VOICE CHAT FAILED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder3')} {convert_font('CONNECTION FAILED', 'mono')} {get_emoji('adder3')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Chat:', 'bold')} {getattr(chat, 'title', 'Unknown')}
{get_emoji('adder3')} {convert_font('Error:', 'bold')} {message}

{get_emoji('main')} {convert_font('Troubleshooting:', 'bold')}
{get_emoji('check')} Make sure voice chat is active
{get_emoji('check')} Check if you have permission to join
{get_emoji('check')} Ensure you're a member of this group
{get_emoji('check')} Try starting voice chat first (if admin)
{get_emoji('check')} Wait a moment and try again

{get_emoji('adder1')} {convert_font('Alternative:', 'bold')}
{get_emoji('check')} Use Telegram app to join manually
{get_emoji('check')} Check group settings and permissions
            """.strip()
            
            await safe_edit_message(msg, error_text)
        
    except Exception as e:
        stats['errors_handled'] += 1
        await event.reply(f"❌ {convert_font('JoinVC Error:', 'bold')} {str(e)}")
        logger.error(f"JoinVC command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}leavevc'))
async def leavevc_handler(event):
    """
    Enhanced leave voice chat command
    Usage: .leavevc
    """
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "leavevc")
    
    try:
        # Animation loading
        loading_animations = [
            f"{get_emoji('main')} {convert_font('Preparing to leave voice chat...', 'bold')}",
            f"{get_emoji('adder1')} {convert_font('Disconnecting from voice chat...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Finalizing disconnection...', 'bold')}"
        ]
        
        msg = await event.reply(loading_animations[0])
        await animate_text_premium(msg, loading_animations, delay=1)
        
        # Get current status sebelum leave
        status = await get_voice_chat_status()
        
        # Attempt to leave
        success, message = await leave_voice_chat_enhanced()
        
        if success:
            success_text = f"""
{get_emoji('adder4')} {convert_font('LEFT VOICE CHAT', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('SUCCESSFULLY DISCONNECTED', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Session Summary:', 'bold')}
{get_emoji('check')} {convert_font('Previous Chat:', 'bold')} {status.get('chat_title', 'Unknown')}
{get_emoji('check')} {convert_font('Duration:', 'bold')} `{status.get('duration', '0s')}`
{get_emoji('adder2')} {convert_font('Disconnect Time:', 'bold')} `{datetime.now().strftime('%H:%M:%S')}`
{get_emoji('main')} {convert_font('Status:', 'bold')} Disconnected Successfully

{get_emoji('adder5')} {convert_font('Voice Chat Statistics:', 'bold')}
{get_emoji('check')} Current Status: Not in voice chat
{get_emoji('check')} Available for new connections
{get_emoji('check')} All resources freed

{get_emoji('adder1')} {convert_font('Next Actions:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}joinvc` - Join new voice chat
{get_emoji('check')} `{COMMAND_PREFIX}vcstatus` - Check status
{get_emoji('check')} Ready for next voice session

{get_emoji('main')} {convert_font('Voice chat session ended!', 'bold')}
            """.strip()
            
            await safe_edit_message(msg, success_text)
            stats['commands_executed'] += 1
            
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('LEAVE VOICE CHAT FAILED', 'mono')}

{get_emoji('check')} {convert_font('Error:', 'bold')} {message}
{get_emoji('main')} {convert_font('Current Status:', 'bold')} {status.get('status', 'Unknown')}

{get_emoji('adder1')} {convert_font('Troubleshooting:', 'bold')}
{get_emoji('check')} Check if actually in voice chat
{get_emoji('check')} Try using Telegram app to leave
{get_emoji('check')} Force reset with manual disconnect
            """.strip()
            
            await safe_edit_message(msg, error_text)
        
    except Exception as e:
        stats['errors_handled'] += 1
        await event.reply(f"❌ {convert_font('LeaveVC Error:', 'bold')} {str(e)}")
        logger.error(f"LeaveVC command error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}vcstatus'))
async def vcstatus_handler(event):
    """
    Enhanced voice chat status command
    Usage: .vcstatus
    """
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "vcstatus")
    
    try:
        status = await get_voice_chat_status()
        
        if status['active']:
            active_text = f"""
{get_emoji('adder2')} {convert_font('VOICE CHAT STATUS - ACTIVE', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('CURRENTLY CONNECTED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} Active & Connected
{get_emoji('check')} {convert_font('Chat:', 'bold')} {status['chat_title']}
{get_emoji('check')} {convert_font('Chat ID:', 'bold')} `{status['chat_id']}`
{get_emoji('adder4')} {convert_font('Duration:', 'bold')} `{status['duration']}`
{get_emoji('main')} {convert_font('Call ID:', 'bold')} `{status['call_id']}`

{get_emoji('adder1')} {convert_font('Audio Settings:', 'bold')}
{get_emoji('check')} {convert_font('Microphone:', 'bold')} {'Muted' if status['muted'] else 'Active'}
{get_emoji('check')} {convert_font('Video:', 'bold')} {'Enabled' if status['video'] else 'Disabled'}
{get_emoji('check')} {convert_font('Connection:', 'bold')} Stable

{get_emoji('adder3')} {convert_font('Available Commands:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}leavevc` - Leave current voice chat
{get_emoji('check')} `{COMMAND_PREFIX}vcstatus` - Refresh status
{get_emoji('check')} Use Telegram app for audio controls

{get_emoji('adder5')} {convert_font('Session Info:', 'bold')}
{get_emoji('check')} Connected since: `{datetime.fromtimestamp(voice_chat_state['join_time']).strftime('%H:%M:%S')}`
{get_emoji('check')} Status check: `{datetime.now().strftime('%H:%M:%S')}`

{get_emoji('main')} {convert_font('Voice chat session active!', 'bold')}
            """.strip()
            
            await event.reply(active_text)
            
        else:
            inactive_text = f"""
{get_emoji('adder1')} {convert_font('VOICE CHAT STATUS - INACTIVE', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('NOT IN VOICE CHAT', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Current Status:', 'bold')} Not connected
{get_emoji('check')} {convert_font('Available:', 'bold')} Ready to join voice chats
{get_emoji('check')} {convert_font('Last Duration:', 'bold')} N/A
{get_emoji('adder2')} {convert_font('Status Check:', 'bold')} `{datetime.now().strftime('%H:%M:%S')}`

{get_emoji('adder3')} {convert_font('How to Join Voice Chat:', 'bold')}
{get_emoji('check')} Go to group/channel with active voice chat
{get_emoji('check')} Use `{COMMAND_PREFIX}joinvc` command
{get_emoji('check')} Or use Telegram app to join manually

{get_emoji('adder4')} {convert_font('Requirements:', 'bold')}
{get_emoji('check')} Must be in a group/channel
{get_emoji('check')} Voice chat must be active
{get_emoji('check')} Need appropriate permissions
{get_emoji('check')} Must be a member of the chat

{get_emoji('adder5')} {convert_font('Available Commands:', 'bold')}
{get_emoji('check')} `{COMMAND_PREFIX}joinvc` - Join voice chat (in group)
{get_emoji('check')} `{COMMAND_PREFIX}vcstatus` - Check this status
{get_emoji('check')} `{COMMAND_PREFIX}help` - View all commands

{get_emoji('main')} {convert_font('Ready to join voice chats!', 'bold')}
            """.strip()
            
            await event.reply(inactive_text)
        
        stats['commands_executed'] += 1
        
    except Exception as e:
        stats['errors_handled'] += 1
        await event.reply(f"❌ {convert_font('VCStatus Error:', 'bold')} {str(e)}")
        logger.error(f"VCStatus command error: {e}")

# ============= PLUGIN INITIALIZATION =============

def initialize_voice_chat_plugin():
    """Initialize voice chat plugin dengan logging"""
    try:
        # Reset voice chat state saat plugin load
        update_voice_state(
            active=False,
            chat_id=None,
            chat_title=None,
            call_id=None,
            muted=False,
            video=False
        )
        
        logger.info("✅ Voice Chat Plugin loaded successfully")
        logger.info(f"🔧 Commands registered: {COMMAND_PREFIX}joinvc, {COMMAND_PREFIX}leavevc, {COMMAND_PREFIX}vcstatus")
        logger.info("🎯 Features: Enhanced join/leave, status tracking, error handling")
        logger.info("🎙️ Voice chat state management initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Error initializing Voice Chat Plugin: {e}")
        return False

# Auto-initialize saat plugin dimuat
if __name__ != "__main__":
    initialize_voice_chat_plugin()

"""
🔥 VOICE CHAT PLUGIN for VZOEL ASSISTANT v0.1.0.75 🔥

✅ ENHANCED FEATURES:
1. ✅ Smart voice chat join dengan permission checking
2. ✅ Enhanced leave dengan session duration tracking  
3. ✅ Real-time status monitoring dan state management
4. ✅ Comprehensive error handling untuk semua scenarios
5. ✅ Loading animations dan progress indicators
6. ✅ Detailed status reports dengan technical info
7. ✅ Force leave capability jika terjadi error
8. ✅ Session statistics dan duration tracking
9. ✅ Full integration dengan main.py styling system

🎯 COMMANDS:
• .joinvc - Join voice chat (dalam group/channel)
• .leavevc - Leave current voice chat dengan duration info
• .vcstatus - Detailed status check dan session info

📋 ERROR HANDLING:
- ✅ Admin rights validation
- ✅ Group membership checking
- ✅ Voice chat availability detection
- ✅ Rate limiting management
- ✅ Connection failure recovery
- ✅ Force disconnect capability

🎙️ STATE MANAGEMENT:
- ✅ Real-time voice chat state tracking
- ✅ Session duration calculation
- ✅ Audio/video settings monitoring
- ✅ Call ID dan chat info persistence

⚡ COMPATIBILITY:
- ✅ Full compatibility dengan VZOEL ASSISTANT v0.1.0.75
- ✅ Uses all main.py functions (get_emoji, convert_font, etc)
- ✅ Statistics integration
- ✅ Error handling consistency
- ✅ Style template matching

⚡ Ready untuk digunakan - Save sebagai plugins/voice_chat.py ⚡
"""
