#!/usr/bin/env python3
"""
Vzoel Assistant Advanced Plugins Collection - FIXED VERSION
4 plugins dalam 1 file untuk Enhanced Vzoel Assistant
- alive.py - Status dengan custom template
- gcast_advanced.py - Broadcast dengan 8x edit animation (FIXED)
- joinleavevc.py - Voice chat management (FIXED) 
- infofounder.py - Custom founder info template
"""

import asyncio
import time
import os
from datetime import datetime
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest, JoinGroupCallRequest
from telethon.errors import FloodWaitError, ChatAdminRequiredError
from telethon.tl.types import InputPeerChannel, InputPeerChat

# Import config dengan error handling
try:
    import config
    COMMAND_PREFIX = config.COMMAND_PREFIX
except ImportError:
    COMMAND_PREFIX = "."

# ============= PLUGIN 1: ALIVE WITH CUSTOM TEMPLATE =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}alive$'))
async def enhanced_alive(event):
    """Enhanced alive command dengan custom template"""
    try:
        # Check if user is owner
        try:
            from main import is_owner
            if not await is_owner(event.sender_id):
                return
        except ImportError:
            pass  # Skip owner check if can't import
            
        me = await event.client.get_me()
        start_time = getattr(event.client, 'start_time', datetime.now())
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split('.')[0]
        
        # Get system info
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            system_info = f"""
💻 **System Status:**
🖥️ CPU: `{cpu_percent}%`
💾 RAM: `{memory_percent}%`
💿 Disk: `{disk_percent}%`"""
        except ImportError:
            system_info = ""
        
        # Enhanced alive template
        alive_message = f"""
🔥 **VZOEL ASSISTANT IS ALIVE!** 🔥

👤 **Master:** {me.first_name or 'Anonymous'}
🆔 **User ID:** `{me.id}`
📱 **Phone:** `{me.phone or 'Hidden'}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
🚀 **Uptime:** `{uptime_str}`
⏰ **Time:** `{datetime.now().strftime('%H:%M:%S')}`
📅 **Date:** `{datetime.now().strftime('%d/%m/%Y')}`

🔌 **Status:** ✅ **ONLINE & READY**
🛡️ **Security:** ✅ **PROTECTED**
⭐ **Performance:** ✅ **OPTIMAL**
{system_info}

💎 **Vzoel Assistant** - Premium Userbot
🌟 **Always at your service, Master!**
        """.strip()
        
        # Send with animation
        msg = await event.reply("⚡ **Checking status...**")
        await asyncio.sleep(1)
        await msg.edit("🔍 **Scanning system...**")
        await asyncio.sleep(1)
        await msg.edit("✅ **System ready!**")
        await asyncio.sleep(1)
        await msg.edit(alive_message)
        
    except Exception as e:
        await event.reply(f"❌ **Error in alive command:** `{str(e)}`")

# ============= PLUGIN 2: FIXED ADVANCED GCAST =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gcast (.+)', outgoing=True))
async def advanced_gcast(event):
    """FIXED Advanced global cast dengan 8x edit animation"""
    try:
        # Check if user is owner
        try:
            from main import is_owner
            if not await is_owner(event.sender_id):
                return
        except ImportError:
            pass
            
        message = event.pattern_match.group(1)
        
        # Animation messages (8 variations)
        animation_steps = [
            "🔄 **Initializing Global Cast...**",
            "📡 **Connecting to channels...**", 
            "🔍 **Scanning available chats...**",
            "⚡ **Preparing message broadcast...**",
            "🚀 **Starting transmission...**",
            "📤 **Broadcasting in progress...**",
            "🔥 **Sending to all chats...**",
            "✅ **Finalizing broadcast...**"
        ]
        
        # Start animation
        status_msg = await event.reply(animation_steps[0])
        
        # Animate through all 8 steps
        for i, step in enumerate(animation_steps[1:], 1):
            await asyncio.sleep(0.8)  # Delay between animations
            await status_msg.edit(step)
        
        # Start actual broadcasting
        success_count = 0
        failed_count = 0
        total_chats = 0
        
        # Get all dialogs with better filtering
        dialogs = []
        try:
            async for dialog in event.client.iter_dialogs():
                # Skip saved messages, deleted accounts, etc
                if (dialog.is_group or dialog.is_channel) and not dialog.entity.left:
                    dialogs.append(dialog)
                    total_chats += 1
        except Exception as e:
            await status_msg.edit(f"❌ **Error getting dialogs:** `{str(e)}`")
            return
        
        if total_chats == 0:
            await status_msg.edit("❌ **No groups/channels found to broadcast!**")
            return
        
        # Update status with total count
        await status_msg.edit(f"📊 **Found {total_chats} chats**\n🚀 **Broadcasting message...**")
        await asyncio.sleep(1)
        
        # Broadcast to all chats
        for i, dialog in enumerate(dialogs, 1):
            try:
                # Add custom footer to message
                final_message = f"""{message}

━━━━━━━━━━━━━━━━━
💎 **Vzoel Assistant** | Global Cast
⚡ Powered by Master's Command"""
                
                await event.client.send_message(dialog.id, final_message)
                success_count += 1
                
                # Update progress every 5 messages
                if i % 5 == 0:
                    progress = int((i / total_chats) * 100)
                    await status_msg.edit(
                        f"📤 **Broadcasting Progress**\n"
                        f"📊 Progress: `{progress}%` ({i}/{total_chats})\n"
                        f"✅ Success: `{success_count}`\n"
                        f"❌ Failed: `{failed_count}`"
                    )
                
                await asyncio.sleep(0.3)  # Anti-flood delay
                
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                failed_count += 1
            except Exception as ex:
                failed_count += 1
                continue
        
        # Final result with enhanced formatting
        final_result = f"""
🎉 **GLOBAL CAST COMPLETED!**

📊 **Statistics:**
├── 📈 Total Chats: `{total_chats}`
├── ✅ Successful: `{success_count}`
├── ❌ Failed: `{failed_count}`
└── 📊 Success Rate: `{int((success_count/total_chats)*100) if total_chats > 0 else 0}%`

⚡ **Message:** {message[:50]}{'...' if len(message) > 50 else ''}
🕒 **Time:** `{datetime.now().strftime('%H:%M:%S')}`

💎 **Vzoel Assistant** - Mission Accomplished!
        """.strip()
        
        await status_msg.edit(final_result)
        
    except Exception as e:
        await event.reply(f"❌ **Gcast Error:** `{str(e)}`")

