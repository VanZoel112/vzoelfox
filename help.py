#!/usr/bin/env python3
"""
Enhanced Help Plugin v2.0 - COMPLETE FIXED VERSION
Compatible with AssetJSON v3.0.0 and Enhanced Plugin Loader
File: plugins/help.py
Author: Vzoel Fox's (Enhanced by Morgan)
Version: v2.0.0 - Full Integration with AssetJSON v3.0
"""

import re
import os
import sys
import json
import time
import inspect
from datetime import datetime
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.types import MessageEntityCustomEmoji

# ============= ASSETJSON v3.0.0 INTEGRATION =============

# Global variables for plugin environment
plugin_env = None
asset_manager = None
client = None

def setup(telegram_client):
    """Setup function dipanggil oleh plugin loader"""
    global plugin_env, asset_manager, client
    
    try:
        # Set client reference
        client = telegram_client
        
        # Import AssetJSON v3.0.0 dengan dependency injection
        try:
            from assetjson import initialize_asset_system, create_plugin_environment
            
            # Initialize asset system dengan client
            manager, env = initialize_asset_system(client, auto_load_configs=True, register_commands=False)
            
            # Store references globally
            asset_manager = manager
            plugin_env = env
            
            print("✅ Help plugin: AssetJSON v3.0.0 integration successful")
            return True
            
        except ImportError as ie:
            print(f"⚠️ Help plugin: AssetJSON not available ({ie}), using fallback")
            return setup_fallback()
            
    except Exception as e:
        print(f"❌ Help plugin setup error: {e}")
        return setup_fallback()

def setup_fallback():
    """Fallback setup untuk compatibility"""
    global plugin_env
    
    try:
        # Create basic environment dengan functions dari main.py
        main_module = sys.modules.get('__main__')
        
        plugin_env = {
            'get_emoji': getattr(main_module, 'get_emoji', lambda x: '🤩'),
            'convert_font': getattr(main_module, 'convert_font', lambda text, font='bold': text),
            'create_premium_entities': getattr(main_module, 'create_premium_entities', lambda text: []),
            'safe_send_with_entities': safe_send_fallback,
            'safe_edit_with_entities': safe_edit_fallback,
            'is_owner': getattr(main_module, 'is_owner', default_owner_check),
            'premium_emojis': getattr(main_module, 'PREMIUM_EMOJIS', {}),
            'fonts': getattr(main_module, 'FONTS', {}),
            'get_client': lambda: client,
            'logger': create_simple_logger()
        }
        
        print("✅ Help plugin: Fallback environment created")
        return True
        
    except Exception as e:
        print(f"❌ Help plugin fallback setup error: {e}")
        return False

async def safe_send_fallback(event_or_chat, text, buttons=None):
    """Fallback function untuk sending messages"""
    try:
        if hasattr(event_or_chat, 'reply'):
            return await event_or_chat.reply(text, buttons=buttons)
        elif client:
            return await client.send_message(event_or_chat, text, buttons=buttons)
    except Exception as e:
        print(f"Error in safe_send_fallback: {e}")
        return None

async def safe_edit_fallback(message, text, use_premium=True):
    """Fallback function untuk editing messages"""
    try:
        await message.edit(text)
    except Exception as e:
        print(f"Error in safe_edit_fallback: {e}")

async def default_owner_check(user_id):
    """Default owner check"""
    try:
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

def create_simple_logger():
    """Create simple logger for fallback"""
    import logging
    return logging.getLogger("help_plugin")

# ============= UTILITY FUNCTIONS =============

def get_emoji(emoji_type: str) -> str:
    """Get premium emoji with fallback"""
    if plugin_env and 'get_emoji' in plugin_env:
        return plugin_env['get_emoji'](emoji_type)
    return '🤩'

def convert_font(text: str, font_type: str = 'bold') -> str:
    """Convert font with fallback"""
    if plugin_env and 'convert_font' in plugin_env:
        return plugin_env['convert_font'](text, font_type)
    return text

