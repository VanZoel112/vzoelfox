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
import asyncio
from telethon import events, Button
from telethon.tl.types import MessageEntityCustomEmoji
from datetime import datetime

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "help",
    "version": "3.1.0",
    "description": "Command-based navigation help system dengan .next/.back untuk browse plugins",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".help", ".help <category>", ".next", ".back", ".help categories", ".help status"],
    "features": ["command navigation", "premium emoji integration", "auto plugin detection", ".next/.back pagination", "category system"]
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

# Import font helper
try:
    import sys
    sys.path.append('utils')
    from font_helper import convert_font, process_all_markdown, bold, mono
    FONT_HELPER_AVAILABLE = True
except ImportError:
    FONT_HELPER_AVAILABLE = False
    
    def convert_font(text, font_type='bold'):
        """Fallback font conversion"""
        if font_type == 'bold':
            return f"**{text}**"  # Fallback to markdown
        elif font_type == 'mono':
            return f"`{text}`"  # Fallback to markdown
        return text
    
    def process_all_markdown(text):
        """Fallback markdown processor"""
        return text
    
    def bold(text):
        return f"**{text}**"
    
    def mono(text):
        return f"`{text}`"

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

def count_loaded_plugins():
    """Count loaded plugins dynamically"""
    try:
        import glob
        plugins = glob.glob("plugins/*.py")
        # Exclude __pycache__ and non-plugin files
        valid_plugins = [p for p in plugins if not p.endswith('__init__.py') and 'test' not in p.lower()]
        return len(valid_plugins)
    except:
        return 25  # fallback

def get_all_plugins_info():
    """Get info from all available plugins"""
    try:
        import glob
        import sys
        import importlib
        
        plugins_info = {}
        plugins_dir = "plugins"
        
        # Get all plugin files
        plugin_files = glob.glob(f"{plugins_dir}/*.py")
        
        for plugin_file in plugin_files:
            plugin_name = plugin_file.replace(f"{plugins_dir}/", "").replace(".py", "")
            
            # Skip special files
            if plugin_name in ['__init__', 'test', 'database_helper']:
                continue
            
            try:
                # Add plugins directory to path if not already there
                if plugins_dir not in sys.path:
                    sys.path.append(plugins_dir)
                
                # Import plugin module
                plugin_module = importlib.import_module(plugin_name)
                
                # Get plugin info
                if hasattr(plugin_module, 'get_plugin_info'):
                    info = plugin_module.get_plugin_info()
                    plugins_info[plugin_name] = info
                elif hasattr(plugin_module, 'PLUGIN_INFO'):
                    plugins_info[plugin_name] = plugin_module.PLUGIN_INFO
                else:
                    # Create basic info
                    plugins_info[plugin_name] = {
                        'name': plugin_name,
                        'commands': [],
                        'description': 'No description available'
                    }
                    
            except Exception as e:
                print(f"[Help] Error loading plugin {plugin_name}: {e}")
                continue
        
        return plugins_info
    except Exception as e:
        print(f"[Help] Error getting plugins info: {e}")
        return {}

def categorize_plugins_auto():
    """Auto categorize plugins based on their commands and descriptions"""
    plugins_info = get_all_plugins_info()
    
    auto_categories = {
        "CORE": {
            "description": "Essential userbot functions",
            "plugins": {}
        },
        "COMMUNICATION": {
            "description": "Messaging & broadcasting tools",
            "plugins": {}
        },
        "MEDIA": {
            "description": "Media processing & download",
            "plugins": {}
        },
        "AUTOMATION": {
            "description": "AI & automation features",
            "plugins": {}
        },
        "MANAGEMENT": {
            "description": "Group & user management",
            "plugins": {}
        },
        "SECURITY": {
            "description": "Security & privacy tools",
            "plugins": {}
        },
        "SYSTEM": {
            "description": "System utilities & monitoring",
            "plugins": {}
        },
        "OTHER": {
            "description": "Other useful plugins",
            "plugins": {}
        }
    }
    
    # Categorization keywords
    category_keywords = {
        "CORE": ["help", "ping", "alive", "update", "restart"],
        "COMMUNICATION": ["gcast", "broadcast", "tagall", "welcome", "message"],
        "MEDIA": ["music", "video", "photo", "download", "curi", "secret"],
        "AUTOMATION": ["ai", "auto", "bot", "smart", "llama"],
        "MANAGEMENT": ["grup", "group", "admin", "ban", "kick", "blacklist"],
        "SECURITY": ["spam", "limit", "bypass", "reset", "session"],
        "SYSTEM": ["log", "database", "backup", "clean", "monitor"]
    }
    
    # Categorize each plugin
    for plugin_name, plugin_info in plugins_info.items():
        plugin_desc = plugin_info.get('description', '').lower()
        plugin_commands = plugin_info.get('commands', [])
        
        categorized = False
        
        # Check against category keywords
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if (keyword in plugin_name.lower() or 
                    keyword in plugin_desc or 
                    any(keyword in str(cmd).lower() for cmd in plugin_commands)):
                    auto_categories[category]["plugins"][plugin_name] = plugin_info
                    categorized = True
                    break
            if categorized:
                break
        
        # If not categorized, put in OTHER
        if not categorized:
            auto_categories["OTHER"]["plugins"][plugin_name] = plugin_info
    
    return auto_categories

