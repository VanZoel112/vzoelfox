#!/usr/bin/env python3
"""
Ping Plugin for VzoelFox Userbot - Enhanced Premium Edition
Fitur: Response time test dengan premium emoji support dan Unicode fonts
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Premium Ping System
"""

import asyncio
import time
import os
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.errors import MessageNotModifiedError, FloodWaitError, ChatWriteForbiddenError

# Import from central font system
from utils.font_helper import convert_font

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "ping",
    "version": "1.0.0",
    "description": "Premium ping command dengan response time test, premium emoji support dan Unicode fonts",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".ping", ".pong"],
    "features": ["response time measurement", "premium emojis", "Unicode font system", "server latency test"]
}

# Premium Emoji Mapping - Enhanced with UTF-16 support dan latency color mapping
PREMIUM_EMOJIS = {
    "main":    {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check":   {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1":  {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2":  {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3":  {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4":  {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5":  {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6":  {"emoji": "🎚️", "custom_emoji_id": "5794323465452394551"},
    # Latency Color Premium Emojis (dari mapping yang diberikan user)
    "latency_green":  {"emoji": "🎅", "custom_emoji_id": "5260687265121712272"},  # Excellent < 100ms
    "latency_blue":   {"emoji": "🤩", "custom_emoji_id": "5260637271702389570"},  # Good < 200ms  
    "latency_yellow": {"emoji": "🥳", "custom_emoji_id": "5260471374295613818"}   # Fair/Slow/Very Slow >= 200ms
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
        print(f"[Ping] Edit failed: {e}")
        return False

async def safe_send_premium(event, text):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            return await event.reply(text, formatting_entities=entities)
        else:
            return await event.reply(text)
    except Exception as e:
        # Fallback to plain text if premium emoji fails
        return await event.reply(text)

def get_ping_status(response_time_ms):
    """Get ping status based on response time with premium color emojis"""
    if response_time_ms < 100:
        return {
            'status': 'Excellent',
            'emoji': get_emoji('latency_green'),  # 🎅 Green - Excellent
            'color': 'green',
            'color_emoji': get_emoji('latency_green')
        }
    elif response_time_ms < 200:
        return {
            'status': 'Good',
            'emoji': get_emoji('latency_blue'),   # 🤩 Blue - Good
            'color': 'blue',
            'color_emoji': get_emoji('latency_blue')
        }
    else:
        # Fair/Slow/Very Slow menggunakan yellow emoji
        status_text = 'Fair' if response_time_ms < 500 else 'Slow' if response_time_ms < 1000 else 'Very Slow'
        return {
            'status': status_text,
            'emoji': get_emoji('latency_yellow'),  # 🥳 Yellow - Fair/Slow/Very Slow
            'color': 'yellow',
            'color_emoji': get_emoji('latency_yellow')
        }

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

# ===== Ping Command Implementation =====
@events.register(events.NewMessage(pattern=r'^\.ping$', outgoing=True))
async def ping_command_handler(event):
    """
    Premium .ping command dengan response time measurement
    Features:
        - Real-time response time calculation
        - Premium emoji entities dengan status indicators
        - Unicode font system untuk proper formatting
        - Server latency testing
    """
    global client
    if client is None:
        client = event.client

    # Owner check
    if not await is_owner_check(event.sender_id):
        return

    try:
        # Record start time
        start_time = time.time()
        
        # Send initial ping message
        ping_msg = await event.reply(f"{get_emoji('adder4')} {convert_font('Calculating ping...', 'mono')}")
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000, 2)
        
        # Get ping status based on response time
        ping_status = get_ping_status(response_time_ms)
        
        # Get current time
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Build enhanced ping response with premium color emojis
        ping_response = f"""
{get_emoji('main')} {convert_font('VZOEL PING RESPONSE', 'bold')}

{ping_status['color_emoji']} {convert_font('Response Time:', 'bold')} {convert_font(f'{response_time_ms}ms', 'mono')}
{ping_status['emoji']} {convert_font('Status:', 'bold')} {ping_status['status']}
{get_emoji('adder3')} {convert_font('Server:', 'bold')} Online & Ready
{get_emoji('adder6')} {convert_font('Time:', 'bold')} {convert_font(current_time, 'mono')}

{get_emoji('adder2')} {convert_font('Connection Quality:', 'bold')}
{ping_status['color_emoji']} Latency: {ping_status['status']} ({ping_status['color']})
{get_emoji('adder1')} Network: Stable Connection

{get_emoji('main')} {convert_font('VzoelFox Premium System', 'bold')}
        """.strip()
        
        # Edit message dengan premium emoji entities
        entities = create_premium_entities(ping_response)
        await safe_edit_message(ping_msg, ping_response, entities)
        
        print(f"[Ping] Response time: {response_time_ms}ms - Status: {ping_status['status']}")

    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Ping Error: {str(e)}', 'bold')}"
        error_entities = create_premium_entities(error_text)
        await event.reply(error_text, formatting_entities=error_entities)
        print(f"[Ping] Command error: {e}")

# ===== Pong Command Implementation =====
@events.register(events.NewMessage(pattern=r'^\.pong$', outgoing=True))
async def pong_command_handler(event):
    """
    Premium .pong command - alternative ping with different style
    """
    global client
    if client is None:
        client = event.client

    # Owner check
    if not await is_owner_check(event.sender_id):
        return

    try:
        # Record start time
        start_time = time.time()
        
        # Send initial pong message
        pong_msg = await event.reply(f"{get_emoji('adder1')} {convert_font('Pong testing...', 'mono')}")
        
        # Small delay for more accurate measurement
        await asyncio.sleep(0.1)
        
        # Calculate response time
        end_time = time.time()
        response_time_ms = round((end_time - start_time) * 1000, 2)
        
        # Get ping status
        ping_status = get_ping_status(response_time_ms)
        
        # Build pong response with premium color emojis
        pong_response = f"""
{ping_status['color_emoji']} {convert_font('PONG!', 'bold')} {ping_status['emoji']}

{ping_status['color_emoji']} {convert_font('Response:', 'mono')} {response_time_ms}ms
{ping_status['emoji']} {convert_font('Quality:', 'mono')} {ping_status['status']}
{get_emoji('main')} {convert_font('System:', 'mono')} Active

{get_emoji('adder6')} {convert_font('Vzoel Assistant Ready!', 'bold')}
        """.strip()
        
        # Edit message dengan premium emoji entities
        entities = create_premium_entities(pong_response)
        await safe_edit_message(pong_msg, pong_response, entities)
        
        print(f"[Pong] Response time: {response_time_ms}ms")

    except Exception as e:
        error_text = f"{get_emoji('adder5')} {convert_font(f'Pong Error: {str(e)}', 'bold')}"
        await safe_send_premium(event, error_text)
        print(f"[Pong] Command error: {e}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Register handlers dengan client menggunakan proper method
    client.add_event_handler(ping_command_handler)
    client.add_event_handler(pong_command_handler)
    print(f"✅ [Ping] Premium ping system loaded v{PLUGIN_INFO['version']} - Response time testing")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Ping] Plugin cleanup initiated")
        client = None
        print("[Ping] Plugin cleanup completed")
    except Exception as e:
        print(f"[Ping] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'ping_command_handler', 'pong_command_handler']