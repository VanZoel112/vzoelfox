# userbot by Vzoel Fox's
# plugins/__init__.py
"""
Vzoel Assistant Plugins Package
Author: Vzoel Fox's (LTPN)
"""
# plugins/__init__.py
from .vzoel_assistant import *
from .vzoel_complete import *

# Atau lebih spesifik
from .vzoel_assistant import assistant_handler
from .vzoel_complete import complete_handler

# Export semua
__all__ = ['assistant_handler', 'complete_handler']

# This file makes the plugins directory a Python package
# Required for dynamic plugin loading system

__version__ = "1.0.0"
__author__ = "Vzoel Fox's (LTPN)"
__description__ = "Dynamic plugin system for Vzoel Assistant"

# Plugin metadata
PLUGIN_SYSTEM_VERSION = "3.0.0"
SUPPORTED_PLUGINS = [
    "alive",
    "gcast", 
    "sangmata",
    "user_id"
]

# Plugin system info
print("🔌 Vzoel Assistant Plugin System Loaded")
print(f"📦 Version: {PLUGIN_SYSTEM_VERSION}")
print(f"🚀 Ready to load plugins...")