async def safe_send_with_entities(event_or_chat, text: str, buttons=None):
    """Safe send with premium entities"""
    try:
        if plugin_env and 'safe_send_with_entities' in plugin_env:
            if buttons:
                # Untuk compatibility, coba send dengan buttons terpisah
                try:
                    msg = await plugin_env['safe_send_with_entities'](event_or_chat, text, use_premium=True)
                    if hasattr(msg, 'edit') and buttons:
                        await msg.edit(text, buttons=buttons)
                    return msg
                except Exception:
                    # Fallback ke event.reply
                    pass
            else:
                return await plugin_env['safe_send_with_entities'](event_or_chat, text, use_premium=True)
        
        # Final fallback
        return await safe_send_fallback(event_or_chat, text, buttons)
    except Exception as e:
        print(f"Error in safe_send_with_entities: {e}")
        return await safe_send_fallback(event_or_chat, text, buttons)

async def safe_edit_with_entities(message, text: str, buttons=None):
    """Safe edit with premium entities"""
    try:
        if plugin_env and 'safe_edit_with_entities' in plugin_env:
            await plugin_env['safe_edit_with_entities'](message, text, use_premium=True)
        else:
            await safe_edit_fallback(message, text)
        
        # Update buttons if provided
        if buttons:
            await message.edit(text, buttons=buttons)
            
    except Exception as e:
        print(f"Error in safe_edit_with_entities: {e}")
        try:
            await message.edit(text, buttons=buttons)
        except Exception as e2:
            print(f"Fallback edit also failed: {e2}")

async def is_owner_check(user_id: int) -> bool:
    """Enhanced owner check"""
    if plugin_env and 'is_owner' in plugin_env:
        return await plugin_env['is_owner'](user_id)
    else:
        return await default_owner_check(user_id)

def get_prefix() -> str:
    """Get command prefix"""
    try:
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

# ============= PLUGIN DISCOVERY SYSTEM =============

def get_plugin_loader():
    """Get plugin loader instance dari main module"""
    try:
        main_module = sys.modules.get('__main__')
        if main_module and hasattr(main_module, 'plugin_loader'):
            return getattr(main_module, 'plugin_loader')
    except Exception as e:
        print(f"Error getting plugin loader: {e}")
    return None

def discover_plugins() -> Dict[str, Any]:
    """Discover all loaded plugins dan commands"""
    plugins_info = {
        'total_plugins': 0,
        'loaded_plugins': 0,
        'plugin_list': [],
        'commands': {},
        'categories': set(),
        'plugin_details': {}
    }
    
    try:
        # Get plugin loader
        plugin_loader = get_plugin_loader()
        
        if plugin_loader:
            # Get status dari plugin loader
            status = plugin_loader.get_status()
            plugin_list = plugin_loader.list_plugins()
            
            plugins_info['total_plugins'] = status.get('total_plugins', 0)
            plugins_info['loaded_plugins'] = status.get('total_loaded', 0)
            plugins_info['plugin_list'] = plugin_list.get('loaded', [])
            
            # Get detailed plugin info
            for plugin_name in plugin_list.get('loaded', []):
                try:
                    plugin_module = plugin_loader.get_plugin(plugin_name)
                    if plugin_module:
                        # Get plugin info
                        if hasattr(plugin_module, 'get_plugin_info'):
                            info = plugin_module.get_plugin_info()
                            if isinstance(info, dict):
                                plugins_info['plugin_details'][plugin_name] = info
                                
                                # Extract commands
                                if 'commands' in info:
                                    plugins_info['commands'][plugin_name] = info['commands']
                                
                                # Extract categories
                                if 'categories' in info:
                                    plugins_info['categories'].update(info['categories'])
                        
                        # Fallback: scan module for event handlers
                        else:
                            commands = scan_module_for_commands(plugin_module)
                            if commands:
                                plugins_info['commands'][plugin_name] = commands
                                
                except Exception as plugin_error:
                    print(f"Error getting info for plugin {plugin_name}: {plugin_error}")
                    
        else:
            # Fallback: manual plugin directory scan
            plugins_info = scan_plugins_directory()
    
    except Exception as e:
        print(f"Error in discover_plugins: {e}")
    
    plugins_info['categories'] = list(plugins_info['categories'])
    return plugins_info

