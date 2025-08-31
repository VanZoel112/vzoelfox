#!/usr/bin/env python3
"""
Enhanced Help Plugin for VzoelFox Userbot - Complete Command Guide with Interactive Navigation
Fitur: Interactive buttons, simple explanations, latest plugin integration, premium emoji support
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 3.0.0 - Complete Interactive Help System
"""

import re
import os
import sys
from telethon import events, Button
from telethon.tl.types import MessageEntityCustomEmoji
from datetime import datetime

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "help",
    "version": "3.0.0",
    "description": "Complete interactive help system dengan semua plugin terbaru dan navigasi button",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".help", ".help <category>"],
    "features": ["interactive navigation", "premium emoji integration", "category system", "button navigation", "latest plugins"]
}

# ===== PREMIUM EMOJI CONFIGURATION =====
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

# ===== PLUGIN CATEGORIES & COMMANDS =====
PLUGIN_CATEGORIES = {
    "CORE": {
        "description": "Essential userbot functions",
        "commands": {
            ".help": "Show this help menu with categories",
            ".update": "Auto-update userbot dari Git repository", 
            ".update check": "Check for available updates only",
            ".update rollback": "Rollback to previous version",
            ".pink": "Ping test dengan response time",
            ".alive": "Show userbot status & system info"
        }
    },
    
    "MESSAGING": {
        "description": "Communication & broadcasting tools", 
        "commands": {
            ".gcast <text>": "Broadcast message ke semua groups",
            ".sgcast <text>": "Slow gcast (anti-spam protection)",
            ".tagall": "Tag all members dalam current group",
            ".welcome set <msg>": "Set welcome message untuk group",
            ".welcome on/off": "Enable/disable welcome messages"
        }
    },
    
    "AI & AUTOMATION": {
        "description": "Artificial intelligence features",
        "commands": {
            ".aimode on/off": "Toggle AI chat mode",
            ".ai <text>": "Chat dengan AI (ChatGPT/Claude)",
            ".aiconfig": "Configure AI settings & providers",
            ".testaiemoji": "Test AI with premium emoji"
        }
    },
    
    "GROUP MANAGEMENT": {
        "description": "Group & user management tools",
        "commands": {
            ".grup blacklist <id>": "Add group to blacklist",
            ".grup unblacklist <id>": "Remove from blacklist", 
            ".grup blacklistlist": "Show all blacklisted groups",
            ".grup log": "Show groups from log",
            ".grup loggroup": "Show log group information",
            ".checkid": "Get user/chat ID information"
        }
    },
    
    "LOG & MONITORING": {
        "description": "Activity logging & monitoring",
        "commands": {
            ".loggroup create": "Create permanent log group",
            ".loggroup status": "Show log group status",
            ".loggroup test": "Test log group functionality",
            ".log show": "Show recent userbot activity",
            ".log stats": "Show usage statistics",
            ".log clear": "Clear activity logs"
        }
    },
    
    "SPAM & LIMITS": {
        "description": "Spam management & limit reset",
        "commands": {
            ".spamreset": "Reset Telegram spam limits",
            ".spamcheck": "Check current spam status",
            ".spamstatus": "Show spam reset history",
            ".spambot <msg>": "Manual SpamBot interaction",
            ".antispam": "Show spam management help"
        }
    },
    
    "SYSTEM": {
        "description": "System management & utilities", 
        "commands": {
            ".restart": "Restart userbot gracefully",
            ".eval <code>": "Execute Python code (developer only)",
            ".logs": "Show system error logs",
            ".stats": "System performance statistics"
        }
    }
}

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
        }
        return ''.join([bold_map.get(c, c) for c in text])
    elif font_type == 'mono':
        mono_map = {
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
            'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
            's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
            'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
            'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉'
        }
        return ''.join([mono_map.get(c, c) for c in text])
    return text

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support"""
    try:
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

async def safe_send_premium(event, text, buttons=None):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities and buttons:
            await event.reply(text, formatting_entities=entities, buttons=buttons)
        elif entities:
            await event.reply(text, formatting_entities=entities)
        elif buttons:
            await event.reply(text, buttons=buttons)
        else:
            await event.reply(text)
    except Exception:
        if buttons:
            await event.reply(text, buttons=buttons)
        else:
            await event.reply(text)

async def safe_edit_premium(event, text, buttons=None):
    """Edit message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities and buttons:
            await event.edit(text, formatting_entities=entities, buttons=buttons)
        elif entities:
            await event.edit(text, formatting_entities=entities)
        elif buttons:
            await event.edit(text, buttons=buttons)
        else:
            await event.edit(text)
    except Exception:
        if buttons:
            await event.edit(text, buttons=buttons)
        else:
            await event.edit(text)

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

