#!/usr/bin/env python3
"""
Enhanced Vzoel Asistant Plugin System Core
Handles plugin loading, management, and utilities for plugins folder
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for importing main modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from config import COMMAND_PREFIX, OWNER_ID
except ImportError:
    # Fallback values
    COMMAND_PREFIX = "."
    OWNER_ID = None

logger = logging.getLogger(__name__)

# ============= CUSTOM WORD REPLACER SYSTEM =============

class CustomWordReplacer:
    """Advanced word replacement system for plugins"""
    
    def __init__(self):
        self.words_file = os.path.join(parent_dir, "data", "custom_words.json")
        self.custom_words = self.load_words()
        self.replacement_history = []
        
    def load_words(self) -> Dict[str, Any]:
        """Load custom words from JSON file"""
        # Default words untuk gcast dan commands lain
        default_words = {
            # Greeting variations
            "hello": ["hai bos", "halo gan", "selamat datang", "apa kabar"],
            "hi": ["hai", "halo", "hey", "woy"],
            "good morning": ["selamat pagi", "pagi bos", "morning gan"],
            "good night": ["selamat malam", "malam bos", "oyasumi"],
            
            # Common responses
            "thanks": ["makasih", "terima kasih", "thx gan", "thanks bro"],
            "sorry": ["maaf", "sorry gan", "my bad", "sori"],
            "yes": ["iya", "yep", "betul", "bener"],
            "no": ["tidak", "nope", "engga", "ga"],
            
            # Gcast specific
            "info": ["informasi", "kabar", "update", "berita"],
            "update": ["kabar terbaru", "info terkini", "update-an", "berita baru"],
            "group": ["grup", "gc", "grub", "komunitas"],
            "admin": ["admin", "mimin", "pengelola", "moderator"],
            
            # Casual words
            "cool": ["keren", "mantap", "bagus", "oke"],
            "nice": ["bagus", "keren", "mantap", "oke banget"],
            "awesome": ["keren banget", "mantap jiwa", "luar biasa", "incredible"],
            "please": ["tolong", "mohon", "please", "minta"],
            
            # Time expressions
            "now": ["sekarang", "saat ini", "skrg", "now"],
            "today": ["hari ini", "today", "skrg", "saat ini"],
            "tomorrow": ["besok", "tomorrow", "esok hari"],
            
            # Action words
            "join": ["gabung", "ikut", "masuk", "join"],
            "leave": ["keluar", "pergi", "cabut", "leave"],
            "help": ["bantuan", "tolong", "help", "bantu"],
            "check": ["cek", "lihat", "periksa", "check"]
        }
        
        if os.path.exists(self.words_file):
            try:
                with open(self.words_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    default_words.update(loaded)
                    return default_words
            except Exception as e:
                logger.error(f"Error loading custom words: {e}")
        
        # Create data directory if not exists
        os.makedirs(os.path.dirname(self.words_file), exist_ok=True)
        self.save_words(default_words)
        return default_words
    
    def save_words(self, words: Dict[str, Any] = None):
        """Save custom words to JSON file"""
        try:
            words_to_save = words or self.custom_words
            os.makedirs(os.path.dirname(self.words_file), exist_ok=True)
            with open(self.words_file, 'w', encoding='utf-8') as f:
                json.dump(words_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving custom words: {e}")
    
    def process_text(self, text: str, context: str = "general", intensity: float = 0.7) -> str:
        """
        Process text dengan word replacement
        intensity: 0.0-1.0, seberapa sering replace (0.7 = 70% chance)
        """
        if not text or not isinstance(text, str):
            return text
        
        result = text
        replacements_made = []
        
        # Process each word in custom_words
        for original, replacements in self.custom_words.items():
            # Check if word exists in text (case insensitive)
            if original.lower() in result.lower():
                # Apply intensity filter
                if random.random() <= intensity:
                    if isinstance(replacements, list):
                        replacement = random.choice(replacements)
                    else:
                        replacement = replacements
                    
                    # Replace with case preservation attempt
                    pattern = original
                    if original.lower() in result.lower():
                        # Find actual case in text
                        import re
                        match = re.search(re.escape(original), result, re.IGNORECASE)
                        if match:
                            original_word = match.group()
                            result = result.replace(original_word, replacement, 1)
                            replacements_made.append(f"{original_word} → {replacement}")
        
        # Log replacements for debugging
        if replacements_made and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Word replacements in {context}: {replacements_made}")
        
        return result
    
    def add_word(self, original: str, replacement: str) -> bool:
        """Add or update custom word"""
        try:
            original = original.lower().strip()
            replacement = replacement.strip()
            
            if original in self.custom_words:
                if isinstance(self.custom_words[original], list):
                    if replacement not in self.custom_words[original]:
                        self.custom_words[original].append(replacement)
                else:
                    # Convert single value to list
                    existing = self.custom_words[original]
                    self.custom_words[original] = [existing, replacement]
            else:
                self.custom_words[original] = [replacement]
            
            self.save_words()
            return True
        except Exception as e:
            logger.error(f"Error adding word: {e}")
            return False
    
    def remove_word(self, original: str) -> bool:
        """Remove custom word completely"""
        try:
            original = original.lower().strip()
            if original in self.custom_words:
                del self.custom_words[original]
                self.save_words()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing word: {e}")
            return False
    
    def remove_replacement(self, original: str, replacement: str) -> bool:
        """Remove specific replacement for a word"""
        try:
            original = original.lower().strip()
            if original in self.custom_words:
                replacements = self.custom_words[original]
                if isinstance(replacements, list):
                    if replacement in replacements:
                        replacements.remove(replacement)
                        if len(replacements) == 1:
                            self.custom_words[original] = replacements[0]
                        elif len(replacements) == 0:
                            del self.custom_words[original]
                        self.save_words()
                        return True
                elif replacements == replacement:
                    del self.custom_words[original]
                    self.save_words()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error removing replacement: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get word replacer statistics"""
        total_words = len(self.custom_words)
        total_replacements = sum(
            len(v) if isinstance(v, list) else 1 
            for v in self.custom_words.values()
        )
        
        return {
            "total_words": total_words,
            "total_replacements": total_replacements,
            "categories": {
                "greetings": len([k for k in self.custom_words.keys() 
                               if k in ["hello", "hi", "good morning", "good night"]]),
                "responses": len([k for k in self.custom_words.keys() 
                               if k in ["thanks", "sorry", "yes", "no"]]),
                "actions": len([k for k in self.custom_words.keys() 
                              if k in ["join", "leave", "help", "check"]])
            }
        }

