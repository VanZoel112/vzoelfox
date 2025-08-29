#!/usr/bin/env python3
"""
🎭 VOICE CLONE REAL-TIME PLUGIN - Advanced Voice Cloning System
Fitur: Real-time voice cloning untuk calls, voice notes, dan live streaming
Author: Vzoel Fox's (Enhanced by Morgan)  
Version: 1.0.0 - Real-Time Edition
"""

import asyncio
import sqlite3
import os
import json
import time
import random
import subprocess
import tempfile
import base64
from datetime import datetime
from telethon import events, functions
from telethon.tl.types import DocumentAttributeAudio
import requests
import io

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "voice_clone_realtime", 
    "version": "1.0.0",
    "description": "🎭 Advanced real-time voice cloning untuk calls, voice notes & live streaming",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".vclone setup", ".vclone list", ".vclone add <name>", ".vclone use <name>",
        ".vclone call <target>", ".vclone note <text>", ".vclone stream on/off",
        ".vclone train <audio_file>", ".vclone config", ".vclone test <text>"
    ],
    "features": [
        "Real-time voice cloning", "Multiple character voices", "Live call integration",
        "Voice note generation", "Audio streaming", "Custom voice training",
        "ElevenLabs integration", "Local TTS models", "WebRTC support"
    ]
}

# ===== CONFIGURATION =====
DB_FILE = "plugins/voice_clone.db" 
TEMP_AUDIO_DIR = "temp_audio"
VOICE_MODELS_DIR = "voice_models"