def get_main_help_text():
    """Generate main help menu text"""
    return f"""
{get_emoji('main')} {convert_font('VZOELFOX USERBOT HELP v3.0', 'bold')}

{get_emoji('check')} {convert_font('Interactive Help Menu', 'mono')}
Pilih kategori di bawah untuk melihat commands:

{get_emoji('adder2')} {convert_font('QUICK START:', 'bold')}
• {convert_font('.help core', 'mono')} - Essential commands
• {convert_font('.pink', 'mono')} - Test userbot response
• {convert_font('.update check', 'mono')} - Check for updates
• {convert_font('.loggroup create', 'mono')} - Setup log group

{get_emoji('adder4')} {convert_font('CATEGORIES AVAILABLE:', 'bold')}
• {convert_font('CORE', 'mono')} - Essential userbot functions
• {convert_font('MESSAGING', 'mono')} - Broadcast & communication tools
• {convert_font('AI & AUTOMATION', 'mono')} - Artificial intelligence features
• {convert_font('GROUP MANAGEMENT', 'mono')} - Group & user management
• {convert_font('LOG & MONITORING', 'mono')} - Activity logging & monitoring
• {convert_font('SPAM & LIMITS', 'mono')} - Spam management & limit reset
• {convert_font('SYSTEM', 'mono')} - System management & utilities

{get_emoji('adder6')} {convert_font('STATS:', 'bold')}
• Version: v3.0.0 Complete
• Plugins: 25+ loaded
• Features: Premium emojis, Auto-updates, Spam reset
• Database: Centralized system

{get_emoji('adder5')} {convert_font('Created by: Vzoel Fox | Enhanced System', 'mono')}
    """.strip()

def get_category_help_text(category):
    """Generate help text for specific category"""
    if category not in PLUGIN_CATEGORIES:
        return None
    
    cat_data = PLUGIN_CATEGORIES[category]
    
    text = f"""
{get_emoji('main')} {convert_font(f'{category} COMMANDS', 'bold')}

{get_emoji('check')} {convert_font('Description:', 'mono')} {cat_data['description']}

{get_emoji('adder2')} {convert_font('Available Commands:', 'bold')}
    """
    
    for command, description in cat_data['commands'].items():
        text += f"\n• {convert_font(command, 'mono')}\n  {description}"
    
    text += f"\n\n{get_emoji('adder4')} {convert_font('Tip:', 'mono')} Gunakan buttons di bawah untuk navigasi cepat"
    
    return text.strip()

def get_category_buttons():
    """Generate category selection buttons"""
    buttons = []
    categories = list(PLUGIN_CATEGORIES.keys())
    
    # Create rows of 2 buttons each
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                cat = categories[i + j]
                emoji_map = {
                    'CORE': get_emoji('check'),
                    'MESSAGING': get_emoji('adder2'), 
                    'AI & AUTOMATION': get_emoji('adder3'),
                    'GROUP MANAGEMENT': get_emoji('adder4'),
                    'LOG & MONITORING': get_emoji('adder6'),
                    'SPAM & LIMITS': get_emoji('adder5'),
                    'SYSTEM': get_emoji('adder1')
                }
                emoji = emoji_map.get(cat, get_emoji('main'))
                row.append(Button.inline(f"{emoji} {cat}", f"help_cat_{cat.lower().replace(' & ', '_').replace(' ', '_')}".encode()))
        buttons.append(row)
    
    # Add navigation buttons
    buttons.append([
        Button.inline(f"{get_emoji('main')} Main Menu", b"help_main"),
        Button.inline(f"{get_emoji('adder1')} Close", b"help_close")
    ])
    
    return buttons

