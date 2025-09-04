#!/usr/bin/env python3
"""
AIMode Simple Plugin for Vzoel Assistant (No External Dependencies)
Fitur: Mode AI sederhana tanpa external API untuk testing
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0 - Simple Edition
"""

import sqlite3
import os
import json
import time
import random
from datetime import datetime
from telethon import events

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "aimode_simple",
    "version": "1.0.0",
    "description": "AI Mode sederhana tanpa external dependencies untuk testing",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".aimode on", ".aimode off", ".aimode status", ".ai <text>"],
    "features": ["ai mode toggle", "simple ai responses", "status persist"]
}

# ===== CONFIGURATION =====
DB_FILE = "plugins/aimode_simple.db"
AI_RESPONSES = [
    "Itu pertanyaan yang menarik! 🤔",
    "Hmm, biar saya pikirkan dulu... 💭", 
    "Sebenarnya, menurut saya... 🧠",
    "Wah, topik yang kompleks nih! 📚",
    "Saya setuju dengan pendapat kamu! ✅",
    "Bisa dijelaskan lebih detail? 🔍",
    "Kalau dari sudut pandang saya... 👀",
    "Itu ide yang brilian! 💡",
    "Mungkin kita bisa coba approach lain? 🚀",
    "Saya masih belajar tentang ini... 📖"
]

# Premium emoji configuration
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
}

# Unicode fonts
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
ai_mode_enabled = False
last_ai_response = 0
cooldown = 10  # 10 seconds

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
def init_aimode_db():
    """Initialize AI mode database"""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # AI mode settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_settings (
                id INTEGER PRIMARY KEY,
                ai_mode_enabled BOOLEAN DEFAULT 0,
                cooldown INTEGER DEFAULT 10,
                total_responses INTEGER DEFAULT 0,
                last_updated TEXT
            )
        ''')
        
        # AI response logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT,
                ai_response TEXT,
                timestamp TEXT,
                chat_id INTEGER,
                user_id INTEGER
            )
        ''')
        
        # Insert default settings if not exists
        cursor.execute('SELECT COUNT(*) FROM ai_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO ai_settings (id, ai_mode_enabled, cooldown, total_responses, last_updated)
                VALUES (1, 0, 10, 0, ?)
            ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"AI DB init error: {e}")
        return False

