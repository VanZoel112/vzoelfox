#!/usr/bin/env python3
"""
🤖 AIMODE LLAMA2 PLUGIN - Advanced AI Integration
Fitur: LLaMA2, GPT, Claude, Groq, Ollama support dengan premium emoji
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - LLaMA2 Edition
"""

import asyncio
import sqlite3
import os
import json
import time
import random
import re
from datetime import datetime
from telethon import events

# Try aiohttp first, fallback to requests
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    import requests
    print("⚠️ aiohttp not available, using requests as fallback")

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "aimode_llama2",
    "version": "2.0.0",
    "description": "🤖 Advanced AI Mode dengan LLaMA2, GPT, Claude, dan multiple AI providers",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".ai <text>", ".aimode on/off", ".aimode status", ".aiconfig", 
        ".aimodel <model>", ".aillama <text>", ".aigpt <text>", ".aiclaude <text>"
    ],
    "features": [
        "LLaMA2 integration", "Multiple AI providers", "Smart model switching",
        "Response caching", "Context awareness", "Premium emoji support"
    ]
}

# ===== CONFIGURATION =====
DB_FILE = "plugins/aimode_llama2.db"

# Multiple AI Providers Configuration
AI_PROVIDERS = {
    "llama2": {
        "name": "LLaMA 2",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama2-70b-4096",
        "headers": {"Authorization": "Bearer YOUR_GROQ_API_KEY"},
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "llama2_13b": {
        "name": "LLaMA 2 13B",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions", 
        "model": "llama2-13b-4096",
        "headers": {"Authorization": "Bearer YOUR_GROQ_API_KEY"},
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "mixtral": {
        "name": "Mixtral 8x7B",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": "mixtral-8x7b-32768", 
        "headers": {"Authorization": "Bearer YOUR_GROQ_API_KEY"},
        "max_tokens": 32768,
        "temperature": 0.7
    },
    "gpt4": {
        "name": "GPT-4",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4",
        "headers": {"Authorization": "Bearer YOUR_OPENAI_API_KEY"},
        "max_tokens": 8192,
        "temperature": 0.7
    },
    "gpt3_turbo": {
        "name": "GPT-3.5 Turbo", 
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-3.5-turbo",
        "headers": {"Authorization": "Bearer YOUR_OPENAI_API_KEY"},
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "claude": {
        "name": "Claude 3",
        "endpoint": "https://api.anthropic.com/v1/messages",
        "model": "claude-3-sonnet-20240229",
        "headers": {
            "Authorization": "Bearer YOUR_ANTHROPIC_API_KEY",
            "anthropic-version": "2023-06-01"
        },
        "max_tokens": 4096,
        "temperature": 0.7
    },
    "ollama": {
        "name": "Ollama Local",
        "endpoint": "http://localhost:11434/api/generate",
        "model": "llama2",
        "headers": {"Content-Type": "application/json"},
        "max_tokens": 4096,
        "temperature": 0.7
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
current_model = "llama2"
ai_mode_enabled = False
last_response_time = 0
conversation_context = []
MAX_CONTEXT_LENGTH = 10

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
def init_ai_db():
    """Initialize AI database with enhanced tables"""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # AI settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_settings (
                id INTEGER PRIMARY KEY,
                ai_mode_enabled BOOLEAN DEFAULT 0,
                current_model TEXT DEFAULT 'llama2',
                api_keys TEXT,
                system_prompt TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 4096,
                context_enabled BOOLEAN DEFAULT 1,
                auto_model_switch BOOLEAN DEFAULT 1,
                cooldown INTEGER DEFAULT 5,
                total_requests INTEGER DEFAULT 0,
                last_updated TEXT
            )
        ''')
        
        # Conversation logs with context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                model_used TEXT NOT NULL,
                context_data TEXT,
                response_time REAL,
                tokens_used INTEGER,
                timestamp TEXT NOT NULL,
                chat_id INTEGER,
                user_id INTEGER,
                success BOOLEAN DEFAULT 1
            )
        ''')
        
        # Model performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                average_response_time REAL DEFAULT 0,
                total_tokens_used INTEGER DEFAULT 0,
                last_used TEXT,
                performance_score REAL DEFAULT 0
            )
        ''')
        
        # Insert default settings
        cursor.execute('SELECT COUNT(*) FROM ai_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO ai_settings (
                    id, ai_mode_enabled, current_model, system_prompt,
                    temperature, max_tokens, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                1, False, 'llama2',
                'You are a helpful AI assistant. Respond in Indonesian or English as appropriate.',
                0.7, 4096, datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"AI DB init error: {e}")
        return False

def get_ai_settings():
    """Get current AI settings"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ai_mode_enabled, current_model, system_prompt, temperature, 
                   max_tokens, context_enabled, auto_model_switch, cooldown, total_requests
            FROM ai_settings WHERE id = 1
        ''')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'enabled': bool(result[0]),
                'model': result[1],
                'system_prompt': result[2],
                'temperature': result[3],
                'max_tokens': result[4],
                'context_enabled': bool(result[5]),
                'auto_switch': bool(result[6]),
                'cooldown': result[7],
                'total_requests': result[8]
            }
        return None
    except Exception as e:
        print(f"Get AI settings error: {e}")
        return None

