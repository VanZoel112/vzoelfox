#!/usr/bin/env python3
"""
Enhanced Ping Plugin for VzoelFox Userbot - Animated Premium Edition
Fitur: Animated ping dengan premium emoji dan response time analysis
Founder Userbot: Vzoel Fox's Ltpn
Version: 3.0.0 - Animated Premium Ping
"""

import time
import asyncio
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Plugin Info
PLUGIN_INFO = {
    "name": "ping",
    "version": "3.0.0",
    "description": "Enhanced ping dengan animated premium emoji dan latency analysis",
    "author": "Founder Userbot: Vzoel Fox's Ltpn",
    "commands": [".ping"],
    "features": ["animated ping", "premium emoji", "latency analysis", "uptime tracking"]
}

# Premium Emoji Mapping untuk Ping
PREMIUM_EMOJIS = {
    'main': {'id': '5260637271702389570', 'char': '🤩', 'length': 2},
    'check': {'id': '5794353925360457382', 'char': '⚙️', 'length': 2},
    'adder1': {'id': '5794407002566300853', 'char': '⛈', 'length': 1},
    'adder2': {'id': '5793913811471700779', 'char': '✅', 'length': 1}, 
    'adder3': {'id': '5321412209992033736', 'char': '👽', 'length': 2},
    'adder4': {'id': '5793973133559993740', 'char': '✈️', 'length': 2},
    'adder5': {'id': '5357404860566235955', 'char': '😈', 'length': 2},
    'adder6': {'id': '5794323465452394551', 'char': '🎚', 'length': 2},
    # NEW mapping untuk ping animations dengan emoji yang benar
    'adder8': {'id': '5260687265121712272', 'char': '🎅', 'length': 2},  # LOW latency
    'adder9': {'id': '5262927296725007707', 'char': '🤪', 'length': 2},  # MEDIUM latency - NEW EMOJI
    'adder10': {'id': '5260471374295613818', 'char': '🥳', 'length': 2}  # HIGH latency
}

# Global variables
client = None
start_time = None

# Import font helper
try:
    from utils.font_helper import convert_font
except ImportError:
    def convert_font(text, style):
        return text

# ============= EMOJI FUNCTIONS =============

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def create_premium_entities(text):
    """Create premium emoji entities untuk ping animations"""
    entities = []
    
    try:
        utf16_offset = 0
        char_index = 0
        
        while char_index < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_len = len(emoji_char)
                
                if text[char_index:char_index + emoji_len] == emoji_char:
                    try:
                        emoji_utf16_length = emoji_data.get('length', 2)
                        
                        entity = MessageEntityCustomEmoji(
                            offset=utf16_offset,
                            length=emoji_utf16_length,
                            document_id=int(emoji_data['id'])
                        )
                        entities.append(entity)
                        
                        char_index += emoji_len
                        utf16_offset += emoji_utf16_length
                        found_emoji = True
                        break
                        
                    except (ValueError, OverflowError):
                        break
            
            if not found_emoji:
                try:
                    char = text[char_index]
                    char_utf16_bytes = char.encode('utf-16-le')
                    char_utf16_length = len(char_utf16_bytes) // 2
                    utf16_offset += char_utf16_length
                    char_index += 1
                except Exception:
                    char_index += 1
                    utf16_offset += 1
        
        return entities
        
    except Exception:
        return []

async def safe_send_premium(event, text):
    """Send message dengan premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            return await event.reply(text, formatting_entities=entities)
        else:
            return await event.reply(text)
    except Exception:
        return await event.reply(text)

async def safe_edit_premium(message, text):
    """Edit message dengan premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await message.edit(text, formatting_entities=entities)
        else:
            await message.edit(text)
    except Exception:
        await message.edit(text)

# ============= PING FUNCTIONS =============

def get_latency_level(ping_ms):
    """Determine latency level and appropriate emoji"""
    if ping_ms < 100:
        return "LOW", get_emoji('adder8')  # 🎅
    elif ping_ms < 300:
        return "MEDIUM", get_emoji('adder9')  # 🤩  
    else:
        return "HIGH", get_emoji('adder10')  # 🥳

def get_uptime():
    """Get uptime since bot started"""
    if start_time:
        uptime = datetime.now() - start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"
    return "Unknown"

