"""
JoinLeave Plugin for Vzoel Assistant - Enhanced UTF-16 Premium Edition
Fitur: Join/Leave voice chat dengan dukungan premium emoji mapping terbaru
dari formorgan.py dengan UTF-16 encoding yang sudah diperbaiki.
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.1.1 (Enhanced Premium Mapping)
"""

import asyncio
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.types import DataJSON, MessageEntityCustomEmoji

# Plugin Info
PLUGIN_INFO = {
    "name": "joinleave",
    "version": "1.1.1", 
    "description": "Join/Leave voice chat dengan enhanced premium emoji mapping support",
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
    """Automatically create MessageEntityCustomEmoji entities for premium emojis"""
    entities = []
    utf16_offset = 0
    
    # Process text character by character to get accurate UTF-16 offsets
    for i, char in enumerate(text):
        # Check if this character matches any premium emoji
        for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
            if char == emoji_data["emoji"]:
                # Get actual UTF-16 length of this emoji
                emoji_length = get_utf16_length(char)
                
                # Create custom emoji entity with automatic offset/length
                entity = MessageEntityCustomEmoji(
                    offset=utf16_offset,
                    length=emoji_length,
                    document_id=int(emoji_data["custom_emoji_id"])
                )
                entities.append(entity)
                break
        
        # Update UTF-16 offset for next character
        utf16_offset += get_utf16_length(char)
    
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

async def is_owner_check(client, user_id):
    """Simple owner check - replace with your owner ID"""
    OWNER_ID = 7847025168  # Replace with your actual owner ID
    return user_id == OWNER_ID

async def joinvc_handler(event):
    """Handler for .joinvc command"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        
        # Check if there's an active voice chat
        if not hasattr(chat, 'call') or chat.call is None:
            text = f"{get_emoji('main')} Tidak ada voice chat aktif di grup ini!"
            await safe_send_message(event, text)
            return
        
        # Join voice chat with corrected parameters
        try:
            await event.client(JoinGroupCallRequest(
                call=chat.call,
                join_as=await event.client.get_me(),
                params=DataJSON(data='{}')
            ))
        except TypeError:
            # Fallback for older API versions
            await event.client(JoinGroupCallRequest(
                call=chat.call,
                join_as=await event.client.get_me(),
                params=DataJSON(data='{}')
            ))
        
        text = f"{get_emoji('check')} Berhasil join voice chat!"
        await safe_send_message(event, text)
        
    except ChatAdminRequiredError:
        text = f"{get_emoji('devil')} Butuh admin untuk join voice chat!"
        await safe_send_message(event, text)
    except UserAlreadyInvitedError:
        text = f"{get_emoji('storm')} Sudah join di voice chat!"
        await safe_send_message(event, text)
    except Exception as e:
        text = f"{get_emoji('alien')} Error join VC: {str(e)}"
        await safe_send_message(event, text)

async def leavevc_handler(event):
    """Handler for .leavevc command"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        
        # Check if there's an active voice chat
        if not hasattr(chat, 'call') or chat.call is None:
            text = f"{get_emoji('main')} Tidak ada voice chat aktif di grup ini!"
            await safe_send_message(event, text)
            return
        
        # Leave voice chat
        await event.client(LeaveGroupCallRequest(
            call=chat.call
        ))
        
        text = f"{get_emoji('plane')} Berhasil leave voice chat!"
        await safe_send_message(event, text)
        
    except Exception as e:
        text = f"{get_emoji('alien')} Error leave VC: {str(e)}"
        await safe_send_message(event, text)

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