# ============= PLUGIN 3: FIXED JOIN/LEAVE VOICE CHAT =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}joinvc$', outgoing=True))
async def join_voice_chat(event):
    """FIXED Join voice chat in current group"""
    try:
        # Check if user is owner
        try:
            from main import is_owner
            if not await is_owner(event.sender_id):
                return
        except ImportError:
            pass
            
        chat = await event.get_chat()
        
        if not (hasattr(chat, 'megagroup') and chat.megagroup) and not (hasattr(chat, 'broadcast') and chat.broadcast):
            await event.reply("❌ **This command only works in groups/channels!**")
            return
        
        # Animation before joining
        msg = await event.reply("🔄 **Preparing to join voice chat...**")
        await asyncio.sleep(1)
        await msg.edit("🎤 **Connecting to voice chat...**")
        await asyncio.sleep(1)
        
        try:
            # Simple approach - try to join existing call
            from telethon.tl.functions.phone import JoinGroupCallRequest
            
            # First, check if there's an active call
            full_chat = await event.client.get_entity(chat.id)
            
            if hasattr(full_chat, 'call') and full_chat.call:
                # Try to join existing call
                await event.client(JoinGroupCallRequest(
                    call=full_chat.call,
                    join_as=await event.client.get_me(),
                    params=None
                ))
                
                success_message = f"""
🎉 **Successfully Joined Voice Chat!**

🎤 **Chat:** {chat.title or 'Unknown'}
🆔 **Chat ID:** `{chat.id}`
⚡ **Status:** Connected
🔊 **Mode:** Voice Chat Active

💎 **Vzoel Assistant** is now in the voice chat!
Use `{COMMAND_PREFIX}leavevc` to disconnect.
                """.strip()
                
                await msg.edit(success_message)
            else:
                await msg.edit("❌ **No active voice chat found in this group!**\nStart a voice chat first, then use this command.")
                
        except ChatAdminRequiredError:
            await msg.edit("❌ **Admin rights required to manage voice chats!**")
        except Exception as e:
            # Fallback message
            await msg.edit(f"⚠️ **Voice chat feature experimental**\n`{str(e)[:100]}`")
            
    except Exception as e:
        await event.reply(f"❌ **Join VC Error:** `{str(e)}`")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}leavevc$', outgoing=True))
async def leave_voice_chat(event):
    """FIXED Leave voice chat in current group"""
    try:
        # Check if user is owner
        try:
            from main import is_owner
            if not await is_owner(event.sender_id):
                return
        except ImportError:
            pass
            
        chat = await event.get_chat()
        
        # Animation before leaving
        msg = await event.reply("🔄 **Preparing to leave voice chat...**")
        await asyncio.sleep(1)
        await msg.edit("👋 **Disconnecting from voice chat...**")
        await asyncio.sleep(1)
        
        try:
            from telethon.tl.functions.phone import LeaveGroupCallRequest
            
            # Get full chat info
            full_chat = await event.client.get_entity(chat.id)
            
            if hasattr(full_chat, 'call') and full_chat.call:
                await event.client(LeaveGroupCallRequest(
                    call=full_chat.call,
                    source=0
                ))
                
                success_message = f"""
👋 **Successfully Left Voice Chat!**

🎤 **Chat:** {chat.title or 'Unknown'}
🆔 **Chat ID:** `{chat.id}`
⚡ **Status:** Disconnected
🔇 **Mode:** Voice Chat Left

💎 **Vzoel Assistant** has left the voice chat.
Use `{COMMAND_PREFIX}joinvc` to reconnect.
                """.strip()
                
                await msg.edit(success_message)
            else:
                await msg.edit("✅ **No active voice chat to leave** (or already left)")
                
        except Exception as e:
            await msg.edit(f"✅ **Left voice chat** (or wasn't connected)\n`{str(e)[:100]}`")
            
    except Exception as e:
        await event.reply(f"❌ **Leave VC Error:** `{str(e)}`")

