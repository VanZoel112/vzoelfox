# plugins/user_id.py
"""
User ID Plugin - Get user information by reply or username
Author: Vzoel Fox's (LTPN)
"""

import asyncio
import re
from telethon import events
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError
from telethon.tl.types import User, Chat, Channel

async def setup(client):
    """Plugin initialization function"""
    
    @client.on(events.NewMessage(pattern=r'\.id$'))
    async def id_handler(event):
        """Get ID of replied user or current chat"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            reply = await event.get_reply_message()
            
            if reply:
                # Get replied user info
                user = await reply.get_sender()
                chat = await event.get_chat()
                
                if user:
                    user_info = f"""
🆔 **USER INFORMATION**

╔══════════════════════════════╗
   👤 𝗨𝗦𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 👤
╚══════════════════════════════╝

🏷️ **Name:** {user.first_name or 'Unknown'} {user.last_name or ''}
🆔 **User ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}
🤖 **Is Bot:** {'Yes' if getattr(user, 'bot', False) else 'No'}
🔒 **Verified:** {'Yes' if getattr(user, 'verified', False) else 'No'}
🌟 **Premium:** {'Yes' if getattr(user, 'premium', False) else 'No'}
🚫 **Deleted:** {'Yes' if getattr(user, 'deleted', False) else 'No'}

📞 **Phone:** {getattr(user, 'phone', 'Hidden')}
🌍 **Language:** {getattr(user, 'lang_code', 'Unknown')}
📝 **Bio:** {getattr(user, 'about', 'No bio')[:50]}{'...' if len(getattr(user, 'about', '')) > 50 else ''}

💬 **Chat ID:** `{chat.id}`
📊 **Chat Type:** {type(chat).__name__}

⚡ **Plugin by Vzoel Fox's (LTPN)**
                    """.strip()
                    
                    await event.edit(user_info)
                else:
                    await event.edit("❌ **Could not get user information from replied message**")
            else:
                # Get current chat info
                chat = await event.get_chat()
                
                chat_info = f"""
🆔 **CHAT INFORMATION**

╔══════════════════════════════╗
   💬 𝗖𝗛𝗔𝗧 𝗗𝗘𝗧𝗔𝗜𝗟𝗦 💬
╚══════════════════════════════╝

🏷️ **Title:** {getattr(chat, 'title', 'Private Chat')}
🆔 **Chat ID:** `{chat.id}`
📊 **Type:** {type(chat).__name__}
👥 **Members:** {getattr(chat, 'participants_count', 'Unknown')}

📱 **Username:** @{getattr(chat, 'username', 'None')}
📝 **Description:** {getattr(chat, 'about', 'No description')[:50]}{'...' if len(getattr(chat, 'about', '')) > 50 else ''}

🔒 **Verified:** {'Yes' if getattr(chat, 'verified', False) else 'No'}
🚫 **Restricted:** {'Yes' if getattr(chat, 'restricted', False) else 'No'}

