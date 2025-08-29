#!/usr/bin/env python3
"""
Enhanced Plugin Loader System - FIXED VERSION
Compatible dengan VZOEL ASSISTANT v0.1.0.75
Author: Morgan (Enhanced for Vzoel Fox's)
"""

import os
import sys
import importlib.util
import logging
import traceback
import asyncio
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

class PluginLoader:
    def __init__(self, client=None):
        self.client = client
        self.plugins = {}
        self.loaded_plugins = []
        self.failed_plugins = []
        self.plugins_dir = None
        self.shared_functions = {}
        self.plugin_info = {}
    
    def add_shared_function(self, name: str, func: Callable):
        """Add shared function yang bisa diakses oleh semua plugins"""
        self.shared_functions[name] = func
    
    def get_status(self) -> Dict[str, int]:
        """Return plugin loading status"""
        return {
            'total_plugins': len(self.plugins) + len(self.failed_plugins),
            'total_loaded': len(self.loaded_plugins),
            'total_failed': len(self.failed_plugins)
        }
    
    def inject_dependencies(self, module):
        """Inject client dan shared functions ke plugin module"""
        try:
            # Inject client - PERBAIKAN: Set sebagai global juga
            if self.client:
                setattr(module, 'client', self.client)
                # Set as global in module dict
                if hasattr(module, '__dict__'):
                    module.__dict__['client'] = self.client
                # IMPORTANT: Set as global for decorators
                if hasattr(module, '__globals__'):
                    module.__globals__['client'] = self.client
            
            # Inject shared functions
            for func_name, func in self.shared_functions.items():
                setattr(module, func_name, func)
                if hasattr(module, '__dict__'):
                    module.__dict__[func_name] = func
                if hasattr(module, '__globals__'):
                    module.__globals__[func_name] = func
            
            logger.debug(f"Dependencies injected successfully to {module.__name__ if hasattr(module, '__name__') else 'unknown'}")
            
        except Exception as e:
            logger.error(f"Error injecting dependencies: {e}")
    
    def load_plugin(self, plugin_name: str, plugin_path: str) -> bool:
        """Load individual plugin dengan dependency injection"""
        try:
            # Check if file exists
            if not os.path.exists(plugin_path):
                raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create spec for {plugin_name}")
            
            # Create module from spec
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to prevent import issues
            sys.modules[f"plugin_{plugin_name}"] = module
            
            # PERBAIKAN CRITICAL: Set client sebagai global untuk plugin
            if self.client:
                # Set in module namespace sebelum execution
                setattr(module, 'client', self.client)
                
                # Set as global using sys.modules approach
                original_builtins = None
                try:
                    import builtins
                    if not hasattr(builtins, 'client'):
                        builtins.client = self.client
                        original_builtins = True
                except Exception:
                    pass
            
            # Execute module dengan client tersedia
            spec.loader.exec_module(module)
            
            # Clean up builtins to avoid pollution  
            try:
                import builtins
                if original_builtins and hasattr(builtins, 'client'):
                    delattr(builtins, 'client')
            except Exception:
                pass
            
            # Inject other dependencies
            self.inject_dependencies(module)
            
            # PERBAIKAN: Call setup function for plugins that use it
            if hasattr(module, 'setup'):
                try:
                    setup_result = module.setup(self.client)
                    if asyncio.iscoroutine(setup_result):
                        logger.warning(f"Plugin {plugin_name} has async setup - consider using sync setup")
                    logger.info(f"✅ Plugin {plugin_name} setup completed")
                except Exception as setup_error:
                    logger.error(f"Plugin {plugin_name} setup error: {setup_error}")
            
            # Call plugin initialization if exists (legacy support)
            elif hasattr(module, 'initialize_plugin'):
                try:
                    init_result = module.initialize_plugin()
                    if asyncio.iscoroutine(init_result):
                        logger.warning(f"Plugin {plugin_name} has async initialization - skipping for now")
                except Exception as init_error:
                    logger.warning(f"Plugin {plugin_name} initialization error: {init_error}")
            
            # For plugins without setup function, event handlers should already be registered via decorators
            
            # Get plugin info if available
            if hasattr(module, 'get_plugin_info'):
                try:
                    self.plugin_info[plugin_name] = module.get_plugin_info()
                except Exception as info_error:
                    logger.warning(f"Error getting plugin info for {plugin_name}: {info_error}")
            
            # Store plugin
            self.plugins[plugin_name] = module
            self.loaded_plugins.append(plugin_name)
            
            logger.info(f"✅ Plugin loaded successfully: {plugin_name}")
            return True
            
        except Exception as e:
            self.failed_plugins.append(plugin_name)
            logger.error(f"❌ Failed to load plugin {plugin_name}: {e}")
            logger.debug(f"Plugin {plugin_name} traceback: {traceback.format_exc()}")
            return False
    
    def load_all_plugins(self, plugins_dir: str) -> Dict[str, Any]:
        """Load all plugins from directory dengan enhanced error handling"""
        self.plugins_dir = plugins_dir
        results = {
            'loaded': [],
            'failed': [],
            'total': 0,
            'errors': {}
        }
        
        # Create plugins directory if not exists
        Path(plugins_dir).mkdir(exist_ok=True)
        
        # Find all Python files
        try:
            plugin_files = []
            for file_path in Path(plugins_dir).glob("*.py"):
                if not file_path.name.startswith('__'):
                    plugin_files.append(file_path)
            
            results['total'] = len(plugin_files)
            
            if not plugin_files:
                logger.info(f"No plugins found in {plugins_dir}")
                return results
            
            # Load each plugin
            for plugin_file in plugin_files:
                plugin_name = plugin_file.stem  # filename without extension
                plugin_path = str(plugin_file.absolute())
                
                logger.info(f"Loading plugin: {plugin_name}")
                
                try:
                    if self.load_plugin(plugin_name, plugin_path):
                        results['loaded'].append(plugin_name)
                    else:
                        results['failed'].append(plugin_name)
                        results['errors'][plugin_name] = "Load failed (check logs)"
                        
                except Exception as e:
                    results['failed'].append(plugin_name)
                    results['errors'][plugin_name] = str(e)
                    logger.error(f"Exception loading {plugin_name}: {e}")
            
            # Summary
            logger.info(f"Plugin loading complete: {len(results['loaded'])}/{results['total']} loaded successfully")
            if results['failed']:
                logger.warning(f"Failed plugins: {', '.join(results['failed'])}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error scanning plugins directory: {e}")
            return results
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload specific plugin dengan cleanup"""
        try:
            if plugin_name in self.plugins:
                # Call cleanup if exists
                module = self.plugins[plugin_name]
                if hasattr(module, 'cleanup_plugin'):
                    try:
                        cleanup_result = module.cleanup_plugin()
                        if asyncio.iscoroutine(cleanup_result):
                            logger.warning(f"Plugin {plugin_name} has async cleanup - skipping")
                    except Exception as cleanup_error:
                        logger.warning(f"Plugin {plugin_name} cleanup error: {cleanup_error}")
                
                # Remove from sys.modules
                sys_module_name = f"plugin_{plugin_name}"
                if sys_module_name in sys.modules:
                    del sys.modules[sys_module_name]
                
                # Remove from our tracking
                del self.plugins[plugin_name]
                if plugin_name in self.loaded_plugins:
                    self.loaded_plugins.remove(plugin_name)
                if plugin_name in self.plugin_info:
                    del self.plugin_info[plugin_name]
                
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
            if os.path.exists(plugin_path):
                logger.info(f"Reloading plugin: {plugin_name}")
                self.unload_plugin(plugin_name)
                return self.load_plugin(plugin_name, plugin_path)
        return False
    
    def get_plugin(self, plugin_name: str):
        """Get loaded plugin by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, List[str]]:
        """List all plugins by status dengan info tambahan"""
        return {
            'loaded': self.loaded_plugins.copy(),
            'failed': self.failed_plugins.copy(),
            'all': list(self.plugins.keys()),
            'info': self.plugin_info.copy()
        }
    
    def get_plugin_commands(self) -> Dict[str, List[str]]:
        """Get all commands dari loaded plugins"""
        commands = {}
        for plugin_name, plugin_info in self.plugin_info.items():
            if isinstance(plugin_info, dict) and 'commands' in plugin_info:
                commands[plugin_name] = plugin_info['commands']
        return commands
    
    def cleanup_all_plugins(self):
        """Cleanup all loaded plugins"""
        for plugin_name in self.loaded_plugins.copy():
            self.unload_plugin(plugin_name)


