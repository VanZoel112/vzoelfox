#!/usr/bin/env python3
"""
Pizol Plugin for VzoelFox Userbot - Enhanced Premium Animation System
Fitur: 16-step animated text editing dengan premium emoji support dan Unicode fonts
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Premium Animation System
"""

import asyncio
import os
import glob
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.errors import MessageNotModifiedError, FloodWaitError, ChatWriteForbiddenError

# Import from central font system
from utils.font_helper import convert_font

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "pizol",
    "version": "1.0.0",
    "description": "Premium animated pizol command dengan 16-step animation dan premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".pizol"],
    "features": ["16-step animation", "premium emojis", "Unicode font system", "2s delay per step"]
}

# Premium Emoji Mapping - Enhanced with UTF-16 support
PREMIUM_EMOJIS = {
    "main":    {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check":   {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1":  {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2":  {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3":  {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4":  {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5":  {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6":  {"emoji": "🎚️", "custom_emoji_id": "5794323465452394551"}
}

# ===== Global Client Variable =====
client = None

# ===== Helper Functions =====
def get_emoji(emoji_name):
    """Get emoji from premium mapping"""
    return PREMIUM_EMOJIS.get(emoji_name, {}).get("emoji", "❓")

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support"""
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
                        # Calculate UTF-16 length properly
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
    """Safe message editing with error handling and premium emoji support"""
    try:
        if entities:
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
        return True
    except MessageNotModifiedError:
        # Content identical - skip silently
        return False
    except FloodWaitError as e:
        # Rate limited - wait and retry
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
        print(f"[Pizol] Edit failed: {e}")
        return False

def count_plugins():
    """Count total plugins in plugins directory"""
    try:
        plugin_files = glob.glob("plugins/*.py")
        plugins = []
        
        for plugin_file in plugin_files:
            plugin_name = os.path.basename(plugin_file).replace('.py', '')
            if plugin_name not in ['__init__', 'database_helper']:
                plugins.append(plugin_name)
        
        return len(plugins)
    except Exception:
        return 0

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        if client:
            owner_id = os.getenv("OWNER_ID")
            if owner_id:
                return user_id == int(owner_id)
            me = await client.get_me()
            return user_id == me.id
    except Exception as e:
        print(f"Error checking owner: {e}")
    return False

# ===== Pizol Command Implementation =====
@events.register(events.NewMessage(pattern=r'^\.pizol$', outgoing=True))
async def pizol_command_handler(event):
    """
    Premium .pizol command with 16-step animated text editing
    Animation Sequence:
        - 16 animation steps with 2 seconds delay per step
        - Final message with premium emojis and Unicode fonts
        - Enhanced premium emoji entities support
    """
    global client
    if client is None:
        client = event.client

    # Owner check
    if not await is_owner_check(event.sender_id):
        return

    try:
        # Get plugin count for final message
        plugin_count = count_plugins()
        
        # 16 animation steps dengan premium emoji dan Unicode fonts
        animation_steps = [
            f"{get_emoji('adder1')} {convert_font('Initializing Pizol System...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Loading Core Modules...', 'bold')}",
            f"{get_emoji('adder2')} {convert_font('Connecting Database...', 'bold')}",
            f"{get_emoji('adder3')} {convert_font('Verifying User Credentials...', 'bold')}",
            f"{get_emoji('adder4')} {convert_font('Loading Plugin System...', 'bold')}",
            f"{get_emoji('adder5')} {convert_font('Checking Dependencies...', 'bold')}",
            f"{get_emoji('adder6')} {convert_font('Optimizing Performance...', 'bold')}",
            f"{get_emoji('main')} {convert_font('Preparing Interface...', 'bold')}",
            f"{get_emoji('adder1')} {convert_font('Loading Premium Features...', 'bold')}",
            f"{get_emoji('check')} {convert_font('Configuring Emojis...', 'bold')}",
            f"{get_emoji('adder2')} {convert_font('Setting Up Animation...', 'bold')}",
            f"{get_emoji('adder3')} {convert_font('Validating System...', 'bold')}",
            f"{get_emoji('adder4')} {convert_font('Final Configuration...', 'bold')}",
            f"{get_emoji('adder5')} {convert_font('Preparing Launch...', 'bold')}",
            f"{get_emoji('adder6')} {convert_font('Almost Ready...', 'bold')}",
            f"{get_emoji('main')} {convert_font('System Ready!', 'bold')}"
        ]
        
        # Send initial message
        progress_msg = await event.reply("Starting Pizol System...")

        # 16-step animation sequence dengan 2 detik delay per step
        for step_number, animation_text in enumerate(animation_steps, 1):
            # Apply premium emoji entities to each frame
            entities = create_premium_entities(animation_text)
            
            # Edit message dengan premium emoji support
            success = await safe_edit_message(progress_msg, animation_text, entities)
            
            if success:
                print(f"[Pizol] Animation step {step_number}/16 completed")
                # 2 second delay per step as requested
                await asyncio.sleep(2)
        
        # Wait sebelum menampilkan final message
        await asyncio.sleep(1)

        # Final message dengan template yang diminta
        final_message = f"""
{get_emoji('adder1')} Vzoel Assistant

{get_emoji('check')} {convert_font('Founder Userbot:', 'bold')} Vzoel Fox's (Lutpan) {get_emoji('main')}
{get_emoji('check')} {convert_font('Code:', 'bold')}                     python3,python2
{get_emoji('check')} {convert_font('Fitur:', 'bold')}                      {plugin_count}
{get_emoji('check')} {convert_font('IG:', 'bold')}                          vzoel.fox_s
{get_emoji('check')} {convert_font('Zone:', 'bold')}                     ID 🇮🇩

{get_emoji('adder5')} {convert_font('NOTE !!!', 'bold')} :
Userbot ini dibuat dengan repo murni oleh Vzoel Fox's..
Bukan hasil fork maupun beli dari seller manapun!!!
Hak cipta sepenuhnya milik Vzoel..

{get_emoji('adder3')} ©2025 ~ Vzoel Fox's (LTPN).
        """.strip()

        # Send final message dengan premium emoji entities
        final_entities = create_premium_entities(final_message)
        await safe_edit_message(progress_msg, final_message, final_entities)
        
        print("[Pizol] Animation sequence completed successfully")

    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Error executing .pizol command: {str(e)}', 'bold')}"
        error_entities = create_premium_entities(error_text)
        await event.reply(error_text, formatting_entities=error_entities)
        print(f"[Pizol] Command error: {e}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    client.add_event_handler(pizol_command_handler, events.NewMessage(pattern=r"\.pizol$"))
    print(f"✅ [Pizol] Premium animation system loaded v{PLUGIN_INFO['version']} - 16 steps with 2s delay")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Pizol] Plugin cleanup initiated")
        client = None
        print("[Pizol] Plugin cleanup completed")
    except Exception as e:
        print(f"[Pizol] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'pizol_command_handler']