def scan_module_for_commands(module) -> List[str]:
    """Scan module untuk mencari event handlers dengan pattern matching"""
    commands = []
    
    try:
        # Get all functions dalam module
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Check untuk decorators atau patterns
                if hasattr(obj, '__name__'):
                    # Look for Telethon event handlers
                    if hasattr(obj, '__wrapped__') or name.endswith('_handler'):
                        # Try to extract command pattern dari function
                        try:
                            source = inspect.getsource(obj)
                            # Look for pattern matches
                            patterns = re.findall(r"pattern=.*?['\"]\\?\.?(\w+)", source)
                            commands.extend(patterns)
                        except Exception:
                            pass
                            
    except Exception as e:
        print(f"Error scanning module: {e}")
    
    return list(set(commands))  # Remove duplicates

def scan_plugins_directory() -> Dict[str, Any]:
    """Fallback: scan plugins directory secara manual"""
    plugins_info = {
        'total_plugins': 0,
        'loaded_plugins': 0,
        'plugin_list': [],
        'commands': {},
        'categories': set(),
        'plugin_details': {}
    }
    
    try:
        plugins_dir = "plugins"
        if os.path.exists(plugins_dir):
            plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith('.py') and not f.startswith('__')]
            plugins_info['total_plugins'] = len(plugin_files)
            plugins_info['plugin_list'] = [f[:-3] for f in plugin_files]  # Remove .py extension
            
            # Basic info untuk fallback
            plugins_info['loaded_plugins'] = len(plugin_files)  # Assume all loaded
            
    except Exception as e:
        print(f"Error scanning plugins directory: {e}")
    
    return plugins_info

# ============= ENHANCED HELP SYSTEM =============

