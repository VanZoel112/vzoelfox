#!/usr/bin/env python3
"""
🎨 CUSTOM MESSAGE MANAGER PLUGIN - Advanced Message Customization System
Fitur: Manajemen pesan custom untuk semua fungsi userbot
Author: Vzoel Fox's (Enhanced by Morgan)  
Version: 1.0.0 - Message Manager Edition
"""

import asyncio
import json
import os
import shutil
import time
import re
from datetime import datetime, timedelta
from telethon import events, functions
from telethon.tl.types import MessageEntityTextUrl
import psutil

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "custom_message_manager", 
    "version": "1.0.0",
    "description": "🎨 Advanced message customization system untuk userbot",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".msgsetup", ".msgedit", ".msgtest", ".msgbackup", ".msgrestore",
        ".msgtheme", ".msgplaceholder", ".msgexport", ".msgimport"
    ],
    "features": [
        "Custom message templates", "Dynamic placeholders", "Theme system",
        "Backup & restore", "Live preview", "Export/import configs"
    ]
}

# ===== CONFIGURATION =====
CONFIG_FILE = "userbot_custom_messages.json"
BACKUP_DIR = "message_backups"
THEMES_DIR = "message_themes"

# Premium emoji configuration
PREMIUM_EMOJIS = {
    'edit': {'id': '5794353925360457382', 'char': '✏️'},
    'check': {'id': '5794407002566300853', 'char': '✅'},
    'theme': {'id': '5793913811471700779', 'char': '🎨'},
    'backup': {'id': '5321412209992033736', 'char': '💾'},
    'test': {'id': '5793973133559993740', 'char': '🧪'},
    'config': {'id': '5357404860566235955', 'char': '⚙️'}
}

def create_premium_message(emoji_key, text):
    emoji = PREMIUM_EMOJIS.get(emoji_key, {'char': '🎨'})
    return f"<emoji id='{emoji['id']}'>{emoji['char']}</emoji> {text}"

# ===== GLOBAL MESSAGE MANAGER =====
class MessageManager:
    def __init__(self):
        self.config = {}
        self.placeholders_cache = {}
        self.load_config()
    
    def load_config(self):
        """Load message configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                print("⚠️ Custom messages config not found, using defaults")
                self.create_default_config()
        except Exception as e:
            print(f"Error loading message config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration if not exists"""
        default_config = {
            "_comment": "Default message configuration",
            "_generated": datetime.now().isoformat(),
            "alive_messages": {
                "default": {
                    "title": "🤖 **VZOEL USERBOT IS ALIVE!**",
                    "content": [
                        "**👤 Owner:** {owner_name}",
                        "**⚡ Uptime:** {uptime}",
                        "**📊 Plugins:** {plugin_count} loaded"
                    ],
                    "footer": "**🚀 VZOEL BOT - Ready!**"
                }
            },
            "ping_messages": {
                "default": {
                    "title": "🏓 **PONG!**",
                    "content": "**⚡ Response Time:** {ping_time}ms"
                }
            }
        }
        
        self.config = default_config
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Create backup first
            if os.path.exists(CONFIG_FILE):
                os.makedirs(BACKUP_DIR, exist_ok=True)
                backup_file = f"{BACKUP_DIR}/config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(CONFIG_FILE, backup_file)
            
            # Save new config
            self.config['_last_updated'] = datetime.now().isoformat()
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_message(self, category, message_type="default", **kwargs):
        """Get formatted message with placeholders"""
        try:
            message_data = self.config.get(category, {}).get(message_type, {})
            if not message_data:
                return f"Message not found: {category}.{message_type}"
            
            # Format message content
            formatted_message = self.format_message(message_data, **kwargs)
            return formatted_message
            
        except Exception as e:
            return f"Error formatting message: {str(e)}"
    
    def format_message(self, message_data, **kwargs):
        """Format message with placeholders"""
        try:
            # Update placeholders with current data
            placeholders = self.get_current_placeholders()
            placeholders.update(kwargs)
            
            # Format title
            title = message_data.get('title', '')
            if title:
                title = self.replace_placeholders(title, placeholders)
            
            # Format content
            content = message_data.get('content', [])
            if isinstance(content, str):
                content = [content]
            
            formatted_content = []
            for line in content:
                formatted_line = self.replace_placeholders(line, placeholders)
                formatted_content.append(formatted_line)
            
            # Format footer
            footer = message_data.get('footer', '')
            if footer:
                footer = self.replace_placeholders(footer, placeholders)
            
            # Combine message parts
            message_parts = []
            if title:
                message_parts.append(title)
            if formatted_content:
                message_parts.extend(formatted_content)
            if footer:
                message_parts.append(footer)
            
            return '\n'.join(message_parts)
            
        except Exception as e:
            return f"Format error: {str(e)}"
    
    def replace_placeholders(self, text, placeholders):
        """Replace placeholders in text"""
        try:
            for placeholder, value in placeholders.items():
                text = text.replace(f'{{{placeholder}}}', str(value))
            return text
        except Exception as e:
            return text
    
    def get_current_placeholders(self):
        """Get current system placeholders"""
        try:
            # Cache placeholders for performance
            current_time = time.time()
            if hasattr(self, 'placeholders_cache_time') and \
               current_time - self.placeholders_cache_time < 30:  # 30 second cache
                return self.placeholders_cache
            
            # System info
            memory = psutil.virtual_memory()
            boot_time = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(boot_time)
            
            placeholders = {
                # Bot info
                'bot_version': 'v1.0.0.75',
                'owner_name': 'Vzoel Fox',
                'uptime': str(uptime).split('.')[0],
                'plugin_count': len([f for f in os.listdir('plugins') if f.endswith('.py')]) if os.path.exists('plugins') else 0,
                
                # System info
                'memory_usage': f"{memory.percent}%",
                'python_version': f"{psutil.python_version}",
                'current_time': datetime.now().strftime("%H:%M:%S"),
                'server_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'date': datetime.now().strftime("%Y-%m-%d"),
                
                # Network info (defaults)
                'ping_time': '0',
                'dc_id': '2',
                'connection_type': 'WiFi',
                
                # Placeholders for dynamic content
                'mention': '@user',
                'username': 'username',
                'user_id': '123456',
                'first_name': 'First',
                'last_name': 'Last',
                'full_name': 'Full Name',
                'chat_title': 'Chat Title',
                'chat_id': '-123456',
                'members_count': '100',
                'admins_count': '5'
            }
            
            self.placeholders_cache = placeholders
            self.placeholders_cache_time = current_time
            
            return placeholders
            
        except Exception as e:
            return {'error': str(e)}