def get_auto_category_help_text(category_name, category_data):
    """Generate help text for auto-detected category"""
    plugins = category_data.get('plugins', {})
    description = category_data.get('description', 'No description available')
    
    if not plugins:
        return f"""{get_emoji('adder3')} **{category_name} Category**
        
{get_emoji('adder5')} **Description:** {description}
{get_emoji('adder6')} **Status:** No plugins found in this category

{get_vzoel_signature()}"""
    
    plugin_list = []
    for plugin_name, plugin_info in plugins.items():
        name = plugin_info.get('name', plugin_name)
        desc = plugin_info.get('description', 'No description')
        commands = plugin_info.get('commands', [])
        
        plugin_list.append(f"{get_emoji('check')} **{name.title()}**")
        plugin_list.append(f"   {desc[:100]}{'...' if len(desc) > 100 else ''}")
        
        if commands:
            cmd_list = []
            for cmd in commands[:3]:  # Show max 3 commands
                if isinstance(cmd, str):
                    cmd_list.append(f"`{cmd}`")
            if cmd_list:
                plugin_list.append(f"   Commands: {', '.join(cmd_list)}")
        plugin_list.append("")
    
    plugin_text = "\n".join(plugin_list)
    
    return f"""{get_emoji('main')} **{category_name} CATEGORY**

{get_emoji('adder4')} **Description:** {description}
{get_emoji('adder6')} **Plugins:** {len(plugins)} available

{plugin_text}

{get_vzoel_signature()}"""

def get_auto_category_buttons(categories_dict):
    """Generate buttons for auto-detected categories"""
    buttons = []
    
    for category_name, category_data in categories_dict.items():
        plugin_count = len(category_data.get('plugins', {}))
        if plugin_count > 0:
            button_text = f"{get_emoji('adder2')} {category_name} ({plugin_count})"
            callback_data = f"help_autocat_{category_name}".encode()
            buttons.append([Button.inline(button_text, callback_data)])
    
    # Add back button
    buttons.append([Button.inline(f"{get_emoji('adder1')} Back to Main", b"help_main")])
    
    return buttons

async def get_ping_ms():
    """Get ping measurement in milliseconds"""
    try:
        import time
        start = time.time()
        # Simple ping simulation
        await asyncio.sleep(0.001)
        end = time.time()
        ping = round((end - start) * 1000, 2)
        return ping if ping > 0.1 else round(ping * 100, 1)
    except:
        return "N/A"

