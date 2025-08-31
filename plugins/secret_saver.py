#!/usr/bin/env python3
"""
Secret Chat Saver Plugin for VzoelFox Userbot - Extreme Media Bypass & Auto Gallery Save
Fitur: Bypass sekali lihat, auto save ke galeri, support semua chat, stealth mode
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Extreme Secret Media Saver
"""

import os
import asyncio
import shutil
from datetime import datetime
from telethon import events
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo,
    DocumentAttributeAudio, DocumentAttributeAnimated, MessageMediaWebPage
)
from telethon.errors import FloodWaitError

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('secret_saver')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

# Import font helper
try:
    import sys
    sys.path.append('utils')
    from font_helper import convert_font, process_all_markdown, bold, mono
    FONT_HELPER_AVAILABLE = True
except ImportError:
    FONT_HELPER_AVAILABLE = False
    
    def convert_font(text, font_type='bold'):
        return f"**{text}**" if font_type == 'bold' else f"`{text}`"
    def bold(text):
        return f"**{text}**"
    def mono(text):
        return f"`{text}`"

PLUGIN_INFO = {
    "name": "secret_saver",
    "version": "1.0.0",
    "description": "Extreme secret media saver - bypass sekali lihat, auto save ke galeri dari semua chat",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".secreton", ".secretoff", ".secretstatus", ".secretmode", ".secrethelp", ".gallerysave"],
    "features": ["sekali lihat bypass", "auto gallery save", "stealth mode", "all chat support", "background monitoring", "premium branding"]
}

# Premium Emoji Mapping
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

# Secret Saver Configuration
SECRET_SAVER_STATE = {
    'active': False,
    'stealth_mode': True,
    'auto_save_gallery': True,
    'save_count': 0,
    'last_save': None,
    'supported_chats': []
}

SAVE_DIRECTORY = os.path.expanduser("~/VzoelFox_SecretSaver")
GALLERY_DIR = os.path.expanduser("~/storage/pictures/VzoelFox_Secret")

def ensure_directories():
    """Ensure save directories exist"""
    for directory in [SAVE_DIRECTORY, GALLERY_DIR]:
        os.makedirs(directory, exist_ok=True, mode=0o755)

def get_vzoel_signature():
    """Get Vzoel Fox's signature branding"""
    return f"""
{get_emoji('main')} {convert_font('VzoelFox Secret Saver', 'bold')}
{get_emoji('adder3')} {convert_font('Extreme Media Bypass System', 'mono')}
{get_emoji('adder6')} {convert_font('© 2025 Vzoel Fox\'s (LTPN) - Secret Technology', 'mono')}
    """.strip()

def save_state():
    """Save secret saver state to database"""
    try:
        if DB_COMPATIBLE and plugin_db:
            # Use correct database methods
            import json
            data = {
                'key': 'secret_state',
                'state_data': json.dumps(SECRET_SAVER_STATE),
                'updated_at': datetime.now().isoformat()
            }
            plugin_db.insert('secret_config', data)
        else:
            # Fallback to file
            ensure_directories()
            state_file = os.path.join(SAVE_DIRECTORY, '.secret_state.json')
            import json
            with open(state_file, 'w') as f:
                json.dump(SECRET_SAVER_STATE, f, indent=2)
    except Exception as e:
        print(f"[SecretSaver] Save state error: {e}")

def load_state():
    """Load secret saver state from database"""
    global SECRET_SAVER_STATE
    try:
        if DB_COMPATIBLE and plugin_db:
            # Use correct database methods
            rows = plugin_db.select('secret_config', 'key = ?', ('secret_state',))
            if rows:
                import json
                SECRET_SAVER_STATE = json.loads(rows[0]['state_data'])
        else:
            # Fallback to file
            state_file = os.path.join(SAVE_DIRECTORY, '.secret_state.json')
            if os.path.exists(state_file):
                import json
                with open(state_file, 'r') as f:
                    SECRET_SAVER_STATE = json.load(f)
    except Exception as e:
        print(f"[SecretSaver] Load state error: {e}")

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

