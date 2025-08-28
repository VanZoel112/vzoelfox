# plugin_loader.py
"""
Plugin Loader System untuk Userbot
Memuat semua plugin dari folder plugins secara otomatis
"""

import os
import sys
import importlib.util
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Setup logger
logger = logging.getLogger(__name__)

class PluginLoader:
    def __init__(self, client, plugins_dir: str = "plugins"):
        """
        Initialize Plugin Loader
        
        Args:
            client: Instance dari Pyrogram Client
            plugins_dir: Direktori tempat plugins disimpan
        """
        self.client = client
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, Any] = {}
        self.failed_plugins: Dict[str, str] = {}
        
        # Buat folder plugins jika belum ada
        self.plugins_dir.mkdir(exist_ok=True)
        
        # Buat __init__.py jika belum ada
        init_file = self.plugins_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
    
    def load_plugin(self, plugin_path: Path) -> bool:
        """
        Load single plugin dari file
        
        Args:
            plugin_path: Path ke file plugin
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            # Skip __init__.py dan file yang bukan .py
            if plugin_path.name == "__init__.py" or not plugin_path.suffix == ".py":
                return False
            
            plugin_name = plugin_path.stem
            
            # Skip jika sudah dimuat
            if plugin_name in self.loaded_plugins:
                logger.info(f"Plugin {plugin_name} sudah dimuat, skip...")
                return True
            
            # Load module secara dinamis
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}", 
                plugin_path
            )
            
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"plugins.{plugin_name}"] = module
                
                # Execute module
                spec.loader.exec_module(module)
                
                # Cek apakah ada fungsi setup_plugin (opsional)
                if hasattr(module, 'setup_plugin'):
                    module.setup_plugin(self.client)
                
                # Simpan referensi module
                self.loaded_plugins[plugin_name] = module
                
                logger.info(f"✅ Plugin '{plugin_name}' berhasil dimuat")
                return True
            
        except Exception as e:
            error_msg = f"Error loading {plugin_name}: {str(e)}\n{traceback.format_exc()}"
            self.failed_plugins[plugin_name] = error_msg
            logger.error(f"❌ Gagal memuat plugin '{plugin_name}': {e}")
            return False
        
        return False
    
    def load_all_plugins(self) -> Dict[str, Any]:
        """
        Load semua plugins dari folder plugins
        
        Returns:
            Dict berisi info plugins yang dimuat
        """
        logger.info(f"🔍 Mencari plugins di: {self.plugins_dir}")
        
        # List semua file .py di folder plugins
        plugin_files = list(self.plugins_dir.glob("*.py"))
        
        if not plugin_files:
            logger.warning("Tidak ada plugin ditemukan")
            return self.get_status()
        
        logger.info(f"📦 Ditemukan {len(plugin_files)} file plugin")
        
        # Load setiap plugin
        for plugin_file in sorted(plugin_files):
            self.load_plugin(plugin_file)
        
        return self.get_status()
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload plugin yang sudah dimuat
        
        Args:
            plugin_name: Nama plugin (tanpa .py)
            
        Returns:
            bool: True jika berhasil
        """
        try:
            # Unload dulu jika ada
            if plugin_name in self.loaded_plugins:
                self.unload_plugin(plugin_name)
            
            # Load ulang
            plugin_path = self.plugins_dir / f"{plugin_name}.py"
            if plugin_path.exists():
                return self.load_plugin(plugin_path)
            else:
                logger.error(f"Plugin {plugin_name} tidak ditemukan")
                return False
                
        except Exception as e:
            logger.error(f"Error reloading {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload plugin dari memory
        
        Args:
            plugin_name: Nama plugin
            
        Returns:
            bool: True jika berhasil
        """
        try:
            if plugin_name in self.loaded_plugins:
                # Panggil fungsi cleanup jika ada
                module = self.loaded_plugins[plugin_name]
                if hasattr(module, 'cleanup_plugin'):
                    module.cleanup_plugin(self.client)
                
                # Hapus dari loaded plugins
                del self.loaded_plugins[plugin_name]
                
                # Hapus dari sys.modules
                module_name = f"plugins.{plugin_name}"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                logger.info(f"Plugin {plugin_name} berhasil di-unload")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unloading {plugin_name}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status semua plugins
        
        Returns:
            Dict berisi info status plugins
        """
        return {
            "loaded": list(self.loaded_plugins.keys()),
            "failed": list(self.failed_plugins.keys()),
            "total_loaded": len(self.loaded_plugins),
            "total_failed": len(self.failed_plugins),
            "plugins_dir": str(self.plugins_dir.absolute())
        }
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get info detail tentang plugin
        
        Args:
            plugin_name: Nama plugin
            
        Returns:
            Dict info plugin atau None
        """
        if plugin_name in self.loaded_plugins:
            module = self.loaded_plugins[plugin_name]
            info = {
                "name": plugin_name,
                "status": "loaded",
                "path": str(self.plugins_dir / f"{plugin_name}.py"),
                "has_setup": hasattr(module, 'setup_plugin'),
                "has_cleanup": hasattr(module, 'cleanup_plugin'),
            }
            
            # Tambah info dari module jika ada
            if hasattr(module, '__version__'):
                info['version'] = module.__version__
            if hasattr(module, '__description__'):
                info['description'] = module.__description__
            if hasattr(module, '__author__'):
                info['author'] = module.__author__
                
            return info
            
        elif plugin_name in self.failed_plugins:
            return {
                "name": plugin_name,
                "status": "failed",
                "error": self.failed_plugins[plugin_name]
            }
        
        return None

# Fungsi helper untuk integrasi mudah
def setup_plugins(client, plugins_dir: str = "plugins") -> PluginLoader:
    """
    Setup dan load semua plugins
    
    Args:
        client: Pyrogram Client instance
        plugins_dir: Direktori plugins
        
    Returns:
        PluginLoader instance
    """
    loader = PluginLoader(client, plugins_dir)
    status = loader.load_all_plugins()
    
    # Log status
    logger.info("=" * 50)
    logger.info(f"📊 Plugin Loading Summary:")
    logger.info(f"✅ Loaded: {status['total_loaded']} plugins")
    if status['total_failed'] > 0:
        logger.info(f"❌ Failed: {status['total_failed']} plugins")
    logger.info("=" * 50)
    
    return loader