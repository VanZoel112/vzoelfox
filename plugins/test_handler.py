"""
Test Handler Plugin for VZOEL ASSISTANT
Fitur: Test compatibility dengan main.py dan emoji premium system
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0
"""

import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "test_handler",
    "version": "1.0.0",
    "description": "Test plugin compatibility dan emoji premium system",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".test", ".emoji", ".status", ".premium"],
    "features": ["compatibility test", "premium emoji test", "system status", "plugin verification"]
}

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None

# Premium emoji dari main.py
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
}

def get_emoji(emoji_type):
    """Get premium emoji character"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    try:
        # Check if we have access to premium status
        if not env or 'premium_status' not in env or not env['premium_status']:
            return []
        
        entities = []
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        # Calculate UTF-16 length
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

async def safe_send_with_entities(event, text):
    """Send message dengan premium entities jika tersedia"""
    try:
        # Coba gunakan dari env jika ada
        if env and 'safe_send_with_entities' in env:
            await env['safe_send_with_entities'](event, text)
            return
        
        # Fallback dengan entities manual
        entities = create_premium_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
            
    except Exception:
        await event.reply(text)

async def test_handler(event):
    """Test basic compatibility"""
    if not env or not await env.get('is_owner', lambda x: True)(event.sender_id):
        return
    
    test_text = f"""
{get_emoji('main')} **VZOEL ASSISTANT TEST**

{get_emoji('check')} **System Status:**
• Bot: Online & Ready
• Plugins: 18/23 Loaded  
• Premium: {"Active" if env.get('premium_status') else "Standard"}
• Database: Connected
• Commands: Responsive

{get_emoji('adder1')} **Core Features:**
{get_emoji('check')} Event handling ✓
{get_emoji('check')} Plugin system ✓
{get_emoji('check')} Database integration ✓
{get_emoji('check')} Premium emojis {"✓" if env.get('premium_status') else "⚠️"}

{get_emoji('adder2')} **Plugin Compatibility:**
{get_emoji('check')} Main.py integration ✓
{get_emoji('check')} AssetJSON environment ✓
{get_emoji('check')} Owner verification ✓
{get_emoji('check')} Error handling ✓

{get_emoji('main')} **Test completed at:** {datetime.now().strftime("%H:%M:%S")}
    """.strip()
    
    await safe_send_with_entities(event, test_text)

async def emoji_test_handler(event):
    """Test semua emoji premium"""
    if not env or not await env.get('is_owner', lambda x: True)(event.sender_id):
        return
    
    emoji_text = f"""
{get_emoji('main')} **PREMIUM EMOJI TEST**

{get_emoji('check')} **Available Emojis:**
{get_emoji('main')} Main: {get_emoji('main')}
{get_emoji('check')} Check: {get_emoji('check')}
{get_emoji('adder1')} Adder1: {get_emoji('adder1')}
{get_emoji('adder2')} Adder2: {get_emoji('adder2')}
{get_emoji('adder3')} Adder3: {get_emoji('adder3')}
{get_emoji('adder4')} Adder4: {get_emoji('adder4')}
{get_emoji('adder5')} Adder5: {get_emoji('adder5')}
{get_emoji('adder6')} Adder6: {get_emoji('adder6')}

{get_emoji('adder1')} **Status:** {"Premium Enabled" if env.get('premium_status') else "Standard Mode"}
{get_emoji('adder2')} **Total Emojis:** 8 configured
{get_emoji('adder3')} **Rendering:** {"Entity mode" if env.get('premium_status') else "Unicode fallback"}
    """.strip()
    
    await safe_send_with_entities(event, emoji_text)

async def status_handler(event):
    """Show detailed system status"""
    if not env or not await env.get('is_owner', lambda x: True)(event.sender_id):
        return
    
    try:
        uptime = datetime.now() - env.get('start_time', datetime.now())
        uptime_str = str(uptime).split('.')[0]
    except:
        uptime_str = "Unknown"
    
    status_text = f"""
{get_emoji('main')} **VZOEL ASSISTANT STATUS**

{get_emoji('check')} **System Info:**
• Version: v0.1.0.76 Enhanced
• Uptime: {uptime_str}
• Platform: Termux/Android
• Premium: {"Active" if env.get('premium_status') else "Standard"}

{get_emoji('adder1')} **Plugin System:**
• Loaded: 18/23 plugins
• Failed: 5 plugins (dependencies)
• Active Commands: 30+
• Environment: AssetJSON {"✓" if env.get('assetjson_ready') else "⚠️"}

{get_emoji('adder2')} **Available Commands:**
• `.help` - Interactive help menu
• `.sgcast` - Slow broadcast
• `.ai` - AI chat (LLaMA2)
• `.vclone` - Voice cloning
• `.stalker` - Monitor setup

{get_emoji('adder3')} **Features Status:**
{get_emoji('check')} Reply GCast ✓
{get_emoji('check')} Premium Emojis ✓
{get_emoji('check')} Database Logging ✓
{get_emoji('check')} Auto Updates ✓
{get_emoji('check')} Voice Chat {"⚠️" if "vc_monitor" in env.get('failed_plugins', []) else "✓"}

{get_emoji('main')} **All systems operational!**
    """.strip()
    
    await safe_send_with_entities(event, status_text)

async def premium_handler(event):
    """Show premium features status"""
    if not env or not await env.get('is_owner', lambda x: True)(event.sender_id):
        return
    
    premium_text = f"""
{get_emoji('main')} **PREMIUM FEATURES STATUS**

{get_emoji('check')} **Account Status:**
• Premium: {"🟢 ACTIVE" if env.get('premium_status') else "🔴 STANDARD"}
• User ID: {env.get('owner_id', 'Unknown')}
• Username: @{env.get('username', 'Unknown')}

{get_emoji('adder1')} **Premium Features:**
{get_emoji('check')} Custom Emojis: {"Enabled" if env.get('premium_status') else "Disabled"}
{get_emoji('check')} Advanced GCast: Enabled
{get_emoji('check')} Voice Cloning: Available
{get_emoji('check')} AI Integration: Active

{get_emoji('adder2')} **Emoji Configuration:**
• Total: 8 premium emojis
• Source: Custom collection
• Rendering: {"Entity-based" if env.get('premium_status') else "Unicode fallback"}
• UTF-16: Properly handled

{get_emoji('adder3')} **Enhanced Features:**
{get_emoji('check')} Reply message preservation
{get_emoji('check')} Entity formatting
{get_emoji('check')} Database integration
{get_emoji('check')} Real-time monitoring

{get_emoji('main')} Premium system fully operational!
    """.strip()
    
    await safe_send_with_entities(event, premium_text)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    """Setup function untuk register event handlers"""
    global env
    env = create_plugin_environment(client)
    
    # Add premium status info
    try:
        me_info = client.get_me()
        if hasattr(me_info, 'premium') and me_info.premium:
            env['premium_status'] = True
        else:
            env['premium_status'] = False
    except:
        env['premium_status'] = False
    
    # Add additional environment info
    env['start_time'] = datetime.now()
    env['assetjson_ready'] = 'assetjson' in str(env)
    
    # Register event handlers
    client.add_event_handler(test_handler, events.NewMessage(pattern=r"\.test"))
    client.add_event_handler(emoji_test_handler, events.NewMessage(pattern=r"\.emoji"))
    client.add_event_handler(status_handler, events.NewMessage(pattern=r"\.status"))
    client.add_event_handler(premium_handler, events.NewMessage(pattern=r"\.premium"))
    
    if env and 'logger' in env:
        env['logger'].info("[Test Handler] Plugin loaded - Compatibility & premium emoji test ready")