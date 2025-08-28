#!/usr/bin/env python3
"""
Asset JSON Manager Plugin untuk VZOEL ASSISTANT
File: plugins/assetjson.py
Fungsi: Mengekstrak dan mengelola assets dari main.py untuk plugin lain
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
import json
import time
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
from datetime import datetime

# Asset files
ASSET_FILES = {
    'emoji': 'plugins/assets/emoji_config.json',
    'fonts': 'plugins/assets/fonts_config.json',
    'settings': 'plugins/assets/bot_settings.json'
}

# Extracted assets (akan diisi otomatis)
EXTRACTED_ASSETS = {
    'premium_emojis': {},
    'fonts': {},
    'premium_status': False,
    'command_prefix': '.',
    'last_updated': None,
    'version': 'v0.1.0.75'
}

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        me = await client.get_me()
        return user_id == me.id
    except:
        return True

def ensure_assets_directory():
    """Pastikan directory assets exists"""
    assets_dir = 'plugins/assets'
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        print(f"Created assets directory: {assets_dir}")

def extract_from_main_module():
    """Extract assets dari main module"""
    try:
        # Cari main module
        main_module = None
        for name, module in sys.modules.items():
            if hasattr(module, 'PREMIUM_EMOJIS') and hasattr(module, 'FONTS'):
                main_module = module
                break
        
        if not main_module:
            # Coba akses __main__
            import __main__
            main_module = __main__
        
        if main_module:
            # Extract premium emojis
            if hasattr(main_module, 'PREMIUM_EMOJIS'):
                EXTRACTED_ASSETS['premium_emojis'] = getattr(main_module, 'PREMIUM_EMOJIS', {})
            
            # Extract fonts
            if hasattr(main_module, 'FONTS'):
                EXTRACTED_ASSETS['fonts'] = getattr(main_module, 'FONTS', {})
            
            # Extract premium status
            if hasattr(main_module, 'premium_status'):
                EXTRACTED_ASSETS['premium_status'] = getattr(main_module, 'premium_status', False)
            
            # Extract command prefix
            if hasattr(main_module, 'COMMAND_PREFIX'):
                EXTRACTED_ASSETS['command_prefix'] = getattr(main_module, 'COMMAND_PREFIX', '.')
            
            EXTRACTED_ASSETS['last_updated'] = datetime.now().isoformat()
            
            print(f"Successfully extracted assets from main module")
            return True
        
        return False
    except Exception as e:
        print(f"Error extracting from main module: {e}")
        return False

def extract_from_file_parsing():
    """Extract assets dengan parsing main.py file"""
    try:
        main_py_path = 'main.py'
        if not os.path.exists(main_py_path):
            return False
        
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract PREMIUM_EMOJIS
        emoji_pattern = r'PREMIUM_EMOJIS\s*=\s*({.*?})'
        emoji_match = re.search(emoji_pattern, content, re.DOTALL)
        if emoji_match:
            try:
                # Evaluasi dictionary secara aman
                emoji_dict = eval(emoji_match.group(1))
                EXTRACTED_ASSETS['premium_emojis'] = emoji_dict
            except:
                pass
        
        # Extract FONTS
        fonts_pattern = r'FONTS\s*=\s*({.*?})'
        fonts_match = re.search(fonts_pattern, content, re.DOTALL)
        if fonts_match:
            try:
                fonts_dict = eval(fonts_match.group(1))
                EXTRACTED_ASSETS['fonts'] = fonts_dict
            except:
                pass
        
        # Extract COMMAND_PREFIX
        prefix_pattern = r'COMMAND_PREFIX\s*=\s*os\.getenv\("COMMAND_PREFIX",\s*"([^"]*)"'
        prefix_match = re.search(prefix_pattern, content)
        if prefix_match:
            EXTRACTED_ASSETS['command_prefix'] = prefix_match.group(1)
        
        EXTRACTED_ASSETS['last_updated'] = datetime.now().isoformat()
        print("Successfully extracted assets via file parsing")
        return True
        
    except Exception as e:
        print(f"Error in file parsing: {e}")
        return False

def save_assets_to_files():
    """Save extracted assets ke JSON files"""
    ensure_assets_directory()
    
    try:
        # Save emoji config
        emoji_data = {
            'premium_emojis': EXTRACTED_ASSETS['premium_emojis'],
            'premium_status': EXTRACTED_ASSETS['premium_status'],
            'last_updated': EXTRACTED_ASSETS['last_updated']
        }
        with open(ASSET_FILES['emoji'], 'w') as f:
            json.dump(emoji_data, f, indent=2)
        
        # Save fonts config
        fonts_data = {
            'fonts': EXTRACTED_ASSETS['fonts'],
            'last_updated': EXTRACTED_ASSETS['last_updated']
        }
        with open(ASSET_FILES['fonts'], 'w') as f:
            json.dump(fonts_data, f, indent=2)
        
        # Save bot settings
        settings_data = {
            'command_prefix': EXTRACTED_ASSETS['command_prefix'],
            'version': EXTRACTED_ASSETS['version'],
            'last_updated': EXTRACTED_ASSETS['last_updated']
        }
        with open(ASSET_FILES['settings'], 'w') as f:
            json.dump(settings_data, f, indent=2)
        
        print("Assets saved to JSON files successfully")
        return True
        
    except Exception as e:
        print(f"Error saving assets: {e}")
        return False

def load_assets_from_files():
    """Load assets dari JSON files"""
    try:
        for asset_type, file_path in ASSET_FILES.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                    if asset_type == 'emoji':
                        EXTRACTED_ASSETS['premium_emojis'] = data.get('premium_emojis', {})
                        EXTRACTED_ASSETS['premium_status'] = data.get('premium_status', False)
                    elif asset_type == 'fonts':
                        EXTRACTED_ASSETS['fonts'] = data.get('fonts', {})
                    elif asset_type == 'settings':
                        EXTRACTED_ASSETS['command_prefix'] = data.get('command_prefix', '.')
                        EXTRACTED_ASSETS['version'] = data.get('version', 'v0.1.0.75')
        
        print("Assets loaded from JSON files")
        return True
    except Exception as e:
        print(f"Error loading assets: {e}")
        return False

def get_premium_emoji(emoji_type):
    """Public function untuk mendapatkan premium emoji"""
    emojis = EXTRACTED_ASSETS.get('premium_emojis', {})
    if emoji_type in emojis:
        return emojis[emoji_type].get('char', '🤩')
    return '🤩'

def get_premium_emoji_id(emoji_type):
    """Get premium emoji ID"""
    emojis = EXTRACTED_ASSETS.get('premium_emojis', {})
    if emoji_type in emojis:
        return emojis[emoji_type].get('id', '')
    return ''

def convert_text_font(text, font_type='bold'):
    """Convert text menggunakan extracted fonts"""
    fonts = EXTRACTED_ASSETS.get('fonts', {})
    if font_type not in fonts:
        return text
    
    font_map = fonts[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def get_command_prefix():
    """Get command prefix"""
    return EXTRACTED_ASSETS.get('command_prefix', '.')

def get_premium_status():
    """Get premium status"""
    return EXTRACTED_ASSETS.get('premium_status', False)

def create_premium_entities_from_assets(text):
    """Create premium entities menggunakan extracted assets"""
    if not EXTRACTED_ASSETS.get('premium_status', False):
        return []
    
    entities = []
    current_offset = 0
    i = 0
    
    try:
        emojis = EXTRACTED_ASSETS.get('premium_emojis', {})
        
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in emojis.items():
                emoji_char = emoji_data.get('char', '')
                emoji_id = emoji_data.get('id', '')
                
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
                    except:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except:
        return []

# COMMAND: Extract Assets
@client.on(events.NewMessage(pattern=rf'\.extract'))
async def extract_assets_handler(event):
    """Command untuk extract assets dari main.py"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        msg = await event.reply("🔄 Extracting assets from main.py...")
        
        # Try extraction methods
        success = False
        methods_tried = []
        
        # Method 1: Module extraction
        if extract_from_main_module():
            success = True
            methods_tried.append("Module Access ✅")
        else:
            methods_tried.append("Module Access ❌")
        
        # Method 2: File parsing (backup)
        if not success and extract_from_file_parsing():
            success = True
            methods_tried.append("File Parsing ✅")
        else:
            methods_tried.append("File Parsing ❌")
        
        if success:
            # Save to files
            save_success = save_assets_to_files()
            
            # Generate report
            emoji_count = len(EXTRACTED_ASSETS.get('premium_emojis', {}))
            font_count = len(EXTRACTED_ASSETS.get('fonts', {}))
            
            result_text = f"""
✅ **ASSET EXTRACTION COMPLETED**

📊 **Extraction Results:**
• Premium Emojis: `{emoji_count}` types
• Font Mappings: `{font_count}` sets
• Command Prefix: `{EXTRACTED_ASSETS['command_prefix']}`
• Premium Status: {'Active' if EXTRACTED_ASSETS['premium_status'] else 'Standard'}

🔧 **Methods Tried:**
{chr(10).join(f'• {method}' for method in methods_tried)}

💾 **File Operations:**
• JSON Files: {'Saved ✅' if save_success else 'Failed ❌'}
• Assets Directory: Created/Updated

⏰ **Updated:** `{EXTRACTED_ASSETS['last_updated']}`

🔧 Use `.assets` to view extracted data
            """.strip()
            
            await msg.edit(result_text)
        else:
            await msg.edit("❌ **Asset extraction failed** - No valid extraction method succeeded")
    
    except Exception as e:
        await event.reply(f"❌ **Extraction Error:** {str(e)}")