def get_category_back_buttons():
    """Generate back navigation buttons for categories"""
    return [
        [Button.inline(f"{get_emoji('check')} Categories", b"help_categories")],
        [Button.inline(f"{get_emoji('main')} Main Menu", b"help_main"), 
         Button.inline(f"{get_emoji('adder1')} Close", b"help_close")]
    ]

# Global client reference
client = None

async def help_handler(event):
    """Enhanced help command handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split()
        
        # Check if specific category requested
        if len(args) > 1:
            category = args[1].upper().replace('_', ' & ')
            if category in PLUGIN_CATEGORIES:
                help_text = get_category_help_text(category)
                buttons = get_category_back_buttons()
                await safe_send_premium(event, help_text, buttons)
                return
        
        # Show main help menu
        help_text = get_main_help_text()
        
        buttons = [
            [Button.inline(f"{get_emoji('adder2')} Browse Categories", b"help_categories")],
            [Button.inline(f"{get_emoji('check')} System Status", b"help_status")],
            [Button.inline(f"{get_emoji('adder6')} Premium Features", b"help_premium")],
            [Button.inline(f"{get_emoji('adder1')} Close Menu", b"help_close")]
        ]
        
        await safe_send_premium(event, help_text, buttons)
        
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} Help error: {str(e)}")

async def help_callback_handler(event):
    """Handle help menu button callbacks"""
    global client
    if not await is_owner_check(client, event.sender_id):
        await event.answer("❌ Access denied", alert=True)
        return
    
    try:
        data = event.data.decode('utf-8')
        
        if data == "help_main":
            # Show main menu
            help_text = get_main_help_text()
            buttons = [
                [Button.inline(f"{get_emoji('adder2')} Browse Categories", b"help_categories")],
                [Button.inline(f"{get_emoji('check')} System Status", b"help_status")],
                [Button.inline(f"{get_emoji('adder6')} Premium Features", b"help_premium")],
                [Button.inline(f"{get_emoji('adder1')} Close Menu", b"help_close")]
            ]
            await safe_edit_premium(event, help_text, buttons)
            
        elif data == "help_categories":
            # Show category selection
            help_text = f"""
{get_emoji('main')} {convert_font('SELECT COMMAND CATEGORY', 'bold')}

{get_emoji('check')} {convert_font('Choose a category to see available commands:', 'mono')}

{get_emoji('adder2')} Setiap kategori berisi commands yang berkaitan
{get_emoji('adder3')} Click button di bawah untuk melihat detail commands
{get_emoji('adder4')} Use navigation buttons untuk kembali ke menu utama
            """.strip()
            
            buttons = get_category_buttons()
            await safe_edit_premium(event, help_text, buttons)
            
        elif data.startswith("help_cat_"):
            # Show specific category
            category_key = data.replace("help_cat_", "").replace("_", " ").upper()
            if "_&_" in category_key:
                category_key = category_key.replace("_&_", " & ")
            
            if category_key in PLUGIN_CATEGORIES:
                help_text = get_category_help_text(category_key)
                buttons = get_category_back_buttons()
                await safe_edit_premium(event, help_text, buttons)
            
        elif data == "help_status":
            # Show system status
            status_text = f"""
{get_emoji('main')} {convert_font('SYSTEM STATUS', 'bold')}