def generate_help_content(category: Optional[str] = None) -> Dict[str, Any]:
    """Generate help content berdasarkan discovered plugins"""
    prefix = get_prefix()
    plugins_info = discover_plugins()
    
    # Base categories
    base_categories = {
        'basic': {
            'title': 'BASIC COMMANDS',
            'emoji': 'check',
            'description': 'Status & diagnostic commands',
            'commands': [
                {'cmd': f'{prefix}alive', 'desc': 'Show comprehensive bot status with statistics'},
                {'cmd': f'{prefix}ping', 'desc': 'Test response time and latency analysis'},
                {'cmd': f'{prefix}help [category]', 'desc': 'Show command help (this menu)'},
                {'cmd': f'{prefix}plugins', 'desc': 'Show loaded plugins status'},
            ]
        },
        'gcast': {
            'title': 'BROADCAST COMMANDS',
            'emoji': 'adder1',
            'description': 'Global casting enhanced',
            'commands': [
                {'cmd': f'{prefix}gcast <message>', 'desc': 'Standard broadcast to all groups/channels'},
                {'cmd': f'Reply + {prefix}gcast', 'desc': 'Enhanced gcast with entity preservation'},
                {'cmd': f'{prefix}sgcast <message>', 'desc': 'Slow broadcast with anti-spam delay'},
                {'cmd': f'Reply + {prefix}sgcast', 'desc': 'Forward message with slow broadcast'},
            ]
        },
        'emoji': {
            'title': 'PREMIUM EMOJI SYSTEM',
            'emoji': 'adder2',
            'description': 'Emoji management tools',
            'commands': [
                {'cmd': f'Reply + {prefix}setemoji', 'desc': 'Auto-extract ALL premium emojis from message'},
                {'cmd': f'{prefix}setemoji <type> <id>', 'desc': 'Manually set premium emoji by ID'},
            ]
        },
        'user': {
            'title': 'USER INFORMATION TOOLS',
            'emoji': 'adder3',
            'description': 'User info and utilities',
            'commands': [
                {'cmd': f'{prefix}info [user]', 'desc': 'Get detailed user information'},
                {'cmd': f'{prefix}id', 'desc': 'Get current chat and user IDs'},
                {'cmd': f'{prefix}vzl <user> <text>', 'desc': 'Create stylized user mention'},
            ]
        },
        'voice': {
            'title': 'VOICE CHAT CONTROLS',
            'emoji': 'adder4',
            'description': 'Voice chat management',
            'commands': [
                {'cmd': f'{prefix}joinvc', 'desc': 'Join voice chat in current group/channel'},
                {'cmd': f'{prefix}leavevc', 'desc': 'Leave current voice chat'},
                {'cmd': f'{prefix}vcstatus', 'desc': 'Check voice chat monitoring status'},
            ]
        },
        'manage': {
            'title': 'BLACKLIST & SETTINGS',
            'emoji': 'adder5',
            'description': 'Management tools',
            'commands': [
                {'cmd': f'{prefix}addbl [chat_id]', 'desc': 'Add chat to gcast blacklist'},
                {'cmd': f'{prefix}rmbl <chat_id>', 'desc': 'Remove chat from blacklist'},
                {'cmd': f'{prefix}listbl', 'desc': 'Show all blacklisted chats'},
                {'cmd': f'{prefix}sg', 'desc': 'Toggle spam guard on/off'},
            ]
        },
        'system': {
            'title': 'SYSTEM ADMINISTRATION',
            'emoji': 'adder6',
            'description': 'System management',
            'commands': [
                {'cmd': f'{prefix}restart', 'desc': 'Restart the bot (with confirmation)'},
                {'cmd': f'{prefix}infofounder', 'desc': 'Show founder and bot information'},
            ]
        }
    }
    
    # Add plugin-based categories
    plugin_categories = {}
    for plugin_name, commands in plugins_info['commands'].items():
        if commands:
            plugin_categories[f'plugin_{plugin_name}'] = {
                'title': f'{plugin_name.upper()} PLUGIN',
                'emoji': 'main',
                'description': f'Commands from {plugin_name} plugin',
                'commands': [{'cmd': f'{prefix}{cmd}', 'desc': f'{plugin_name} command'} for cmd in commands],
                'is_plugin': True,
                'plugin_name': plugin_name
            }
    
    # Combine categories
    all_categories = {**base_categories, **plugin_categories}
    
    # Generate content berdasarkan category request
    if not category:
        # Main menu
        total_commands = sum(len(cat['commands']) for cat in all_categories.values())
        
        content = {
            'type': 'main_menu',
            'title': f'{convert_font("VZOEL ASSISTANT v0.1.0.76 HELP", "mono")}',
            'stats': {
                'total_commands': total_commands,
                'total_categories': len(all_categories),
                'loaded_plugins': plugins_info['loaded_plugins'],
                'total_plugins': plugins_info['total_plugins']
            },
            'categories': all_categories,
            'quick_commands': [
                f'`{prefix}alive` - Bot status',
                f'`{prefix}gcast <text>` - Broadcast message',
                f'`{prefix}sgcast <text>` - Slow broadcast (anti-spam)',
                f'Reply + `{prefix}gcast` - Enhanced gcast',
                f'Reply + `{prefix}setemoji` - Auto extract emojis'
            ]
        }
        
    elif category in all_categories:
        # Specific category
        cat_info = all_categories[category]
        content = {
            'type': 'category',
            'category': category,
            'title': cat_info['title'],
            'emoji': cat_info['emoji'],
            'description': cat_info['description'],
            'commands': cat_info['commands'],
            'is_plugin': cat_info.get('is_plugin', False),
            'plugin_name': cat_info.get('plugin_name', '')
        }
        
    else:
        # Invalid category
        content = {
            'type': 'error',
            'message': f'Invalid category: {category}',
            'available_categories': list(all_categories.keys())
        }
    
    return content

def format_help_message(content: Dict[str, Any]) -> str:
    """Format help content menjadi message text dengan premium emojis"""
    
    if content['type'] == 'main_menu':
        # Main help menu
        text = f"""
[🚩]({get_logo_url()}) {content['title']}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('COMMAND CATEGORIES', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Quick Usage:', 'bold')}
"""
        
        # Add quick commands
        for cmd in content['quick_commands']:
            text += f"{get_emoji('check')} {cmd}\n"
        
        text += f"""
{convert_font('Click buttons below for detailed help:', 'bold')}
{get_emoji('check')} {convert_font(f'Total Commands: {content["stats"]["total_commands"]}+', 'bold')}
{get_emoji('adder1')} {convert_font(f'Loaded Plugins: {content["stats"]["loaded_plugins"]}/{content["stats"]["total_plugins"]}', 'bold')}
        """.strip()
        
    elif content['type'] == 'category':
        # Category-specific help
        cat_emoji = get_emoji(content['emoji'])
        text = f"""
{cat_emoji} {convert_font(content['title'], 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font(content['description'].upper(), 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

"""
        
        # Add plugin info if applicable
        if content.get('is_plugin'):
            text += f"{get_emoji('adder2')} {convert_font(f'Plugin: {content['plugin_name']}', 'bold')}\n\n"
        
        # Add commands
        for cmd_info in content['commands']:
            text += f"{get_emoji('check')} `{cmd_info['cmd']}`\n{cmd_info['desc']}\n\n"
        
        text = text.strip()
        
    else:
        # Error message
        text = f"""
{get_emoji('adder3')} {convert_font('INVALID CATEGORY', 'mono')}

{get_emoji('check')} Available categories:
"""
        
        for cat in content['available_categories'][:10]:  # Limit to first 10
            text += f"• {cat}\n"
        
        text += f"\n{get_emoji('main')} Use `{get_prefix()}help` for main menu"
    
    return text.strip()