# COMMAND: View Assets
@client.on(events.NewMessage(pattern=rf'\.assets'))
async def view_assets_handler(event):
    """Command untuk melihat extracted assets"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        # Load from files if empty
        if not EXTRACTED_ASSETS.get('premium_emojis'):
            load_assets_from_files()
        
        emoji_count = len(EXTRACTED_ASSETS.get('premium_emojis', {}))
        font_types = list(EXTRACTED_ASSETS.get('fonts', {}).keys())
        
        # Sample emojis
        sample_emojis = []
        for emoji_type, emoji_data in list(EXTRACTED_ASSETS.get('premium_emojis', {}).items())[:5]:
            sample_emojis.append(f"{emoji_type}: {emoji_data.get('char', '?')}")
        
        assets_text = f"""
📦 **EXTRACTED ASSETS STATUS**

🎭 **Premium Emojis:** `{emoji_count}` types
{chr(10).join(f'• {sample}' for sample in sample_emojis)}
{'• ... and more' if emoji_count > 5 else ''}

🔤 **Font Mappings:** `{len(font_types)}` types
• Available: {', '.join(font_types)}

⚙️ **Settings:**
• Prefix: `{EXTRACTED_ASSETS.get('command_prefix', '.')}`
• Premium: {'Active' if EXTRACTED_ASSETS.get('premium_status') else 'Standard'}
• Version: `{EXTRACTED_ASSETS.get('version', 'Unknown')}`

