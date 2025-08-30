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
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import DataJSON, MessageEntityCustomEmoji, InputPeerSelf

# Plugin Info
PLUGIN_INFO = {
    "name": "joinleave",
    "version": "1.2.0", 
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
    "alien": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "plane": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "devil": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "slider": {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

def get_utf16_length(emoji_char):
    """Get UTF-16 length of emoji character"""
    try:
        # Convert to UTF-16 and get byte length, then divide by 2 for character count
        utf16_bytes = emoji_char.encode('utf-16le')
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
    """Send message with premium emoji entities"""
    try:
        entities = create_premium_emoji_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception as e:
        # Fallback to regular message if premium emojis fail
        await event.reply(text)

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
    """Enhanced handler for .joinvc command dengan proper voice chat detection"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        
        # Loading message dengan premium emoji
        loading_msg = await safe_send_message(event, f"{get_emoji('storm')} Mencari voice chat aktif...")
        
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
                # Regular group - cek call attribute langsung
                active_call = getattr(chat, 'call', None)
                
        except Exception as chat_error:
            # Fallback: cek call attribute langsung dari chat
            active_call = getattr(chat, 'call', None)
            print(f"[JoinVC] Chat info error: {chat_error}, using fallback")
        
        if not active_call:
            text = f"""
{get_emoji('alien')} **VOICE CHAT STATUS**

{get_emoji('check')} Chat: {getattr(chat, 'title', 'Unknown')}
{get_emoji('cross')} Status: Tidak ada voice chat aktif
{get_emoji('plane')} Solusi: 
• Mulai voice chat di grup ini
• Atau gunakan command di grup dengan voice chat aktif

{get_emoji('slider')} Coba lagi setelah voice chat dimulai!
            """.strip()
            
            await loading_msg.edit(text, formatting_entities=create_premium_emoji_entities(text))
            return
        
        # Update loading message
        await loading_msg.edit(
            f"{get_emoji('check')} Voice chat ditemukan! Bergabung...",
            formatting_entities=create_premium_emoji_entities(f"{get_emoji('check')} Voice chat ditemukan! Bergabung...")
        )
        
        # Join voice chat dengan parameter yang benar
        try:
            # Method 1: Standard join
            await event.client(JoinGroupCallRequest(
                call=active_call,
                join_as=InputPeerSelf(),  # Join sebagai diri sendiri
                params=DataJSON(data='{"ufrag":"","pwd":""}'),
                muted=False,
                video_stopped=True
            ))
            
            success_text = f"""
{get_emoji('check')} **BERHASIL JOIN VOICE CHAT!**

{get_emoji('main')} Chat: {getattr(chat, 'title', 'Unknown')}
{get_emoji('plane')} Status: Connected ke voice chat
{get_emoji('storm')} Mode: Audio only (video disabled)
{get_emoji('devil')} Muted: No (unmuted)

{get_emoji('slider')} Gunakan `{get_prefix()}leavevc` untuk keluar
            """.strip()
            
            await loading_msg.edit(success_text, formatting_entities=create_premium_emoji_entities(success_text))
            
        except Exception as join_error:
            # Method 2: Fallback dengan parameter minimal
            try:
                await event.client(JoinGroupCallRequest(
                    call=active_call,
                    join_as=await event.client.get_me(),
                    params=DataJSON(data='{}')
                ))
                
                fallback_text = f"""
{get_emoji('check')} **JOIN VOICE CHAT (FALLBACK)**

{get_emoji('main')} Berhasil join dengan mode fallback
{get_emoji('storm')} Chat: {getattr(chat, 'title', 'Unknown')}
{get_emoji('plane')} Status: Connected

{get_emoji('slider')} Gunakan `{get_prefix()}leavevc` untuk keluar
                """.strip()
                
                await loading_msg.edit(fallback_text, formatting_entities=create_premium_emoji_entities(fallback_text))
                
            except Exception as fallback_error:
                error_text = f"""
{get_emoji('alien')} **GAGAL JOIN VOICE CHAT**

{get_emoji('cross')} Primary Error: {str(join_error)[:50]}
{get_emoji('cross')} Fallback Error: {str(fallback_error)[:50]}

{get_emoji('devil')} Kemungkinan penyebab:
• Tidak punya permission join voice chat
• Voice chat penuh atau restricted
• Connection issue dengan Telegram servers
• Bot belum join grup sebagai member

{get_emoji('storm')} Solusi:
• Pastikan bot adalah admin atau member grup
• Coba restart bot dan ulangi command
• Periksa connection internet
                """.strip()
                
                await loading_msg.edit(error_text, formatting_entities=create_premium_emoji_entities(error_text))
        
    except ChatAdminRequiredError:
        text = f"""
{get_emoji('devil')} **ADMIN REQUIRED**

{get_emoji('cross')} Bot membutuhkan admin permission
{get_emoji('check')} Atau pastikan voice chat open untuk semua member
{get_emoji('storm')} Contact admin grup untuk permission
        """.strip()
        await safe_send_message(event, text)
        
    except UserAlreadyInvitedError:
        text = f"""
{get_emoji('check')} **SUDAH JOIN VOICE CHAT**

{get_emoji('main')} Bot sudah berada di voice chat ini
{get_emoji('plane')} Gunakan `{get_prefix()}leavevc` untuk keluar dulu
{get_emoji('storm')} Kemudian coba join lagi jika perlu
        """.strip()
        await safe_send_message(event, text)
        
    except Exception as e:
        error_text = f"""
{get_emoji('alien')} **UNEXPECTED ERROR**

{get_emoji('cross')} Error: {str(e)}
{get_emoji('storm')} Type: {type(e).__name__}

{get_emoji('devil')} Coba:
• Restart bot
• Check internet connection 
• Verify grup permissions
        """.strip()
        await safe_send_message(event, error_text)

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
            
            await loading_msg.edit(text, formatting_entities=create_premium_emoji_entities(text))
            return
        
        # Leave voice chat
        try:
            await event.client(LeaveGroupCallRequest(call=active_call))
            
            success_text = f"""
{get_emoji('plane')} **BERHASIL KELUAR VOICE CHAT**

{get_emoji('check')} Chat: {getattr(chat, 'title', 'Unknown')}
{get_emoji('main')} Status: Disconnected dari voice chat
{get_emoji('storm')} Action: Left voice chat successfully

{get_emoji('slider')} Gunakan `{get_prefix()}joinvc` untuk join lagi
            """.strip()
            
            await loading_msg.edit(success_text, formatting_entities=create_premium_emoji_entities(success_text))
            
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
            
            await loading_msg.edit(error_text, formatting_entities=create_premium_emoji_entities(error_text))
        
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