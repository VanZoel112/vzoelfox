#!/usr/bin/env python3
"""
AI Topic Responder Plugin dengan Premium Emoji Support
File: plugins/aitopicresponder.py
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
import json
import asyncio
import aiohttp
import subprocess
import shutil
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Premium emoji configuration (copy dari main.py)
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
}

# Unicode Fonts
FONTS = {
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
    }
}

# Global variables
premium_status = None
topic_memory = {}
ai_enabled_chats = set()
response_cooldowns = {}
chat_contexts = defaultdict(list)

# Configuration files
TOPICS_FILE = "data/ai_topics.json"
AI_CHATS_FILE = "data/ai_enabled_chats.json"
CONTEXT_FILE = "data/chat_contexts.json"
AI_CONFIG_FILE = "data/ai_config.json"

# AI Configuration Template dengan Auto-Management
DEFAULT_AI_CONFIG = {
    "api_type": "ollama",  # ollama (auto-managed), huggingface, groq, openrouter, gemini, openai, anthropic, custom
    "api_endpoint": "http://localhost:11434/api/chat",
    "api_key": "not_required",
    "model": "llama2",
    "max_tokens": 200,
    "temperature": 0.8,
    "system_prompt": "Kamu adalah AI assistant yang membantu di grup Telegram. Jawab dengan natural dan membantu tentang topik yang sudah dipelajari dari conversation sebelumnya. Jawab dalam bahasa Indonesia jika ditanya dalam bahasa Indonesia, atau bahasa Inggris jika ditanya dalam bahasa Inggris.",
    "response_prefix": "🤖",
    "response_suffix": "",
    "enable_context_learning": True,
    "max_context_messages": 30,
    "cooldown_seconds": 15,
    "auto_managed": True,
    "completely_free": True,
    "zero_setup": True,
    
    # Free API Templates (untuk alternative)
    "free_apis": {
        "ollama_auto": {
            "api_type": "ollama",
            "api_endpoint": "http://localhost:11434/api/chat",
            "api_key": "not_required", 
            "model": "llama2",
            "note": "100% FREE, AUTO-MANAGED by bot! Zero setup required."
        },
        "huggingface": {
            "api_type": "huggingface",
            "api_endpoint": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            "api_key": "hf_your_token_here",
            "model": "microsoft/DialoGPT-medium",
            "note": "Free with rate limits. Get token from huggingface.co"
        },
        "groq": {
            "api_type": "groq", 
            "api_endpoint": "https://api.groq.com/openai/v1/chat/completions",
            "api_key": "gsk_your_groq_key_here",
            "model": "mixtral-8x7b-32768",
            "note": "Fast inference, generous free tier. Get key from console.groq.com"
        },
        "openrouter": {
            "api_type": "openrouter",
            "api_endpoint": "https://openrouter.ai/api/v1/chat/completions", 
            "api_key": "sk-or-your_key_here",
            "model": "mistralai/mistral-7b-instruct:free",
            "note": "Multiple free models available. Get key from openrouter.ai"
        },
        "gemini": {
            "api_type": "gemini",
            "api_endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            "api_key": "your_google_ai_key_here", 
            "model": "gemini-pro",
            "note": "Google AI Studio free tier. Get key from aistudio.google.com"
        }
    }
}

async def check_premium_status():
    """Check premium status in plugin"""
    global premium_status
    try:
        me = await client.get_me()
        premium_status = getattr(me, 'premium', False)
        return premium_status
    except Exception:
        premium_status = False
        return False

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def get_emoji(emoji_type):
    """Get premium emoji character"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    if not premium_status:
        return []
    
    entities = []
    current_offset = 0
    i = 0
    
    try:
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
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
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available"""
    try:
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return True

def get_prefix():
    """Get command prefix"""
    try:
        import os
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

def ensure_data_directory():
    """Ensure data directory exists"""
    os.makedirs("data", exist_ok=True)

def load_topics():
    """Load topic memory from file"""
    try:
        ensure_data_directory()
        if os.path.exists(TOPICS_FILE):
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading topics: {e}")
    return {}

def save_topics():
    """Save topic memory to file"""
    try:
        ensure_data_directory()
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(topic_memory, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving topics: {e}")
        return False

def load_ai_chats():
    """Load AI enabled chats from file"""
    try:
        ensure_data_directory()
        if os.path.exists(AI_CHATS_FILE):
            with open(AI_CHATS_FILE, 'r') as f:
                data = json.load(f)
                return set(data)
    except Exception as e:
        print(f"Error loading AI chats: {e}")
    return set()

def save_ai_chats():
    """Save AI enabled chats to file"""
    try:
        ensure_data_directory()
        with open(AI_CHATS_FILE, 'w') as f:
            json.dump(list(ai_enabled_chats), f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving AI chats: {e}")
        return False

def load_ai_config():
    """Load AI configuration"""
    try:
        ensure_data_directory()
        if os.path.exists(AI_CONFIG_FILE):
            with open(AI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults for missing keys
                for key, value in DEFAULT_AI_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        print(f"Error loading AI config: {e}")
    
    # Create default config file
    try:
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_AI_CONFIG, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    
    return DEFAULT_AI_CONFIG.copy()

def save_chat_contexts():
    """Save chat contexts to file"""
    try:
        ensure_data_directory()
        # Convert defaultdict to regular dict for JSON serialization
        contexts_dict = dict(chat_contexts)
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(contexts_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving contexts: {e}")

def load_chat_contexts():
    """Load chat contexts from file"""
    try:
        ensure_data_directory()
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
                contexts_dict = json.load(f)
                return defaultdict(list, contexts_dict)
    except Exception as e:
        print(f"Error loading contexts: {e}")
    return defaultdict(list)

async def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

async def install_ollama():
    """Auto-install Ollama"""
    try:
        print("🤖 Auto-installing Ollama...")
        
        # Detect OS and install
        import platform
        system = platform.system().lower()
        
        if system == "linux":
            # Install for Linux
            process = subprocess.Popen(
                ['bash', '-c', 'curl -fsSL https://ollama.com/install.sh | sh'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                print("✅ Ollama installed successfully!")
                return True
            else:
                print(f"❌ Installation failed: {stderr.decode()}")
                return False
                
        elif system == "darwin":  # macOS
            # Try with brew first
            if shutil.which('brew'):
                result = subprocess.run(['brew', 'install', 'ollama'], capture_output=True)
                return result.returncode == 0
            else:
                print("❌ macOS requires Homebrew or manual install from ollama.com")
                return False
                
        else:
            print("❌ Auto-install not supported for this OS. Please install manually from ollama.com")
            return False
            
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

async def start_ollama_service():
    """Auto-start Ollama service"""
    try:
        # Check if already running
        result = subprocess.run(['pgrep', 'ollama'], capture_output=True)
        if result.returncode == 0:
            print("✅ Ollama service already running")
            return True
        
        print("🚀 Starting Ollama service...")
        
        # Start Ollama in background
        process = subprocess.Popen(
            ['ollama', 'serve'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Wait a bit for startup
        await asyncio.sleep(3)
        
        # Test if service is running
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:11434/api/version', timeout=5) as response:
                    if response.status == 200:
                        print("✅ Ollama service started successfully!")
                        return True
        except:
            pass
        
        print("❌ Failed to start Ollama service")
        return False
        
    except Exception as e:
        print(f"❌ Service start error: {e}")
        return False

async def download_ollama_model(model_name="llama2"):
    """Auto-download Ollama model"""
    try:
        print(f"📥 Downloading model: {model_name}")
        
        # Check if model already exists
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0 and model_name in result.stdout:
            print(f"✅ Model {model_name} already downloaded")
            return True
        
        # Download model
        print(f"⏳ Downloading {model_name} (this may take a few minutes)...")
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print(f"✅ Model {model_name} downloaded successfully!")
            return True
        else:
            print(f"❌ Model download failed: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Model download error: {e}")
        return False

async def auto_setup_ollama():
    """Complete auto-setup of Ollama"""
    try:
        print("🤖 Starting automatic Ollama setup...")
        
        # Step 1: Check if Ollama is installed
        if not await check_ollama_installed():
            print("📦 Ollama not found, installing...")
            if not await install_ollama():
                return False, "Failed to install Ollama"
        else:
            print("✅ Ollama already installed")
        
        # Step 2: Start service
        if not await start_ollama_service():
            return False, "Failed to start Ollama service"
        
        # Step 3: Download default model
        if not await download_ollama_model("llama2"):
            print("⚠️ llama2 failed, trying phi (smaller model)...")
            if not await download_ollama_model("phi"):
                return False, "Failed to download any model"
        
        # Step 4: Create config
        config = {
            "api_type": "ollama",
            "api_endpoint": "http://localhost:11434/api/chat",
            "api_key": "not_required",
            "model": "llama2",
            "max_tokens": 200,
            "temperature": 0.8,
            "system_prompt": "Kamu adalah AI assistant yang membantu di grup Telegram. Jawab dengan natural dan membantu tentang topik yang sudah dipelajari dari conversation sebelumnya.",
            "response_prefix": "🤖",
            "response_suffix": "",
            "enable_context_learning": True,
            "max_context_messages": 30,
            "cooldown_seconds": 15,
            "auto_managed": True,
            "completely_free": True
        }
        
        ensure_data_directory()
        with open(AI_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ Complete auto-setup finished!")
        return True, "Ollama setup completed successfully"
        
    except Exception as e:
        return False, f"Auto-setup error: {str(e)}"

async def ensure_ollama_running():
    """Ensure Ollama is running before API calls"""
    try:
        # Quick health check
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:11434/api/version', timeout=3) as response:
                    if response.status == 200:
                        return True
            except:
                pass
        
        # If not running, try to start
        print("⚠️ Ollama not responding, attempting to start...")
        return await start_ollama_service()
        
    except Exception as e:
        print(f"Error checking Ollama: {e}")
        return False
    """Extract keywords from text"""
    # Simple keyword extraction
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
    # Filter common words
    stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'about', 'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'ini', 'itu', 'tidak', 'ya', 'sudah'}
    return [word for word in words if word not in stopwords]

def check_topic_match(text, topics):
    """Check if text matches any monitored topics"""
    text_lower = text.lower()
    keywords = extract_keywords(text)
    
    matched_topics = []
    for topic, data in topics.items():
        topic_keywords = data.get('keywords', [])
        
        # Check exact topic match
        if topic.lower() in text_lower:
            matched_topics.append(topic)
            continue
        
        # Check keyword matches
        for keyword in topic_keywords:
            if keyword.lower() in text_lower or keyword.lower() in keywords:
                matched_topics.append(topic)
                break
    
    return matched_topics

async def call_ai_api(prompt, context_messages=None):
    """Call AI API with template system"""
    try:
        config = load_ai_config()
        
        if not config.get('api_key') or config['api_key'] == 'your_api_key_here':
            return "❌ AI API key not configured. Use .aiconfig to set up."
        
        # Build messages
     
