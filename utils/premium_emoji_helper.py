#!/usr/bin/env python3
"""
Premium Emoji Helper for VzoelFox Userbot - Universal Premium Emoji System
Fitur: Premium emoji integration, UTF-16 entities, universal compatibility
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Universal Premium Emoji System
"""

from telethon.tl.types import MessageEntityCustomEmoji

# Premium Emoji Mapping - Vzoel Fox's Collection
PREMIUM_EMOJIS = {
    "main": {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6": {"emoji": "🎚️", "custom_emoji_id": "5794323465452394551"}
}

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('emoji', '🤩')

def get_emoji_id(emoji_type):
    """Get premium emoji custom ID"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('custom_emoji_id', '6156784006194009426')

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['emoji']
                emoji_id = emoji_data['custom_emoji_id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        i += len(emoji_char)
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

async def safe_send_premium(event, text, file=None, buttons=None):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        kwargs = {}
        
        if entities:
            kwargs['formatting_entities'] = entities
        if file:
            kwargs['file'] = file
        if buttons:
            kwargs['buttons'] = buttons
            
        await event.reply(text, **kwargs)
    except Exception:
        # Fallback without entities
        kwargs = {}
        if file:
            kwargs['file'] = file
        if buttons:
            kwargs['buttons'] = buttons
        await event.reply(text, **kwargs)

async def safe_edit_premium(message, text, buttons=None):
    """Edit message with premium entities"""
    try:
        entities = create_premium_entities(text)
        kwargs = {}
        
        if entities:
            kwargs['formatting_entities'] = entities
        if buttons:
            kwargs['buttons'] = buttons
            
        await message.edit(text, **kwargs)
    except Exception:
        # Fallback without entities
        kwargs = {}
        if buttons:
            kwargs['buttons'] = buttons
        await message.edit(text, **kwargs)

def get_vzoel_signature():
    """Get universal Vzoel Fox's signature"""
    return f"""
{get_emoji('main')} VzoelFox Premium System
{get_emoji('adder3')} Powered by Vzoel Fox's Technology
{get_emoji('adder6')} - 2025 Vzoel Fox's (LTPN) - Premium Userbot
    """.strip()

def inject_premium_emoji_support(plugin_module):
    """Inject premium emoji support into plugin module"""
    try:
        # Add premium emoji functions to plugin
        plugin_module.get_emoji = get_emoji
        plugin_module.get_emoji_id = get_emoji_id
        plugin_module.create_premium_entities = create_premium_entities
        plugin_module.safe_send_premium = safe_send_premium
        plugin_module.safe_edit_premium = safe_edit_premium
        plugin_module.get_vzoel_signature = get_vzoel_signature
        plugin_module.PREMIUM_EMOJIS = PREMIUM_EMOJIS
        
        # Mark as premium enabled
        plugin_module.PREMIUM_EMOJI_ENABLED = True
        
        return True
    except Exception as e:
        print(f"[PremiumEmoji] Injection error: {e}")
        return False

# Export functions
__all__ = [
    'get_emoji', 'get_emoji_id', 'create_premium_entities', 
    'safe_send_premium', 'safe_edit_premium', 'get_vzoel_signature',
    'inject_premium_emoji_support', 'PREMIUM_EMOJIS'
]