def create_help_buttons(content: Dict[str, Any]) -> List[List[Button]]:
    """Create inline buttons untuk help menu"""
    if content['type'] != 'main_menu':
        # Back button untuk category pages
        return [[Button.inline(f"{get_emoji('main')} Back to Menu", b"help_main")]]
    
    # Main menu buttons
    buttons = []
    categories = content['categories']
    
    # Base category buttons (2 per row)
    base_cats = ['basic', 'gcast', 'emoji', 'user', 'voice', 'manage', 'system']
    base_emojis = ['check', 'adder1', 'adder2', 'adder3', 'adder4', 'adder5', 'adder6']
    
    for i in range(0, len(base_cats), 2):
        row = []
        for j in range(2):
            if i + j < len(base_cats):
                cat = base_cats[i + j]
                emoji = base_emojis[i + j]
                if cat in categories:
                    row.append(Button.inline(
                        f"{get_emoji(emoji)} {cat.title()}", 
                        f"help_{cat}".encode()
                    ))
        if row:
            buttons.append(row)
    
    # Plugin category buttons (jika ada)
    plugin_cats = [cat for cat in categories.keys() if cat.startswith('plugin_')]
    if plugin_cats:
        # Add separator
        buttons.append([Button.inline(f"{get_emoji('main')} PLUGIN COMMANDS {get_emoji('main')}", b"help_plugins_header")])
        
        # Plugin buttons (1 per row untuk readability)
        for cat in plugin_cats[:5]:  # Limit to 5 plugins
            cat_info = categories[cat]
            plugin_name = cat_info.get('plugin_name', cat.replace('plugin_', ''))
            buttons.append([Button.inline(
                f"{get_emoji('main')} {plugin_name.title()}", 
                f"help_{cat}".encode()
            )])
    
    # Control buttons
    control_row = [
        Button.inline("🔄 Refresh", b"help_main"),
        Button.inline("📊 Plugin Stats", b"help_plugin_stats")
    ]
    buttons.append(control_row)
    
    return buttons

def get_logo_url() -> str:
    """Get logo URL"""
    return "https://imgur.com/gallery/logo-S6biYEi"

# ============= EVENT HANDLERS =============

@client.on(events.NewMessage(pattern=rf'\.help(\s+(.+))?'))
async def help_handler(event):
    """Enhanced help command with plugin discovery"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        command_arg = event.pattern_match.group(2)
        category = command_arg.strip().lower() if command_arg else None
        
        # Generate help content dengan plugin discovery
        content = generate_help_content(category)
        
        # Format message
        help_text = format_help_message(content)
        
        # Create buttons
        buttons = create_help_buttons(content)
        
        # Send message dengan buttons
        msg = await safe_send_with_entities(event, help_text)
        
        # Edit dengan buttons setelah send
        if msg and buttons:
            try:
                await msg.edit(help_text, buttons=buttons)
            except Exception as button_error:
                print(f"Button edit error: {button_error}")
        
    except Exception as e:
        error_text = f"""
{get_emoji('adder3')} {convert_font('Help Error:', 'bold')} {str(e)}

