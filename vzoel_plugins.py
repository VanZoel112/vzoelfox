#!/usr/bin/env python3
"""
QUICK FIX VERSION - Vzoel Assistant Plugin
Simplified version yang dipastikan bisa work dengan sistem Enhanced Vzoel Assistant
"""

import asyncio
import re
from datetime import datetime
from telethon import events

# Hardcoded config to avoid import issues
COMMAND_PREFIX = "."  # Change if your prefix is different

# Simple owner check without imports
async def simple_owner_check(event):
    """Simple owner check - modify as needed"""
    try:
        me = await event.client.get_me()
        return event.sender_id == me.id
    except:
        return True  # Fallback - allow all

# ============= PLUGIN 1: SIMPLE ALIVE =============

@events.register(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}alive$', outgoing=True))
async def simple_alive(event):
    """Simple alive command that should work"""
    try:
        if not await simple_owner_check(event):
            return
            
        me = await event.client.get_me()
        
        alive_text = f"""
🔥 **VZOEL ASSISTANT ALIVE!**

👤 **User:** {me.first_name or 'Unknown'}
🆔 **ID:** `{me.id}`
⚡ **Prefix:** `{COMMAND_PREFIX}`
🕐 **Time:** `{datetime.now().strftime('%H:%M:%S')}`

✅ **Status:** Online & Ready!
🚀 **System:** Operational
        """.strip()
        
        await event.edit(alive_text)
        
    except Exception as e:
        await event.edit(f"❌ Error: `{str(e)}`")

# ============= PLUGIN 2: SIMPLE GCAST =============

@events.register(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}gcast (.+)', outgoing=True))
async def simple_gcast(event):
    """Simple global cast without complex animation"""
    try:
        if not await simple_owner_check(event):
            return
            
        message = event.pattern_match.group(1)
        
        # Start broadcasting
        msg = await event.reply("🔄 **Starting global cast...**")
        
        success = 0
        failed = 0
        
        async for dialog in event.client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                try:
                    await event.client.send_message(dialog.id, message)
                    success += 1
                    await asyncio.sleep(0.5)  # Anti-flood
                except:
                    failed += 1
                    
                # Update every 10 messages
                if (success + failed) % 10 == 0:
                    await msg.edit(f"📤 **Broadcasting...**\n✅ Sent: {success}\n❌ Failed: {failed}")
        
        await msg.edit(f"✅ **Global cast completed!**\n📊 Success: {success}, Failed: {failed}")
        
    except Exception as e:
        await event.reply(f"❌ Gcast error: `{str(e)}`")

# ============= PLUGIN 3: SIMPLE INFO =============

@events.register(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}simpleinfo$', outgoing=True))
async def simple_info(event):
    """Simple info command"""
    try:
        if not await simple_owner_check(event):
            return
            
        me = await event.client.get_me()
        
        # Count dialogs
        total = 0
        groups = 0
        channels = 0
        
        async for dialog in event.client.iter_dialogs():
            total += 1
            if dialog.is_group:
                groups += 1
            elif dialog.is_channel:
                channels += 1
            
            if total >= 100:  # Limit for speed
                break
        
        info_text = f"""
📊 **SIMPLE INFO**

👤 **User Info:**
├── Name: {me.first_name or 'Unknown'}
├── Username: @{me.username or 'None'}
└── ID: `{me.id}`

📱 **Chats:**
├── Total: `{total}+`
├── Groups: `{groups}`
└── Channels: `{channels}`

⚡ **System:**
├── Prefix: `{COMMAND_PREFIX}`
├── Time: `{datetime.now().strftime('%H:%M:%S')}`
└── Date: `{datetime.now().strftime('%d/%m/%Y')}`

🔧 **Commands:**
• `{COMMAND_PREFIX}alive` - Status check
• `{COMMAND_PREFIX}gcast <msg>` - Global broadcast
• `{COMMAND_PREFIX}simpleinfo` - This info
        """.strip()
        
        await event.edit(info_text)
        
    except Exception as e:
        await event.edit(f"❌ Info error: `{str(e)}`")

# ============= PLUGIN 4: TEST COMMAND =============

@events.register(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}testplugin$', outgoing=True))
async def test_plugin(event):
    """Test if plugin system works"""
    try:
        if not await simple_owner_check(event):
            return
            
        test_text = f"""
✅ **PLUGIN TEST SUCCESSFUL!**

🔌 **Plugin Status:** Working correctly
📂 **Location:** Root directory  
⚡ **Commands:** 4 available
🕐 **Test Time:** `{datetime.now().strftime('%H:%M:%S')}`

💡 **Available Commands:**
• `{COMMAND_PREFIX}alive` - Enhanced status
• `{COMMAND_PREFIX}gcast <message>` - Global cast
• `{COMMAND_PREFIX}simpleinfo` - System info
• `{COMMAND_PREFIX}testplugin` - This test

🎯 **Plugin system is working perfectly!**
        """.strip()
        
        await event.edit(test_text)
        
    except Exception as e:
        await event.edit(f"❌ Test failed: `{str(e)}`")

# ============= PLUGIN INFO =============

# Simple plugin info for management system
PLUGIN_INFO = {
    'name': 'Quick Fix Vzoel Plugins',
    'version': '1.0.0',
    'description': 'Simplified working version of vzoel plugins',
    'commands': [
        f'{COMMAND_PREFIX}alive - Simple status check',
        f'{COMMAND_PREFIX}gcast <message> - Simple global broadcast',
        f'{COMMAND_PREFIX}simpleinfo - Basic system information',
        f'{COMMAND_PREFIX}testplugin - Test plugin functionality'
    ]
}

print(f"🔌 Quick Fix Vzoel Plugins loaded! Commands: {len(PLUGIN_INFO['commands'])}")