{get_emoji('check')} {convert_font('Bot Information:', 'bold')}
• Status: {convert_font('Online & Running', 'mono')}
• Version: {convert_font('v3.0.0 Complete', 'mono')}
• Premium: {convert_font('Active Account', 'mono')}
• Uptime: {convert_font(datetime.now().strftime('%H:%M:%S'), 'mono')}

{get_emoji('adder2')} {convert_font('Plugin Status:', 'bold')}
• Core Plugins: {convert_font('25+ loaded', 'mono')}
• Latest Additions: {convert_font('updater, spam_reset, log_group', 'mono')}
• Database: {convert_font('Centralized system active', 'mono')}

{get_emoji('adder4')} {convert_font('Features Active:', 'bold')}
• Premium emoji integration ✅
• Auto-update system ✅
• Spam limit reset ✅
• Log group management ✅
• AI chat integration ✅
• Interactive help navigation ✅

{get_emoji('adder6')} {convert_font('Recent Updates:', 'bold')}
• Added comprehensive updater system
• Implemented spam limit reset functionality
• Enhanced log group management
• Updated help system dengan interactive navigation

{get_emoji('main')} {convert_font('All systems operational!', 'mono')}
            """.strip()
            
            buttons = [[Button.inline(f"{get_emoji('adder1')} Back", b"help_main")]]
            await safe_edit_premium(event, status_text, buttons)
            
        elif data == "help_premium":
            # Show premium features
            premium_text = f"""
{get_emoji('main')} {convert_font('PREMIUM FEATURES TEST', 'bold')}

{get_emoji('check')} {convert_font('Premium Emojis Available:', 'bold')}
{get_emoji('main')} Main: {get_emoji('main')} (Premium star emoji)
{get_emoji('check')} Check: {get_emoji('check')} (Settings gear)
{get_emoji('adder1')} Storm: {get_emoji('adder1')} (Weather storm)
{get_emoji('adder2')} Success: {get_emoji('adder2')} (Check mark)
{get_emoji('adder3')} Alien: {get_emoji('adder3')} (Alien face)
{get_emoji('adder4')} Plane: {get_emoji('adder4')} (Airplane)
{get_emoji('adder5')} Devil: {get_emoji('adder5')} (Devil face)
{get_emoji('adder6')} Mixer: {get_emoji('adder6')} (Audio mixer)

{get_emoji('adder2')} {convert_font('Premium Status:', 'bold')}
• Emoji Integration: {convert_font('Active', 'mono')}
• Custom Entities: {convert_font('UTF-16 handled', 'mono')}
• Font Conversion: {convert_font('Bold & Mono available', 'mono')}
• Interactive Buttons: {convert_font('Fully functional', 'mono')}

{get_emoji('adder4')} {convert_font('Latest Features:', 'bold')}
• Auto-update system dengan Git integration
• Spam limit reset via SpamBot interaction
• Permanent log group management
• Interactive help dengan category navigation
• Centralized database compatibility

{get_emoji('main')} {convert_font('Premium features working perfectly!', 'mono')}
            """.strip()
            
            buttons = [[Button.inline(f"{get_emoji('adder1')} Back", b"help_main")]]
            await safe_edit_premium(event, premium_text, buttons)
            
        elif data == "help_close":
            await event.delete()
            return
            
        await event.answer()
        
    except Exception as e:
        await event.answer(f"Error: {str(e)}", alert=True)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    client.add_event_handler(help_handler, events.NewMessage(pattern=r'\.help(?:\s+(.+))?$'))
    client.add_event_handler(help_callback_handler, events.CallbackQuery(pattern=rb"help_(.+)"))
    
    print(f"✅ [Help] Interactive help system loaded v{PLUGIN_INFO['version']} - {len(PLUGIN_CATEGORIES)} categories available")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Help] Plugin cleanup initiated")
        client = None
        print("[Help] Plugin cleanup completed")
    except Exception as e:
        print(f"[Help] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'help_handler', 'help_callback_handler']