# ============= ANIMATION SEQUENCES =============

def get_animation_frames():
    """Get ping animation frames dengan variasi semua emoji premium"""
    return [
        f"{get_emoji('main')} {convert_font('bentar otw cek ping', 'italic')}",
        f"{get_emoji('adder8')} {convert_font('nyala bang tenang aja', 'italic')}",
        f"{get_emoji('adder9')} {convert_font('gacor masa ga nyala', 'italic')}",
        f"nihh {get_emoji('adder10')}",
        f"{get_emoji('adder1')} {get_emoji('adder2')} {get_emoji('adder3')}",
        f"{get_emoji('main')} {get_emoji('adder4')} {get_emoji('adder5')} {get_emoji('adder6')}",
        f"{get_emoji('adder8')} {get_emoji('adder9')} {get_emoji('adder10')} {get_emoji('main')}",
        f"{get_emoji('adder1')} {get_emoji('adder2')} {get_emoji('adder3')} {get_emoji('adder4')} {get_emoji('adder5')}",
        f"{get_emoji('main')} {get_emoji('adder6')} {get_emoji('adder8')} {get_emoji('adder9')} {get_emoji('adder10')}",
        f"{get_emoji('adder1')} {get_emoji('main')} {get_emoji('adder2')} {get_emoji('adder3')} {get_emoji('adder4')} {get_emoji('adder5')}",
        f"{get_emoji('adder6')} {get_emoji('adder8')} {get_emoji('main')} {get_emoji('adder9')} {get_emoji('adder10')} {get_emoji('adder1')}",
        f"{get_emoji('adder2')} {get_emoji('adder3')} {get_emoji('adder4')} {get_emoji('main')} {get_emoji('adder5')} {get_emoji('adder6')}",
        f"{get_emoji('adder8')} {get_emoji('adder9')} {get_emoji('adder10')} {get_emoji('main')} {get_emoji('adder1')} {get_emoji('adder2')}",
        f"{get_emoji('main')} {get_emoji('adder3')} {get_emoji('adder4')} {get_emoji('adder5')} {get_emoji('adder6')} {get_emoji('adder8')}"
    ]

async def animate_ping(message, ping_time):
    """Animate ping dengan premium emojis"""
    frames = get_animation_frames()
    
    # Show animation frames
    for frame in frames:
        await safe_edit_premium(message, frame)
        await asyncio.sleep(0.8)
    
    # Show final result
    latency_level, latency_emoji = get_latency_level(ping_time)
    uptime = get_uptime()
    
    final_message = f"""{get_emoji('main')} {convert_font('VZOEL ASSISTANT', 'bold')}

{get_emoji('adder1')} {convert_font('PONG !!!!!!', 'bold')}
{get_emoji('check')} LATENCY: {latency_level} {latency_emoji}
{get_emoji('check')} uptime: {uptime}"""
    
    await safe_edit_premium(message, final_message)

# ============= EVENT HANDLERS =============

async def ping_handler(event):
    """Enhanced ping command dengan animations"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        # Record start time
        ping_start = time.time()
        
        # Start with first animation frame
        msg = await safe_send_premium(event, f"{get_emoji('main')} {convert_font('bentar otw cek ping', 'italic')}")
        
        # Calculate ping time
        ping_end = time.time()
        ping_time = (ping_end - ping_start) * 1000
        
        # Run animation
        await animate_ping(msg, ping_time)
        
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Ping error: {str(e)}")

async def is_owner_check(user_id):
    """Simple owner check"""
    OWNER_ID = 7847025168
    return user_id == OWNER_ID

# ============= PLUGIN SETUP =============

def get_plugin_info():
    """Return plugin info"""
    return PLUGIN_INFO

def setup(client_instance):
    """Setup plugin"""
    global client, start_time
    client = client_instance
    start_time = datetime.now()
    
    # Register ping handler
    client.add_event_handler(
        ping_handler, 
        events.NewMessage(pattern=r'\.ping$')
    )
    
    print(f"✅ [Ping] Animated premium version loaded v{PLUGIN_INFO['version']}")
    print(f"✅ [Ping] New emoji mappings: adder8(🎅), adder9(🤩), adder10(🥳)")

# Export functions
__all__ = ['setup', 'get_plugin_info', 'ping_handler']