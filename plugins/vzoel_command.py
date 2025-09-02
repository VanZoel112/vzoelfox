#!/usr/bin/env python3
"""
Vzoel Custom Command Plugin dengan Premium Emoji Support - Enhanced UTF-16 Edition
File: plugins/vzoel_command.py
Founder : Vzoel Fox's Ltpn (Enhanced Premium Emoji Mapping)
Description:
    Plugin untuk command custom .vzoel dengan animasi teks bertahap dan premium emoji
    Fitur: Animated text editing dengan timing berbeda-beda + emoji premium template
    
References:
- Official Telethon Documentation: https://docs.telethon.dev/
- Message Editing API: https://tl.telethon.dev/methods/messages/edit_message.html  
- Telethon Event Handling: https://docs.telethon.dev/en/stable/modules/events.html
- Asyncio Sleep Patterns: https://docs.python.org/3/library/asyncio-task.html#asyncio.sleep
- MessageNotModifiedError: https://docs.telethon.dev/en/stable/modules/errors.html
"""

import asyncio
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.errors import MessageNotModifiedError, FloodWaitError, ChatWriteForbiddenError

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "vzoel_command",
    "version": "1.0.0", 
    "description": "Custom .vzoel command with animated text editing and premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".vzoel"],
    "features": ["animated text editing", "premium emojis", "custom timing sequences"]
}

