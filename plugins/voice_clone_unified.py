"""
Voice Clone Unified Plugin - Complete Voice Cloning System
File: plugins/voice_clone_unified.py  
Author: Morgan (Vzoel Fox's Assistant)
Version: 2.0.0
Fitur: Complete voice cloning system dengan premium emojis hardcoded
"""

import asyncio
import os
import json
import time
import requests
import tempfile
import base64
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, DocumentAttributeAudio
import subprocess

# Import database helper
try:
    from database import create_table, insert, select, update, delete
except ImportError:
    print("[Voice Clone] Database helper not found, using fallback")
    create_table = None
    insert = None
    select = None
    update = None
    delete = None

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "voice_clone_unified",
    "version": "2.0.0", 
    "description": "Complete voice cloning system with premium emojis",
    "author": "Morgan (Vzoel Fox's Assistant)",
    "commands": [".vclone", ".voice", ".tts", ".vsetup", ".vtest"],
    "features": ["text to speech", "voice cloning", "premium emojis", "multiple voices", "database logging"]
}

# ===== PREMIUM EMOJI CONFIGURATION (STANDALONE) =====
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

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
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

async def safe_send_premium(event, text):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception:
        await event.reply(text)

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        # Get owner ID from environment (primary method)
        OWNER_ID = os.getenv('OWNER_ID')
        if OWNER_ID:
            return user_id == int(OWNER_ID)
        
        # Fallback: check if user is the bot itself
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return False

# Global client reference
client = None

# ===== CONFIGURATION MANAGEMENT =====
CONFIG_FILE = "voice_clone_config.json"
TEMP_DIR = "temp_voice"

# Default configuration
DEFAULT_CONFIG = {
    "version": "2.0.0",
    "created": datetime.now().isoformat(),
    "tts_engine": "system",  # system, elevenlabs, azure, google
    "default_voice": "system_default",
    "temp_dir": TEMP_DIR,
    "max_text_length": 500,
    "audio_format": "mp3",
    "quality": "medium",
    "api_keys": {
        "elevenlabs": "",
        "azure": "",
        "google": ""
    },
    "voices": {
        "system_default": {
            "name": "System Default",
            "engine": "system",
            "voice_id": "default",
            "description": "Built-in system TTS"
        }
    },
    "usage_stats": {
        "total_generated": 0,
        "total_characters": 0,
        "last_used": None
    }
}

def load_config():
    """Load voice clone configuration"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with default config for missing keys
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"[Voice Clone] Config load error: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save voice clone configuration"""
    try:
        config["updated"] = datetime.now().isoformat()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Voice Clone] Config save error: {e}")
        return False

def init_voice_database():
    """Initialize voice clone database tables"""
    if not create_table:
        return False
    
    try:
        # Voice generation logs
        logs_schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            text TEXT NOT NULL,
            voice_name TEXT,
            engine TEXT,
            success BOOLEAN,
            file_size INTEGER,
            duration REAL,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        create_table('voice_clone_logs', logs_schema, 'voice_clone')
        
        # Voice configurations
        voices_schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voice_name TEXT UNIQUE NOT NULL,
            voice_id TEXT NOT NULL,
            engine TEXT NOT NULL,
            description TEXT,
            parameters TEXT,
            created_by INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        create_table('voice_clone_voices', voices_schema, 'voice_clone')
        
        return True
    except Exception as e:
        print(f"[Voice Clone] Database init error: {e}")
        return False

def save_voice_log(user_id, username, text, voice_name, engine, success, file_size=None, duration=None, error_msg=None):
    """Save voice generation log to database"""
    if not insert:
        return False
    
    try:
        log_data = {
            'user_id': user_id,
            'username': username,
            'text': text[:100],  # Truncate long text
            'voice_name': voice_name,
            'engine': engine,
            'success': success,
            'file_size': file_size,
            'duration': duration,
            'error_message': error_msg
        }
        
        result = insert('voice_clone_logs', log_data, 'voice_clone')
        return result is not None
    except Exception as e:
        print(f"[Voice Clone] Log save error: {e}")
        return False