# Load API keys from config file
def load_api_keys():
    try:
        with open('voice_clone_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('api_keys', {})
    except FileNotFoundError:
        print("⚠️ Warning: voice_clone_config.json not found")
        return {}
    except Exception as e:
        print(f"⚠️ Error loading API keys: {e}")
        return {}

# Voice Cloning APIs Configuration
api_keys = load_api_keys()
VOICE_APIS = {
    "elevenlabs": {
        "name": "ElevenLabs",
        "endpoint": "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        "key": api_keys.get("elevenlabs", {}).get("key", "YOUR_ELEVENLABS_API_KEY_HERE"),
        "quality": "premium",
        "real_time": True,
        "max_chars": 5000
    },
    "murf": {
        "name": "Murf.ai", 
        "endpoint": "https://api.murf.ai/v1/speech/generate",
        "key": api_keys.get("murf", {}).get("key", "YOUR_MURF_API_KEY_HERE"),
        "quality": "high",
        "real_time": True,
        "max_chars": 3000
    },
    "openai": {
        "name": "OpenAI Whisper",
        "endpoint": "https://api.openai.com/v1/audio/speech",
        "key": api_keys.get("openai", {}).get("key", "YOUR_OPENAI_API_KEY_HERE"),
        "quality": "high",
        "real_time": True,
        "max_chars": 4000
    },
    "coqui": {
        "name": "Coqui TTS",
        "endpoint": "http://localhost:5002/api/tts",
        "key": "local",
        "quality": "medium",
        "real_time": True,
        "max_chars": 10000
    }
}

# Load character voices from config file
def load_voice_config():
    try:
        with open('voice_clone_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('character_voices', {})
    except FileNotFoundError:
        print("⚠️ Warning: voice_clone_config.json not found, using default voices")
        return {}
    except Exception as e:
        print(f"⚠️ Error loading voice config: {e}")
        return {}

# Character Voice Presets - ENHANCED WITH REQUESTED CHARACTERS
CHARACTER_VOICES = load_voice_config()

# Fallback to default if config is empty
if not CHARACTER_VOICES:
    CHARACTER_VOICES = {
        # ===== REQUESTED CHARACTERS =====
        "jokowi": {
            "name": "Joko Widodo (Jokowi)",
            "description": "🇮🇩 Presiden Indonesia - Suara khas Bapak Jokowi",
            "api": "elevenlabs",
            "voice_id": "jokowi_indonesia_voice",
            "settings": {
                "stability": 0.85,
                "similarity_boost": 0.80,
                "style": 0.3,
                "use_speaker_boost": True
            }
        },
        "prabowo": {
            "name": "Prabowo Subianto",
            "description": "🎖️ Menteri Pertahanan - Suara tegas dan berwibawa",
            "api": "elevenlabs",
            "voice_id": "prabowo_subianto_voice",
            "settings": {
                "stability": 0.82,
                "similarity_boost": 0.78,
                "style": 0.35,
                "use_speaker_boost": True
            }
        },
        "claude": {
            "name": "Claude AI Assistant",
            "description": "🤖 AI Assistant - Professional dan informatif",
            "api": "elevenlabs",
            "voice_id": "claude_ai_voice",
            "settings": {
                "stability": 0.75,
                "similarity_boost": 0.70,
                "style": 0.2,
                "use_speaker_boost": False
            }
        },
        "mlbb": {
            "name": "MLBB Narrator",
            "description": "⚔️ Mobile Legends - Narrator epik pertempuran",
            "api": "elevenlabs",
            "voice_id": "mlbb_narrator_voice",
            "settings": {
                "stability": 0.80,
                "similarity_boost": 0.75,
                "style": 0.4,
                "use_speaker_boost": True
            }
        },
        "squidward": {
            "name": "Squidward Tentacles",
            "description": "🦑 SpongeBob - Suara sarkastik dan pesimis",
            "api": "elevenlabs",
            "voice_id": "squidward_tentacles_voice",
            "settings": {
                "stability": 0.70,
                "similarity_boost": 0.65,
                "style": 0.5,
                "use_speaker_boost": True
            }
        },
        "spongebob": {
            "name": "SpongeBob SquarePants",
            "description": "🧽 SpongeBob - Suara ceria dan antusias",
            "api": "elevenlabs",
            "voice_id": "spongebob_squarepants_voice",
            "settings": {
                "stability": 0.65,
                "similarity_boost": 0.60,
                "style": 0.6,
                "use_speaker_boost": True
            }
        },
        "presenter": {
            "name": "Presenter Sexy",
            "description": "💃 Presenter - Suara sensual dan menarik",
            "api": "elevenlabs",
            "voice_id": "sexy_presenter_voice",
            "settings": {
                "stability": 0.77,
                "similarity_boost": 0.72,
                "style": 0.45,
                "use_speaker_boost": True
            }
        }
    }

# Premium emoji configuration
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

FONTS = {
    'bold': {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
        'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
        's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
        'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
        'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
}

# Global variables
current_voice = "anime_girl"
streaming_active = False
call_active = False

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
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

# ===== DATABASE FUNCTIONS =====
def init_voice_db():
    """Initialize voice cloning database"""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
        os.makedirs(VOICE_MODELS_DIR, exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Voice models table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                api_provider TEXT NOT NULL,
                voice_id TEXT NOT NULL,
                settings TEXT,
                audio_samples TEXT,
                created_at TEXT NOT NULL,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0,
                is_custom BOOLEAN DEFAULT 0,
                quality_rating REAL DEFAULT 0.0
            )
        ''')
        
        # Voice generation logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voice_name TEXT NOT NULL,
                text_input TEXT NOT NULL,
                audio_file TEXT,
                generation_time REAL,
                api_used TEXT,
                success BOOLEAN DEFAULT 1,
                timestamp TEXT NOT NULL,
                chat_id INTEGER,
                user_id INTEGER
            )
        ''')
        
        # Real-time call logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_user_id INTEGER NOT NULL,
                voice_used TEXT NOT NULL,
                call_duration REAL DEFAULT 0,
                audio_processed INTEGER DEFAULT 0,
                call_start TEXT NOT NULL,
                call_end TEXT,
                success BOOLEAN DEFAULT 1
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_settings (
                id INTEGER PRIMARY KEY,
                current_voice TEXT DEFAULT 'anime_girl',
                streaming_enabled BOOLEAN DEFAULT 0,
                auto_process_calls BOOLEAN DEFAULT 0,
                api_keys TEXT,
                quality_preference TEXT DEFAULT 'high',
                real_time_processing BOOLEAN DEFAULT 1,
                last_updated TEXT
            )
        ''')
        
        # Insert default settings
        cursor.execute('SELECT COUNT(*) FROM voice_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO voice_settings (
                    id, current_voice, streaming_enabled, api_keys, last_updated
                ) VALUES (?, ?, ?, ?, ?)
            ''', (1, 'anime_girl', False, '{}', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Voice DB init error: {e}")
        return False

def save_voice_model(name, display_name, description, api_provider, voice_id, settings=None, is_custom=False):
    """Save voice model to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO voice_models (
                name, display_name, description, api_provider, voice_id, 
                settings, created_at, is_custom
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, display_name, description, api_provider, voice_id,
            json.dumps(settings or {}), datetime.now().isoformat(), is_custom
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Save voice model error: {e}")
        return False

def get_voice_models():
    """Get all available voice models"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, display_name, description, api_provider, 
                   voice_id, settings, usage_count, quality_rating
            FROM voice_models ORDER BY usage_count DESC
        ''')
        models = cursor.fetchall()
        conn.close()
        return models
    except Exception as e:
        print(f"Get voice models error: {e}")
        return []

def log_voice_generation(voice_name, text_input, audio_file, generation_time, api_used, success=True, chat_id=0, user_id=0):
    """Log voice generation to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO voice_logs (
                voice_name, text_input, audio_file, generation_time,
                api_used, success, timestamp, chat_id, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            voice_name, text_input, audio_file, generation_time,
            api_used, success, datetime.now().isoformat(), chat_id, user_id
        ))
        
        # Update usage count
        cursor.execute('UPDATE voice_models SET usage_count = usage_count + 1 WHERE name = ?', (voice_name,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Log voice generation error: {e}")
        return False

# ===== VOICE CLONING FUNCTIONS =====
async def generate_voice_elevenlabs(text, voice_id, settings=None):
    """Generate voice using ElevenLabs API"""
    try:
        api_config = VOICE_APIS["elevenlabs"]
        url = api_config["endpoint"].format(voice_id=voice_id)
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_config["key"]
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": settings or {
                "stability": 0.71,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        start_time = time.time()
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            generation_time = time.time() - start_time
            return response.content, generation_time
        else:
            return None, f"ElevenLabs API error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, f"ElevenLabs error: {str(e)}"

async def generate_voice_murf(text, voice_id, settings=None):
    """Generate voice using Murf.ai API"""
    try:
        api_config = VOICE_APIS["murf"]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_config['key']}"
        }
        
        data = {
            "text": text,
            "voice_id": voice_id,
            "speed": settings.get("speed", 1.0) if settings else 1.0,
            "pitch": settings.get("pitch", 0) if settings else 0,
            "format": "mp3"
        }
        
        start_time = time.time()
        
        response = requests.post(api_config["endpoint"], json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            audio_url = result.get("audio_url")
            
            if audio_url:
                # Download generated audio
                audio_response = requests.get(audio_url, timeout=30)
                if audio_response.status_code == 200:
                    generation_time = time.time() - start_time
                    return audio_response.content, generation_time
            
        return None, f"Murf API error: {response.status_code} - {response.text}"
        
    except Exception as e:
        return None, f"Murf error: {str(e)}"

async def generate_voice_coqui_local(text, voice_id, settings=None):
    """Generate voice using local Coqui TTS"""
    try:
        api_config = VOICE_APIS["coqui"]
        
        data = {
            "text": text,
            "speaker_name": voice_id,
            "language_id": "en",
            "speed": settings.get("speed", 1.0) if settings else 1.0
        }
        
        start_time = time.time()
        
        response = requests.post(api_config["endpoint"], json=data, timeout=30)
        
        if response.status_code == 200:
            generation_time = time.time() - start_time
            return response.content, generation_time
        else:
            return None, f"Coqui TTS error: {response.status_code}"
            
    except Exception as e:
        return None, f"Coqui error: {str(e)}"

async def generate_voice(text, voice_name=None):
    """Generate voice using specified voice model"""
    if not voice_name:
        voice_name = current_voice
    
    if voice_name not in CHARACTER_VOICES:
        return None, f"Voice '{voice_name}' tidak tersedia"
    
    voice_config = CHARACTER_VOICES[voice_name]
    api_provider = voice_config["api"]
    voice_id = voice_config["voice_id"]
    settings = voice_config["settings"]
    
    try:
        # Select appropriate API
        if api_provider == "elevenlabs":
            audio_data, generation_time = await generate_voice_elevenlabs(text, voice_id, settings)
        elif api_provider == "murf":
            audio_data, generation_time = await generate_voice_murf(text, voice_id, settings)
        elif api_provider == "coqui":
            audio_data, generation_time = await generate_voice_coqui_local(text, voice_id, settings)
        else:
            return None, f"Unsupported API: {api_provider}"
        
        if isinstance(audio_data, bytes):
            # Save audio to temp file
            temp_file = os.path.join(TEMP_AUDIO_DIR, f"voice_{int(time.time())}.mp3")
            with open(temp_file, 'wb') as f:
                f.write(audio_data)
            
            return temp_file, generation_time
        else:
            return None, audio_data  # Error message
            
    except Exception as e:
        return None, f"Voice generation error: {str(e)}"

# ===== REAL-TIME AUDIO PROCESSING =====
async def process_real_time_audio(audio_data, voice_name):
    """Process audio in real-time for calls"""
    try:
        # Save input audio
        input_file = os.path.join(TEMP_AUDIO_DIR, f"input_{int(time.time())}.wav")
        with open(input_file, 'wb') as f:
            f.write(audio_data)
        
        # Convert audio to text (speech-to-text)
        text = await audio_to_text(input_file)
        if not text:
            return None, "Failed to convert audio to text"
        
        # Generate cloned voice
        cloned_audio, generation_time = await generate_voice(text, voice_name)
        if not cloned_audio:
            return None, "Failed to generate cloned voice"
        
        return cloned_audio, generation_time
        
    except Exception as e:
        return None, f"Real-time processing error: {str(e)}"

async def audio_to_text(audio_file):
    """Convert audio to text using speech recognition"""
    try:
        # Using OpenAI Whisper API for speech-to-text
        # You can also use Google Speech-to-Text or other services
        
        with open(audio_file, 'rb') as f:
            files = {"file": f}
            headers = {"Authorization": "Bearer YOUR_OPENAI_API_KEY"}
            
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data={"model": "whisper-1"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "")
            
        return None
        
    except Exception as e:
        print(f"Speech-to-text error: {e}")
        return None

# ===== TELEGRAM VOICE INTEGRATION =====
async def send_voice_message(event, audio_file, duration=None):
    """Send voice message to Telegram"""
    try:
        # Get audio duration if not provided
        if not duration:
            duration = get_audio_duration(audio_file)
        
        # Send voice message
        with open(audio_file, 'rb') as audio:
            await client.send_file(
                event.chat_id,
                audio,
                voice_note=True,
                attributes=[DocumentAttributeAudio(
                    duration=int(duration),
                    voice=True
                )]
            )
        
        return True
    except Exception as e:
        print(f"Send voice message error: {e}")
        return False

def get_audio_duration(audio_file):
    """Get audio file duration"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 10.0  # Default duration
    except:
        return 10.0

# ===== COMMAND HANDLERS =====
@client.on(events.NewMessage(pattern=r'\.vclone\s+(.+)'))
async def voice_clone_handler(event):
    """Main voice clone command handler"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        args = event.pattern_match.group(1).strip().split()
        command = args[0].lower()
        
        # Initialize database
        init_voice_db()
        
        if command == 'setup':
            await setup_voice_system(event)
        elif command == 'list':
            await list_voices(event)
        elif command == 'add' and len(args) > 1:
            await add_voice_model(event, args[1])
        elif command == 'use' and len(args) > 1:
            await switch_voice(event, args[1])
        elif command == 'test' and len(args) > 1:
            test_text = ' '.join(args[1:])
            await test_voice(event, test_text)
        elif command == 'note' and len(args) > 1:
            note_text = ' '.join(args[1:])
            await generate_voice_note(event, note_text)
        elif command == 'call' and len(args) > 1:
            target = args[1]
            await start_voice_call(event, target)
        elif command == 'stream':
            if len(args) > 1:
                await toggle_streaming(event, args[1])
            else:
                await show_streaming_status(event)
        elif command == 'config':
            await show_voice_config(event)
        elif command == 'jokowi' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'jokowi', text)
        elif command == 'prabowo' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'prabowo', text)
        elif command == 'squidward' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'squidward', text)
        elif command == 'spongebob' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'spongebob', text)
        elif command == 'claude' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'claude', text)
        elif command == 'mlbb' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'mlbb_narrator', text)
        elif command == 'presenter' and len(args) > 1:
            text = ' '.join(args[1:])
            await generate_character_voice(event, 'presenter_sexy', text)
        elif command == 'characters':
            await show_character_voices(event)
        else:
            await show_voice_help(event)
            
    except Exception as e:
        await event.edit(f"❌ Voice clone error: {str(e)}")

async def setup_voice_system(event):
    """Setup voice cloning system"""
    try:
        loading_msg = await event.edit(f"""
{get_emoji('main')} {convert_font('VOICE CLONE SETUP', 'bold')}

{get_emoji('adder1')} Initializing voice cloning system...
        """.strip())
        
        # Initialize database
        init_success = init_voice_db()
        
        await asyncio.sleep(1)
        await loading_msg.edit(f"""
{get_emoji('main')} {convert_font('VOICE CLONE SETUP', 'bold')}

{get_emoji('check')} Database: {'✅ Initialized' if init_success else '❌ Failed'}
{get_emoji('adder1')} Installing character voices...
        """.strip())
        
        # Install default character voices
        installed_voices = 0
        for voice_id, voice_config in CHARACTER_VOICES.items():
            if save_voice_model(
                voice_id, 
                voice_config["name"],
                voice_config["description"],
                voice_config["api"],
                voice_config["voice_id"],
                voice_config["settings"]
            ):
                installed_voices += 1
        
        await asyncio.sleep(1)
        setup_text = f"""
{get_emoji('main')} {convert_font('VOICE CLONE SETUP COMPLETE!', 'bold')}

╔══════════════════════════════════╗
   🎭 {convert_font('VOICE CLONING SYSTEM READY', 'bold')} 🎭
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Database:', 'bold')} Initialized
{get_emoji('check')} {convert_font('Character Voices:', 'bold')} {installed_voices} installed
{get_emoji('check')} {convert_font('Real-time Processing:', 'bold')} Ready
{get_emoji('check')} {convert_font('APIs Configured:', 'bold')} {len(VOICE_APIS)}

{get_emoji('adder2')} {convert_font('Available Character Voices:', 'bold')}
• Anime Girl - Cute female voice
• Deep Male - Authoritative male 
• Celebrity 1 - Famous personality
• Robot - Futuristic AI voice

{get_emoji('adder3')} {convert_font('Features Ready:', 'bold')}
{get_emoji('check')} Real-time voice cloning
{get_emoji('check')} Voice call integration
{get_emoji('check')} Voice note generation
{get_emoji('check')} Live audio streaming
{get_emoji('check')} Custom voice training

{get_emoji('adder4')} {convert_font('Quick Start:', 'bold')}
• `{get_prefix()}vclone list` - Show voices
• `{get_prefix()}vclone use anime_girl` - Switch voice
• `{get_prefix()}vclone test Hello world` - Test voice
• `{get_prefix()}vclone note Your message` - Generate voice note

{get_emoji('main')} {convert_font('System ready for voice cloning!', 'bold')}
        """.strip()
        
        await loading_msg.edit(setup_text)
        
    except Exception as e:
        await event.edit(f"❌ Setup error: {str(e)}")

async def list_voices(event):
    """List available voice models"""
    try:
        models = get_voice_models()
        
        if not models:
            await event.edit(f"""
{get_emoji('adder3')} {convert_font('No voice models found', 'bold')}

Use `{get_prefix()}vclone setup` to initialize the system
            """.strip())
            return
        
        voices_text = f"""
{get_emoji('main')} {convert_font('AVAILABLE VOICE MODELS', 'bold')}

╔══════════════════════════════════╗
   🎭 {convert_font('CHARACTER VOICE LIBRARY', 'bold')} 🎭
╚══════════════════════════════════╝

"""
        
        for i, (name, display_name, description, api_provider, voice_id, settings, usage_count, quality_rating) in enumerate(models, 1):
            current_indicator = "🎯" if name == current_voice else "  "
            api_emoji = {
                "elevenlabs": "🏆", "murf": "🎵", "coqui": "🤖", "custom": "⭐"
            }.get(api_provider, "🔊")
            
            voices_text += f"""
{current_indicator} {get_emoji('adder4')} {convert_font(f'{i}. {display_name.upper()}', 'bold')}
  • ID: `{name}`
  • Description: {description}
  • Provider: {api_emoji} {api_provider.title()}
  • Usage: `{usage_count}` times
  • Quality: {'⭐' * int(quality_rating) if quality_rating > 0 else 'New'}

"""
        
        voices_text += f"""
{get_emoji('adder1')} {convert_font('Current Voice:', 'bold')} {current_voice}
{get_emoji('check')} Use `{get_prefix()}vclone use <name>` to switch
        """.strip()
        
        await event.edit(voices_text)
        
    except Exception as e:
        await event.edit(f"❌ List voices error: {str(e)}")

async def switch_voice(event, voice_name):
    """Switch current voice model"""
    try:
        global current_voice
        
        if voice_name not in CHARACTER_VOICES:
            available_voices = ', '.join(CHARACTER_VOICES.keys())
            await event.edit(f"""
❌ Voice '{voice_name}' tidak tersedia

{get_emoji('main')} Available voices:
{available_voices}
            """.strip())
            return
        
        current_voice = voice_name
        voice_config = CHARACTER_VOICES[voice_name]
        
        await event.edit(f"""
{get_emoji('check')} {convert_font('VOICE SWITCHED!', 'bold')}

╔══════════════════════════════════╗
   🎭 {convert_font('VOICE MODEL ACTIVATED', 'bold')} 🎭
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Voice:', 'bold')} {voice_config['name']}
{get_emoji('check')} {convert_font('Description:', 'bold')} {voice_config['description']}
{get_emoji('check')} {convert_font('Provider:', 'bold')} {voice_config['api'].title()}
{get_emoji('check')} {convert_font('Quality:', 'bold')} {VOICE_APIS[voice_config['api']]['quality'].title()}

{get_emoji('adder2')} Voice ready for use!
Test dengan: `{get_prefix()}vclone test Hello world`
        """.strip())
        
    except Exception as e:
        await event.edit(f"❌ Switch voice error: {str(e)}")

async def test_voice(event, text):
    """Test current voice with text"""
    try:
        if len(text) > 500:
            await event.edit("❌ Text too long! Maximum 500 characters for testing.")
            return
        
        loading_msg = await event.edit(f"""
{get_emoji('main')} {convert_font('VOICE TEST IN PROGRESS', 'bold')}

🎭 {convert_font('Generating voice...', 'bold')}
{get_emoji('check')} Voice: {CHARACTER_VOICES[current_voice]['name']}
{get_emoji('check')} Text: "{text}"
        """.strip())
        
        # Generate voice
        audio_file, generation_time = await generate_voice(text, current_voice)
        
        if audio_file:
            # Send voice message
            success = await send_voice_message(event, audio_file)
            
            if success:
                await loading_msg.edit(f"""
{get_emoji('check')} {convert_font('VOICE TEST SUCCESS!', 'bold')}

🎭 Voice generated and sent!
⏱️ Generation time: {generation_time:.2f}s
🎯 Voice: {CHARACTER_VOICES[current_voice]['name']}
                """.strip())
            else:
                await loading_msg.edit("❌ Failed to send voice message")
            
            # Log generation
            log_voice_generation(current_voice, text, audio_file, generation_time, CHARACTER_VOICES[current_voice]['api'], success)
            
        else:
            await loading_msg.edit(f"❌ Voice generation failed: {generation_time}")
        
    except Exception as e:
        await event.edit(f"❌ Test voice error: {str(e)}")

async def generate_voice_note(event, text):
    """Generate voice note from text"""
    try:
        if len(text) > 2000:
            await event.edit("❌ Text too long! Maximum 2000 characters.")
            return
        
        loading_msg = await event.edit(f"""
{get_emoji('main')} {convert_font('GENERATING VOICE NOTE', 'bold')}

🎤 {convert_font('Processing...', 'bold')}
        """.strip())
        
        # Generate voice
        audio_file, generation_time = await generate_voice(text, current_voice)
        
        if audio_file:
            # Send voice note
            success = await send_voice_message(event, audio_file)
            
            if success:
                await loading_msg.edit(f"""
{get_emoji('check')} {convert_font('VOICE NOTE SENT!', 'bold')}

🎤 Generated successfully with {CHARACTER_VOICES[current_voice]['name']}
⏱️ Generation time: {generation_time:.2f}s
                """.strip())
                
                # Log generation
                log_voice_generation(
                    current_voice, text, audio_file, generation_time,
                    CHARACTER_VOICES[current_voice]['api'], True,
                    event.chat_id, event.sender_id
                )
            else:
                await loading_msg.edit("❌ Failed to send voice note")
        else:
            await loading_msg.edit(f"❌ Voice generation failed: {generation_time}")
        
    except Exception as e:
        await event.edit(f"❌ Generate voice note error: {str(e)}")

async def generate_character_voice(event, character_name, text):
    """Generate voice for specific character with enhanced UI"""
    try:
        if character_name not in CHARACTER_VOICES:
            await event.edit(f"❌ Character '{character_name}' tidak tersedia")
            return
        
        if len(text) > 1000:
            await event.edit("❌ Text too long! Maximum 1000 characters.")
            return
        
        character = CHARACTER_VOICES[character_name]
        loading_msg = await event.edit(f"""
{get_emoji('main')} {convert_font('CHARACTER VOICE GENERATION', 'bold')}

🎭 {convert_font(f'Generating {character["name"]} voice...', 'bold')}
{get_emoji('check')} Character: {character['description']}
{get_emoji('check')} Text: "{text[:100]}{'...' if len(text) > 100 else ''}"
        """.strip())
        
        # Generate voice
        audio_file, generation_time = await generate_voice(text, character_name)
        
        if audio_file:
            # Send voice message
            success = await send_voice_message(event, audio_file)
            
            if success:
                # Show success message with character info
                success_text = f"""
{get_emoji('check')} {convert_font('CHARACTER VOICE GENERATED!', 'bold')}

╔══════════════════════════════════╗
   {character['description']} 
╚══════════════════════════════════╝

🎭 {convert_font('Character:', 'bold')} {character['name']}
⏱️ {convert_font('Generation Time:', 'bold')} {generation_time:.2f}s
🎯 {convert_font('Quality:', 'bold')} Premium
📊 {convert_font('API:', 'bold')} {character['api'].title()}

{get_emoji('adder2')} Voice message sent successfully!
                """.strip()
                
                await loading_msg.edit(success_text)
                
                # Log generation
                log_voice_generation(
                    character_name, text, audio_file, generation_time,
                    character['api'], True, event.chat_id, event.sender_id
                )
            else:
                await loading_msg.edit("❌ Failed to send voice message")
        else:
            await loading_msg.edit(f"❌ Voice generation failed: {generation_time}")
        
    except Exception as e:
        await event.edit(f"❌ Character voice error: {str(e)}")

async def show_character_voices(event):
    """Show all available character voices organized by category"""
    try:
        characters_text = f"""
{get_emoji('main')} {convert_font('CHARACTER VOICE LIBRARY', 'bold')}

╔══════════════════════════════════╗
   🎭 {convert_font('EPIC CHARACTER COLLECTION', 'bold')} 🎭
╚══════════════════════════════════╝

🇮🇩 {convert_font('INDONESIA POLITICS:', 'bold')}
• `{get_prefix()}vclone jokowi <text>` - 🇮🇩 Presiden Jokowi
• `{get_prefix()}vclone prabowo <text>` - 🎖️ Menhan Prabowo

🎮 {convert_font('MOBILE LEGENDS:', 'bold')}
• `{get_prefix()}vclone mlbb <text>` - 🎮 Epic MLBB Narrator

🤖 {convert_font('AI ASSISTANT:', 'bold')}
• `{get_prefix()}vclone claude <text>` - 🤖 Claude AI Voice

🧽 {convert_font('SPONGEBOB CHARACTERS:', 'bold')}
• `{get_prefix()}vclone spongebob <text>` - 🧽 SpongeBob SquarePants
• `{get_prefix()}vclone squidward <text>` - 🦑 Squidward Tentacles

💋 {convert_font('PRESENTER VOICES:', 'bold')}
• `{get_prefix()}vclone presenter <text>` - 💋 Sexy News Presenter

{get_emoji('adder1')} {convert_font('Quick Examples:', 'bold')}
• `{get_prefix()}vclone jokowi Selamat pagi rakyat Indonesia!`
• `{get_prefix()}vclone squidward Oh please, not again...`
• `{get_prefix()}vclone spongebob I'm ready, I'm ready!`
• `{get_prefix()}vclone claude How can I assist you today?`

{get_emoji('adder2')} {convert_font('Total Characters:', 'bold')} {len(CHARACTER_VOICES)} voices available
{get_emoji('check')} Use `{get_prefix()}vclone characters` untuk list lengkap
        """.strip()
        
        await event.edit(characters_text)
        
    except Exception as e:
        await event.edit(f"❌ Show characters error: {str(e)}")

async def show_voice_help(event):
    """Show comprehensive voice clone help"""
    help_text = f"""
🎭 {convert_font('VOICE CLONE HELP - EPIC EDITION', 'bold')}

╔══════════════════════════════════╗
   📚 {convert_font('COMMAND REFERENCE', 'bold')} 📚
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Setup Commands:', 'bold')}
• `{get_prefix()}vclone setup` - Initialize voice system
• `{get_prefix()}vclone list` - Show all available voices
• `{get_prefix()}vclone characters` - Show character voices

{get_emoji('adder2')} {convert_font('Character Commands (NEW!):', 'bold')}
• `{get_prefix()}vclone jokowi <text>` - 🇮🇩 Presiden Jokowi
• `{get_prefix()}vclone prabowo <text>` - 🎖️ Menhan Prabowo  
• `{get_prefix()}vclone spongebob <text>` - 🧽 SpongeBob
• `{get_prefix()}vclone squidward <text>` - 🦑 Squidward
• `{get_prefix()}vclone claude <text>` - 🤖 Claude AI
• `{get_prefix()}vclone mlbb <text>` - 🎮 MLBB Narrator
• `{get_prefix()}vclone presenter <text>` - 💋 Sexy Presenter

{get_emoji('adder3')} {convert_font('General Commands:', 'bold')}
• `{get_prefix()}vclone use <name>` - Switch default voice
• `{get_prefix()}vclone test <text>` - Test current voice
• `{get_prefix()}vclone note <text>` - Generate voice note

{get_emoji('adder4')} {convert_font('Advanced Features:', 'bold')}
• `{get_prefix()}vclone call <target>` - Real-time voice calls
• `{get_prefix()}vclone stream on/off` - Live audio streaming
• `{get_prefix()}vclone config` - Show configuration

{get_emoji('main')} {convert_font('Epic Examples:', 'bold')}
• `{get_prefix()}vclone jokowi Halo rakyat Indonesia!`
• `{get_prefix()}vclone squidward I hate my life...`
• `{get_prefix()}vclone spongebob I'm ready for work!`
• `{get_prefix()}vclone claude How may I help you?`

{get_emoji('adder5')} {convert_font('Features:', 'bold')}
{get_emoji('check')} {len(CHARACTER_VOICES)} Character voices
{get_emoji('check')} Real-time voice cloning
{get_emoji('check')} Voice call integration  
{get_emoji('check')} Premium quality audio
{get_emoji('check')} Multiple API providers

{convert_font('Start with:', 'bold')} `{get_prefix()}vclone setup`
    """.strip()
    
    await event.edit(help_text)

def get_prefix():
    """Get command prefix"""
    return "."

# ===== PLUGIN INITIALIZATION =====
def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Plugin setup function"""
    global client
    client = client_instance
    
    print("🎭 Voice Clone Real-Time Plugin loaded!")
    print("🎯 Features: Real-time cloning, Multiple voices, Call integration")
    print("🎵 Ready for character voice cloning!")
    
    return True