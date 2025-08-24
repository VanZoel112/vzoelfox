#!/usr/bin/env python3
"""
Enhanced Vzoel Assistant Plugin System Core
Handles plugin loading, management, and utilities with improved folder support
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

# Add plugins directory to Python path
plugins_dir = os.path.join(current_dir, "plugins")
if os.path.exists(plugins_dir):
    sys.path.insert(0, plugins_dir)

from config import *

logger = logging.getLogger(__name__)

# ============= PLUGIN MANAGER =============
class PluginManager:
    """Advanced plugin management system with enhanced folder support"""
    
    def __init__(self):
        self.loaded_plugins = {}
        self.plugin_commands = {}
        self.plugin_info = {}
        self.plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    
    def ensure_plugins_directory(self):
        """Create plugins directory if it doesn't exist"""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            logger.info(f"Created plugins directory: {self.plugins_dir}")
            
            # Create __init__.py in plugins directory
            init_file = os.path.join(self.plugins_dir, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write('"""Vzoel Assistant Plugins Directory"""\n')
                logger.info(f"Created __init__.py in plugins directory")
    
    def discover_plugins(self, directory: str = ".") -> List[Dict[str, str]]:
        """Discover all Python plugin files with enhanced folder support"""
        plugin_files = []
        
        # Files to skip
        skip_files = ['main.py', 'config.py', '__init__.py']
        
        # Check current directory for plugins
        current_dir_files = glob.glob(os.path.join(directory, "*.py"))
        for file in current_dir_files:
            filename = os.path.basename(file)
            if filename not in skip_files:
                plugin_files.append({
                    'path': file,
                    'name': Path(file).stem,
                    'location': 'root',
                    'relative_path': filename
                })
        
        # Check plugins directory
        self.ensure_plugins_directory()
        
        if os.path.exists(self.plugins_dir):
            plugins_dir_files = glob.glob(os.path.join(self.plugins_dir, "*.py"))
            for file in plugins_dir_files:
                filename = os.path.basename(file)
                if filename != '__init__.py':
                    plugin_files.append({
                        'path': file,
                        'name': Path(file).stem,
                        'location': 'plugins',
                        'relative_path': os.path.join('plugins', filename)
                    })
            
            # Also check for subdirectories in plugins folder
            for subdir in glob.glob(os.path.join(self.plugins_dir, "*/")):
                if os.path.isdir(subdir):
                    subdir_name = os.path.basename(subdir.rstrip('/'))
                    subdir_files = glob.glob(os.path.join(subdir, "*.py"))
                    
                    for file in subdir_files:
                        filename = os.path.basename(file)
                        if filename != '__init__.py':
                            plugin_files.append({
                                'path': file,
                                'name': f"{subdir_name}_{Path(file).stem}",
                                'location': f'plugins/{subdir_name}',
                                'relative_path': os.path.join('plugins', subdir_name, filename)
                            })
        
        logger.info(f"Discovered {len(plugin_files)} plugin files")
        for plugin in plugin_files:
            logger.debug(f"Found plugin: {plugin['name']} at {plugin['location']}")
        
        return plugin_files
    
    def load_plugin(self, plugin_info: Dict[str, str]) -> bool:
        """Load single plugin file with enhanced error handling"""
        file_path = plugin_info['path']
        plugin_name = plugin_info['name']
        location = plugin_info['location']
        
        try:
            # Add plugin directory to sys.path temporarily if needed
            plugin_dir = os.path.dirname(file_path)
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
                temp_path_added = True
            else:
                temp_path_added = False
            
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
                'location': location,
                'relative_path': plugin_info['relative_path'],
                'handlers': 0,
                'commands': []
            }
            
            # Count event handlers and extract commands
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
                            command_str = pattern.pattern if hasattr(pattern, 'pattern') else str(pattern)
                            commands.append(command_str)
                
                # Also check for _plugin_command attribute
                if hasattr(attr, '_plugin_command'):
                    commands.append(attr._plugin_command)
            
            self.loaded_plugins[plugin_name]['handlers'] = handlers_count
            self.loaded_plugins[plugin_name]['commands'] = list(set(commands))  # Remove duplicates
            
            logger.info(f"✅ Plugin loaded: {plugin_name} from {location} ({handlers_count} handlers)")
            
            # Clean up temporary path
            if temp_path_added:
                sys.path.remove(plugin_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {plugin_name} from {location}: {e}")
            # Clean up on error
            if plugin_name in self.loaded_plugins:
                del self.loaded_plugins[plugin_name]
            return False
    
    def load_all_plugins(self, directory: str = ".") -> Dict[str, Any]:
        """Load all discovered plugins with enhanced reporting"""
        plugin_files = self.discover_plugins(directory)
        results = {
            'loaded': [],
            'failed': [],
            'total_handlers': 0,
            'by_location': {
                'root': [],
                'plugins': [],
                'subdirs': []
            }
        }
        
        logger.info(f"🔍 Discovered {len(plugin_files)} plugin files")
        
        for plugin_info in plugin_files:
            plugin_name = plugin_info['name']
            location = plugin_info['location']
            
            if self.load_plugin(plugin_info):
                results['loaded'].append(plugin_name)
                results['total_handlers'] += self.loaded_plugins[plugin_name]['handlers']
                
                # Categorize by location
                if location == 'root':
                    results['by_location']['root'].append(plugin_name)
                elif location == 'plugins':
                    results['by_location']['plugins'].append(plugin_name)
                else:
                    results['by_location']['subdirs'].append(f"{plugin_name} ({location})")
            else:
                results['failed'].append(f"{plugin_name} ({location})")
        
        logger.info(f"✅ Loaded {len(results['loaded'])} plugins with {results['total_handlers']} handlers")
        
        # Log location statistics
        if results['by_location']['root']:
            logger.info(f"📁 Root directory: {len(results['by_location']['root'])} plugins")
        if results['by_location']['plugins']:
            logger.info(f"📂 Plugins directory: {len(results['by_location']['plugins'])} plugins")
        if results['by_location']['subdirs']:
            logger.info(f"📁 Subdirectories: {len(results['by_location']['subdirs'])} plugins")
            
        if results['failed']:
            logger.warning(f"❌ Failed to load {len(results['failed'])} plugins: {results['failed']}")
        
        return results
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get detailed information about loaded plugins"""
        return {
            'count': len(self.loaded_plugins),
            'plugins': self.loaded_plugins,
            'total_handlers': sum(p['handlers'] for p in self.loaded_plugins.values()),
            'by_location': self._group_plugins_by_location()
        }
    
    def _group_plugins_by_location(self) -> Dict[str, List[str]]:
        """Group plugins by their location"""
        grouped = {'root': [], 'plugins': [], 'subdirs': []}
        
        for name, info in self.loaded_plugins.items():
            location = info['location']
            if location == 'root':
                grouped['root'].append(name)
            elif location == 'plugins':
                grouped['plugins'].append(name)
            else:
                grouped['subdirs'].append(f"{name} ({location})")
        
        return grouped
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload specific plugin"""
        if plugin_name not in self.loaded_plugins:
            logger.error(f"Plugin {plugin_name} not found")
            return False
        
        plugin_info_dict = self.loaded_plugins[plugin_name]
        file_path = plugin_info_dict['file_path']
        location = plugin_info_dict['location']
        relative_path = plugin_info_dict['relative_path']
        
        # Create plugin info dict for reload
        plugin_info = {
            'path': file_path,
            'name': plugin_name,
            'location': location,
            'relative_path': relative_path
        }
        
        # Remove old plugin
        del self.loaded_plugins[plugin_name]
        
        # Reload plugin
        return self.load_plugin(plugin_info)
    
    def get_plugin_by_location(self, location: str) -> List[str]:
        """Get plugins by location (root, plugins, or subdir name)"""
        result = []
        for name, info in self.loaded_plugins.items():
            if info['location'] == location:
                result.append(name)
        return result

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
def create_plugin_template(plugin_name: str, save_to: str = None, in_plugins_dir: bool = True) -> str:
    """Create a plugin template file with option to save in plugins directory"""
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
        # Default to plugins directory if in_plugins_dir is True
        if in_plugins_dir:
            pm = get_plugin_manager()
            pm.ensure_plugins_directory()
            file_path = os.path.join(pm.plugins_dir, f"{plugin_name}.py")
        else:
            file_path = os.path.join(save_to, f"{plugin_name}.py")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        logger.info(f"✅ Plugin template created: {file_path}")
    
    return template

def list_plugins_structure():
    """Show the structure of plugins directory"""
    pm = get_plugin_manager()
    pm.ensure_plugins_directory()
    
    structure = []
    structure.append("📁 Vzoel Assistant Plugin Structure:")
    structure.append("├── main.py")
    structure.append("├── config.py")
    structure.append("├── __init__.py")
    structure.append("├── *.py (root level plugins)")
    structure.append("└── plugins/")
    structure.append("    ├── __init__.py")
    structure.append("    ├── *.py (plugin files)")
    structure.append("    └── subdirectories/")
    structure.append("        └── *.py (organized plugins)")
    
    return "\n".join(structure)

# ============= VERSION INFO =============
__version__ = "2.1.0"
__author__ = "Enhanced Vzoel Assistant"
__description__ = "Advanced plugin system with enhanced folder support for Telegram Vzoel Assistant"

# ============= EXPORTS =============
__all__ = [
    'PluginManager',
    'get_plugin_manager', 
    'cmd',
    'owner_only',
    'log_command_usage',
    'create_plugin_template',
    'list_plugins_structure',
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
    
    if results['by_location']['root']:
        print(f"📁 Root: {len(results['by_location']['root'])} plugins")
    if results['by_location']['plugins']:
        print(f"📂 Plugins dir: {len(results['by_location']['plugins'])} plugins")
    if results['by_location']['subdirs']:
        print(f"📁 Subdirs: {len(results['by_location']['subdirs'])} plugins")
