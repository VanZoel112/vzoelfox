#!/usr/bin/env python3
"""
Fixed Plugin Loader untuk VZOEL ASSISTANT v0.1.0.75
File: plugin_loader.py
"""

import os
import sys
import importlib.util  # FIX: Import util explicitly
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PluginLoader:
    def __init__(self, client=None):
        self.client = client
        self.plugins = {}
        self.loaded_plugins = []
        self.failed_plugins = []
        self.plugins_dir = None
    
    def get_status(self) -> Dict[str, int]:
        """Return plugin loading status"""
        return {
            'total_plugins': len(self.plugins),
            'total_loaded': len(self.loaded_plugins),
            'total_failed': len(self.failed_plugins)
        }
    
    def load_plugin(self, plugin_name: str, plugin_path: str) -> bool:
        """Load individual plugin with proper error handling"""
        try:
            # Check if file exists
            if not os.path.exists(plugin_path):
                raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
            
            # Import plugin module using proper importlib
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None:
                raise ImportError(f"Could not create spec for {plugin_name}")
            
            if spec.loader is None:
                raise ImportError(f"No loader available for {plugin_name}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to prevent import issues
            sys.modules[f"plugin_{plugin_name}"] = module
            
            # Set up plugin environment - make client available to plugin
            if self.client:
                # Inject client into module globals
                module.__dict__['client'] = self.client
                
                # Also make it available in builtins for easier access
                import builtins
                if not hasattr(builtins, 'client'):
                    builtins.client = self.client
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # Store plugin
            self.plugins[plugin_name] = module
            self.loaded_plugins.append(plugin_name)
            
            logger.info(f"✅ Plugin loaded: {plugin_name}")
            return True
            
        except Exception as e:
            self.failed_plugins.append(plugin_name)
            logger.error(f"❌ Failed to load plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self, plugins_dir: str) -> Dict[str, Any]:
        """Load all plugins from directory"""
        self.plugins_dir = plugins_dir
        results = {
            'loaded': [],
            'failed': [],
            'total': 0
        }
        
        # Create plugins directory if it doesn't exist
        if not os.path.exists(plugins_dir):
            try:
                os.makedirs(plugins_dir)
                logger.info(f"📁 Created plugins directory: {plugins_dir}")
                
                # Create __init__.py file
                init_file = os.path.join(plugins_dir, "__init__.py")
                with open(init_file, 'w') as f:
                    f.write("# Plugins package\n")
                
            except Exception as e:
                logger.error(f"❌ Failed to create plugins directory: {e}")
                return results
        
        # Find all Python files in plugins directory
        plugin_files = []
        try:
            for file in os.listdir(plugins_dir):
                if (file.endswith('.py') and 
                    not file.startswith('__') and 
                    not file.startswith('.')):
                    plugin_files.append(file)
        except Exception as e:
            logger.error(f"❌ Error reading plugins directory: {e}")
            return results
        
        results['total'] = len(plugin_files)
        
        if not plugin_files:
            logger.info("📂 No plugins found in plugins directory")
            return results
        
        # Load each plugin
        for plugin_file in plugin_files:
            plugin_name = plugin_file[:-3]  # Remove .py extension
            plugin_path = os.path.join(plugins_dir, plugin_file)
            
            logger.info(f"🔄 Loading plugin: {plugin_name}")
            
            if self.load_plugin(plugin_name, plugin_path):
                results['loaded'].append(plugin_name)
            else:
                results['failed'].append(plugin_name)
        
        # Log summary
        if results['loaded']:
            logger.info(f"✅ Successfully loaded plugins: {', '.join(results['loaded'])}")
        
        if results['failed']:
            logger.warning(f"❌ Failed to load plugins: {', '.join(results['failed'])}")
        
        logger.info(f"📊 Plugin loading complete: {len(results['loaded'])}/{results['total']} loaded")
        return results
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload specific plugin"""
        try:
            if plugin_name in self.plugins:
                # Remove from sys.modules
                module_key = f"plugin_{plugin_name}"
                if module_key in sys.modules:
                    del sys.modules[module_key]
                
                # Remove from our storage
                del self.plugins[plugin_name]
                if plugin_name in self.loaded_plugins:
                    self.loaded_plugins.remove(plugin_name)
                
                logger.info(f"🗑️ Plugin unloaded: {plugin_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error unloading plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload specific plugin"""
        if plugin_name in self.plugins and self.plugins_dir:
            plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
            if os.path.exists(plugin_path):
                logger.info(f"🔄 Reloading plugin: {plugin_name}")
                self.unload_plugin(plugin_name)
                return self.load_plugin(plugin_name, plugin_path)
        return False
    
    def get_plugin(self, plugin_name: str):
        """Get loaded plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, List[str]]:
        """List all plugins by status"""
        return {
            'loaded': self.loaded_plugins.copy(),
            'failed': self.failed_plugins.copy(),
            'all': list(self.plugins.keys())
        }
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict]:
        """Get plugin information if available"""
        plugin = self.get_plugin(plugin_name)
        if plugin and hasattr(plugin, 'get_plugin_info'):
            try:
                return plugin.get_plugin_info()
            except Exception as e:
                logger.error(f"Error getting plugin info for {plugin_name}: {e}")
        return None

def setup_plugins(client, plugins_dir: str = "plugins") -> PluginLoader:
    """
    Setup and initialize plugin system
    
    Args:
        client: Telegram client instance
        plugins_dir: Directory containing plugin files
    
    Returns:
        PluginLoader instance
    """
    try:
        logger.info(f"🔧 Initializing plugin system...")
        loader = PluginLoader(client=client)
        results = loader.load_all_plugins(plugins_dir)
        
        logger.info(f"📊 Plugin system initialized:")
        logger.info(f"  - Total plugins found: {results['total']}")
        logger.info(f"  - Successfully loaded: {len(results['loaded'])}")
        logger.info(f"  - Failed to load: {len(results['failed'])}")
        
        if results['failed']:
            logger.warning(f"⚠️ Failed plugins: {', '.join(results['failed'])}")
        
        if results['loaded']:
            logger.info(f"✅ Loaded plugins: {', '.join(results['loaded'])}")
        
        return loader
        
    except Exception as e:
        logger.error(f"❌ Plugin system initialization failed: {e}")
        # Return empty loader instead of crashing
        return PluginLoader(client=client)
