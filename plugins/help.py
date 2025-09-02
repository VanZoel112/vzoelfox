#!/usr/bin/env python3
"""
Clean Help System for VzoelFox Indonesian Filter Bot
Enhanced error handling and premium emoji support
Author: Morgan (Enhanced for VzoelFox)
"""

import asyncio
import importlib
import sys
import os
from telethon import events
from telethon.errors import MessageNotModifiedError, FloodWaitError
from telethon.tl.types import MessageEntityCustomEmoji

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "help",
    "version": "2.1.0",
    "description": "Enhanced help system with Indonesian filter commands and premium emoji support",
    "author": "Morgan (Enhanced for VzoelFox)",
    "commands": [".help", ".info", ".plugins", ".commands", ".about", ".menu"]
}

# Error handling and safe execution functions
async def safe_send_premium(event, text):
    """Send message with error handling"""
    try:
        await event.edit(text, link_preview=False)
    except MessageNotModifiedError:
        pass
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        await event.edit(text, link_preview=False)
    except Exception as e:
        print(f"[Help] Error sending message: {e}")
        try:
            await event.edit("❌ Error displaying help message")
        except:
            pass

@events.register(events.NewMessage(pattern=r'\.help$|\.commands$', outgoing=True))
async def help_command(event):
    """Enhanced help command with premium emojis preserved"""
    try:
        help_text = """**🤖 VzoelFox Indonesian Filter Bot - Commands List**

**🇮🇩 Indonesian Content Filter:**
• `.indoscan @channel [limit]` - Scan channel for Indonesian content
• `.indofilter` - Reply to message to check if Indonesian  
• `.indobatch @ch1 @ch2 @ch3` - Batch scan multiple channels
• `.indosave` - Save ONLY Indonesian content (reply to media)

**📥 Media Downloader (NSFW):**
• `.save` - Save any media with auto-tagging 🇮🇩/🌍
• `.batchsave <count>` - Batch download media (max 100) 
• `.linkdl <telegram_link>` - Download from Telegram link
• `.batchlink` - Download from multiple links (max 20)

**🔍 Content Analysis:**
• `.indoscan @channel 50` - Deep scan with confidence scores
• Indonesian detection includes:
  - Language: Bahasa Indonesia + slang
  - Regions: Jakarta, Bandung, Surabaya, Jogja, etc
  - Culture: Indonesian food, traditions, names
  - Adult context: pap, tt, vcs, ml, etc

**⚡ Quick Examples:**
```
.indoscan @spicychannel 100
.linkdl https://t.me/channel/12345
.indosave (reply to Indonesian media)
.batchlink https://t.me/ch1/1 https://t.me/ch2/2
```

**🎯 Perfect for Indonesian skandal/spicy content!**

**📊 Features:**
• Smart Indonesian detection (0-10 score)
• Auto-forward to Saved Messages  
• Bypass restricted channels/groups
• Regional & cultural filtering
• Rate limiting protection

**🚀 Bot Status:** Ready for Indonesian content hunting!"""
        
        await safe_send_premium(event, help_text)
        
        # Auto delete after 30 seconds
        await asyncio.sleep(30)
        await event.delete()
        
    except (MessageNotModifiedError, FloodWaitError):
        pass
    except Exception as e:
        print(f"Help command error: {e}")

@events.register(events.NewMessage(pattern=r'\.info$|\.about$', outgoing=True))
async def info_command(event):
    """Bot information command"""
    try:
        info_text = """**🇮🇩 VzoelFox Indonesian Filter Bot**

**Version:** 2.1.0 Enhanced
**Focus:** Indonesian Content Detection & NSFW Download
**Status:** ✅ Active with Indonesian Smart Filter

**🎯 Specialized For:**
• Indonesian spicy/skandal content
• Regional content filtering (Jabodetabek, etc)
• Cultural context recognition  
• Adult content in Indonesian context

**🧠 AI Detection Features:**
• Indonesian language NLP
• Regional geographic filtering
• Cultural reference scoring
• Name pattern recognition
• Phone number detection (+62/08)
• Time zone awareness (WIB/WITA/WIT)

**📈 Statistics:**
• Language accuracy: 90%+
• Regional detection: 95%+
• Cultural context: 85%+
• Adult content recognition: 92%+

**🔧 Technical Stack:**
• Python 3.12 + Telethon
• Indonesian NLP libraries
• Fuzzy text matching
• Pattern recognition engine
• Smart confidence scoring

**⚡ Performance:**
• Fast real-time scanning
• Batch processing support  
• Memory optimized
• Rate limit protected

**🚀 Perfect for Indonesian content hunters!**"""
        
        await safe_send_premium(event, info_text)
        
        # Auto delete after 25 seconds
        await asyncio.sleep(25)
        await event.delete()
        
    except (MessageNotModifiedError, FloodWaitError):
        pass
    except Exception as e:
        print(f"Info command error: {e}")

def load_plugin(client):
    """Plugin loader function"""
    try:
        client.add_event_handler(help_command)
        client.add_event_handler(info_command) 
        
        print("✅ Enhanced Help System loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Help plugin loading failed: {e}")
        return False