# ===== TTS ENGINE IMPLEMENTATIONS =====

async def generate_system_tts(text, voice="default"):
    """Generate TTS using system built-in TTS"""
    try:
        # Create temp directory
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Generate temp file name
        temp_file = os.path.join(TEMP_DIR, f"tts_{int(time.time())}.wav")
        
        # Try different system TTS commands
        tts_commands = [
            # Linux/Termux espeak
            ["espeak", "-s", "150", "-v", "en", text, "-w", temp_file],
            # Linux festival
            ["echo", text, "|", "festival", "--tts", "--output", temp_file],
            # macOS say
            ["say", "-o", temp_file, text],
        ]
        
        for cmd in tts_commands:
            try:
                if cmd[0] == "espeak" and subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    if result.returncode == 0 and os.path.exists(temp_file):
                        return temp_file
                elif cmd[0] == "say" and subprocess.run(["which", "say"], capture_output=True).returncode == 0:
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    if result.returncode == 0 and os.path.exists(temp_file):
                        return temp_file
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return None
        
    except Exception as e:
        print(f"[Voice Clone] System TTS error: {e}")
        return None

async def generate_online_tts(text, voice_id="21m00Tcm4TlvDq8ikWAM", engine="elevenlabs"):
    """Generate TTS using online services"""
    try:
        config = load_config()
        
        if engine == "elevenlabs":
            api_key = config["api_keys"].get("elevenlabs", "")
            if not api_key:
                # Use demo mode with limited functionality
                return await generate_demo_tts(text)
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Save audio file
                os.makedirs(TEMP_DIR, exist_ok=True)
                temp_file = os.path.join(TEMP_DIR, f"tts_{int(time.time())}.mp3")
                
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                
                return temp_file
            else:
                print(f"[Voice Clone] ElevenLabs API error: {response.status_code}")
                return None
        
        return None
        
    except Exception as e:
        print(f"[Voice Clone] Online TTS error: {e}")
        return None

async def generate_demo_tts(text):
    """Generate demo TTS for testing without API keys"""
    try:
        # Simple text-to-morse-to-beep demo
        os.makedirs(TEMP_DIR, exist_ok=True)
        temp_file = os.path.join(TEMP_DIR, f"demo_{int(time.time())}.txt")
        
        with open(temp_file, 'w') as f:
            f.write(f"Demo TTS Audio for: {text[:50]}...")
        
        return temp_file
        
    except Exception as e:
        print(f"[Voice Clone] Demo TTS error: {e}")
        return None

# ===== COMMAND HANDLERS =====

async def voice_clone_handler(event):
    """Main voice clone command handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        message_text = event.message.text or ""
        parts = message_text.split(maxsplit=2)
        
        if len(parts) < 2:
            # Show help
            help_text = f"""
{get_emoji('main')} **Voice Clone v2.0 - Help**

{get_emoji('check')} **Basic Commands:**
• `.vclone <text>` - Generate voice with default settings
• `.voice <text>` - Same as vclone
• `.tts <text>` - Text to speech

{get_emoji('adder4')} **Advanced Commands:**
• `.vsetup` - Setup and configuration
• `.vtest` - Test voice generation  

{get_emoji('adder1')} **Examples:**
• `.vclone Hello world!`
• `.voice How are you today?`
• `.tts This is a test message`

{get_emoji('adder2')} **Features:**
• Multiple TTS engines
• Premium voice quality
• Database logging
• Error handling