async def save_media_to_gallery(client, message, media_type="unknown"):
    """Save media to gallery dengan metadata"""
    try:
        ensure_directories()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chat_info = "unknown"
        
        try:
            chat = await client.get_entity(message.chat_id)
            chat_info = getattr(chat, 'title', getattr(chat, 'first_name', f'chat_{message.chat_id}'))
            chat_info = "".join(c for c in chat_info if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
        except:
            chat_info = f"chat_{message.chat_id}"
        
        # Download media
        if message.media:
            file_extension = "jpg"  # default
            
            if isinstance(message.media, MessageMediaPhoto):
                file_extension = "jpg"
                media_type = "photo"
            elif isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                file_extension = doc.mime_type.split('/')[-1] if doc.mime_type else "bin"
                
                # Check document attributes
                for attr in doc.attributes:
                    if isinstance(attr, DocumentAttributeVideo):
                        media_type = "video"
                        file_extension = "mp4"
                    elif isinstance(attr, DocumentAttributeAudio):
                        media_type = "audio" 
                        file_extension = "mp3"
                    elif isinstance(attr, DocumentAttributeAnimated):
                        media_type = "gif"
                        file_extension = "gif"
            
            # Create filename
            filename = f"VzoelSecret_{timestamp}_{chat_info}_{media_type}.{file_extension}"
            temp_path = os.path.join(SAVE_DIRECTORY, filename)
            gallery_path = os.path.join(GALLERY_DIR, filename)
            
            # Download to temp first
            await client.download_media(message, temp_path)
            
            # Copy to gallery
            shutil.copy2(temp_path, gallery_path)
            
            # Update stats
            SECRET_SAVER_STATE['save_count'] += 1
            SECRET_SAVER_STATE['last_save'] = datetime.now().isoformat()
            save_state()
            
            return {
                'success': True,
                'temp_path': temp_path,
                'gallery_path': gallery_path,
                'filename': filename,
                'media_type': media_type,
                'chat_info': chat_info
            }
    
    except Exception as e:
        print(f"[SecretSaver] Save media error: {e}")
        return {'success': False, 'error': str(e)}

async def handle_secret_media(client, event):
    """Handle secret/sekali lihat media"""
    try:
        if not SECRET_SAVER_STATE['active']:
            return
        
        message = event.message
        
        # Check if message has media
        if not message.media:
            return
        
        # Check for "sekali lihat" atau self-destructing media
        is_secret = False
        
        # Check TTL (Time To Live) for secret media
        if hasattr(message.media, 'ttl_seconds') and message.media.ttl_seconds:
            is_secret = True
        
        # Check for photo with TTL
        if isinstance(message.media, MessageMediaPhoto):
            if hasattr(message.media.photo, 'ttl_seconds') and message.media.photo.ttl_seconds:
                is_secret = True
        
        # Check for document with TTL
        if isinstance(message.media, MessageMediaDocument):
            if hasattr(message.media.document, 'ttl_seconds') and message.media.document.ttl_seconds:
                is_secret = True
        
        # Always save if auto_save_gallery is enabled (extreme mode)
        if SECRET_SAVER_STATE['auto_save_gallery'] or is_secret:
            result = await save_media_to_gallery(client, message)
            
            if result['success'] and not SECRET_SAVER_STATE['stealth_mode']:
                # Send notification (only if not stealth)
                notification = f"""
{get_emoji('adder2')} {convert_font('SECRET MEDIA SAVED!', 'bold')}

{get_emoji('check')} {convert_font('Type:', 'mono')} {result['media_type']}
{get_emoji('adder4')} {convert_font('From:', 'mono')} {result['chat_info']}
{get_emoji('adder6')} {convert_font('Saved to Gallery:', 'mono')} ✓
{get_emoji('main')} {convert_font('Total Saved:', 'mono')} {SECRET_SAVER_STATE['save_count']}

{get_vzoel_signature()}
                """.strip()
                
                try:
                    me = await client.get_me()
                    await client.send_message(me.id, notification)
                except:
                    pass  # Silent fail in stealth mode
    
    except Exception as e:
        print(f"[SecretSaver] Handle secret media error: {e}")

# Global client reference
client = None

async def secreton_handler(event):
    """Turn on secret saver"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        SECRET_SAVER_STATE['active'] = True
        save_state()
        
        response = f"""
{get_emoji('adder2')} {convert_font('SECRET SAVER ACTIVATED!', 'bold')}

{get_emoji('check')} {convert_font('Status:', 'mono')} Active & Monitoring
{get_emoji('adder4')} {convert_font('Auto Gallery Save:', 'mono')} {'On' if SECRET_SAVER_STATE['auto_save_gallery'] else 'Off'}
{get_emoji('adder6')} {convert_font('Stealth Mode:', 'mono')} {'On' if SECRET_SAVER_STATE['stealth_mode'] else 'Off'}
{get_emoji('main')} {convert_font('Coverage:', 'mono')} All Chats (Groups, Channels, DM)

{get_emoji('adder5')} {convert_font('EXTREME MODE ENABLED:', 'bold')}
• Bypass sekali lihat photos
• Auto save to gallery
• Background monitoring
• Stealth operation

{get_vzoel_signature()}
        """.strip()
        
        await event.reply(response)
    
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def secretoff_handler(event):
    """Turn off secret saver"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        SECRET_SAVER_STATE['active'] = False
        save_state()
        
        response = f"""
{get_emoji('adder1')} {convert_font('SECRET SAVER DEACTIVATED', 'bold')}

{get_emoji('check')} {convert_font('Status:', 'mono')} Inactive
{get_emoji('adder3')} {convert_font('Total Saved:', 'mono')} {SECRET_SAVER_STATE['save_count']} files
{get_emoji('adder4')} {convert_font('Last Activity:', 'mono')} {SECRET_SAVER_STATE['last_save'] or 'Never'}

{get_emoji('main')} Secret monitoring stopped

{get_vzoel_signature()}
        """.strip()
        
        await event.reply(response)
    
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def secretstatus_handler(event):
    """Show secret saver status"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        status_text = f"""
{get_emoji('main')} {convert_font('SECRET SAVER STATUS', 'bold')}

{get_emoji('check')} {convert_font('System Status:', 'mono')} {'🟢 Active' if SECRET_SAVER_STATE['active'] else '🔴 Inactive'}
{get_emoji('adder4')} {convert_font('Auto Gallery Save:', 'mono')} {'✅ Enabled' if SECRET_SAVER_STATE['auto_save_gallery'] else '❌ Disabled'}
{get_emoji('adder6')} {convert_font('Stealth Mode:', 'mono')} {'🥷 On' if SECRET_SAVER_STATE['stealth_mode'] else '👁️ Off'}

{get_emoji('adder2')} {convert_font('Statistics:', 'bold')}
{get_emoji('check')} Files Saved: {SECRET_SAVER_STATE['save_count']}
{get_emoji('adder3')} Last Save: {SECRET_SAVER_STATE['last_save'][:19] if SECRET_SAVER_STATE['last_save'] else 'Never'}

{get_emoji('adder5')} {convert_font('Directories:', 'bold')}
{get_emoji('check')} Temp: {SAVE_DIRECTORY}
{get_emoji('check')} Gallery: {GALLERY_DIR}

{get_emoji('adder1')} {convert_font('Coverage:', 'bold')}
• Private chats ✓
• Group chats ✓  
• Channels ✓
• Secret chats ✓

{get_vzoel_signature()}
        """.strip()
        
        await event.reply(status_text)
    
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def secretmode_handler(event):
    """Toggle secret saver modes"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split()
        if len(args) < 2:
            help_text = f"""
{get_emoji('main')} {convert_font('SECRET MODE SETTINGS', 'bold')}

{get_emoji('check')} {convert_font('Available Modes:', 'bold')}
• {convert_font('.secretmode stealth', 'mono')} - Toggle stealth mode
• {convert_font('.secretmode gallery', 'mono')} - Toggle auto gallery save
• {convert_font('.secretmode extreme', 'mono')} - Enable all extreme features

{get_emoji('adder4')} {convert_font('Current Settings:', 'bold')}
{get_emoji('check')} Stealth: {'On' if SECRET_SAVER_STATE['stealth_mode'] else 'Off'}
{get_emoji('check')} Auto Gallery: {'On' if SECRET_SAVER_STATE['auto_save_gallery'] else 'Off'}

{get_vzoel_signature()}
            """.strip()
            await event.reply(help_text)
            return
        
        mode = args[1].lower()
        
        if mode == 'stealth':
            SECRET_SAVER_STATE['stealth_mode'] = not SECRET_SAVER_STATE['stealth_mode']
            status = 'enabled' if SECRET_SAVER_STATE['stealth_mode'] else 'disabled'
            await event.reply(f"{get_emoji('adder3')} Stealth mode {status}")
            
        elif mode == 'gallery':
            SECRET_SAVER_STATE['auto_save_gallery'] = not SECRET_SAVER_STATE['auto_save_gallery']
            status = 'enabled' if SECRET_SAVER_STATE['auto_save_gallery'] else 'disabled'
            await event.reply(f"{get_emoji('adder4')} Auto gallery save {status}")
            
        elif mode == 'extreme':
            SECRET_SAVER_STATE['stealth_mode'] = True
            SECRET_SAVER_STATE['auto_save_gallery'] = True
            SECRET_SAVER_STATE['active'] = True
            await event.reply(f"""
{get_emoji('adder5')} {convert_font('EXTREME MODE ACTIVATED!', 'bold')}

{get_emoji('check')} Stealth Mode: On
{get_emoji('check')} Auto Gallery: On  
{get_emoji('check')} System: Active
{get_emoji('main')} All secret media will be saved silently

{get_vzoel_signature()}
            """.strip())
        
        save_state()
    
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def secrethelp_handler(event):
    """Show secret saver help"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        help_text = f"""
{get_emoji('main')} {convert_font('VZOELFOX SECRET SAVER HELP', 'bold')}

{get_emoji('adder2')} {convert_font('Main Commands:', 'bold')}
• {convert_font('.secreton', 'mono')} - Activate secret saver
• {convert_font('.secretoff', 'mono')} - Deactivate secret saver
• {convert_font('.secretstatus', 'mono')} - Show current status
• {convert_font('.secretmode <option>', 'mono')} - Toggle modes
• {convert_font('.secrethelp', 'mono')} - Show this help

{get_emoji('adder4')} {convert_font('Features:', 'bold')}
🔥 Bypass foto sekali lihat
📱 Auto save to phone gallery
🥷 Stealth mode operation
📂 Support all chat types
⚡ Background monitoring
🛡️ Extreme bypass technology

{get_emoji('adder6')} {convert_font('How It Works:', 'bold')}
1. Enable dengan {convert_font('.secreton', 'mono')}
2. System monitors semua chat otomatis
3. Foto/video sekali lihat auto tersimpan
4. Files tersimpan di gallery phone
5. Stealth mode = no notifications

{get_emoji('adder5')} {convert_font('EXTREME FEATURES:', 'bold')}
• Works di group, channel, private chat
• Bypass Telegram restrictions
• Auto gallery integration
• No trace left behind
• 100% stealth operation

{get_vzoel_signature()}
        """.strip()
        
        await event.reply(help_text)
    
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def gallerysave_handler(event):
    """Manual save current replied media to gallery"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        if not event.is_reply:
            await event.reply(f"{get_emoji('adder5')} Reply to a media message to save it manually!")
            return
        
        reply_msg = await event.get_reply_message()
        if not reply_msg.media:
            await event.reply(f"{get_emoji('adder3')} No media found in replied message!")
            return
        
        # Save the media
        result = await save_media_to_gallery(client, reply_msg)
        
        if result['success']:
            response = f"""
{get_emoji('adder2')} {convert_font('MEDIA SAVED TO GALLERY!', 'bold')}

{get_emoji('check')} {convert_font('File:', 'mono')} {result['filename']}
{get_emoji('adder4')} {convert_font('Type:', 'mono')} {result['media_type']}
{get_emoji('adder6')} {convert_font('From:', 'mono')} {result['chat_info']}
{get_emoji('main')} {convert_font('Gallery Path:', 'mono')} ✓

{get_vzoel_signature()}
            """.strip()
        else:
            response = f"{get_emoji('adder5')} Save failed: {result.get('error', 'Unknown error')}"
        
        await event.reply(response)
    
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Ensure directories exist
    ensure_directories()
    
    # Load saved state
    load_state()
    
    # Register command handlers
    client.add_event_handler(secreton_handler, events.NewMessage(pattern=r'\.secreton$'))
    client.add_event_handler(secretoff_handler, events.NewMessage(pattern=r'\.secretoff$'))
    client.add_event_handler(secretstatus_handler, events.NewMessage(pattern=r'\.secretstatus$'))
    client.add_event_handler(secretmode_handler, events.NewMessage(pattern=r'\.secretmode(?:\s+(.+))?$'))
    client.add_event_handler(secrethelp_handler, events.NewMessage(pattern=r'\.secrethelp$'))
    client.add_event_handler(gallerysave_handler, events.NewMessage(pattern=r'\.gallerysave$'))
    
    # Register background monitor for secret media
    client.add_event_handler(
        lambda event: handle_secret_media(client, event),
        events.NewMessage()
    )
    
    print(f"✅ [SecretSaver] VzoelFox Secret Media Saver loaded v{PLUGIN_INFO['version']}")
    print(f"✅ [SecretSaver] Extreme bypass technology activated")
    print(f"✅ [SecretSaver] Status: {'Active' if SECRET_SAVER_STATE['active'] else 'Inactive'}")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[SecretSaver] Plugin cleanup initiated")
        save_state()
        client = None
        print("[SecretSaver] Plugin cleanup completed")
    except Exception as e:
        print(f"[SecretSaver] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info']