def get_main_help_text():
    """Generate main help menu text with auto plugin detection"""
    plugin_count = count_loaded_plugins()
    auto_categories = categorize_plugins_auto()
    
    # Count plugins per category
    category_counts = {}
    for cat_name, cat_data in auto_categories.items():
        plugin_count_in_cat = len(cat_data.get('plugins', {}))
        if plugin_count_in_cat > 0:
            category_counts[cat_name] = plugin_count_in_cat
    
    category_list = ""
    for cat_name, count in category_counts.items():
        if count > 0:
            category_list += f"• {convert_font(cat_name, 'mono')} - {count} plugins ({auto_categories[cat_name]['description']})\n"
    
    return f"""
{get_emoji('adder1')} {convert_font('Vzoel Assistant', 'bold')}

{get_emoji('check')} {convert_font('Founder Userbot', 'mono')} : Vzoel Fox's (Lutpan) {get_emoji('main')}
{get_emoji('check')} {convert_font('Code', 'mono')}                     : python3,python2
{get_emoji('check')} {convert_font('Fitur', 'mono')}                      : {plugin_count} plugins
{get_emoji('check')} {convert_font('IG', 'mono')}                          : vzoel.fox_s
{get_emoji('check')} {convert_font('PING', 'mono')}                    : {{ping_placeholder}} ms

{get_emoji('adder5')} {convert_font('NOTE !!!', 'bold')} :
Userbot ini dibuat dengan repo murni oleh Vzoel Fox's..
Bukan hasil fork maupun beli dari seller manapun!!!
Hak cipta sepenuhnya milik Vzoel..

{get_emoji('adder3')} ©2025 ~ Vzoel Fox's (LTPN).

{get_emoji('adder4')} {convert_font('AUTO-DETECTED CATEGORIES:', 'bold')}
{category_list}

{get_emoji('adder2')} {convert_font('QUICK START:', 'bold')}
• {convert_font('.help categories', 'mono')} - Browse all plugin categories
• {convert_font('.pink', 'mono')} - Test userbot response  
• {convert_font('.secreton', 'mono')} - Activate secret saver
• {convert_font('.play <song>', 'mono')} - Download music
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

# Global client reference and navigation state
client = None

# Navigation state untuk setiap user
HELP_STATE = {
    'current_page': 0,
    'current_category': 'main',
    'categories_list': [],
    'plugins_per_page': 5
}

def get_vzoel_signature():
    """Get VzoelFox signature"""
    return f"""
{get_emoji('main')} VzoelFox Premium System
{get_emoji('adder3')} Powered by Vzoel Fox's Technology  
{get_emoji('adder6')} © 2025 Vzoel Fox's (LTPN) - Premium Userbot
    """.strip()

def get_help_navigation_text():
    """Get navigation help text"""
    return f"""
{get_emoji('adder4')} **Navigation Commands:**
• {convert_font('.help', 'mono')} - Show main help menu
• {convert_font('.next', 'mono')} - Next page of plugins/categories
• {convert_font('.back', 'mono')} - Previous page or back to main
• {convert_font('.help <category>', 'mono')} - Jump to specific category

{get_emoji('adder2')} **Quick Commands:**
• {convert_font('.help categories', 'mono')} - Browse all categories
• {convert_font('.help status', 'mono')} - Show system status
"""

async def help_handler(event):
    """Enhanced help command handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split()
        
        # Reset navigation state untuk new help request
        HELP_STATE['current_page'] = 0
        HELP_STATE['current_category'] = 'main'
        
        # Handle special commands
        if len(args) > 1:
            command = args[1].lower()
            
            if command == 'categories':
                await show_categories_page(event, 0)
                return
            elif command == 'status':
                await show_status_page(event)
                return
            else:
                # Try to find category
                auto_categories = categorize_plugins_auto()
                category_upper = command.upper()
                if category_upper in auto_categories:
                    HELP_STATE['current_category'] = category_upper
                    await show_category_page(event, category_upper, 0)
                    return
        
        # Show main help menu
        await show_main_help(event)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Help error:** {str(e)}\n\n{get_vzoel_signature()}")

async def show_main_help(event):
    """Show main help menu"""
    try:
        # Get dynamic ping measurement
        ping_ms = await get_ping_ms()
        
        # Show main help menu dengan dynamic values
        help_text = get_main_help_text().replace('{ping_placeholder}', str(ping_ms))
        
        help_text += f"\n\n{get_help_navigation_text()}"
        help_text += f"\n{get_vzoel_signature()}"
        
        await safe_send_premium(event, help_text)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** {str(e)}\n\n{get_vzoel_signature()}")