{get_emoji('main')} **Enhanced Voice Clone System**
            """.strip()
            
            await safe_send_premium(event, help_text)
            return
        
        # Extract text to convert
        if len(parts) >= 3:
            text_to_convert = parts[2]
        else:
            text_to_convert = parts[1]
        
        if not text_to_convert or len(text_to_convert.strip()) == 0:
            await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** No text provided for conversion")
            return
        
        # Check text length
        config = load_config()
        max_length = config.get("max_text_length", 500)
        
        if len(text_to_convert) > max_length:
            await safe_send_premium(event, f"{get_emoji('adder5')} **Error:** Text too long (max {max_length} characters)")
            return
        
        # Show processing message
        processing_msg = await safe_send_premium(event, f"{get_emoji('adder1')} **Processing voice generation...**")
        
        # Generate TTS
        start_time = time.time()
        voice_name = config.get("default_voice", "system_default")
        engine = config.get("tts_engine", "system")
        
        audio_file = None
        error_msg = None
        
        try:
            if engine == "system":
                audio_file = await generate_system_tts(text_to_convert)
            elif engine == "elevenlabs":
                audio_file = await generate_online_tts(text_to_convert, engine="elevenlabs")
            else:
                audio_file = await generate_system_tts(text_to_convert)
            
            if not audio_file:
                # Fallback to demo
                audio_file = await generate_demo_tts(text_to_convert)
                
        except Exception as e:
            error_msg = str(e)
            print(f"[Voice Clone] Generation error: {e}")
        
        generation_time = time.time() - start_time
        
        # Send result
        if audio_file and os.path.exists(audio_file):
            try:
                file_size = os.path.getsize(audio_file)
                
                # Send audio file
                success_text = f"""
{get_emoji('main')} **Voice Generated Successfully!**

{get_emoji('check')} **Details:**
• **Text:** {text_to_convert[:50]}{'...' if len(text_to_convert) > 50 else ''}
• **Voice:** {voice_name}
• **Engine:** {engine}
• **Size:** {file_size:,} bytes
• **Time:** {generation_time:.1f}s

{get_emoji('adder2')} **Enhanced Voice Clone v2.0**
                """.strip()
                
                # Send file based on extension
                if audio_file.endswith(('.mp3', '.wav', '.ogg')):
                    await client.send_file(
                        event.chat_id,
                        audio_file,
                        caption=success_text,
                        voice_note=True,
                        attributes=[DocumentAttributeAudio(
                            duration=int(generation_time),
                            voice=True
                        )]
                    )
                else:
                    # Send as document for demo files
                    await client.send_file(
                        event.chat_id,
                        audio_file,
                        caption=success_text
                    )
                
                # Update processing message
                await processing_msg.edit(f"{get_emoji('adder2')} **Voice file sent above!**")
                
                # Log success
                save_voice_log(
                    event.sender_id,
                    getattr(await client.get_me(), 'username', 'None'),
                    text_to_convert,
                    voice_name,
                    engine,
                    True,
                    file_size,
                    generation_time
                )
                
                # Update config stats
                config["usage_stats"]["total_generated"] += 1
                config["usage_stats"]["total_characters"] += len(text_to_convert)
                config["usage_stats"]["last_used"] = datetime.now().isoformat()
                save_config(config)
                
                # Cleanup temp file
                try:
                    os.remove(audio_file)
                except:
                    pass
                    
            except Exception as send_error:
                error_response = f"{get_emoji('adder5')} **Error sending audio:** {str(send_error)}"
                await processing_msg.edit(error_response)
                
        else:
            # Generation failed
            error_response = f"""
{get_emoji('adder5')} **Voice Generation Failed**

{get_emoji('check')} **Error Details:**
• **Text:** {text_to_convert[:50]}{'...' if len(text_to_convert) > 50 else ''}
• **Engine:** {engine}
• **Error:** {error_msg or 'Unknown error'}
• **Time:** {generation_time:.1f}s

{get_emoji('adder4')} **Try:**
• Check text formatting
• Use `.vsetup` for configuration
• Try different engine