⏰ **Last Updated:** `{EXTRACTED_ASSETS.get('last_updated', 'Never')}`

💡 **Available Functions:**
• `get_premium_emoji(type)` - Get emoji character
• `get_premium_emoji_id(type)` - Get emoji ID  
• `convert_text_font(text, type)` - Convert text font
• `create_premium_entities_from_assets(text)` - Create entities
        """.strip()
        
        await event.reply(assets_text)
    
    except Exception as e:
        await event.reply(f"❌ **Assets Error:** {str(e)}")

# COMMAND: Reload Assets
@client.on(events.NewMessage(pattern=rf'\.reload_assets'))
async def reload_assets_handler(event):
    """Command untuk reload assets dari files"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        success = load_assets_from_files()
        if success:
            await event.reply("✅ **Assets reloaded from JSON files successfully**")
        else:
            await event.reply("❌ **Failed to reload assets from files**")
    except Exception as e:
        await event.reply(f"❌ **Reload Error:** {str(e)}")

# AUTO-EXTRACTION pada plugin load
def auto_extract_on_load():
    """Auto extract saat plugin dimuat"""
    try:
        print("🔄 Auto-extracting assets on plugin load...")
        
        # Try extraction
        if extract_from_main_module() or extract_from_file_parsing():
            save_assets_to_files()
            print("✅ Auto-extraction completed successfully")
        else:
            # Load from existing files
            load_assets_from_files()
            print("📂 Loaded existing assets from files")
    except Exception as e:
        print(f"⚠️ Auto-extraction warning: {e}")

# Plugin info
PLUGIN_INFO = {
    'name': 'assetjson',
    'version': '1.0.0',
    'description': 'Asset manager untuk mengekstrak konfigurasi dari main.py',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['extract', 'assets', 'reload_assets'],
    'functions': ['get_premium_emoji', 'convert_text_font', 'create_premium_entities_from_assets']
}

def get_plugin_info():
    return PLUGIN_INFO

# Export functions untuk plugin lain
__all__ = [
    'get_premium_emoji',
    'get_premium_emoji_id', 
    'convert_text_font',
    'get_command_prefix',
    'get_premium_status',
    'create_premium_entities_from_assets',
    'EXTRACTED_ASSETS'
]

# Auto-extract saat plugin dimuat
auto_extract_on_load()

print("✅ AssetJSON plugin loaded with auto-extraction")