async def show_categories_page(event, page=0):
    """Show categories with pagination"""
    try:
        auto_categories = categorize_plugins_auto()
        active_categories = {k: v for k, v in auto_categories.items() if v.get('plugins')}
        
        categories_list = list(active_categories.items())
        HELP_STATE['categories_list'] = categories_list
        HELP_STATE['current_category'] = 'categories'
        HELP_STATE['current_page'] = page
        
        categories_per_page = 3
        start_idx = page * categories_per_page
        end_idx = start_idx + categories_per_page
        page_categories = categories_list[start_idx:end_idx]
        
        total_pages = (len(categories_list) - 1) // categories_per_page + 1
        
        help_text = f"""{get_emoji('main')} **PLUGIN CATEGORIES** (Page {page + 1}/{total_pages})

{get_emoji('check')} **Found {len(active_categories)} categories with {sum(len(cat.get('plugins', {})) for cat in active_categories.values())} plugins**

"""
        
        for idx, (cat_name, cat_data) in enumerate(page_categories, start_idx + 1):
            plugin_count = len(cat_data.get('plugins', {}))
            description = cat_data.get('description', 'No description')
            
            help_text += f"""{get_emoji('adder2')} **{idx}. {cat_name}** ({plugin_count} plugins)
   {description[:80]}{'...' if len(description) > 80 else ''}
   Use: {convert_font(f'.help {cat_name.lower()}', 'mono')}

"""
        
        # Navigation info
        nav_info = f"\n{get_emoji('adder4')} **Navigation:**\n"
        if page > 0:
            nav_info += f"• {convert_font('.back', 'mono')} - Previous page\n"
        if page < total_pages - 1:
            nav_info += f"• {convert_font('.next', 'mono')} - Next page\n"
        nav_info += f"• {convert_font('.help', 'mono')} - Back to main menu"
        
        help_text += nav_info + f"\n\n{get_vzoel_signature()}"
        
        await safe_send_premium(event, help_text)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** {str(e)}\n\n{get_vzoel_signature()}")

async def show_category_page(event, category_name, page=0):
    """Show specific category with plugins pagination"""
    try:
        auto_categories = categorize_plugins_auto()
        
        if category_name not in auto_categories:
            await safe_send_premium(event, f"{get_emoji('adder5')} **Category not found:** {category_name}\n\n{get_vzoel_signature()}")
            return
        
        category_data = auto_categories[category_name]
        plugins = list(category_data.get('plugins', {}).items())
        
        HELP_STATE['current_category'] = category_name
        HELP_STATE['current_page'] = page
        
        plugins_per_page = HELP_STATE['plugins_per_page']
        start_idx = page * plugins_per_page
        end_idx = start_idx + plugins_per_page
        page_plugins = plugins[start_idx:end_idx]
        
        total_pages = (len(plugins) - 1) // plugins_per_page + 1 if plugins else 1
        
        help_text = f"""{get_emoji('main')} **{category_name} PLUGINS** (Page {page + 1}/{total_pages})

{get_emoji('adder4')} **Description:** {category_data.get('description', 'No description')}
{get_emoji('check')} **Total Plugins:** {len(plugins)}

"""
        
        if not plugins:
            help_text += f"{get_emoji('adder3')} No plugins found in this category."
        else:
            for idx, (plugin_name, plugin_info) in enumerate(page_plugins, start_idx + 1):
                name = plugin_info.get('name', plugin_name)
                description = plugin_info.get('description', 'No description')
                commands = plugin_info.get('commands', [])
                
                help_text += f"""{get_emoji('adder2')} **{idx}. {name.title()}**
   {description[:100]}{'...' if len(description) > 100 else ''}
"""
                
                if commands:
                    cmd_list = []
                    for cmd in commands[:3]:  # Show max 3 commands
                        if isinstance(cmd, str):
                            cmd_list.append(f"`{cmd}`")
                    if cmd_list:
                        help_text += f"   **Commands:** {', '.join(cmd_list)}"
                        if len(commands) > 3:
                            help_text += f" (+{len(commands) - 3} more)"
                
                help_text += "\n\n"
        
        # Navigation info
        nav_info = f"{get_emoji('adder6')} **Navigation:**\n"
        if page > 0:
            nav_info += f"• {convert_font('.back', 'mono')} - Previous page\n"
        if page < total_pages - 1:
            nav_info += f"• {convert_font('.next', 'mono')} - Next page\n"
        nav_info += f"• {convert_font('.help categories', 'mono')} - Back to categories\n"
        nav_info += f"• {convert_font('.help', 'mono')} - Main menu"
        
        help_text += nav_info + f"\n\n{get_vzoel_signature()}"
        
        await safe_send_premium(event, help_text)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** {str(e)}\n\n{get_vzoel_signature()}")

