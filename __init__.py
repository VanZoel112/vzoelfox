#!/usr/bin/env python3
"""
Enhanced Vzoel Assistant Plugin System Core
Handles plugin loading, management, and utilities
"""

import os
import sys
import glob
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config import *

logger = logging.getLogger(__name__)

# ============= PLUGIN MANAGER =============
class PluginManager:
    """Advanced plugin management system"""
    
    def __init__(self):
        self.loaded_plugins = {}
        self.plugin_commands = {}
        self.plugin_info = {}
    
    def discover_plugins(self, directory: str = ".") -> List[str]:
        """Discover all Python plugin files"""
        plugin_files = []
        
        # Check current directory
        for file in glob.glob(os.path.join(directory, "*.py")):
            filename = os.path.basename(file)
            if filename not in ['main.py', 'config.py', '__init__.py']:
                plugin_files.append(file)
        
        # Check plugins directory if exists
        plugins_dir = os.path.join(directory, "plugins")
        if os.path.exists(plugins_dir):
            for file in glob.glob(os.path.join(plugins_dir, "*.py")):
                filename = os.path.basename(file)
                if filename != '__init__.py':
                    plugin_files.append(file)
        
        return plugin_files
    
    def load_plugin(self, file_path: str) -> bool:
        """Load single plugin file"""
        try:
            plugin_name = Path(file_path).stem
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(plugin_name, file_path)
            if not spec or not spec.loader:
                logger.error(f"Cannot create spec for {plugin_name}")
                return False
            
            # Load module
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Store plugin info
            self.loaded_plugins[plugin_name] = {
                'module': module,
                'file_path': file_path,
                'handlers': 0,
                'commands': []
            }
            
            # Count event handlers
            handlers_count = 0
            commands = []
            
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, '_telethon_event'):
                    handlers_count += 1
                    
                    # Try to extract command from pattern
                    if hasattr(attr, '_telethon_event') and hasattr(attr._telethon_event, 'pattern'):
                        pattern = attr._telethon_event.pattern
                        if pattern:
                            commands.append(pattern.pattern if hasattr(pattern, 'pattern') else str(pattern))
            
            self.loaded_plugins[plugin_name]['handlers'] = handlers_count
            self.loaded_plugins[plugin_name]['commands'] = commands
            
            logger.info(f"✅ Plugin loaded: {plugin_name} ({handlers_count} handlers)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {file_path}: {e}")
            return False
    
    def load_all_plugins(self, directory: str = ".") -> Dict[str, Any]:
        """Load all discovered plugins"""
        plugin_files = self.discover_plugins(directory)
        results = {
            'loaded': [],
            'failed': [],
            'total_handlers': 0
        }
        
        logger.info(f"🔍 Discovered {len(plugin_files)} plugin files")
        
        for file_path in plugin_files:
            plugin_name = Path(file_path).stem
            if self.load_plugin(file_path):
                results['loaded'].append(plugin_name)
                results['total_handlers'] += self.loaded_plugins[plugin_name]['handlers']
            else:
                results['failed'].append(plugin_name)
        
        logger.info(f"✅ Loaded {len(results['loaded'])} plugins with {results['total_handlers']} handlers")
        if results['failed']:
            logger.warning(f"❌ Failed to load {len(results['failed'])} plugins: {results['failed']}")
        
        return results
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about loaded plugins"""
        return {
            'count': len(self.loaded_plugins),
            'plugins': self.loaded_plugins,
            'total_handlers': sum(p['handlers'] for p in self.loaded_plugins.values())
        }
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload specific plugin"""
        if plugin_name not in self.loaded_plugins:
            logger.error(f"Plugin {plugin_name} not found")
            return False
        
        file_path = self.loaded_plugins[plugin_name]['file_path']
        
        # Remove old plugin
        del self.loaded_plugins[plugin_name]
        
        # Reload plugin
        return self.load_plugin(file_path)

# ============= UTILITY FUNCTIONS =============
def get_plugin_manager():
    """Get global plugin manager instance"""
    if not hasattr(get_plugin_manager, 'instance'):
        get_plugin_manager.instance = PluginManager()
    return get_plugin_manager.instance

def cmd(pattern: str):
    """Decorator untuk membuat command dengan prefix otomatis"""
    if not pattern.startswith(COMMAND_PREFIX):
        pattern = COMMAND_PREFIX + pattern
    
    def decorator(func):
        # Store command info untuk help system
        if not hasattr(func, '_plugin_command'):
            func._plugin_command = pattern
        return func
    return decorator

def owner_only(func):
    """Decorator untuk command yang hanya bisa digunakan owner"""
    async def wrapper(event):
        # Import here to avoid circular import
        from main import is_owner
        if not await is_owner(event.sender_id):
            return
        return await func(event)
    
    # Copy function attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    if hasattr(func, '_telethon_event'):
        wrapper._telethon_event = func._telethon_event
    if hasattr(func, '_plugin_command'):
        wrapper._plugin_command = func._plugin_command
    
    return wrapper

def log_command_usage(func):
    """Decorator untuk log penggunaan command"""
    async def wrapper(event):
        try:
            # Import here to avoid circular import  
            from main import log_command
            command_name = getattr(func, '_plugin_command', func.__name__)
            await log_command(event, command_name)
        except:
            pass  # Ignore logging errors
        
        return await func(event)
    
    # Copy function attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    if hasattr(func, '_telethon_event'):
        wrapper._telethon_event = func._telethon_event
    if hasattr(func, '_plugin_command'):
        wrapper._plugin_command = func._plugin_command
    
    return wrapper

# ============= HELPER FUNCTIONS =============
def create_plugin_template(plugin_name: str, save_to: str = None) -> str:
    """Create a plugin template file"""
    template = f'''#!/usr/bin/env python3
"""
{plugin_name.title()} Plugin for Enhanced Vzoel Assistant
Auto-generated template
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage

@events.register(events.NewMessage(pattern=rf'{{COMMAND_PREFIX}}{plugin_name}'))
@owner_only
@log_command_usage
async def {plugin_name}_handler(event):
    """{plugin_name.title()} command"""
    await event.reply(f"🎉 {plugin_name.title()} plugin is working!")

# Optional: Add more functions here
'''
    
    if save_to:
        file_path = os.path.join(save_to, f"{plugin_name}.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        logger.info(f"✅ Plugin template created: {file_path}")
    
    return template

# ============= VERSION INFO =============
__version__ = "2.0.0"
__author__ = "Enhanced Vzoel Assistant"
__description__ = "Advanced plugin system for Telegram Vzoel Assistant"

# ============= EXPORTS =============
__all__ = [
    'PluginManager',
    'get_plugin_manager', 
    'cmd',
    'owner_only',
    'log_command_usage',
    'create_plugin_template',
    'COMMAND_PREFIX',
    'OWNER_ID',
    'SESSION_NAME'
]

# ============= AUTO-INITIALIZATION =============
if __name__ == "__main__":
    print("🔌 Enhanced Vzoel Assistant Plugin System")
    print(f"📋 Version: {__version__}")
    print("🔧 Initializing plugin manager...")
    
    pm = get_plugin_manager()
    results = pm.load_all_plugins()
    
    print(f"✅ Plugin system ready!")
    print(f"📊 Loaded: {len(results['loaded'])} plugins")
    print(f"🎯 Total handlers: {results['total_handlers']}")