# Global message manager instance
msg_manager = MessageManager()

# ===== UTILITY FUNCTIONS =====
def get_available_themes():
    """Get available message themes"""
    themes = ["default", "premium", "gaming", "minimal", "colorful"]
    return themes

def apply_theme(theme_name):
    """Apply theme to messages"""
    try:
        theme_config = msg_manager.config.get('themes', {}).get(theme_name, {})
        if not theme_config:
            return False
        
        # Update customization settings
        msg_manager.config['customization_settings']['current_theme'] = theme_name
        msg_manager.save_config()
        return True
    except Exception as e:
        print(f"Apply theme error: {e}")
        return False

def export_messages(export_type="all"):
    """Export message configuration"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"message_export_{timestamp}.json"
        
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "type": export_type,
                "version": "1.0.0"
            },
            "data": msg_manager.config
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return export_file
    except Exception as e:
        print(f"Export error: {e}")
        return None

# ===== EVENT HANDLERS =====
@client.on(events.NewMessage(pattern=r'^\.msgsetup$'))
async def message_setup_menu(event):
    """Show message customization menu"""
    try:
        menu_text = f"""**🎨 MESSAGE CUSTOMIZATION MENU**

**📋 Available Categories:**
• `.msgedit alive` - Customize alive messages
• `.msgedit ping` - Customize ping messages  
• `.msgedit gcast` - Customize gcast messages
• `.msgedit afk` - Customize AFK messages
• `.msgedit help` - Customize help messages
• `.msgedit error` - Customize error messages

**🎭 Theme Management:**
• `.msgtheme list` - Available themes
• `.msgtheme set <name>` - Apply theme

**💾 Backup & Restore:**
• `.msgbackup` - Create backup
• `.msgrestore <file>` - Restore from backup

**🔧 Advanced:**
• `.msgplaceholder` - View placeholders
• `.msgtest <category>` - Test messages
• `.msgexport` - Export configuration