def get_ai_settings():
    """Get AI mode settings from database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT ai_mode_enabled, cooldown, total_responses FROM ai_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'enabled': bool(result[0]),
                'cooldown': result[1],
                'total_responses': result[2]
            }
        return {'enabled': False, 'cooldown': 10, 'total_responses': 0}
    except Exception:
        return {'enabled': False, 'cooldown': 10, 'total_responses': 0}

def save_ai_settings(enabled=None, cooldown=None):
    """Save AI mode settings to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if enabled is not None:
            cursor.execute('UPDATE ai_settings SET ai_mode_enabled = ?, last_updated = ? WHERE id = 1', 
                          (enabled, datetime.now().isoformat()))
        
        if cooldown is not None:
            cursor.execute('UPDATE ai_settings SET cooldown = ?, last_updated = ? WHERE id = 1', 
                          (cooldown, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Save AI settings error: {e}")
        return False

def log_ai_response(user_message, ai_response, chat_id, user_id):
    """Log AI response to database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_logs (user_message, ai_response, timestamp, chat_id, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_message, ai_response, datetime.now().isoformat(), chat_id, user_id))
        
        # Update total responses count
        cursor.execute('UPDATE ai_settings SET total_responses = total_responses + 1 WHERE id = 1')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Log AI response error: {e}")
        return False

# ===== AI RESPONSE FUNCTIONS =====
def generate_simple_response(message_text):
    """Generate simple AI response"""
    try:
        message_lower = message_text.lower().strip()
        
        # Specific responses for common questions
        if any(word in message_lower for word in ['halo', 'hai', 'hello', 'hi']):
            responses = [
                f"{get_emoji('main')} Halo juga! Apa kabar hari ini?",
                f"{get_emoji('check')} Hai! Ada yang bisa saya bantu?",
                f"{get_emoji('adder1')} Hello! Selamat datang!"
            ]
        elif any(word in message_lower for word in ['apa kabar', 'how are you', 'gimana']):
            responses = [
                f"{get_emoji('check')} Saya baik-baik saja! Terima kasih sudah bertanya.",
                f"{get_emoji('main')} Baik sekali! Bagaimana dengan kamu?",
                f"{get_emoji('adder2')} Alhamdulillah sehat! Kamu gimana?"
            ]
        elif any(word in message_lower for word in ['terima kasih', 'thanks', 'makasih']):
            responses = [
                f"{get_emoji('check')} Sama-sama! Senang bisa membantu.",
                f"{get_emoji('main')} You're welcome!",
                f"{get_emoji('adder1')} Dengan senang hati!"
            ]
        elif any(word in message_lower for word in ['siapa kamu', 'who are you', 'kamu siapa']):
            responses = [
                f"{get_emoji('adder3')} Saya AI assistant dari Vzoel Fox's userbot!",
                f"{get_emoji('main')} Saya adalah AI helper yang siap membantu kamu.",
                f"{get_emoji('check')} Saya bot AI sederhana yang dibuat untuk membantu."
            ]
        elif '?' in message_text:
            # For questions
            responses = [
                f"{get_emoji('adder1')} Pertanyaan yang menarik! {random.choice(AI_RESPONSES)}",
                f"{get_emoji('main')} Hmm, biar saya pikirkan... {random.choice(AI_RESPONSES)}",
                f"{get_emoji('check')} {random.choice(AI_RESPONSES)}"
            ]
        else:
            # General responses
            responses = [
                f"{get_emoji('main')} {random.choice(AI_RESPONSES)}",
                f"{get_emoji('check')} Saya mengerti maksud kamu. {random.choice(AI_RESPONSES)}",
                f"{get_emoji('adder2')} {random.choice(AI_RESPONSES)}"
            ]
        
        return random.choice(responses)
        
    except Exception as e:
        print(f"Generate response error: {e}")
        return f"{get_emoji('adder3')} Maaf, saya sedang bingung nih... 🤔"

# ===== COMMAND HANDLERS =====
@client.on(events.NewMessage(pattern=r'\.aimode\s?(.*)?'))
async def aimode_command_handler(event):
    """AI Mode command handler"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        args = event.pattern_match.group(1).strip().split() if event.pattern_match.group(1) else []
        command = args[0].lower() if args else 'status'
        
        # Initialize database
        init_aimode_db()
        
        if command == 'on':
            await enable_aimode(event)
        elif command == 'off':
            await disable_aimode(event)
        elif command == 'status':
            await aimode_status(event)
        else:
            await aimode_help(event)
            
    except Exception as e:
        await event.reply(f"{get_emoji('adder5')} AI Mode error: {str(e)}")

async def enable_aimode(event):
    """Enable AI mode"""
    global ai_mode_enabled
    
    save_ai_settings(enabled=True)
    ai_mode_enabled = True
    
    await event.edit(f"""
{get_emoji('main')} {convert_font('AI MODE ACTIVATED!', 'bold')}

╔══════════════════════════════════╗
   🤖 {convert_font('AI ASSISTANT ONLINE', 'bold')} 🤖
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} ACTIVE
{get_emoji('check')} {convert_font('Response Type:', 'bold')} Simple AI
{get_emoji('check')} {convert_font('Cooldown:', 'bold')} {cooldown} seconds
{get_emoji('check')} {convert_font('Database:', 'bold')} Initialized

{get_emoji('adder1')} {convert_font('AI Features:', 'bold')}
• Contextual responses
• Smart question answering  
• Greeting detection
• Response logging

{get_emoji('adder2')} Sekarang saya akan merespon pesan otomatis!
Use `.ai <text>` untuk test response.
    """.strip())

async def disable_aimode(event):
    """Disable AI mode"""
    global ai_mode_enabled
    
    save_ai_settings(enabled=False)
    ai_mode_enabled = False
    
    await event.edit(f"""
{get_emoji('adder3')} {convert_font('AI MODE DEACTIVATED', 'bold')}

╔══════════════════════════════════╗
   🛑 {convert_font('AI ASSISTANT OFFLINE', 'bold')} 🛑
╚══════════════════════════════════╝

{get_emoji('check')} AI mode disabled
{get_emoji('check')} Auto responses stopped
{get_emoji('check')} Settings saved to database

Use `.aimode on` untuk mengaktifkan kembali.
    """.strip())

async def aimode_status(event):
    """Show AI mode status"""
    settings = get_ai_settings()
    
    status_text = f"""
{get_emoji('main')} {convert_font('AI MODE STATUS', 'bold')}

╔══════════════════════════════════╗
   📊 {convert_font('AI ASSISTANT DASHBOARD', 'bold')} 📊
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} {'🟢 ACTIVE' if settings['enabled'] else '🔴 INACTIVE'}
{get_emoji('check')} {convert_font('Response Type:', 'bold')} Simple AI
{get_emoji('check')} {convert_font('Cooldown:', 'bold')} {settings['cooldown']} seconds
{get_emoji('check')} {convert_font('Total Responses:', 'bold')} `{settings['total_responses']}`

{get_emoji('adder1')} {convert_font('Available Commands:', 'bold')}
• `.aimode on` - Enable AI mode
• `.aimode off` - Disable AI mode
• `.ai <text>` - Test AI response

{get_emoji('adder2')} {convert_font('Features:', 'bold')}
{get_emoji('check')} Smart contextual responses
{get_emoji('check')} Greeting & question detection
{get_emoji('check')} Response logging
{get_emoji('check')} Database persistence
    """.strip()
    
    await event.edit(status_text)

async def aimode_help(event):
    """Show AI mode help"""
    help_text = f"""
🤖 {convert_font('AI MODE HELP', 'bold')}

╔══════════════════════════════════╗
   📚 {convert_font('COMMAND REFERENCE', 'bold')} 📚
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Main Commands:', 'bold')}
• `.aimode on` - Aktifkan AI mode
• `.aimode off` - Matikan AI mode  
• `.aimode status` - Lihat status AI
• `.ai <text>` - Test AI response

{get_emoji('adder2')} {convert_font('AI Capabilities:', 'bold')}
{get_emoji('check')} Contextual responses
{get_emoji('check')} Greeting detection
{get_emoji('check')} Question answering
{get_emoji('check')} Smart conversations

{get_emoji('adder3')} {convert_font('How It Works:', 'bold')}
1. AI mode detects incoming messages
2. Generates appropriate responses  
3. Logs conversation to database
4. Respects cooldown settings

{get_emoji('main')} Simple AI without external APIs
{convert_font('Perfect for testing & basic usage', 'bold')}
    """.strip()
    
    await event.edit(help_text)

# ===== AI TEST COMMAND =====
@client.on(events.NewMessage(pattern=r'\.ai\s+(.+)'))
async def ai_test_handler(event):
    """Test AI response command"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        user_message = event.pattern_match.group(1).strip()
        
        # Initialize database
        init_aimode_db()
        
        # Generate response
        ai_response = generate_simple_response(user_message)
        
        # Log response
        log_ai_response(user_message, ai_response, event.chat_id, event.sender_id)
        
        # Show response
        response_text = f"""
{get_emoji('main')} {convert_font('AI RESPONSE TEST', 'bold')}

╔══════════════════════════════════╗
   🤖 {convert_font('AI ASSISTANT RESPONSE', 'bold')} 🤖
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Your Message:', 'bold')}
"{user_message}"

{get_emoji('adder2')} {convert_font('AI Response:', 'bold')}
{ai_response}

{get_emoji('check')} Response logged to database
        """.strip()
        
        await event.edit(response_text)
        
    except Exception as e:
        await event.edit(f"❌ AI test error: {str(e)}")

# ===== AUTO AI RESPONSES (when mode is enabled) =====
@client.on(events.NewMessage(incoming=True))
async def auto_ai_responder(event):
    """Auto AI responder when AI mode is enabled"""
    global last_ai_response, ai_mode_enabled
    
    try:
        # Check if AI mode is enabled
        if not ai_mode_enabled:
            settings = get_ai_settings()
            ai_mode_enabled = settings['enabled']
            
        if not ai_mode_enabled:
            return
            
        # Check cooldown
        current_time = time.time()
        if current_time - last_ai_response < cooldown:
            return
            
        # Skip own messages
        me = await client.get_me()
        if event.sender_id == me.id:
            return
            
        # Skip empty messages
        if not event.text:
            return
            
        # Generate and send AI response
        ai_response = generate_simple_response(event.text)
        
        await event.reply(ai_response)
        
        # Log response
        log_ai_response(event.text, ai_response, event.chat_id, event.sender_id)
        
        # Update cooldown
        last_ai_response = current_time
        
    except Exception as e:
        print(f"Auto AI responder error: {e}")

# ===== PLUGIN INITIALIZATION =====
def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Plugin setup function"""
    global client, ai_mode_enabled
    client = client_instance
    
    # Initialize database and load settings
    init_aimode_db()
    settings = get_ai_settings()
    ai_mode_enabled = settings['enabled']
    
    print(f"🤖 AI Mode Simple Plugin loaded! Status: {'ON' if ai_mode_enabled else 'OFF'}")
    return True