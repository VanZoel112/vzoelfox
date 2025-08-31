#!/usr/bin/env python3
"""
Tag All Plugin dengan Premium Emoji Support - Enhanced UTF-16 Edition
"""

import re
import asyncio
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError, FloodWaitError

@events.register(events.NewMessage(pattern=r'^\.tagall(?:\s+(.*))?$', outgoing=True))
async def tagall_handler(event):
    global client
    if client is None:
        client = event.client
    
    try:
        # Check if in group/channel
        chat = await event.get_chat()
        if not isinstance(chat, (Channel, Chat)):
            return
        
        # Get all participants
        participants = await client.get_participants(event.chat_id)
        
        # Tag users
        for user in participants:
            if hasattr(user, 'username') and user.username:
                current_tags += f"@{user.username} "
            elif hasattr(user, 'first_name'):
                current_tags += f"[{user.first_name}](tg://user?id={user.id}) "
                
    except ChatAdminRequiredError:
        pass
    except FloodWaitError as e:
        pass

@events.register(events.NewMessage(pattern=r'^\.cekid(?:\s+@?(\w+))?$', outgoing=True))
async def cekid_handler(event):
    global client
    if client is None:
        client = event.client
    
    try:
        target_user = None
        username = event.pattern_match.group(1)
        
        if event.is_reply:
            reply_message = await event.get_reply_message()
            if reply_message.sender:
                target_user = reply_message.sender
        elif username:
            target_user = await client.get_entity(username)
        
        # Display user info using properties
        user_id = target_user.id
        first_name = target_user.first_name or 'Tidak ada'
        username_display = target_user.username or 'Tidak ada'
        is_bot = getattr(target_user, 'bot', False)
        is_premium = getattr(target_user, 'premium', False)
        
    except Exception as e:
        pass