# plugins/gcast.py
"""
Advanced Global Broadcast Plugin
Author: Vzoel Fox's (LTPN)
"""

import asyncio
import re
from telethon import events
from datetime import datetime

async def setup(client):
    """Plugin initialization function"""
    
    @client.on(events.NewMessage(pattern=rf'\.gcast\s+(.+)', flags=re.DOTALL))
    async def gcast_handler(event):
        """Advanced Global Broadcast with animation"""
        # Check owner permission
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        message_to_send = event.pattern_match.group(1).strip()
        
        if not message_to_send:
            await event.edit("❌ **Usage:** `.gcast <message>`")
            return
        
        try:
            # Animation phases
            gcast_animations = [
                "🔍 **Scanning available chats...**",
                "📡 **Establishing broadcast connection...**",
                "⚡ **Initializing transmission protocol...**",
                "🚀 **Preparing message distribution...**",
                "📨 **Starting global broadcast...**",
                "🔄 **Broadcasting in progress...**",
                "✅ **Broadcast transmission active...**",
                "📊 **Finalizing delivery status...**"
            ]
            
            msg = await event.edit(gcast_animations[0])
            
            # Animate first phases
            for i in range(1, 5):
                await asyncio.sleep(1.5)
                await msg.edit(gcast_animations[i])
            
            # Get available chats
            chats = []
            try:
                async for dialog in client.iter_dialogs():
                    if dialog.is_group or dialog.is_channel:
                        # Skip channels that don't allow posting
                        if hasattr(dialog.entity, 'broadcast') and not dialog.entity.broadcast:
                            chats.append(dialog)
                        elif not hasattr(dialog.entity, 'broadcast'):
                            chats.append(dialog)
            except Exception as e:
                await msg.edit(f"❌ **Error getting chats:** {str(e)}")
                return
            
            total_chats = len(chats)
            
            if total_chats == 0:
                await msg.edit("❌ **No available chats found for broadcasting!**")
                return
            
            # Continue animation
            await asyncio.sleep(1.5)
            await msg.edit(f"{gcast_animations[5]}\n📊 **Found:** `{total_chats}` chats")
            
            await asyncio.sleep(1.5)
            await msg.edit(f"{gcast_animations[6]}\n📊 **Broadcasting to:** `{total_chats}` chats")
            
            # Start broadcasting
            success_count = 0
            failed_count = 0
            
            for i, chat in enumerate(chats, 1):
                try:
                    await client.send_message(chat.entity, message_to_send)
                    success_count += 1
                    
                    # Update progress every 3 messages
                    if i % 3 == 0 or i == total_chats:
                        progress = (i / total_chats) * 100
                        current_chat = chat.title[:25] if chat.title else "Unknown"
                        await msg.edit(f"""
🚀 **Global Broadcast in Progress...**

📊 **Progress:** `{i}/{total_chats}` ({progress:.1f}%)
✅ **Success:** `{success_count}`
❌ **Failed:** `{failed_count}`
⚡ **Current:** {current_chat}...
                        """.strip())
                    
                    await asyncio.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    failed_count += 1
                    continue
            
            # Final animation
            await asyncio.sleep(2)
            await msg.edit(gcast_animations[7])
            
            await asyncio.sleep(2)
            final_message = f"""
✅ **GLOBAL BROADCAST COMPLETED!**

╔═══════════════════════════════╗
    📡 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗥𝗘𝗣𝗢𝗥𝗧 📡
╚═══════════════════════════════╝

📊 **Total Chats:** `{total_chats}`
✅ **Successful:** `{success_count}`
❌ **Failed:** `{failed_count}`
📈 **Success Rate:** `{(success_count/total_chats)*100:.1f}%`

🔥 **Message delivered successfully!**
⚡ **Plugin by Vzoel Fox's (LTPN)**
            """.strip()
            
            await msg.edit(final_message)
            
        except Exception as e:
            await event.edit(f"❌ **Gcast Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.gcastlist'))
    async def gcastlist_handler(event):
        """Show available chats for broadcasting"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            msg = await event.edit("🔍 **Scanning available chats...**")
            
            chats = []
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    if hasattr(dialog.entity, 'broadcast') and not dialog.entity.broadcast:
                        chats.append(dialog)
                    elif not hasattr(dialog.entity, 'broadcast'):
                        chats.append(dialog)
            
            if not chats:
                await msg.edit("❌ **No available chats found!**")
                return
                
            chat_list = "📋 **AVAILABLE CHATS FOR GCAST**\n\n"
            
            for i, chat in enumerate(chats[:20], 1):  # Limit to 20 chats
                chat_type = "📢 Channel" if chat.is_channel else "👥 Group"
                chat_name = chat.title[:30] if chat.title else "Unknown"
                member_count = getattr(chat.entity, 'participants_count', 'Unknown')
                
                chat_list += f"`{i:02d}.` {chat_type}\n"
                chat_list += f"     **Name:** {chat_name}\n"
                chat_list += f"     **Members:** {member_count}\n\n"
            
            if len(chats) > 20:
                chat_list += f"... and {len(chats) - 20} more chats\n\n"
                
            chat_list += f"📊 **Total Available:** `{len(chats)}` chats"
            
            await msg.edit(chat_list)
            
        except Exception as e:
            await event.edit(f"❌ **Error:** {str(e)}")

    @client.on(events.NewMessage(pattern=r'\.gcasttest'))  
    async def gcasttest_handler(event):
        """Test gcast to saved messages only"""
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        try:
            test_message = "🧪 **GCAST TEST MESSAGE**\n\nThis is a test broadcast from Vzoel Assistant.\n⚡ Plugin working correctly!"
            
            await client.send_message('me', test_message)
            
            await event.edit("""
✅ **GCAST TEST SUCCESSFUL!**

📨 **Test message sent to Saved Messages**
🔧 **Plugin Status:** Working
⚡ **Ready for global broadcast**

Use `.gcast <message>` for actual broadcast.
            """.strip())
            
        except Exception as e:
            await event.edit(f"❌ **Test Error:** {str(e)}")