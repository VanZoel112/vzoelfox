"""
JoinLeave Plugin for Vzoel Assistant
Fitur: Join/Leave voice chat sederhana tanpa monitoring, mapping emoji manual premium support.
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0
"""

import asyncio
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.types import DataJSON

# Plugin Info
PLUGIN_INFO = {
    "name": "joinleave",
    "version": "1.0.0", 
    "description": "Join/Leave voice chat sederhana dengan premium emoji support manual mapping.",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".joinvc", ".leavevc"],
    "features": ["join voice chat", "leave voice chat", "premium emoji"]
}

# Manual Premium Emoji Mapping berdasarkan data yang diberikan
PREMIUM_EMOJIS = {
    "main": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "storm": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "check": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "alien": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "plane": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "devil": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "slider": {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

def get_emoji(emoji_type):
    """Get premium emoji with fallback"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

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
            await event.reply(f"{get_emoji('main')} Tidak ada voice chat aktif di grup ini!")
            return
        
        # Join voice chat
        await event.client(JoinGroupCallRequest(
            call=chat.call,
            join_as=await event.client.get_me(),
            params=DataJSON(data='{}')
        ))
        
        await event.reply(f"{get_emoji('check')} Berhasil join voice chat!")
        
    except ChatAdminRequiredError:
        await event.reply(f"{get_emoji('devil')} Butuh admin untuk join voice chat!")
    except UserAlreadyInvitedError:
        await event.reply(f"{get_emoji('storm')} Sudah join di voice chat!")
    except Exception as e:
        await event.reply(f"{get_emoji('alien')} Error join VC: {str(e)}")

async def leavevc_handler(event):
    """Handler for .leavevc command"""
    if not await is_owner_check(event.client, event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        
        # Check if there's an active voice chat
        if not hasattr(chat, 'call') or chat.call is None:
            await event.reply(f"{get_emoji('main')} Tidak ada voice chat aktif di grup ini!")
            return
        
        # Leave voice chat
        await event.client(LeaveGroupCallRequest(
            call=chat.call
        ))
        
        await event.reply(f"{get_emoji('plane')} Berhasil leave voice chat!")
        
    except Exception as e:
        await event.reply(f"{get_emoji('alien')} Error leave VC: {str(e)}")

def get_plugin_info():
    """Return plugin info for plugin loader"""
    return PLUGIN_INFO

def setup(client):
    """Setup plugin handlers"""
    client.add_event_handler(joinvc_handler, events.NewMessage(pattern=r"\.joinvc"))
    client.add_event_handler(leavevc_handler, events.NewMessage(pattern=r"\.leavevc"))
    print("[JoinLeave] Plugin loaded successfully!")