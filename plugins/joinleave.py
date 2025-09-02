"""
JoinLeave Plugin for Vzoel Assistant - Enhanced UTF-16 Premium Edition
Fitur: Join/Leave voice chat dengan dukungan premium emoji mapping terbaru
dari formorgan.py dengan UTF-16 encoding yang sudah diperbaiki.
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.1.1 (Enhanced Premium Mapping)
"""

import asyncio
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError, UserNotParticipantError
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.types import InputPeerSelf
from telethon.tl.functions.phone import CreateGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import MessageEntityCustomEmoji

# Plugin Info
PLUGIN_INFO = {
    "name": "joinleave",
    "version": "1.2.1", 
    "description": "Enhanced voice chat handling dengan proper detection dan premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".joinvc", ".leavevc", ".testvcemoji"],
    "features": ["join voice chat", "leave voice chat", "auto UTF-16 premium emoji"]
}

# Premium Emoji Mapping - Enhanced dari formorgan.py (UTF-16 compliant)
PREMIUM_EMOJIS = {
    "main": {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "storm": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "check": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "cross": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "alien": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "plane": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "devil": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "slider": {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

def get_utf16_length(emoji_char):
    """Get UTF-16 length of emoji character"""
    try:
        # Convert to UTF-16 and get byte length, then divide by 2 for character count
        utf16_bytes = emoji_char.encode('utf-16-le')
        return len(utf16_bytes) // 2
    except:
        return 1

def create_premium_emoji_entities(text):
    """Enhanced: Create MessageEntityCustomEmoji entities with compound character support"""
    entities = []
    utf16_offset = 0
    text_pos = 0
    
    # Process text dengan handling compound characters (seperti ⚙️)
    while text_pos < len(text):
        found_emoji = False
        
        # Check setiap premium emoji
        for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
            emoji_char = emoji_data["emoji"]
            emoji_len = len(emoji_char)
            
            # Cek apakah text di posisi ini cocok dengan emoji
            if text[text_pos:text_pos + emoji_len] == emoji_char:
                # Get actual UTF-16 length dari emoji character
                emoji_utf16_length = get_utf16_length(emoji_char)
                
                # Create custom emoji entity
                entity = MessageEntityCustomEmoji(
                    offset=utf16_offset,
                    length=emoji_utf16_length,
                    document_id=int(emoji_data["custom_emoji_id"])
                )
                entities.append(entity)
                
                # Skip emoji characters
                text_pos += emoji_len
                utf16_offset += emoji_utf16_length
                found_emoji = True
                break
        
        if not found_emoji:
            # Regular character, advance by 1
            char = text[text_pos]
            char_utf16_length = get_utf16_length(char)
            utf16_offset += char_utf16_length
            text_pos += 1
    
    return entities

def get_emoji(emoji_type):
    """Get premium emoji with fallback"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

async def safe_send_message(event, text):
    """Send message with premium emoji entities - FIXED: Return message object"""
    try:
        entities = create_premium_emoji_entities(text)
        if entities:
            return await event.reply(text, formatting_entities=entities)
        else:
            return await event.reply(text)
    except Exception as e:
        # Fallback to regular message if premium emojis fail
        return await event.reply(text)

async def safe_edit_message(message, text):
    """Safely edit message dengan error handling"""
    if not message:
        return False
    try:
        entities = create_premium_emoji_entities(text)
        if entities:
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
        return True
    except Exception as e:
        print(f"[JoinLeave] Edit message error: {e}")
        return False

def get_prefix():
    """Ambil prefix command dari environment atau default '.'"""
    try:
        import os
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

async def is_owner_check(client, user_id):
    """Simple owner check - replace with your owner ID"""
    OWNER_ID = 7847025168  # Replace with your actual owner ID
    return user_id == OWNER_ID

async def joinvc_handler(event):
    """Enhanced userbot voice chat join - simple participant join without admin requirements"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        
        # Loading message dengan premium emoji
        loading_msg = await safe_send_message(event, f"{get_emoji('storm')} **Connecting to voice chat...**")
        
        # ENHANCED USERBOT: Detect voice chat dengan multiple methods
        active_call = None
        
        try:
            # Method 1: Full chat request (recommended)
            if hasattr(chat, 'broadcast') and not chat.broadcast:  # Not a channel
                full_chat = await event.client(GetFullChannelRequest(chat))
                active_call = getattr(full_chat.full_chat, 'call', None)
            elif hasattr(chat, 'megagroup') and chat.megagroup:  # Supergroup
                full_chat = await event.client(GetFullChannelRequest(chat))
                active_call = getattr(full_chat.full_chat, 'call', None)
            else:
                # Method 2: Direct attribute check
                active_call = getattr(chat, 'call', None)
        except Exception as detection_error:
            # Method 3: Fallback detection
            active_call = getattr(chat, 'call', None)
            print(f"[JoinVC] Detection fallback used: {detection_error}")
        
        if not active_call:
            no_vc_text = f"""{get_emoji('alien')} **NO ACTIVE VOICE CHAT**

{get_emoji('check')} **Chat:** {getattr(chat, 'title', 'Unknown')}
{get_emoji('cross')} **Status:** Voice chat tidak aktif
{get_emoji('plane')} **Action:** Start voice chat di grup ini dulu

{get_emoji('slider')} **Tip:** Voice chat harus dimulai oleh admin grup terlebih dahulu!"""
            
            await safe_edit_message(loading_msg, no_vc_text)
            return
        
        # Update status - voice chat found
        await safe_edit_message(loading_msg, f"{get_emoji('check')} **Voice chat detected! Joining...**")
        
        try:
            # SIMPLE USERBOT JOIN: Create proper join request with required parameters
            from telethon.tl.types import DataJSON
            
            # Create empty params for simple voice join (not video/screen share)
            join_params = DataJSON(data='{}')
            
            await event.client(JoinGroupCallRequest(
                call=active_call,
                join_as=InputPeerSelf(),
                params=join_params
            ))
            
            # Success message
            success_text = f"""{get_emoji('main')} **VOICE CHAT JOINED!**

{get_emoji('check')} **Chat:** {getattr(chat, 'title', 'Unknown')}
{get_emoji('plane')} **Status:** Connected as voice participant
{get_emoji('storm')} **Mode:** Simple user join (no music bot)

{get_emoji('slider')} **Use** `.leavevc` **to disconnect**"""
            
            await safe_edit_message(loading_msg, success_text)
            
        except Exception as join_error:
            # Handle join failures dengan detailed info
            error_name = type(join_error).__name__
            error_msg = str(join_error)[:100]
            
            fail_text = f"""{get_emoji('devil')} **JOIN VOICE CHAT FAILED**

{get_emoji('cross')} **Error:** {error_name}
{get_emoji('alien')} **Details:** {error_msg}

{get_emoji('storm')} **Possible Issues:**
• Voice chat restricted to admins only
• Group doesn't allow regular users in VC  
• Network/connection problems
• Voice chat participant limit reached

{get_emoji('check')} **Solutions:**
• Ask admin to open VC for all members
• Check internet connection
• Try again after a few seconds
• Verify you're still in the group"""
            
            await safe_edit_message(loading_msg, fail_text)
        
    except ChatAdminRequiredError:
        admin_text = f"""{get_emoji('devil')} **ADMIN ACCESS REQUIRED**

{get_emoji('cross')} **Issue:** Bot needs admin permissions
{get_emoji('check')} **Solution:** Ask admin to allow all members to join voice chat
{get_emoji('storm')} **Alternative:** Make bot admin temporarily"""
        
        await safe_send_message(event, admin_text)
        
    except UserAlreadyInvitedError:
        already_text = f"""{get_emoji('check')} **ALREADY IN VOICE CHAT**

{get_emoji('main')} **Status:** Bot sudah terhubung ke voice chat
{get_emoji('plane')} **Action:** Use `.leavevc` to disconnect first
{get_emoji('slider')} **Then:** Try `.joinvc` again if needed"""
        
        await safe_send_message(event, already_text)
        
    except Exception as e:
        # Generic error handler
        generic_error = f"""{get_emoji('alien')} **UNEXPECTED ERROR**

{get_emoji('cross')} **Error:** {str(e)[:80]}
{get_emoji('storm')} **Type:** {type(e).__name__}

{get_emoji('devil')} **Try:**
• Restart the userbot
• Check internet connection
• Verify group permissions
• Contact support if issue persists"""
        
        await safe_send_message(event, generic_error)

async def leavevc_handler(event):
    """Enhanced handler for .leavevc command dengan proper voice chat handling"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        
        # Loading message
        loading_msg = await safe_send_message(event, f"{get_emoji('storm')} Keluar dari voice chat...")
        
        # Get full chat info untuk voice chat data
        full_chat = None
        active_call = None
        
        try:
            if hasattr(chat, 'broadcast') and chat.broadcast:
                # Channel
                full_chat = await event.client(GetFullChannelRequest(chat))
                active_call = getattr(full_chat.full_chat, 'call', None)
            elif hasattr(chat, 'megagroup') or hasattr(chat, 'title'):
                # Supergroup/Group
                full_chat = await event.client(GetFullChannelRequest(chat))
                active_call = getattr(full_chat.full_chat, 'call', None)
            else:
                # Regular group
                active_call = getattr(chat, 'call', None)
                
        except Exception as chat_error:
            # Fallback
            active_call = getattr(chat, 'call', None)
            print(f"[LeaveVC] Chat info error: {chat_error}, using fallback")
        
        if not active_call:
            text = f"""
{get_emoji('alien')} **VOICE CHAT STATUS**

{get_emoji('check')} Chat: {getattr(chat, 'title', 'Unknown')}
{get_emoji('cross')} Status: Tidak ada voice chat aktif
{get_emoji('plane')} Info: Bot mungkin sudah tidak di voice chat

{get_emoji('slider')} Voice chat sudah inactive atau bot sudah keluar
            """.strip()
            
            await safe_edit_message(loading_msg, text)
            return
        
        # Leave voice chat
        try:
            await event.client(LeaveGroupCallRequest(call=active_call))
            
            success_text = f"""
**✈️ BERHASIL KELUAR VOICE CHAT**

**⚙️ Chat:** {getattr(chat, 'title', 'Unknown')}
**🤩 Status:** Disconnected dari voice chat
**⛈ Action:** Left voice chat successfully

**🎚️ Gunakan** `.joinvc` **untuk join lagi**
            """.strip()
            
            await safe_edit_message(loading_msg, success_text)
            
        except Exception as leave_error:
            error_text = f"""
{get_emoji('devil')} **GAGAL KELUAR VOICE CHAT**

{get_emoji('cross')} Error: {str(leave_error)[:60]}
{get_emoji('storm')} Type: {type(leave_error).__name__}

{get_emoji('alien')} Kemungkinan penyebab:
• Bot sudah tidak di voice chat
• Connection issue dengan server
• Voice chat sudah ditutup

{get_emoji('check')} Bot mungkin sudah keluar secara otomatis
            """.strip()
            
            await safe_edit_message(loading_msg, error_text)
        
    except Exception as e:
        error_text = f"""
{get_emoji('alien')} **UNEXPECTED ERROR**

{get_emoji('cross')} Error: {str(e)}
{get_emoji('storm')} Type: {type(e).__name__}

{get_emoji('devil')} Coba restart bot jika masalah berlanjut
        """.strip()
        await safe_send_message(event, error_text)

async def test_vc_emoji_handler(event):
    """Test UTF-16 emoji detection for VC plugin"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    test_text = f"""
{get_emoji('main')} **JOIN/LEAVE VC TEST**

{get_emoji('check')} Join voice chat: `.joinvc`
{get_emoji('plane')} Leave voice chat: `.leavevc`

{get_emoji('storm')} Status emojis:
• {get_emoji('check')} Success
• {get_emoji('devil')} Admin required  
• {get_emoji('storm')} Already joined
• {get_emoji('alien')} Error
• {get_emoji('plane')} Left VC

{get_emoji('slider')} Auto UTF-16 premium emoji detection active!
"""
    
    await safe_send_message(event, test_text.strip())

def get_plugin_info():
    """Return plugin info for plugin loader"""
    return PLUGIN_INFO

def setup(client):
    """Setup plugin handlers"""
    client.add_event_handler(joinvc_handler, events.NewMessage(pattern=r"\.joinvc"))
    client.add_event_handler(leavevc_handler, events.NewMessage(pattern=r"\.leavevc"))
    client.add_event_handler(test_vc_emoji_handler, events.NewMessage(pattern=r"\.testvcemoji"))
    print(f"[JoinLeave] Plugin loaded with auto UTF-16 emoji detection v{PLUGIN_INFO['version']}")