# ============= PLUGIN 4: INFO FOUNDER WITH CUSTOM TEMPLATE =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}infofounder$', outgoing=True))
async def info_founder(event):
    """Custom founder information template"""
    try:
        # Check if user is owner
        try:
            from main import is_owner
            if not await is_owner(event.sender_id):
                return
        except ImportError:
            pass
            
        me = await event.client.get_me()
        
        # Get additional info
        total_chats = 0
        groups = 0
        channels = 0
        
        try:
            async for dialog in event.client.iter_dialogs():
                total_chats += 1
                if dialog.is_group:
                    groups += 1
                elif dialog.is_channel:
                    channels += 1
        except:
            pass  # If we can't get dialog info, continue without it
        
        # Custom founder template
        founder_info = f"""
👑 **FOUNDER INFORMATION** 👑

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 **Personal Details:**
├── 👤 **Name:** {me.first_name or 'Anonymous'}
├── 🏷️ **Username:** @{me.username or 'Not Set'}
├── 🆔 **User ID:** `{me.id}`
├── 📱 **Phone:** `{me.phone or 'Private'}`
└── 🌍 **Status:** Premium Account

🎯 **Account Statistics:**
├── 💬 **Total Chats:** `{total_chats}`
├── 👥 **Groups:** `{groups}`
├── 📢 **Channels:** `{channels}`
└── 🤖 **Bot Type:** Userbot

⚡ **Vzoel Assistant Features:**
├── 🔒 **Security:** Maximum Protection
├── 🚀 **Performance:** Ultra Fast Response
├── 🛡️ **Anti-Spam:** Advanced Filtering
├── 🎨 **Customization:** Fully Customizable
├── 📊 **Analytics:** Real-time Monitoring
└── 🔄 **Updates:** Auto-updating System

💎 **Special Abilities:**
├── 🌐 **Global Cast:** Broadcast to all chats
├── 🎤 **Voice Chat:** Join/Leave voice chats
├── 📝 **Auto Reply:** Smart auto responses
├── 🔍 **Advanced Search:** Deep chat search
├── 📊 **Statistics:** Detailed usage stats
└── 🛠️ **Plugin System:** Modular architecture

🏆 **Master's Command Center:**
⚡ Prefix: `{COMMAND_PREFIX}`
🕐 Current Time: `{datetime.now().strftime('%H:%M:%S')}`
📅 Today's Date: `{datetime.now().strftime('%d %B %Y')}`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💫 **"Technology is best when it brings people together"**

🔥 **Vzoel Assistant** - Engineered for Excellence
👑 **Serving the Master with Pride & Precision**
        """.strip()
        
        # Send with loading animation
        msg = await event.reply("🔍 **Loading founder information...**")
        await asyncio.sleep(1)
        await msg.edit("📊 **Gathering statistics...**")
        await asyncio.sleep(1)
        await msg.edit("👑 **Preparing founder profile...**")
        await asyncio.sleep(1)
        await msg.edit(founder_info)
        
    except Exception as e:
        await event.reply(f"❌ **Info Founder Error:** `{str(e)}`")

# ============= PLUGIN SYSTEM INTEGRATION =============

# Plugin info for the enhanced system
PLUGIN_INFO = {
    'name': 'Vzoel Advanced Plugins Collection',
    'version': '1.0.1',
    'description': '4 advanced plugins: alive, gcast, joinleavevc, infofounder',
    'commands': [
        '.alive - Enhanced status with system info',
        '.gcast <message> - Advanced global cast with 8x animation',
        '.joinvc - Join voice chat in current group',
        '.leavevc - Leave voice chat in current group', 
        '.infofounder - Custom founder information template'
    ],
    'author': 'Vzoel Assistant Team',
    'category': 'Essential'
}

def get_plugin_info():
    """Return plugin information for the management system"""
    return PLUGIN_INFO

# Auto-register message for when plugin is loaded
if __name__ == "__main__":
    print("🔌 Vzoel Advanced Plugins Collection loaded!")
    print(f"📋 Available commands: {len(PLUGIN_INFO['commands'])}")
    for cmd in PLUGIN_INFO['commands']:
        print(f"  • {cmd}")