async def show_status_page(event):
    """Show system status page"""
    try:
        plugin_count = count_loaded_plugins()
        status_text = f"""
{get_emoji('main')} {convert_font('SYSTEM STATUS', 'bold')}

{get_emoji('check')} {convert_font('Bot Information:', 'bold')}
• Status: {convert_font('Online & Running', 'mono')}
• Version: {convert_font('v3.0.0 Navigation Update', 'mono')}
• Premium: {convert_font('Active Account', 'mono')}
• Uptime: {convert_font(datetime.now().strftime('%H:%M:%S'), 'mono')}

{get_emoji('adder2')} {convert_font('Plugin Status:', 'bold')}
• Core Plugins: {convert_font(f'{plugin_count}+ loaded', 'mono')}
• Latest: {convert_font('music_player, secret_saver, help v3.0', 'mono')}
• Database: {convert_font('Centralized system active', 'mono')}

{get_emoji('adder4')} {convert_font('Features Active:', 'bold')}
• Premium emoji integration ✅
• Command-based navigation ✅
• Auto plugin detection ✅ 
• Secret media saver ✅
• Music download system ✅
• Spam limit reset ✅

{get_emoji('adder6')} {convert_font('Navigation System:', 'bold')}
• .help - Main menu
• .next/.back - Page navigation
• .help categories - Browse all
• .help <category> - Direct access

{get_emoji('main')} {convert_font('All systems operational!', 'mono')}

{get_vzoel_signature()}
        """.strip()
        
        await safe_send_premium(event, status_text)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** {str(e)}\n\n{get_vzoel_signature()}")

async def next_handler(event):
    """Handle .next command for pagination"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        current_category = HELP_STATE.get('current_category', 'main')
        current_page = HELP_STATE.get('current_page', 0)
        
        if current_category == 'main':
            await safe_send_premium(event, f"{get_emoji('adder5')} **Use .help categories first to browse pages**\n\n{get_vzoel_signature()}")
            return
        elif current_category == 'categories':
            # Navigate categories
            categories_list = HELP_STATE.get('categories_list', [])
            categories_per_page = 3
            total_pages = (len(categories_list) - 1) // categories_per_page + 1
            
            if current_page < total_pages - 1:
                await show_categories_page(event, current_page + 1)
            else:
                await safe_send_premium(event, f"{get_emoji('adder5')} **Already at last page of categories**\n\n{get_vzoel_signature()}")
        else:
            # Navigate category plugins
            auto_categories = categorize_plugins_auto()
            if current_category in auto_categories:
                plugins = list(auto_categories[current_category].get('plugins', {}).items())
                plugins_per_page = HELP_STATE['plugins_per_page']
                total_pages = (len(plugins) - 1) // plugins_per_page + 1 if plugins else 1
                
                if current_page < total_pages - 1:
                    await show_category_page(event, current_category, current_page + 1)
                else:
                    await safe_send_premium(event, f"{get_emoji('adder5')} **Already at last page of {current_category}**\n\n{get_vzoel_signature()}")
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Next error:** {str(e)}\n\n{get_vzoel_signature()}")

async def back_handler(event):
    """Handle .back command for navigation"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        current_category = HELP_STATE.get('current_category', 'main')
        current_page = HELP_STATE.get('current_page', 0)
        
        if current_category == 'main':
            await safe_send_premium(event, f"{get_emoji('adder5')} **Already at main menu**\n\n{get_vzoel_signature()}")
            return
        elif current_category == 'categories':
            # Go back in categories or to main
            if current_page > 0:
                await show_categories_page(event, current_page - 1)
            else:
                await show_main_help(event)
        else:
            # Go back in category plugins or to categories
            if current_page > 0:
                await show_category_page(event, current_category, current_page - 1)
            else:
                await show_categories_page(event, 0)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Back error:** {str(e)}\n\n{get_vzoel_signature()}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    client.add_event_handler(help_handler, events.NewMessage(pattern=r'\.help(?:\s+(.+))?$'))
    client.add_event_handler(next_handler, events.NewMessage(pattern=r'\.next$'))
    client.add_event_handler(back_handler, events.NewMessage(pattern=r'\.back$'))
    
    print(f"✅ [Help] Command-based navigation system loaded v{PLUGIN_INFO['version']} - .next/.back navigation active")

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
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'help_handler', 'next_handler', 'back_handler']