⚡ **Plugin by Vzoel Fox's (LTPN)**
                """.strip()
                
                await event.edit(chat_info)
                
        except Exception as e:
            await event.edit(f"❌ **ID Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.id\s+(@?\w+)'))
    async def id_username_handler(event):
        """Get user ID by username"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        username = event.pattern_match.group(1).strip()
        
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]
        
        try:
            msg = await event.edit(f"🔍 **Looking up user:** @{username}...")
            
            try:
                user = await client.get_entity(username)
                
                if isinstance(user, User):
                    user_info = f"""
🆔 **USER LOOKUP RESULT**

╔══════════════════════════════╗
   👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢 👤
╚══════════════════════════════╝

🔍 **Searched:** @{username}
✅ **Found:** Yes

🏷️ **Name:** {user.first_name or 'Unknown'} {user.last_name or ''}
🆔 **User ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}
🤖 **Is Bot:** {'Yes' if getattr(user, 'bot', False) else 'No'}
🔒 **Verified:** {'Yes' if getattr(user, 'verified', False) else 'No'}
🌟 **Premium:** {'Yes' if getattr(user, 'premium', False) else 'No'}
🚫 **Deleted:** {'Yes' if getattr(user, 'deleted', False) else 'No'}

📞 **Phone:** {getattr(user, 'phone', 'Hidden')}
🌍 **Language:** {getattr(user, 'lang_code', 'Unknown')}
📊 **Status:** {getattr(user, 'status', 'Unknown')}

⚡ **Plugin by Vzoel Fox's (LTPN)**
                    """.strip()
                    
                elif isinstance(user, (Chat, Channel)):
                    user_info = f"""
🆔 **CHAT LOOKUP RESULT**

╔══════════════════════════════╗
   💬 𝗖𝗛𝗔𝗧 𝗜𝗡𝗙𝗢 💬
╚══════════════════════════════╝

🔍 **Searched:** @{username}
✅ **Found:** Yes

🏷️ **Title:** {getattr(user, 'title', 'Unknown')}
🆔 **Chat ID:** `{user.id}`
📊 **Type:** {type(user).__name__}
📱 **Username:** @{getattr(user, 'username', 'None')}
👥 **Members:** {getattr(user, 'participants_count', 'Unknown')}

📝 **Description:** {getattr(user, 'about', 'No description')[:100]}{'...' if len(getattr(user, 'about', '')) > 100 else ''}

🔒 **Verified:** {'Yes' if getattr(user, 'verified', False) else 'No'}
🚫 **Restricted:** {'Yes' if getattr(user, 'restricted', False) else 'No'}

⚡ **Plugin by Vzoel Fox's (LTPN)**
                    """.strip()
                else:
                    user_info = f"""
🆔 **ENTITY FOUND**

🔍 **Searched:** @{username}
✅ **Entity ID:** `{user.id}`
📊 **Type:** {type(user).__name__}

⚡ **Plugin by Vzoel Fox's (LTPN)**
                    """.strip()
                
                await msg.edit(user_info)
                
            except UsernameNotOccupiedError:
                await msg.edit(f"""
❌ **USER NOT FOUND**

🔍 **Searched:** @{username}
❌ **Result:** Username not found
                
💡 **Tips:**
• Check spelling of username
• User might have changed username
• User account might be deleted
• Try without @ symbol

⚡ **Plugin by Vzoel Fox's (LTPN)**
                """.strip())
                
            except UsernameInvalidError:
                await msg.edit(f"""
❌ **INVALID USERNAME**

🔍 **Searched:** @{username}
❌ **Error:** Invalid username format
                
💡 **Valid username format:**
• 5-32 characters
• Letters, numbers, underscores only
• Must start with letter
• No consecutive underscores

⚡ **Plugin by Vzoel Fox's (LTPN)**
                """.strip())
                
        except Exception as e:
            await event.edit(f"❌ **Lookup Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.myid'))
    async def myid_handler(event):
        """Get your own ID and info"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            my_info = f"""
🆔 **YOUR ACCOUNT INFORMATION**

╔══════════════════════════════╗
   👤 𝗬𝗢𝗨𝗥 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 👤
╚══════════════════════════════╝

🏷️ **Name:** {me.first_name or 'Unknown'} {me.last_name or ''}
🆔 **User ID:** `{me.id}`
📱 **Username:** @{me.username or 'None'}
📞 **Phone:** +{me.phone or 'Hidden'}

🔒 **Verified:** {'Yes' if getattr(me, 'verified', False) else 'No'}
🌟 **Premium:** {'Yes' if getattr(me, 'premium', False) else 'No'}
🤖 **Is Bot:** {'Yes' if getattr(me, 'bot', False) else 'No'}
🚫 **Restricted:** {'Yes' if getattr(me, 'restricted', False) else 'No'}

🌍 **Language:** {getattr(me, 'lang_code', 'Unknown')}
📝 **Bio:** {getattr(me, 'about', 'No bio')[:100]}{'...' if len(getattr(me, 'about', '')) > 100 else ''}

⚡ **Plugin by Vzoel Fox's (LTPN)**
            """.strip()
            
            await event.edit(my_info)
            
        except Exception as e:
            await event.edit(f"❌ **Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.idinfo'))
    async def idinfo_handler(event):
        """Information about ID plugin"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            info_text = """
🆔 **ID PLUGIN INFORMATION**

╔══════════════════════════════╗
   ℹ️ 𝗣𝗟𝗨𝗚𝗜𝗡 𝗜𝗡𝗙𝗢 ℹ️
╚══════════════════════════════╝

📋 **Available Commands:**
• `.id` - Get chat/user ID (reply to message)
• `.id @username` - Look up user by username
• `.myid` - Get your own account info
• `.idinfo` - Show this information

🔍 **Usage Examples:**
• Reply to message + `.id` → Get user info
• `.id @username` → Look up specific user
• `.id vzoel_fox` → Look up without @
• `.myid` → Get your account details

📊 **Information Provided:**
• User ID & Username
• Full name & phone number
• Bot/Premium/Verified status
• Account language & bio
• Chat details & member count
• Profile verification status

💡 **Tips:**
• Works with users, bots, groups, channels
• Supports both @username and username
• Reply method works for any message
• Shows detailed account information

⚡ **Plugin by Vzoel Fox's (LTPN)**
            """.strip()
            
            await event.edit(info_text)
            
        except Exception as e:
            await event.edit(f"❌ **Error:** {str(e)}")