**Current Theme:** {msg_manager.config.get('customization_settings', {}).get('current_theme', 'default')}
**Messages Loaded:** {len(msg_manager.config)} categories"""
        
        await event.respond(create_premium_message('config', menu_text))
        
    except Exception as e:
        await event.respond(create_premium_message('config', f'**Setup menu error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.msgedit (.+)$'))
async def edit_message_category(event):
    """Edit messages by category"""
    try:
        category = event.pattern_match.group(1).strip().lower()
        
        # Map category shortcuts
        category_map = {
            'alive': 'alive_messages',
            'ping': 'ping_messages',
            'gcast': 'gcast_messages',
            'afk': 'afk_messages',
            'help': 'help_messages',
            'error': 'error_messages',
            'success': 'success_messages',
            'loading': 'loading_messages',
            'welcome': 'welcome_messages',
            'goodbye': 'goodbye_messages'
        }
        
        full_category = category_map.get(category, f"{category}_messages")
        
        if full_category not in msg_manager.config:
            await event.respond(create_premium_message('edit', f'**Category `{category}` not found!**\n\nAvailable: {", ".join(category_map.keys())}'))
            return
        
        # Show current messages in category
        messages_data = msg_manager.config[full_category]
        message_list = []
        
        for msg_type, msg_data in messages_data.items():
            title = msg_data.get('title', 'No title')
            content_preview = str(msg_data.get('content', ''))[:50] + "..." if len(str(msg_data.get('content', ''))) > 50 else str(msg_data.get('content', ''))
            message_list.append(f"**{msg_type}:** {title}\n   *{content_preview}*")
        
        result_text = f"""**✏️ EDITING: {category.upper()} MESSAGES**

{chr(10).join(message_list)}

**🔧 Edit Commands:**
• **View:** `.msgtest {category}` to preview
• **Backup:** `.msgbackup` before editing
• **Manual:** Edit `{CONFIG_FILE}` directly

**💡 Tips:**
• Use placeholders like `{{owner_name}}`, `{{uptime}}`
• Test changes with `.msgtest {category}`
• Keep backups before major changes"""
        
        await event.respond(create_premium_message('edit', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('edit', f'**Edit error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.msgtest (.+)$'))
async def test_message(event):
    """Test message formatting"""
    try:
        category = event.pattern_match.group(1).strip().lower()
        
        # Map category shortcuts
        category_map = {
            'alive': 'alive_messages',
            'ping': 'ping_messages',
            'gcast': 'gcast_messages',
            'afk': 'afk_messages'
        }
        
        full_category = category_map.get(category, f"{category}_messages")
        
        if full_category not in msg_manager.config:
            await event.respond(create_premium_message('test', f'**Category `{category}` not found!**'))
            return
        
        # Test default message from category
        test_message = msg_manager.get_message(full_category, "default", 
                                             ping_time="42",
                                             mention=f"@{event.sender.username or event.sender.first_name}",
                                             username=event.sender.username or "user",
                                             reason="Testing AFK message")
        
        preview_text = f"""**🧪 MESSAGE PREVIEW: {category.upper()}**

**Raw Output:**
{test_message}

**✅ Test completed!** Message formatted successfully."""
        
        await event.respond(create_premium_message('test', preview_text))
        
    except Exception as e:
        await event.respond(create_premium_message('test', f'**Test error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.msgtheme (.+)$'))
async def manage_themes(event):
    """Manage message themes"""
    try:
        action = event.pattern_match.group(1).strip().lower()
        
        if action == "list":
            themes = get_available_themes()
            current_theme = msg_manager.config.get('customization_settings', {}).get('current_theme', 'default')
            
            theme_list = []
            for theme in themes:
                emoji = "🎯" if theme == current_theme else "🎨"
                theme_list.append(f"{emoji} **{theme.title()}**")
            
            result_text = f"""**🎭 AVAILABLE THEMES**

{chr(10).join(theme_list)}

**Usage:** `.msgtheme set <theme_name>`
**Current:** {current_theme}"""
            
            await event.respond(create_premium_message('theme', result_text))
        
        elif action.startswith("set "):
            theme_name = action.replace("set ", "").strip()
            themes = get_available_themes()
            
            if theme_name in themes:
                success = apply_theme(theme_name)
                if success:
                    await event.respond(create_premium_message('theme', f'**✅ Theme `{theme_name}` applied!**\n\nRestart bot to see full effects.'))
                else:
                    await event.respond(create_premium_message('theme', f'**❌ Failed to apply theme `{theme_name}`**'))
            else:
                await event.respond(create_premium_message('theme', f'**Theme `{theme_name}` not found!**\n\nAvailable: {", ".join(themes)}'))
        
        else:
            await event.respond(create_premium_message('theme', '**Usage:** `.msgtheme list` or `.msgtheme set <name>`'))
            
    except Exception as e:
        await event.respond(create_premium_message('theme', f'**Theme error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.msgplaceholder$'))
async def show_placeholders(event):
    """Show available placeholders"""
    try:
        placeholders = msg_manager.get_current_placeholders()
        
        # Group placeholders by category
        user_placeholders = ['{mention}', '{username}', '{user_id}', '{first_name}', '{last_name}', '{full_name}']
        bot_placeholders = ['{owner_name}', '{bot_version}', '{uptime}', '{plugin_count}', '{memory_usage}', '{ping_time}']
        chat_placeholders = ['{chat_title}', '{chat_id}', '{members_count}', '{admins_count}']
        time_placeholders = ['{current_time}', '{server_time}', '{date}', '{since_time}', '{duration}']
        
        result_text = f"""**📝 AVAILABLE PLACEHOLDERS**