def save_ai_settings(**kwargs):
    """Save AI settings to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        for key, value in kwargs.items():
            if key in ['enabled', 'ai_mode_enabled']:
                cursor.execute('UPDATE ai_settings SET ai_mode_enabled = ? WHERE id = 1', (value,))
            elif key == 'model':
                cursor.execute('UPDATE ai_settings SET current_model = ? WHERE id = 1', (value,))
            elif key == 'system_prompt':
                cursor.execute('UPDATE ai_settings SET system_prompt = ? WHERE id = 1', (value,))
            elif key == 'temperature':
                cursor.execute('UPDATE ai_settings SET temperature = ? WHERE id = 1', (value,))
            elif key == 'max_tokens':
                cursor.execute('UPDATE ai_settings SET max_tokens = ? WHERE id = 1', (value,))
        
        cursor.execute('UPDATE ai_settings SET last_updated = ? WHERE id = 1', (datetime.now().isoformat(),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Save AI settings error: {e}")
        return False

def log_ai_conversation(user_msg, ai_response, model, response_time=0, tokens=0, success=True, chat_id=0, user_id=0):
    """Log AI conversation to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Insert conversation log
        cursor.execute('''
            INSERT INTO ai_conversations (
                user_message, ai_response, model_used, response_time,
                tokens_used, timestamp, chat_id, user_id, success
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_msg, ai_response, model, response_time, tokens,
            datetime.now().isoformat(), chat_id, user_id, success
        ))
        
        # Update total requests
        cursor.execute('UPDATE ai_settings SET total_requests = total_requests + 1 WHERE id = 1')
        
        # Update model performance
        cursor.execute('''
            INSERT OR IGNORE INTO model_performance (model_name, total_requests, successful_requests, last_used)
            VALUES (?, 0, 0, ?)
        ''', (model, datetime.now().isoformat()))
        
        cursor.execute('''
            UPDATE model_performance SET
                total_requests = total_requests + 1,
                successful_requests = successful_requests + ?,
                total_tokens_used = total_tokens_used + ?,
                last_used = ?,
                average_response_time = (average_response_time + ?) / 2
            WHERE model_name = ?
        ''', (1 if success else 0, tokens, datetime.now().isoformat(), response_time, model))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Log conversation error: {e}")
        return False

# ===== AI API FUNCTIONS =====
async def call_ai_api(message, model_name=None, use_context=True):
    """Call AI API with specified model (supports both aiohttp and requests)"""
    global conversation_context, current_model
    
    if not model_name:
        model_name = current_model
    
    if model_name not in AI_PROVIDERS:
        return None, f"Model '{model_name}' tidak tersedia"
    
    provider = AI_PROVIDERS[model_name]
    start_time = time.time()
    
    try:
        # Prepare context
        messages = []
        if use_context and conversation_context:
            messages.extend(conversation_context[-MAX_CONTEXT_LENGTH:])
        
        messages.append({"role": "user", "content": message})
        
        # Prepare request payload based on provider
        if model_name == "ollama":
            payload = {
                "model": provider["model"],
                "prompt": message,
                "stream": False,
                "options": {
                    "temperature": provider["temperature"],
                    "num_predict": provider["max_tokens"]
                }
            }
        elif model_name.startswith("claude"):
            # Anthropic Claude API format
            payload = {
                "model": provider["model"],
                "max_tokens": provider["max_tokens"],
                "temperature": provider["temperature"],
                "messages": messages
            }
        else:
            # OpenAI/Groq format (most common)
            payload = {
                "model": provider["model"],
                "messages": messages,
                "max_tokens": provider["max_tokens"],
                "temperature": provider["temperature"]
            }
        
        # Make API request - with aiohttp or requests fallback
        if AIOHTTP_AVAILABLE:
            # Use aiohttp (async)
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    provider["endpoint"],
                    headers=provider["headers"],
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                    else:
                        error_text = await response.text()
                        return None, f"API Error {response.status}: {error_text}"
        else:
            # Use requests (sync, but wrapped in async)
            try:
                response = requests.post(
                    provider["endpoint"],
                    headers=provider["headers"],
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                else:
                    return None, f"API Error {response.status_code}: {response.text}"
            except requests.RequestException as e:
                return None, f"Request error: {str(e)}"
        
        # Parse response based on provider
        if model_name == "ollama":
            ai_response = data.get("response", "")
        elif model_name.startswith("claude"):
            ai_response = data.get("content", [{}])[0].get("text", "")
        else:
            # OpenAI/Groq format
            ai_response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Calculate metrics
        response_time = time.time() - start_time
        tokens_used = data.get("usage", {}).get("total_tokens", 0)
        
        # Update conversation context
        if use_context:
            conversation_context.append({"role": "user", "content": message})
            conversation_context.append({"role": "assistant", "content": ai_response})
            
            # Keep context manageable
            if len(conversation_context) > MAX_CONTEXT_LENGTH * 2:
                conversation_context = conversation_context[-MAX_CONTEXT_LENGTH:]
        
        return ai_response, None
                
    except asyncio.TimeoutError:
        return None, "Request timeout - model mungkin sedang busy"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

async def smart_model_fallback(message, preferred_models=None):
    """Smart model fallback system"""
    if not preferred_models:
        preferred_models = ["llama2", "mixtral", "gpt3_turbo", "llama2_13b"]
    
    for model in preferred_models:
        if model in AI_PROVIDERS:
            try:
                response, error = await call_ai_api(message, model, use_context=True)
                if response:
                    return response, model, None
                else:
                    continue
            except Exception as e:
                continue
    
    return None, None, "Semua AI model tidak tersedia saat ini"

# ===== COMMAND HANDLERS =====
@client.on(events.NewMessage(pattern=re.compile(r'\.ai\s+(.+)', re.DOTALL)))
async def ai_chat_handler(event):
    """Main AI chat handler"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        user_message = event.pattern_match.group(1).strip()
        
        # Initialize database
        init_ai_db()
        settings = get_ai_settings()
        if not settings:
            await event.edit("❌ AI system belum dikonfigurasi. Gunakan `.aiconfig`")
            return
        
        # Show typing indicator
        loading_msg = await event.edit(f"""
{get_emoji('main')} {convert_font('AI PROCESSING...', 'bold')}

{get_emoji('adder1')} Model: {AI_PROVIDERS[current_model]['name']}
{get_emoji('check')} Processing your request...
        """.strip())
        
        # Get AI response
        if settings['auto_switch']:
            ai_response, used_model, error = await smart_model_fallback(user_message)
        else:
            ai_response, error = await call_ai_api(user_message, current_model)
            used_model = current_model
        
        if ai_response:
            # Format response
            response_text = f"""
{get_emoji('main')} {convert_font('AI RESPONSE', 'bold')}

╔══════════════════════════════════╗
   🤖 {convert_font(AI_PROVIDERS[used_model]['name'].upper(), 'bold')} 🤖
╚══════════════════════════════════╝

{get_emoji('adder2')} {convert_font('Your Question:', 'bold')}
"{user_message}"

{get_emoji('adder4')} {convert_font('AI Answer:', 'bold')}
{ai_response}

{get_emoji('check')} Model: {AI_PROVIDERS[used_model]['name']}
{get_emoji('check')} Context: {'Enabled' if settings['context_enabled'] else 'Disabled'}
            """.strip()
            
            await loading_msg.edit(response_text)
            
            # Log conversation
            log_ai_conversation(
                user_message, ai_response, used_model, 
                chat_id=event.chat_id, user_id=event.sender_id, success=True
            )
            
        else:
            error_text = f"""
{get_emoji('adder3')} {convert_font('AI ERROR', 'bold')}

❌ {error or 'Unknown error occurred'}

{get_emoji('check')} Try again atau gunakan `.aimodel` untuk switch model
{get_emoji('check')} Available models: {', '.join(AI_PROVIDERS.keys())}
            """.strip()
            
            await loading_msg.edit(error_text)
            log_ai_conversation(user_message, error or "Error", used_model or current_model, success=False)
        
    except Exception as e:
        await event.edit(f"❌ AI handler error: {str(e)}")

@client.on(events.NewMessage(pattern=re.compile(r'\.aillama\s+(.+)', re.DOTALL)))
async def llama2_handler(event):
    """Dedicated LLaMA2 handler"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        user_message = event.pattern_match.group(1).strip()
        
        loading_msg = await event.edit(f"""
{get_emoji('main')} {convert_font('LLAMA2 PROCESSING...', 'bold')}

🦙 {convert_font('LLaMA 2 70B Model Active', 'bold')}
{get_emoji('check')} Processing with advanced reasoning...
        """.strip())
        
        # Force LLaMA2 model
        ai_response, error = await call_ai_api(user_message, "llama2", use_context=True)
        
        if ai_response:
            response_text = f"""
🦙 {convert_font('LLAMA2 RESPONSE', 'bold')}

╔══════════════════════════════════╗
   🤖 {convert_font('META LLAMA 2 70B', 'bold')} 🤖
╚══════════════════════════════════╝

{get_emoji('adder2')} {convert_font('Question:', 'bold')}
"{user_message}"

{get_emoji('adder4')} {convert_font('LLaMA2 Answer:', 'bold')}
{ai_response}

{get_emoji('check')} Model: Meta LLaMA 2 70B
{get_emoji('check')} Powered by Groq (Ultra Fast)
            """.strip()
            
            await loading_msg.edit(response_text)
        else:
            await loading_msg.edit(f"❌ LLaMA2 error: {error}")
        
    except Exception as e:
        await event.edit(f"❌ LLaMA2 handler error: {str(e)}")

@client.on(events.NewMessage(pattern=r'\.aimodel\s+(.+)'))
async def switch_model_handler(event):
    """Switch AI model"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        model_name = event.pattern_match.group(1).strip().lower()
        
        if model_name in AI_PROVIDERS:
            global current_model
            current_model = model_name
            save_ai_settings(model=model_name)
            
            model_info = AI_PROVIDERS[model_name]
            await event.edit(f"""
{get_emoji('check')} {convert_font('MODEL SWITCHED!', 'bold')}

╔══════════════════════════════════╗
   🤖 {convert_font('NEW AI MODEL ACTIVE', 'bold')} 🤖
╚══════════════════════════════════╝

{get_emoji('main')} {convert_font('Model:', 'bold')} {model_info['name']}
{get_emoji('check')} {convert_font('Max Tokens:', 'bold')} {model_info['max_tokens']}
{get_emoji('check')} {convert_font('Temperature:', 'bold')} {model_info['temperature']}

{get_emoji('adder2')} Model siap digunakan dengan `.ai <text>`
            """.strip())
        else:
            models_list = '\n'.join([f"• {key}: {val['name']}" for key, val in AI_PROVIDERS.items()])
            await event.edit(f"""
❌ Model '{model_name}' tidak tersedia

{get_emoji('main')} {convert_font('Available Models:', 'bold')}
{models_list}

Usage: `.aimodel llama2`
            """.strip())
        
    except Exception as e:
        await event.edit(f"❌ Switch model error: {str(e)}")

@client.on(events.NewMessage(pattern=r'\.aimode\s?(.*)?'))
async def aimode_handler(event):
    """AI mode management"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        args = event.pattern_match.group(1).strip().split() if event.pattern_match.group(1) else []
        command = args[0].lower() if args else 'status'
        
        init_ai_db()
        
        if command == 'on':
            save_ai_settings(enabled=True)
            global ai_mode_enabled
            ai_mode_enabled = True
            
            await event.edit(f"""
{get_emoji('main')} {convert_font('AI MODE ACTIVATED!', 'bold')}

╔══════════════════════════════════╗
   🤖 {convert_font('ADVANCED AI SYSTEM ONLINE', 'bold')} 🤖
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} ACTIVE
{get_emoji('check')} {convert_font('Current Model:', 'bold')} {AI_PROVIDERS[current_model]['name']}
{get_emoji('check')} {convert_font('Smart Fallback:', 'bold')} Enabled
{get_emoji('check')} {convert_font('Context Memory:', 'bold')} Enabled

{get_emoji('adder1')} {convert_font('Available Models:', 'bold')}
• LLaMA 2 70B (Groq) - Ultra Fast
• LLaMA 2 13B - Balanced
• Mixtral 8x7B - Advanced Reasoning
• GPT-4 - Premium Intelligence
• Claude 3 - Anthropic AI

{get_emoji('adder2')} Use `.ai <text>` untuk chat dengan AI
            """.strip())
            
        elif command == 'off':
            save_ai_settings(enabled=False)
            ai_mode_enabled = False
            
            await event.edit(f"""
{get_emoji('adder3')} {convert_font('AI MODE DEACTIVATED', 'bold')}

{get_emoji('check')} AI mode disabled
{get_emoji('check')} Auto responses stopped
{get_emoji('check')} Settings saved

Use `.aimode on` untuk mengaktifkan kembali
            """.strip())
            
        else:  # status
            settings = get_ai_settings()
            if settings:
                await event.edit(f"""
{get_emoji('main')} {convert_font('AI MODE STATUS', 'bold')}

╔══════════════════════════════════╗
   📊 {convert_font('AI SYSTEM DASHBOARD', 'bold')} 📊
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} {'🟢 ACTIVE' if settings['enabled'] else '🔴 INACTIVE'}
{get_emoji('check')} {convert_font('Current Model:', 'bold')} {AI_PROVIDERS[settings['model']]['name']}
{get_emoji('check')} {convert_font('Total Requests:', 'bold')} {settings['total_requests']}
{get_emoji('check')} {convert_font('Smart Fallback:', 'bold')} {'✅' if settings['auto_switch'] else '❌'}
{get_emoji('check')} {convert_font('Context Memory:', 'bold')} {'✅' if settings['context_enabled'] else '❌'}

{get_emoji('adder1')} {convert_font('Available Commands:', 'bold')}
• `.ai <text>` - Chat dengan AI
• `.aillama <text>` - LLaMA2 khusus
• `.aimodel <name>` - Switch model
• `.aiconfig` - Configuration

{get_emoji('adder2')} {convert_font('Quick Models:', 'bold')}
• llama2, mixtral, gpt4, claude
                """.strip())
            else:
                await event.edit("❌ AI system belum dikonfigurasi")
        
    except Exception as e:
        await event.edit(f"❌ AI mode error: {str(e)}")

# ===== PLUGIN INITIALIZATION =====
def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Plugin setup function"""
    global client, current_model, ai_mode_enabled
    client = client_instance
    
    # Initialize database
    init_ai_db()
    
    # Load settings
    settings = get_ai_settings()
    if settings:
        current_model = settings['model']
        ai_mode_enabled = settings['enabled']
    
    print(f"🤖 AI Mode LLaMA2 Plugin loaded! Model: {AI_PROVIDERS[current_model]['name']}")
    return True