# Premium Emoji Template - Updated with UTF-16 support (mapping dari formorgan.py)
PREMIUM_EMOJIS = {
    "main":    {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check":   {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1":  {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2":  {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3":  {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4":  {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5":  {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6":  {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

# ===== Global Client Variable =====
client = None

# ===== Helper Functions =====
def get_emoji(emoji_name):
    """Get emoji from premium mapping"""
    return PREMIUM_EMOJIS.get(emoji_name, {}).get("emoji", "❓")

# Import from central font system
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.font_helper import convert_font, process_markdown_bold, process_all_markdown

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support (TEMPLATE VERSION)"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
                emoji = emoji_data["emoji"]
                custom_emoji_id = int(emoji_data["custom_emoji_id"])
                
                if text[i:].startswith(emoji):
                    try:
                        # Calculate UTF-16 length properly (from emoji_template.py reference)
                        emoji_bytes = emoji.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=custom_emoji_id
                        ))
                        
                        i += len(emoji)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

async def safe_edit_message(message, text, entities=None):
    """Safe message editing with error handling (based on Telethon best practices)"""
    try:
        if entities:
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
        return True
    except MessageNotModifiedError:
        # Content identical - skip silently (Telethon documentation reference)
        return False
    except FloodWaitError as e:
        # Rate limited - wait and retry (Telegram API rate limiting)
        await asyncio.sleep(e.seconds)
        try:
            if entities:
                await message.edit(text, formatting_entities=entities)
            else:
                await message.edit(text)
            return True
        except Exception:
            return False
    except (ChatWriteForbiddenError, Exception) as e:
        print(f"[VzoelCommand] Edit failed: {e}")
        return False

# ===== Vzoel Command Implementation =====
@events.register(events.NewMessage(pattern=r'^\.vzoel$', outgoing=True))
async def vzoel_command_handler(event):
    """
    Custom .vzoel command with animated text editing
    
    Timing Sequence:
    - Edit 1-2: 0.5 seconds interval
    - Edit 3-7: 1.0 seconds interval  
    - Edit 8-10: 2.0 seconds interval
    - Final: Static founder message with premium emojis
    
    References:
    - asyncio.sleep() documentation: https://docs.python.org/3/library/asyncio-task.html#asyncio.sleep
    - Message editing best practices from Telethon community examples
    """
    global client
    if client is None:
        client = event.client
    
    try:
        # 10 kata untuk animasi editing (customizable sequence)
        animation_words = [
            f"{get_emoji('adder1')} Initializing...",
            f"{get_emoji('check')} Loading System...",
            f"{get_emoji('adder2')} Connecting Database...", 
            f"{get_emoji('adder3')} Verifying Credentials...",
            f"{get_emoji('adder4')} Loading Plugins...",
            f"{get_emoji('adder5')} Checking Dependencies...", 
            f"{get_emoji('adder6')} Optimizing Performance...",
            f"{get_emoji('main')} Preparing Interface...",
            f"{get_emoji('adder1')} Final Configuration...",
            f"{get_emoji('adder2')} System Ready!"
        ]
        
        # Send initial message
        progress_msg = await event.reply("Starting Vzoel System...")
        
        # Animation sequence dengan timing berbeda
        for edit_number, word_text in enumerate(animation_words, 1):
            # Apply premium emoji entities to each frame
            entities = create_premium_entities(word_text)
            
            # Edit message dengan premium emoji support
            success = await safe_edit_message(progress_msg, word_text, entities)
            
            if success:
                # Determine delay based on edit number (specification requirements)
                if edit_number <= 2:
                    # Edit 1-2: 0.5 second delay
                    await asyncio.sleep(0.5)
                elif edit_number <= 7:
                    # Edit 3-7: 1.0 second delay  
                    await asyncio.sleep(1.0)
                elif edit_number <= 10:
                    # Edit 8-10: 2.0 second delay
                    await asyncio.sleep(2.0)
        
        # Wait sebelum menampilkan final message
        await asyncio.sleep(1.0)
        
        # Final message: Custom founder message dengan premium emoji template
        final_message = f"""
{get_emoji('main')} {convert_font('VZOEL USERBOT SYSTEM')}

{get_emoji('check')} {convert_font('System Information:')}
{get_emoji('adder2')} Status: Online & Ready
{get_emoji('adder3')} Version: Premium Edition
{get_emoji('adder4')} Features: Advanced Automation
{get_emoji('adder1')} Performance: Optimized
{get_emoji('adder6')} Security: Enhanced Protection

{get_emoji('adder5')} {convert_font('Founder:')} Vzoel Fox's LTPN
{get_emoji('main')} {convert_font('Premium Userbot by VzoeL')}

{get_emoji('adder2')} {convert_font('System fully initialized and ready!')}
        """.strip()
        
        # Send final message dengan premium emoji entities
        final_entities = create_premium_entities(final_message)
        await safe_edit_message(progress_msg, final_message, final_entities)
        
    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Error executing .vzoel command: {str(e)}')}"
        error_entities = create_premium_entities(error_text)
        await event.reply(error_text, formatting_entities=error_entities)

# ===== Template Functions for Other Plugins =====
def get_premium_emoji_template():
    """
    Template function untuk plugins lain
    Return premium emoji mapping untuk konsistensi cross-plugin
    """
    return PREMIUM_EMOJIS.copy()

def create_premium_text_with_entities(text):
    """
    Template function untuk membuat text dengan premium entities
    Usage: text, entities = create_premium_text_with_entities("Hello 🤩 World")
    """
    entities = create_premium_entities(text)
    return text, entities

async def send_premium_message(event, text):
    """
    Template function untuk send message dengan premium emoji
    Usage: await send_premium_message(event, "Hello 🤩 Premium!")
    """
    entities = create_premium_entities(text)
    return await event.reply(text, formatting_entities=entities)

# ===== SETUP FUNCTION FOR PLUGIN LOADER =====
def setup(client):
    """Setup function to register event handlers with client"""
    if client:
        client.add_event_handler(vzoel_command_handler)
        print("⚙️ Vzoel command handler registered to client")

print("🤩 Vzoel Custom Command dengan Premium Emoji Template berhasil dimuat!")
print("Command: .vzoel - Animated text editing dengan timing sequence custom")
print("Template functions available: get_premium_emoji_template(), create_premium_text_with_entities(), send_premium_message()")
print("✅ Event handler registration ready for plugin loader")