**👤 User Placeholders:**
{", ".join(user_placeholders)}

**🤖 Bot Placeholders:**  
{", ".join(bot_placeholders)}

**💬 Chat Placeholders:**
{", ".join(chat_placeholders)}

**🕐 Time Placeholders:**
{", ".join(time_placeholders)}

**📊 Current Values:**
• Owner: {placeholders.get('owner_name', 'N/A')}
• Uptime: {placeholders.get('uptime', 'N/A')}
• Memory: {placeholders.get('memory_usage', 'N/A')}
• Plugins: {placeholders.get('plugin_count', 'N/A')}

**💡 Usage:** Include placeholders in your custom messages"""
        
        await event.respond(create_premium_message('config', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('config', f'**Placeholder error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.msgbackup$'))
async def create_message_backup(event):
    """Create backup of message configuration"""
    try:
        msg = await event.respond(create_premium_message('backup', '**Creating message backup...**'))
        
        # Create backup directory
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Create backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{BACKUP_DIR}/messages_backup_{timestamp}.json"
        
        backup_data = {
            "backup_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "type": "full_backup"
            },
            "configuration": msg_manager.config
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        file_size = os.path.getsize(backup_file)
        file_size_kb = file_size / 1024
        
        await msg.edit(create_premium_message('backup', f"""**✅ Backup Created Successfully!**

**📁 File:** `{backup_file}`
**📊 Size:** {file_size_kb:.1f} KB
**📅 Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Restore:** `.msgrestore {os.path.basename(backup_file)}`"""))
        
    except Exception as e:
        await event.respond(create_premium_message('backup', f'**Backup error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.msgexport$'))
async def export_messages_command(event):
    """Export message configuration"""
    try:
        msg = await event.respond(create_premium_message('backup', '**Exporting message configuration...**'))
        
        export_file = export_messages()
        
        if export_file:
            file_size = os.path.getsize(export_file)
            file_size_kb = file_size / 1024
            
            await msg.edit(create_premium_message('backup', f"""**📤 Export Complete!**

**📁 File:** `{export_file}`  
**📊 Size:** {file_size_kb:.1f} KB

**Share:** Send this file to others
**Import:** `.msgimport <file>`"""))
        else:
            await msg.edit(create_premium_message('backup', '**❌ Export failed!**'))
            
    except Exception as e:
        await event.respond(create_premium_message('backup', f'**Export error:** {str(e)}'))

# ===== MESSAGE INTEGRATION FUNCTIONS =====
def get_alive_message(message_type="default", **kwargs):
    """Get alive message - for integration with alive plugin"""
    return msg_manager.get_message('alive_messages', message_type, **kwargs)

def get_ping_message(message_type="default", **kwargs):
    """Get ping message - for integration with ping plugin"""
    return msg_manager.get_message('ping_messages', message_type, **kwargs)

def get_gcast_message(message_type="default", **kwargs):
    """Get gcast message - for integration with gcast plugin"""  
    return msg_manager.get_message('gcast_messages', message_type, **kwargs)

def get_afk_message(message_type="default", **kwargs):
    """Get AFK message - for integration with AFK plugin"""
    return msg_manager.get_message('afk_messages', message_type, **kwargs)

def get_error_message(error_type="generic", **kwargs):
    """Get error message - for integration with any plugin"""
    return msg_manager.get_message('error_messages', error_type, **kwargs)

def get_success_message(success_type="generic", **kwargs):
    """Get success message - for integration with any plugin"""
    return msg_manager.get_message('success_messages', success_type, **kwargs)

def get_loading_message(loading_type="generic", **kwargs):
    """Get loading message - for integration with any plugin"""
    return msg_manager.get_message('loading_messages', loading_type, **kwargs)

# ===== INITIALIZATION =====
def setup():
    """Plugin setup function"""
    print("🎨 Custom Message Manager Plugin loaded!")
    
    # Create directories
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(THEMES_DIR, exist_ok=True)
    
    # Load configuration
    msg_manager.load_config()
    
    return True

# Export functions for use by other plugins
__all__ = [
    'get_alive_message', 'get_ping_message', 'get_gcast_message', 
    'get_afk_message', 'get_error_message', 'get_success_message',
    'get_loading_message', 'msg_manager'
]

if __name__ == "__main__":
    setup()