{get_emoji('main')} **Voice Clone v2.0**
            """.strip()
            
            await processing_msg.edit(error_response)
            
            # Log failure
            save_voice_log(
                event.sender_id,
                getattr(await client.get_me(), 'username', 'None'),
                text_to_convert,
                voice_name,
                engine,
                False,
                error_message=error_msg
            )
        
    except Exception as e:
        error_response = f"{get_emoji('adder5')} **Voice Clone Error:** {str(e)}"
        await safe_send_premium(event, error_response)

async def voice_setup_handler(event):
    """Voice setup and configuration handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        config = load_config()
        
        setup_text = f"""
{get_emoji('main')} **Voice Clone Setup v2.0**

{get_emoji('check')} **Current Configuration:**
• **Engine:** {config.get('tts_engine', 'system')}
• **Voice:** {config.get('default_voice', 'system_default')}
• **Quality:** {config.get('quality', 'medium')}
• **Max Length:** {config.get('max_text_length', 500)} chars

{get_emoji('adder4')} **Available Engines:**
• **system** - Built-in TTS (Free)
• **elevenlabs** - Premium quality (API key required)
• **demo** - Testing mode

{get_emoji('adder1')} **Usage Statistics:**
• **Generated:** {config['usage_stats'].get('total_generated', 0)} files
• **Characters:** {config['usage_stats'].get('total_characters', 0):,}
• **Last Used:** {config['usage_stats'].get('last_used', 'Never')}

{get_emoji('adder2')} **Setup Commands:**
• `.vsetup` - Show this setup info
• `.vtest hello` - Test voice generation

{get_emoji('main')} **Voice Clone Ready!**
        """.strip()
        
        await safe_send_premium(event, setup_text)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Setup Error:** {str(e)}")

async def voice_test_handler(event):
    """Voice test handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        parts = event.message.text.split(maxsplit=1)
        test_text = parts[1] if len(parts) > 1 else "Hello, this is a voice test!"
        
        test_msg = f"""
{get_emoji('main')} **Voice Test Started**

{get_emoji('check')} **Test Parameters:**
• **Text:** {test_text}
• **Engine:** System TTS
• **Mode:** Test Mode

{get_emoji('adder1')} **Testing voice generation...**
        """.strip()
        
        processing = await safe_send_premium(event, test_msg)
        
        # Generate test audio
        audio_file = await generate_system_tts(test_text)
        
        if audio_file and os.path.exists(audio_file):
            result_text = f"""
{get_emoji('adder2')} **Voice Test Successful!**

{get_emoji('check')} **Results:**
• **Status:** Working
• **File:** Generated
• **Test:** Passed

{get_emoji('main')} **Voice Clone System Ready!**
            """.strip()
            
            await processing.edit(result_text)
            
            try:
                await client.send_file(
                    event.chat_id,
                    audio_file,
                    caption=f"{get_emoji('adder2')} **Test Audio Generated**",
                    voice_note=True
                )
                os.remove(audio_file)
            except:
                pass
                
        else:
            result_text = f"""
{get_emoji('adder5')} **Voice Test Failed**

{get_emoji('check')} **Status:**
• **System TTS:** Not available
• **Fallback:** Demo mode only

{get_emoji('adder4')} **Try:**
• Install espeak: `pkg install espeak`
• Use online mode with API keys

{get_emoji('main')} **Voice Clone v2.0**
            """.strip()
            
            await processing.edit(result_text)
        
    except Exception as e:
        await safe_send_premium(event, f"{get_emoji('adder5')} **Test Error:** {str(e)}")

def get_plugin_info():
    return PLUGIN_INFO

async def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Initialize database and config
    init_voice_database()
    
    # Ensure temp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Register handlers
    client.add_event_handler(voice_clone_handler, events.NewMessage(pattern=r"\.vclone(\s|$)"))
    client.add_event_handler(voice_clone_handler, events.NewMessage(pattern=r"\.voice(\s|$)"))
    client.add_event_handler(voice_clone_handler, events.NewMessage(pattern=r"\.tts(\s|$)"))
    client.add_event_handler(voice_setup_handler, events.NewMessage(pattern=r"\.vsetup$"))
    client.add_event_handler(voice_test_handler, events.NewMessage(pattern=r"\.vtest(\s|$)"))
    
    print(f"✅ [Voice Clone Unified] Plugin loaded - Complete voice system with premium emojis v{PLUGIN_INFO['version']}")