def setup_plugins(client, plugins_dir: str = "plugins") -> PluginLoader:
    """
    FIXED: Setup and initialize plugin system dengan proper dependency injection
    
    Args:
        client: Telegram client instance (FIXED: not 'app')
        plugins_dir: Directory containing plugin files
    
    Returns:
        PluginLoader instance
    """
    try:
        logger.info("🔌 Initializing enhanced plugin system...")
        
        # Create loader dengan client
        loader = PluginLoader(client=client)
        
        # Add shared functions yang sering digunakan plugins
        # Ini memungkinkan plugins untuk mengakses functions dari main.py
        shared_funcs = [
            'convert_font', 'get_emoji', 'create_premium_entities', 'safe_send_with_entities',
            'is_owner', 'apply_rate_limit', 'safe_edit_message', 'check_premium_status'
        ]
        
        # Import functions dari main module jika available
        try:
            main_module = sys.modules.get('__main__')
            if main_module:
                for func_name in shared_funcs:
                    if hasattr(main_module, func_name):
                        loader.add_shared_function(func_name, getattr(main_module, func_name))
                        logger.debug(f"Added shared function: {func_name}")
        except Exception as func_error:
            logger.warning(f"Could not add some shared functions: {func_error}")
        
        # Load all plugins
        results = loader.load_all_plugins(plugins_dir)
        
        # Enhanced logging
        logger.info("🔌 Plugin system initialization complete:")
        logger.info(f"   📁 Plugin directory: {plugins_dir}")
        logger.info(f"   📊 Total found: {results['total']}")
        logger.info(f"   ✅ Successfully loaded: {len(results['loaded'])}")
        logger.info(f"   ❌ Failed to load: {len(results['failed'])}")
        
        if results['loaded']:
            logger.info(f"   🎯 Loaded plugins: {', '.join(results['loaded'])}")
        
        if results['failed']:
            logger.warning(f"   ⚠️ Failed plugins: {', '.join(results['failed'])}")
            # Show error details
            for plugin, error in results.get('errors', {}).items():
                logger.warning(f"      - {plugin}: {error}")
        
        # Show available commands
        commands = loader.get_plugin_commands()
        if commands:
            logger.info("   🎮 Available plugin commands:")
            for plugin_name, plugin_commands in commands.items():
                if plugin_commands:
                    logger.info(f"      - {plugin_name}: {', '.join(plugin_commands)}")
        
        return loader
        
    except Exception as e:
        logger.error(f"❌ Plugin system initialization failed: {e}")
        logger.debug(f"Plugin system error traceback: {traceback.format_exc()}")
        # Return empty loader untuk prevent crashes
        return PluginLoader(client=client)