{get_emoji('check')} Try: `{get_prefix()}help` for main menu
        """.strip()
        await safe_send_with_entities(event, error_text)

@client.on(events.CallbackQuery(pattern=rb"help_(.+)"))
async def help_callback_handler(event):
    """Handle inline button callbacks for help menu"""
    if not await is_owner_check(event.sender_id):
        await event.answer("❌ Only owner can use this!", alert=True)
        return
    
    try:
        callback_data = event.data.decode('utf-8')
        category = callback_data.split('_', 1)[1] if '_' in callback_data else 'main'
        
        # Handle special callbacks
        if category == 'plugins_header':
            await event.answer("Plugin commands section", alert=False)
            return
        elif category == 'plugin_stats':
            await show_plugin_stats(event)
            return
        elif category == 'main':
            category = None
        
        # Generate content
        content = generate_help_content(category)
        help_text = format_help_message(content)
        buttons = create_help_buttons(content)
        
        # Edit message
        await safe_edit_with_entities(event.message, help_text, buttons)
        await event.answer()
        
    except Exception as e:
        await event.answer(f"Error: {str(e)}", alert=True)

async def show_plugin_stats(event):
    """Show detailed plugin statistics"""
    try:
        plugins_info = discover_plugins()
        
        stats_text = f"""
{get_emoji('main')} {convert_font('PLUGIN SYSTEM STATISTICS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('check')} {convert_font('PLUGIN STATUS', 'mono')} {get_emoji('check')}
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('System Status:', 'bold')}
{get_emoji('check')} Total Plugins: `{plugins_info['total_plugins']}`
{get_emoji('check')} Loaded Successfully: `{plugins_info['loaded_plugins']}`
{get_emoji('check')} Available Commands: `{sum(len(cmds) for cmds in plugins_info['commands'].values())}`
{get_emoji('check')} Plugin Categories: `{len(plugins_info['categories'])}`

{get_emoji('adder2')} {convert_font('Loaded Plugins:', 'bold')}
"""
        
        # List loaded plugins
        if plugins_info['plugin_list']:
            for i, plugin in enumerate(plugins_info['plugin_list'][:10], 1):
                cmd_count = len(plugins_info['commands'].get(plugin, []))
                stats_text += f"{get_emoji('check')} {plugin}: `{cmd_count}` commands\n"
            
            if len(plugins_info['plugin_list']) > 10:
                stats_text += f"{get_emoji('main')} ... and {len(plugins_info['plugin_list']) - 10} more plugins\n"
        else:
            stats_text += f"{get_emoji('adder3')} No plugins loaded\n"
        
        stats_text += f"""
{get_emoji('adder3')} {convert_font('AssetJSON Integration:', 'bold')}
{get_emoji('check')} Status: {'Active' if asset_manager else 'Fallback Mode'}
{get_emoji('check')} Premium Emojis: {'Available' if plugin_env else 'Limited'}
{get_emoji('check')} Environment: {'v3.0.0' if asset_manager else 'Legacy'}

{get_emoji('main')} {convert_font('System operating optimally!', 'bold')}
        """.strip()
        
        # Edit with stats
        await safe_edit_with_entities(event.message, stats_text)
        
        # Back button
        back_button = [[Button.inline(f"{get_emoji('main')} Back to Help", b"help_main")]]
        await event.message.edit(stats_text, buttons=back_button)
        await event.answer("Plugin statistics updated!")
        
    except Exception as e:
        await event.answer(f"Stats error: {str(e)}", alert=True)

# ============= PLUGIN INFORMATION =============

def get_plugin_info():
    """Return plugin information for the loader"""
    return {
        'name': 'help',
        'version': '2.0.0',
        'description': 'Enhanced help system with AssetJSON v3.0.0 integration and dynamic plugin discovery',
        'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
        'commands': ['help'],
        'categories': ['system', 'basic'],
        'features': [
            'AssetJSON v3.0.0 integration',
            'Dynamic plugin discovery',
            'Premium emoji support',
            'Interactive button menu',
            'Plugin statistics',
            'Automatic command detection'
        ],
        'dependencies': ['assetjson>=3.0.0', 'telethon'],
        'compatible_with': ['vzoel_assistant>=0.1.0.75']
    }

# Compatibility check
if __name__ == "__main__":
    print("Help Plugin v2.0 - Enhanced with AssetJSON v3.0.0 integration")
    print("Features: Dynamic plugin discovery, premium emoji support, interactive menus")
    print("Run this plugin through the plugin loader system")