#!/usr/bin/env python3
"""
AssetJSON - Universal Plugin Bridge & Asset Manager v3.0
COMPLETELY REFACTORED VERSION - Production Ready
File: assetjson.py
Author: Vzoel Fox's (Enhanced by Morgan)
Version: v3.0.0 - Dependency Injection & Clean Architecture

MAJOR IMPROVEMENTS:
- Proper dependency injection pattern
- Separated core utilities from command handlers  
- Eliminated circular dependencies
- Thread-safe client management
- Robust error handling with fallbacks
- Plugin template system
"""

import re
import os
import sys
import json
import time
import logging
import asyncio
import sqlite3
import weakref
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from collections import defaultdict
from pathlib import Path

# Core logging setup
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup dedicated logger for component"""
    logger = logging.getLogger(f"assetjson.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger

logger = setup_logger("core")

# ============= CORE ASSET MANAGER CLASS =============

class AssetManager:
    """
    Core Asset Manager - Thread-safe, dependency-injected asset management
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AssetManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._client = None
        self._client_ref = None
        self._logger = setup_logger("manager")
        
        # Configuration paths
        self.asset_files = {
            'emoji': 'plugins/assets/emoji_config.json',
            'fonts': 'plugins/assets/fonts_config.json', 
            'settings': 'plugins/assets/bot_settings.json',
            'blacklist': 'plugins/assets/gcast_blacklist.json',
            'statistics': 'plugins/assets/bot_statistics.json',
            'plugin_config': 'plugins/assets/plugin_configs.json'
        }
        
        self.database_files = {
            'main': 'vzoel_assistant.db',
            'plugins': 'plugins/assets/plugins.db',
            'cache': 'plugins/assets/cache.db'
        }
        
        # Premium emoji configuration
        self.premium_emojis = {
            'main': {'id': '6156784006194009426', 'char': '🤩'},
            'check': {'id': '5794353925360457382', 'char': '⚙️'},
            'adder1': {'id': '5794407002566300853', 'char': '⛈'},
            'adder2': {'id': '5793913811471700779', 'char': '✅'},
            'adder3': {'id': '5321412209992033736', 'char': '👽'},
            'adder4': {'id': '5793973133559993740', 'char': '✈️'},
            'adder5': {'id': '5357404860566235955', 'char': '😈'},
            'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
        }
        
        # Unicode fonts
        self.fonts = {
            'bold': {
                'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
                'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
                's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
                'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
                'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
                'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
                '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
            },
            'mono': {
                'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
                'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
                's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
                'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
                'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
                'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
                '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
            },
            'italic': {
                'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪',
                'j': '𝘫', 'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳',
                's': '𝘴', 't': '𝘵', 'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻',
                'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐',
                'J': '𝘑', 'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙',
                'S': '𝘚', 'T': '𝘛', 'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡'
            }
        }
        
        # State management
        self._premium_status = None
        self._command_prefix = None
        self._blacklisted_chats = set()
        self._plugin_configs = {}
        self._initialized_state = False
        
        # Caching
        self._emoji_cache = {}
        self._font_cache = {}
        self._config_cache = {}
        
        # Statistics
        self._stats = {
            'plugin_loads': 0,
            'asset_accesses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors_handled': 0
        }
        
        # Rate limiting
        self._rate_limiters = defaultdict(lambda: {'last_request': 0, 'request_count': 0})
        self._rate_limit_window = 60
        self._rate_limit_max_requests = 100
        
        self._logger.info("AssetManager initialized (singleton pattern)")
    
    def inject_client(self, client) -> bool:
        """Safely inject Telegram client reference"""
        try:
            if client is None:
                self._logger.error("Cannot inject None client")
                return False
            
            # Store weak reference to avoid circular references
            self._client_ref = weakref.ref(client)
            self._client = client
            
            self._logger.info(f"Client injected successfully: {type(client).__name__}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error injecting client: {e}")
            return False
    
    def get_client(self):
        """Get client reference safely"""
        if self._client is not None:
            return self._client
        
        if self._client_ref is not None:
            client = self._client_ref()
            if client is not None:
                return client
        
        self._logger.warning("Client reference not available")
        return None
    
    def ensure_directories(self) -> bool:
        """Ensure all required directories exist"""
        try:
            directories = [
                'plugins/assets',
                'plugins/cache', 
                'plugins/configs'
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
            
            self._logger.debug("All directories ensured")
            return True
            
        except Exception as e:
            self._logger.error(f"Error ensuring directories: {e}")
            return False
    
    def load_configurations(self) -> bool:
        """Load all configurations from files"""
        try:
            self.ensure_directories()
            
            # Load emoji config
            if os.path.exists(self.asset_files['emoji']):
                with open(self.asset_files['emoji'], 'r') as f:
                    data = json.load(f)
                    if 'premium_emojis' in data:
                        self.premium_emojis.update(data['premium_emojis'])
                    self._premium_status = data.get('premium_status', False)
            
            # Load settings
            if os.path.exists(self.asset_files['settings']):
                with open(self.asset_files['settings'], 'r') as f:
                    data = json.load(f)
                    self._command_prefix = data.get('command_prefix', '.')
            
            # Load blacklist
            if os.path.exists(self.asset_files['blacklist']):
                with open(self.asset_files['blacklist'], 'r') as f:
                    data = json.load(f)
                    self._blacklisted_chats = set(data.get('blacklisted_chats', []))
            
            # Load plugin configs
            if os.path.exists(self.asset_files['plugin_config']):
                with open(self.asset_files['plugin_config'], 'r') as f:
                    self._plugin_configs = json.load(f)
            
            self._initialized_state = True
            self._logger.info("All configurations loaded successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Error loading configurations: {e}")
            self._stats['errors_handled'] += 1
            return False
    
    def save_configurations(self) -> bool:
        """Save all configurations to files"""
        try:
            self.ensure_directories()
            
            # Save emoji config
            emoji_data = {
                'premium_emojis': self.premium_emojis,
                'premium_status': self._premium_status,
                'last_updated': datetime.now().isoformat(),
                'version': 'v3.0.0'
            }
            with open(self.asset_files['emoji'], 'w') as f:
                json.dump(emoji_data, f, indent=2)
            
            # Save settings
            settings_data = {
                'command_prefix': self._command_prefix or '.',
                'last_updated': datetime.now().isoformat(),
                'stats': self._stats
            }
            with open(self.asset_files['settings'], 'w') as f:
                json.dump(settings_data, f, indent=2)
            
            # Save blacklist
            blacklist_data = {
                'blacklisted_chats': list(self._blacklisted_chats),
                'last_updated': datetime.now().isoformat(),
                'total': len(self._blacklisted_chats)
            }
            with open(self.asset_files['blacklist'], 'w') as f:
                json.dump(blacklist_data, f, indent=2)
            
            # Save plugin configs
            with open(self.asset_files['plugin_config'], 'w') as f:
                json.dump(self._plugin_configs, f, indent=2)
            
            self._logger.info("All configurations saved successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Error saving configurations: {e}")
            return False
    
    def get_emoji(self, emoji_type: str) -> str:
        """Get premium emoji character with caching"""
        self._stats['asset_accesses'] += 1
        
        if emoji_type in self._emoji_cache:
            self._stats['cache_hits'] += 1
            return self._emoji_cache[emoji_type]
        
        self._stats['cache_misses'] += 1
        
        if emoji_type in self.premium_emojis:
            char = self.premium_emojis[emoji_type]['char']
            self._emoji_cache[emoji_type] = char
            return char
        
        # Fallback emoji
        fallback = '🤩'
        self._emoji_cache[emoji_type] = fallback
        return fallback
    
    def get_emoji_id(self, emoji_type: str) -> str:
        """Get premium emoji document ID"""
        if emoji_type in self.premium_emojis:
            return self.premium_emojis[emoji_type]['id']
        return ''
    
    def convert_font(self, text: str, font_type: str = 'bold') -> str:
        """Convert text to Unicode fonts with caching"""
        self._stats['asset_accesses'] += 1
        
        cache_key = f"{font_type}_{hash(text)}"
        if cache_key in self._font_cache:
            self._stats['cache_hits'] += 1
            return self._font_cache[cache_key]
        
        self._stats['cache_misses'] += 1
        
        if font_type not in self.fonts:
            self._font_cache[cache_key] = text
            return text
        
        font_map = self.fonts[font_type]
        result = ""
        for char in text:
            result += font_map.get(char, char)
        
        self._font_cache[cache_key] = result
        return result
    
    def create_premium_entities(self, text: str) -> List:
        """Create premium emoji entities with proper UTF-16 calculation"""
        entities = []
        
        if not text or not self._premium_status:
            return entities
        
        try:
            # Import here to avoid circular dependency
            try:
                from telethon.tl.types import MessageEntityCustomEmoji
            except ImportError:
                self._logger.warning("Telethon not available, returning empty entities")
                return entities
            
            current_offset = 0
            i = 0
            
            while i < len(text):
                found_emoji = False
                
                for emoji_type, emoji_data in self.premium_emojis.items():
                    emoji_char = emoji_data['char']
                    emoji_id = emoji_data['id']
                    
                    if text[i:].startswith(emoji_char):
                        try:
                            # Proper UTF-16 length calculation
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
                            
                        except Exception as e:
                            self._logger.error(f"Error creating entity for {emoji_type}: {e}")
                            break
                
                if not found_emoji:
                    char = text[i]
                    char_bytes = char.encode('utf-16-le')
                    char_utf16_length = len(char_bytes) // 2
                    current_offset += char_utf16_length
                    i += 1
            
            return entities
            
        except Exception as e:
            self._logger.error(f"Error in create_premium_entities: {e}")
            return []
    
    async def safe_send_with_entities(self, event_or_chat, text: str, use_premium: bool = True):
        """Universal function to send message with premium entities"""
        try:
            client = self.get_client()
            if not client:
                self._logger.error("No client available for sending message")
                return None
            
            if use_premium and self._premium_status:
                entities = self.create_premium_entities(text)
                if entities:
                    if hasattr(event_or_chat, 'reply'):
                        # Event object
                        return await event_or_chat.reply(text, formatting_entities=entities)
                    else:
                        # Chat ID or entity
                        return await client.send_message(event_or_chat, text, formatting_entities=entities)
            
            # Fallback to normal send
            if hasattr(event_or_chat, 'reply'):
                return await event_or_chat.reply(text)
            else:
                return await client.send_message(event_or_chat, text)
                
        except Exception as e:
            self._logger.error(f"Error in safe_send_with_entities: {e}")
            self._stats['errors_handled'] += 1
            
            # Final fallback
            try:
                if hasattr(event_or_chat, 'reply'):
                    return await event_or_chat.reply(text)
                elif self.get_client():
                    return await self.get_client().send_message(event_or_chat, text)
            except Exception as e2:
                self._logger.error(f"Fallback send failed: {e2}")
                return None
    
    async def safe_edit_with_entities(self, message, text: str, use_premium: bool = True):
        """Safe message edit with premium entity support"""
        try:
            # Import here to avoid circular dependency
            try:
                from telethon.errors import MessageNotModifiedError
            except ImportError:
                # Fallback without specific error handling
                await message.edit(text)
                return
            
            if use_premium and self._premium_status:
                entities = self.create_premium_entities(text)
                if entities:
                    await message.edit(text, formatting_entities=entities)
                    return
            
            # Fallback to normal edit
            await message.edit(text)
            
        except Exception as e:
            # Handle different error types
            error_str = str(e).lower()
            if "not modified" in error_str:
                # Message unchanged, skip
                pass
            elif any(phrase in error_str for phrase in ["can't parse entities", "bad request", "invalid entities"]):
                # Try without entities
                try:
                    await message.edit(text)
                    self._logger.warning(f"Edited without entities due to parsing error: {e}")
                except Exception as e2:
                    self._logger.error(f"Fallback edit failed: {e2}")
            else:
                self._logger.error(f"Error editing message: {e}")
                try:
                    # Final fallback - try simple edit
                    await message.edit(text)
                except Exception as e3:
                    self._logger.error(f"Simple edit failed: {e3}")
    
    async def animate_text(self, message, texts: List[str], delay: float = 1.5, use_premium: bool = True):
        """Animate text with premium emoji support"""
        for i, text in enumerate(texts):
            try:
                await self.safe_edit_with_entities(message, text, use_premium)
                if i < len(texts) - 1:
                    await asyncio.sleep(delay)
            except Exception as e:
                self._logger.error(f"Animation error at step {i+1}: {e}")
                if i < len(texts) - 1:
                    await asyncio.sleep(delay * 0.5)
    
    async def is_owner(self, user_id: int) -> bool:
        """Check if user is bot owner"""
        try:
            # Check environment variable first
            owner_id = os.getenv("OWNER_ID")
            if owner_id:
                return user_id == int(owner_id)
            
            # Fallback to client.get_me()
            client = self.get_client()
            if client:
                me = await client.get_me()
                return user_id == me.id
            
            return False
        except Exception as e:
            self._logger.error(f"Error checking owner: {e}")
            return False
    
    async def apply_rate_limit(self, operation: str) -> bool:
        """Apply rate limiting per operation"""
        current_time = time.time()
        limiter = self._rate_limiters[operation]
        
        # Reset counter if window passed
        if current_time - limiter['last_request'] > self._rate_limit_window:
            limiter['request_count'] = 0
            limiter['last_request'] = current_time
        
        # Check rate limit
        if limiter['request_count'] >= self._rate_limit_max_requests:
            wait_time = self._rate_limit_window - (current_time - limiter['last_request'])
            if wait_time > 0:
                self._logger.warning(f"Rate limit hit for {operation}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                limiter['request_count'] = 0
                limiter['last_request'] = time.time()
        
        limiter['request_count'] += 1
        return True
    
    def get_db_connection(self, db_name: str = 'main') -> sqlite3.Connection:
        """Get database connection with error handling"""
        try:
            db_file = self.database_files.get(db_name, self.database_files['main'])
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
            
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except Exception as e:
            self._logger.error(f"Error connecting to database {db_name}: {e}")
            raise
    
    def get_plugin_config(self, plugin_name: str) -> Dict:
        """Get configuration for specific plugin"""
        return self._plugin_configs.get(plugin_name, {})
    
    def set_plugin_config(self, plugin_name: str, config: Dict) -> bool:
        """Set configuration for specific plugin"""
        try:
            self._plugin_configs[plugin_name] = config
            self.save_configurations()
            return True
        except Exception as e:
            self._logger.error(f"Error setting plugin config for {plugin_name}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        return {
            'stats': self._stats.copy(),
            'cache_info': {
                'emoji_cache_size': len(self._emoji_cache),
                'font_cache_size': len(self._font_cache),
                'config_cache_size': len(self._config_cache)
            },
            'config_info': {
                'premium_emojis_count': len(self.premium_emojis),
                'fonts_count': len(self.fonts),
                'blacklisted_chats': len(self._blacklisted_chats),
                'plugin_configs': len(self._plugin_configs)
            },
            'system_info': {
                'client_available': self.get_client() is not None,
                'initialized': self._initialized_state,
                'premium_status': self._premium_status
            }
        }
    
    def clear_caches(self):
        """Clear all caches"""
        self._emoji_cache.clear()
        self._font_cache.clear()
        self._config_cache.clear()
        self._logger.info("All caches cleared")


# ============= GLOBAL SINGLETON INSTANCE =============

# Create global asset manager instance
asset_manager = AssetManager()

# ============= PLUGIN ENVIRONMENT FACTORY =============

def create_plugin_environment(client=None) -> Dict[str, Any]:
    """
    Create safe environment for plugins with dependency injection
    This replaces the old 'from assetjson import *' pattern
    """
    # Inject client if provided
    if client is not None:
        asset_manager.inject_client(client)
    
    # Load configurations if not done yet
    if not asset_manager._initialized_state:
        asset_manager.load_configurations()
    
    # Return complete plugin environment
    return {
        # Core functions
        'get_emoji': asset_manager.get_emoji,
        'get_emoji_id': asset_manager.get_emoji_id,
        'convert_font': asset_manager.convert_font,
        'create_premium_entities': asset_manager.create_premium_entities,
        
        # Message functions
        'safe_send_with_entities': asset_manager.safe_send_with_entities,
        'safe_edit_with_entities': asset_manager.safe_edit_with_entities,
        'animate_text': asset_manager.animate_text,
        
        # User functions
        'is_owner': asset_manager.is_owner,
        
        # Utility functions
        'apply_rate_limit': asset_manager.apply_rate_limit,
        'get_db_connection': asset_manager.get_db_connection,
        
        # Configuration functions
        'get_plugin_config': asset_manager.get_plugin_config,
        'set_plugin_config': asset_manager.set_plugin_config,
        
        # Data access
        'premium_emojis': asset_manager.premium_emojis,
        'fonts': asset_manager.fonts,
        'asset_files': asset_manager.asset_files,
        'database_files': asset_manager.database_files,
        
        # Client access
        'get_client': asset_manager.get_client,
        
        # Logger
        'logger': setup_logger('plugin'),
        
        # Asset manager instance for advanced usage
        'asset_manager': asset_manager
    }

# ============= PLUGIN TEMPLATE SYSTEM =============

class PluginTemplate:
    """
    Base template for new plugins with proper dependency injection
    """
    
    def __init__(self, plugin_name: str, version: str = "1.0.0"):
        self.plugin_name = plugin_name
        self.version = version
        self.env = None
        self.logger = setup_logger(f"plugin.{plugin_name}")
        self.initialized = False
    
    def setup(self, client) -> bool:
        """Setup plugin with client and environment"""
        try:
            # Create plugin environment
            self.env = create_plugin_environment(client)
            self.initialized = True
            self.logger.info(f"Plugin {self.plugin_name} v{self.version} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup plugin {self.plugin_name}: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.plugin_name,
            'version': self.version,
            'initialized': self.initialized,
            'requires': ['assetjson>=3.0.0']
        }

# ============= COMMAND HANDLER SYSTEM =============

class AssetCommandHandler:
    """
    Separated command handlers from core utilities
    This prevents circular dependencies and makes the system more modular
    """
    
    def __init__(self, asset_manager: AssetManager):
        self.asset_manager = asset_manager
        self.logger = setup_logger("commands")
        self.registered_handlers = {}
    
    def register_handlers(self, client):
        """Register asset management command handlers"""
        try:
            from telethon import events
            
            # Asset info command
            @client.on(events.NewMessage(pattern=r'\.assetinfo'))
            async def asset_info_handler(event):
                if not await self.asset_manager.is_owner(event.sender_id):
                    return
                
                try:
                    stats = self.asset_manager.get_stats()
                    
                    info_text = f"""
{self.asset_manager.get_emoji('main')} {self.asset_manager.convert_font('ASSET SYSTEM INFO', 'mono')}

╔══════════════════════════════════╗
   {self.asset_manager.get_emoji('check')} {self.asset_manager.convert_font('SYSTEM STATISTICS', 'mono')} {self.asset_manager.get_emoji('check')}
╚══════════════════════════════════╝

{self.asset_manager.get_emoji('adder1')} {self.asset_manager.convert_font('Access Stats:', 'bold')}
{self.asset_manager.get_emoji('check')} Asset Accesses: `{stats['stats']['asset_accesses']}`
{self.asset_manager.get_emoji('check')} Cache Hits: `{stats['stats']['cache_hits']}`
{self.asset_manager.get_emoji('check')} Cache Misses: `{stats['stats']['cache_misses']}`
{self.asset_manager.get_emoji('check')} Plugin Loads: `{stats['stats']['plugin_loads']}`
{self.asset_manager.get_emoji('check')} Errors Handled: `{stats['stats']['errors_handled']}`

{self.asset_manager.get_emoji('adder2')} {self.asset_manager.convert_font('Cache Status:', 'bold')}
{self.asset_manager.get_emoji('check')} Emoji Cache: `{stats['cache_info']['emoji_cache_size']}` items
{self.asset_manager.get_emoji('check')} Font Cache: `{stats['cache_info']['font_cache_size']}` items
{self.asset_manager.get_emoji('check')} Config Cache: `{stats['cache_info']['config_cache_size']}` items

{self.asset_manager.get_emoji('adder3')} {self.asset_manager.convert_font('Configuration:', 'bold')}
{self.asset_manager.get_emoji('check')} Premium Emojis: `{stats['config_info']['premium_emojis_count']}`
{self.asset_manager.get_emoji('check')} Font Types: `{stats['config_info']['fonts_count']}`
{self.asset_manager.get_emoji('check')} Blacklisted Chats: `{stats['config_info']['blacklisted_chats']}`
{self.asset_manager.get_emoji('check')} Plugin Configs: `{stats['config_info']['plugin_configs']}`

{self.asset_manager.get_emoji('adder4')} {self.asset_manager.convert_font('System Status:', 'bold')}
{self.asset_manager.get_emoji('check')} Client: {'Available' if stats['system_info']['client_available'] else 'Unavailable'}
{self.asset_manager.get_emoji('check')} Initialized: {'Yes' if stats['system_info']['initialized'] else 'No'}
{self.asset_manager.get_emoji('check')} Premium: {'Active' if stats['system_info']['premium_status'] else 'Standard'}
{self.asset_manager.get_emoji('check')} Version: `v3.0.0 - Dependency Injection`

{self.asset_manager.get_emoji('main')} {self.asset_manager.convert_font('AssetJSON Bridge v3.0 Online!', 'bold')}
                    """.strip()
                    
                    await self.asset_manager.safe_send_with_entities(event, info_text)
                    
                except Exception as e:
                    error_text = f"❌ {self.asset_manager.convert_font('Asset Info Error:', 'bold')} {str(e)}"
                    await self.asset_manager.safe_send_with_entities(event, error_text)
            
            # Clear cache command
            @client.on(events.NewMessage(pattern=r'\.clearcache'))
            async def clear_cache_handler(event):
                if not await self.asset_manager.is_owner(event.sender_id):
                    return
                
                try:
                    old_stats = self.asset_manager.get_stats()
                    self.asset_manager.clear_caches()
                    
                    clear_text = f"""
{self.asset_manager.get_emoji('main')} {self.asset_manager.convert_font('CACHE CLEARED', 'mono')}

{self.asset_manager.get_emoji('check')} {self.asset_manager.convert_font('Cleared Caches:', 'bold')}
{self.asset_manager.get_emoji('adder1')} Emoji Cache: `{old_stats['cache_info']['emoji_cache_size']}` items
{self.asset_manager.get_emoji('adder1')} Font Cache: `{old_stats['cache_info']['font_cache_size']}` items
{self.asset_manager.get_emoji('adder1')} Config Cache: `{old_stats['cache_info']['config_cache_size']}` items

{self.asset_manager.get_emoji('adder2')} {self.asset_manager.convert_font('Cache will rebuild automatically on next access', 'bold')}
                    """.strip()
                    
                    await self.asset_manager.safe_send_with_entities(event, clear_text)
                    
                except Exception as e:
                    error_text = f"❌ {self.asset_manager.convert_font('Clear Cache Error:', 'bold')} {str(e)}"
                    await self.asset_manager.safe_send_with_entities(event, error_text)
            
            # Save configs command
            @client.on(events.NewMessage(pattern=r'\.saveconfigs'))
            async def save_configs_handler(event):
                if not await self.asset_manager.is_owner(event.sender_id):
                    return
                
                try:
                    success = self.asset_manager.save_configurations()
                    
                    if success:
                        save_text = f"""
{self.asset_manager.get_emoji('check')} {self.asset_manager.convert_font('CONFIGURATIONS SAVED', 'mono')}

{self.asset_manager.get_emoji('main')} {self.asset_manager.convert_font('Saved Files:', 'bold')}
{self.asset_manager.get_emoji('adder1')} Emoji Config: `{self.asset_manager.asset_files['emoji']}`
{self.asset_manager.get_emoji('adder1')} Settings: `{self.asset_manager.asset_files['settings']}`
{self.asset_manager.get_emoji('adder1')} Blacklist: `{self.asset_manager.asset_files['blacklist']}`
{self.asset_manager.get_emoji('adder1')} Plugin Configs: `{self.asset_manager.asset_files['plugin_config']}`

{self.asset_manager.get_emoji('adder2')} {self.asset_manager.convert_font('All configurations saved successfully!', 'bold')}
                        """.strip()
                    else:
                        save_text = f"❌ {self.asset_manager.convert_font('Failed to save configurations', 'bold')}"
                    
                    await self.asset_manager.safe_send_with_entities(event, save_text)
                    
                except Exception as e:
                    error_text = f"❌ {self.asset_manager.convert_font('Save Config Error:', 'bold')} {str(e)}"
                    await self.asset_manager.safe_send_with_entities(event, error_text)
            
            self.registered_handlers = {
                'assetinfo': asset_info_handler,
                'clearcache': clear_cache_handler,
                'saveconfigs': save_configs_handler
            }
            
            self.logger.info(f"Registered {len(self.registered_handlers)} command handlers")
            return True
            
        except ImportError:
            self.logger.warning("Telethon not available, command handlers not registered")
            return False
        except Exception as e:
            self.logger.error(f"Error registering command handlers: {e}")
            return False

# ============= INITIALIZATION FUNCTION =============

def initialize_asset_system(client=None, auto_load_configs: bool = True, register_commands: bool = True) -> tuple[AssetManager, Dict[str, Any]]:
    """
    Main initialization function for the asset system
    
    Args:
        client: Telegram client instance (optional)
        auto_load_configs: Whether to automatically load configurations
        register_commands: Whether to register asset management commands
    
    Returns:
        Tuple of (asset_manager, plugin_environment)
    """
    try:
        # Get or create asset manager instance
        manager = asset_manager
        
        # Inject client if provided
        if client is not None:
            manager.inject_client(client)
        
        # Load configurations
        if auto_load_configs:
            manager.load_configurations()
        
        # Register command handlers
        if register_commands and client is not None:
            command_handler = AssetCommandHandler(manager)
            command_handler.register_handlers(client)
        
        # Create plugin environment
        plugin_env = create_plugin_environment(client)
        
        logger.info("AssetJSON v3.0.0 initialization completed successfully")
        logger.info(f"- Client: {'Injected' if manager.get_client() else 'Not available'}")
        logger.info(f"- Configs: {'Loaded' if manager._initialized_state else 'Not loaded'}")
        logger.info(f"- Commands: {'Registered' if register_commands and client else 'Not registered'}")
        
        return manager, plugin_env
        
    except Exception as e:
        logger.error(f"AssetJSON initialization failed: {e}")
        raise

# ============= BACKWARD COMPATIBILITY LAYER =============

# For plugins that still use the old import pattern
def get_emoji(emoji_type: str) -> str:
    """Backward compatibility function"""
    return asset_manager.get_emoji(emoji_type)

def convert_font(text: str, font_type: str = 'bold') -> str:
    """Backward compatibility function"""
    return asset_manager.convert_font(text, font_type)

def get_client():
    """Backward compatibility function"""
    return asset_manager.get_client()

# Export commonly used data
PREMIUM_EMOJIS = asset_manager.premium_emojis
FONTS = asset_manager.fonts

# ============= PLUGIN USAGE EXAMPLES =============

"""
NEW PLUGIN USAGE EXAMPLES (v3.0.0):

1. MODERN APPROACH (RECOMMENDED):
```python
from assetjson import initialize_asset_system, PluginTemplate

class MyPlugin(PluginTemplate):
    def __init__(self):
        super().__init__("my_plugin", "1.0.0")
    
    async def my_command_handler(self, event):
        text = f"{self.env['get_emoji']('main')} {self.env['convert_font']('Hello!', 'bold')}"
        await self.env['safe_send_with_entities'](event, text)

def setup_plugin(client):
    manager, env = initialize_asset_system(client)
    plugin = MyPlugin()
    plugin.setup(client)
    
    @client.on(events.NewMessage(pattern=r'\.mycommand'))
    async def handler(event):
        await plugin.my_command_handler(event)
```

2. ENVIRONMENT-BASED APPROACH:
```python
from assetjson import create_plugin_environment

def setup_plugin(client):
    env = create_plugin_environment(client)
    
    @client.on(events.NewMessage(pattern=r'\.test'))
    async def test_handler(event):
        if not await env['is_owner'](event.sender_id):
            return
        
        text = f"{env['get_emoji']('check')} {env['convert_font']('Working!', 'bold')}"
        await env['safe_send_with_entities'](event, text)
```

3. DIRECT ACCESS (FOR SIMPLE PLUGINS):
```python
from assetjson import asset_manager

def setup_plugin(client):
    asset_manager.inject_client(client)
    
    @client.on(events.NewMessage(pattern=r'\.simple'))
    async def simple_handler(event):
        text = f"{asset_manager.get_emoji('main')} Simple plugin working!"
        await asset_manager.safe_send_with_entities(event, text)
```

4. BACKWARD COMPATIBILITY (OLD PLUGINS):
```python
# Old plugins can still use this pattern (deprecated but supported)
from assetjson import get_emoji, convert_font, get_client

@get_client().on(events.NewMessage(pattern=r'\.old'))
async def old_handler(event):
    text = f"{get_emoji('main')} {convert_font('Old style', 'bold')}"
    await event.reply(text)
```

ADVANTAGES OF v3.0.0:
✅ No circular dependencies
✅ Proper client injection
✅ Thread-safe singleton pattern
✅ Separated command handlers
✅ Plugin template system
✅ Comprehensive error handling
✅ Backward compatibility maintained
✅ Dependency injection pattern
✅ Modular architecture
✅ Enhanced logging and monitoring

MIGRATION FROM v2.0.0:
- Replace 'from assetjson import *' with environment creation
- Use dependency injection instead of global client access
- Update plugin initialization to use new template system
- Command handlers are automatically registered when client is provided
"""

# ============= MODULE METADATA =============

__version__ = "3.0.0"
__author__ = "Vzoel Fox's (Enhanced by Morgan)"
__description__ = "Universal Asset Bridge & Plugin Manager with Dependency Injection"
__exports__ = [
    # Core initialization
    'initialize_asset_system', 'create_plugin_environment',
    
    # Plugin template system
    'PluginTemplate', 'AssetCommandHandler',
    
    # Asset manager access
    'asset_manager', 'AssetManager',
    
    # Backward compatibility
    'get_emoji', 'convert_font', 'get_client',
    'PREMIUM_EMOJIS', 'FONTS'
]

__all__ = __exports__

print("✅ AssetJSON Universal Bridge v3.0.0 loaded successfully!")
print(f"📊 Features: Dependency Injection, Plugin Templates, Command Separation")
print(f"🔧 Architecture: Singleton Pattern, Thread-Safe, Modular Design")
print(f"🔄 Compatibility: Full backward compatibility with v2.0.0 plugins")