# ============= PLUGIN DECORATORS & UTILITIES =============

# Global word replacer instance
word_replacer = CustomWordReplacer()

def auto_replace(context: str = "general", intensity: float = 0.7):
    """
    Decorator untuk auto-replace text dalam response
    
    Args:
        context: Context untuk replacement (gcast, alive, etc)
        intensity: Seberapa sering replace (0.0-1.0)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if isinstance(result, str):
                processed = word_replacer.process_text(result, context, intensity)
                logger.debug(f"Auto-replace {context}: {result[:50]}... → {processed[:50]}...")
                return processed
            
            return result
        
        # Preserve function attributes
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        if hasattr(func, '_telethon_event'):
            wrapper._telethon_event = func._telethon_event
        
        return wrapper
    return decorator

def owner_only(func):
    """Decorator untuk command yang hanya bisa digunakan owner"""
    async def wrapper(event):
        try:
            # Import client from main
            from main import client, is_owner
            
            if not await is_owner(event.sender_id):
                return
            
            return await func(event)
        except Exception as e:
            logger.error(f"Error in owner_only decorator: {e}")
            await event.reply(f"❌ Error: {str(e)}")
    
    # Preserve function attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    if hasattr(func, '_telethon_event'):
        wrapper._telethon_event = func._telethon_event
    
    return wrapper

def log_command_usage(func):
    """Decorator untuk log penggunaan command"""
    async def wrapper(event):
        try:
            # Import from main
            from main import log_command
            
            command_name = getattr(func, '__name__', 'unknown')
            await log_command(event, command_name)
        except Exception as e:
            logger.debug(f"Logging error (non-critical): {e}")
        
        return await func(event)
    
    # Preserve function attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    if hasattr(func, '_telethon_event'):
        wrapper._telethon_event = func._telethon_event
    
    return wrapper

def error_handler(func):
    """Decorator untuk handle errors dalam plugin"""
    async def wrapper(event):
        try:
            return await func(event)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            try:
                await event.reply(f"❌ Error in {func.__name__}: {str(e)}")
            except:
                pass  # Ignore if can't send error message
    
    # Preserve function attributes
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    if hasattr(func, '_telethon_event'):
        wrapper._telethon_event = func._telethon_event
    
    return wrapper

# ============= HELPER FUNCTIONS =============

def get_word_replacer() -> CustomWordReplacer:
    """Get global word replacer instance"""
    return word_replacer

def create_plugin_template(plugin_name: str) -> str:
    """Create a plugin template"""
    template = f'''#!/usr/bin/env python3
"""
{plugin_name.title()} Plugin for Enhanced Userbot
Created with plugin template generator
"""

import asyncio
from telethon import events
from plugins import COMMAND_PREFIX, owner_only, log_command_usage, error_handler, auto_replace

@events.register(events.NewMessage(pattern=rf'{{COMMAND_PREFIX}}{plugin_name}'))
@owner_only
@log_command_usage
@error_handler
@auto_replace(context="{plugin_name}", intensity=0.7)
async def {plugin_name}_handler(event):
    """{plugin_name.title()} command"""
    
    # Your plugin logic here
    response = f"🎉 {plugin_name.title()} plugin is working!"
    
    await event.edit(response)

# Additional functions can be added here
'''
    return template

# ============= EXPORTS =============

__all__ = [
    'CustomWordReplacer',
    'word_replacer',
    'auto_replace',
    'owner_only', 
    'log_command_usage',
    'error_handler',
    'get_word_replacer',
    'create_plugin_template',
    'COMMAND_PREFIX',
    'OWNER_ID'
]

logger.info("🔌 Plugin system core loaded successfully")
