# plugin_loader.py - Implementation yang benar

import os
import sys
import importlib
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
        """Load individual plugin"""
        try:
            # Import plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None:
                raise ImportError(f"Could not load spec for {plugin_name}")
            
            module = importlib.util.module_from_spec(spec)
            
            # Set up plugin environment
            if self.client:
                module.client = self.client
            
            spec.loader.exec_module(module)
            
            # Store plugin
            self.plugins[plugin_name] = module
            self.loaded_plugins.append(plugin_name)
            
            logger.info(f"Plugin loaded: {plugin_name}")
            return True
            
        except Exception as e:
            self.failed_plugins.append(plugin_name)
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self, plugins_dir: str) -> Dict[str, Any]:
        """Load all plugins from directory"""
        self.plugins_dir = plugins_dir
        results = {
            'loaded': [],
            'failed': [],
            'total': 0
        }
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            logger.info(f"Created plugins directory: {plugins_dir}")
            return results
        
        # Find all Python files in plugins directory
        plugin_files = []
        for file in os.listdir(plugins_dir):
            if file.endswith('.py') and not file.startswith('__'):
                plugin_files.append(file)
        
        results['total'] = len(plugin_files)
        
        # Load each plugin
        for plugin_file in plugin_files:
            plugin_name = plugin_file[:-3]  # Remove .py extension
            plugin_path = os.path.join(plugins_dir, plugin_file)
            
            if self.load_plugin(plugin_name, plugin_path):
                results['loaded'].append(plugin_name)
            else:
                results['failed'].append(plugin_name)
        
        logger.info(f"Plugin loading complete: {len(results['loaded'])}/{results['total']} loaded")
        return results
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload specific plugin"""
        try:
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
                if plugin_name in self.loaded_plugins:
                    self.loaded_plugins.remove(plugin_name)
                logger.info(f"Plugin unloaded: {plugin_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload specific plugin"""
        if plugin_name in self.plugins:
            plugin_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
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

def setup_plugins(client, plugins_dir: str = "plugins") -> PluginLoader:
    """
    Setup and initialize plugin system
    
    Args:
        client: Telegram client instance (not 'app')
        plugins_dir: Directory containing plugin files
    
    Returns:
        PluginLoader instance
    """
    try:
        loader = PluginLoader(client=client)
        results = loader.load_all_plugins(plugins_dir)
        
        logger.info(f"Plugin system initialized:")
        logger.info(f"  - Total plugins found: {results['total']}")
        logger.info(f"  - Successfully loaded: {len(results['loaded'])}")
        logger.info(f"  - Failed to load: {len(results['failed'])}")
        
        if results['failed']:
            logger.warning(f"Failed plugins: {', '.join(results['failed'])}")
        
        return loader
        
    except Exception as e:
        logger.error(f"Plugin system initialization failed: {e}")
        # Return empty loader instead of crashing
        return PluginLoader(client=client)