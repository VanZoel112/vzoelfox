# plugins/sangmata.py
"""
SangMata History Plugin
Track name/username history using SangMata bot
Author: Vzoel Fox's (LTPN)
"""

import asyncio
import re
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError

async def setup(client):
    """Plugin initialization function"""
    
    @client.on(events.NewMessage(pattern=r'\.sg'))
    async def sangmata_handler(event):
        """Get user history using SangMata bot"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            # Check if replying to a message
            reply = await event.get_reply_message()
            
            if not reply:
                await event.edit("❌ **Reply to a user's message to check their history!**")
                return
            
            user = await reply.get_sender()
            
            if not user:
                await event.edit("❌ **Could not get user information!**")
                return
            
            # Animation
            animations = [
                f"🔍 **Searching history for** {user.first_name}...",
                "📡 **Contacting SangMata bot...**",
                "⚡ **Processing request...**",
                "📊 **Retrieving data...**"
            ]
            
            msg = await event.edit(animations[0])
            
            for anim in animations[1:]:
                await asyncio.sleep(1.5)
                await msg.edit(anim)
            
            # Try to forward message to SangMata bot
            sangmata_bot = "@SangMataInfo_bot"
            
            try:
                # Forward the replied message to SangMata bot
                await client.forward_messages(sangmata_bot, reply)
                
                await msg.edit(f"""
✅ **HISTORY REQUEST SENT!**

👤 **User:** {user.first_name or 'Unknown'} {user.last_name or ''}
🆔 **ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}
🤖 **Bot:** @SangMataInfo_bot

📝 **Check your chat with SangMata bot for results**
⏱️ **Response usually takes 3-10 seconds**

🔍 **What SangMata shows:**
• Name history changes
• Username history changes  
• Profile photo changes
• Join/leave dates in groups

⚡ **Plugin by Vzoel Fox's (LTPN)**
                """.strip())
                
            except Exception as forward_error:
                # Fallback: Send user ID directly to SangMata
                try:
                    await client.send_message(sangmata_bot, str(user.id))
                    
                    await msg.edit(f"""
✅ **HISTORY REQUEST SENT!** (Fallback Method)

👤 **User:** {user.first_name or 'Unknown'} {user.last_name or ''}
🆔 **ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}
🤖 **Bot:** @SangMataInfo_bot

📝 **User ID sent to SangMata bot**
⏱️ **Check @SangMataInfo_bot for results**

🔍 **SangMata will show complete history**
⚡ **Plugin by Vzoel Fox's (LTPN)**
                    """.strip())
                    
                except Exception as send_error:
                    await msg.edit(f"""
⚠️ **MANUAL ACTION REQUIRED**

👤 **User:** {user.first_name or 'Unknown'} {user.last_name or ''}
🆔 **User ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}

❌ **Auto-forward failed:** {str(forward_error)}

🔧 **Manual Steps:**
1. Go to @SangMataInfo_bot
2. Send this User ID: `{user.id}`
3. Or forward the replied message manually

⚡ **Plugin by Vzoel Fox's (LTPN)**
                    """.strip())
                
        except Exception as e:
            await event.edit(f"❌ **SangMata Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.sginfo'))
    async def sangmata_info_handler(event):
        """Information about SangMata plugin"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            info_text = """
🤖 **SANGMATA PLUGIN INFO**

╔══════════════════════════════╗
   🔍 𝗛𝗜𝗦𝗧𝗢𝗥𝗬 𝗧𝗥𝗔𝗖𝗞𝗘𝗥 🔍
╚══════════════════════════════╝

📋 **Available Commands:**
• `.sg` - Check user history (reply to message)
• `.sginfo` - Show this information
• `.sgtest` - Test SangMata bot connection

🔍 **What SangMata Tracks:**
• Name changes (first & last name)
• Username changes (@username)
• Profile picture changes
• Bio/About changes
• Join/leave dates in groups
• Group admin status changes

📝 **How to Use:**
1. Reply to any user's message
2. Type `.sg`
3. Check @SangMataInfo_bot for results

🤖 **SangMata Bot:** @SangMataInfo_bot
⚡ **Plugin by Vzoel Fox's (LTPN)**

💡 **Tip:** SangMata only tracks changes after the user interacts with the bot first time.
            """.strip()
            
            await event.edit(info_text)
            
        except Exception as e:
            await event.edit(f"❌ **Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.sgtest'))
    async def sangmata_test_handler(event):
        """Test SangMata bot connection"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            msg = await event.edit("🧪 **Testing SangMata connection...**")
            
            sangmata_bot = "@SangMataInfo_bot"
            
            # Try to send a test message
            try:
                await client.send_message(sangmata_bot, "/start")
                
                await asyncio.sleep(2)
                
                await msg.edit("""
✅ **SANGMATA TEST SUCCESSFUL!**

🤖 **Bot:** @SangMataInfo_bot
🔌 **Connection:** Active
📡 **Status:** Ready

✅ **Plugin ready for use!**
💡 **Use:** Reply to message + `.sg`

⚡ **Plugin by Vzoel Fox's (LTPN)**
                """.strip())
                
            except Exception as test_error:
                await msg.edit(f"""
⚠️ **SANGMATA TEST RESULTS**

🤖 **Bot:** @SangMataInfo_bot  
❌ **Connection Error:** {str(test_error)}

🔧 **Possible Solutions:**
1. Start chat with @SangMataInfo_bot manually
2. Send `/start` to the bot
3. Check if bot is blocked

💡 **Note:** Plugin may still work for manual forwarding
⚡ **Plugin by Vzoel Fox's (LTPN)**
                """.strip())
                
        except Exception as e:
            await event.edit(f"❌ **Test Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.history'))
    async def history_alternative_handler(event):
        """Alternative history command"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            reply = await event.get_reply_message()
            
            if not reply:
                await event.edit("❌ **Reply to a user's message!**")
                return
                
            user = await reply.get_sender()
            
            if not user:
                await event.edit("❌ **Could not get user information!**")
                return
            
            # Get basic user info
            user_info = f"""
📊 **USER INFORMATION**

👤 **Name:** {user.first_name or 'Unknown'} {user.last_name or ''}
🆔 **ID:** `{user.id}`
📱 **Username:** @{user.username or 'None'}
🤖 **Bot:** {'Yes' if user.bot else 'No'}
🔒 **Verified:** {'Yes' if getattr(user, 'verified', False) else 'No'}
🌟 **Premium:** {'Yes' if getattr(user, 'premium', False) else 'No'}

📞 **Phone:** {getattr(user, 'phone', 'Hidden')}
📝 **Bio:** {getattr(user, 'about', 'No bio')}

💡 **For complete history, use:** `.sg`
🤖 **SangMata Bot:** @SangMataInfo_bot

⚡ **Plugin by Vzoel Fox's (LTPN)**
            """.strip()
            
            await event.edit(user_info)
            
        except Exception as e:
            await event.edit(f"❌ **Error:** {str(e)}")