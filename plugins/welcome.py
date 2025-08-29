"""
Custom Welcome Plugin (SQL3 + Emoji Premium Support)
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Premium Emoji Support
"""

import sqlite3
import os
import json
import logging
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

PLUGIN_INFO = {
    "name": "welcome",
    "version": "2.0.0",
    "description": "Custom welcome dengan emoji premium support, UTF-16 handling, dan SQL3.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".welcome set", ".welcome show", ".welcome on", ".welcome off"],
    "features": ["custom welcome", "premium emoji support", "utf-16 handling", "sql3 direct", "font conversion"]
}

EMOJI_JSON = "data/emoji.json"
DB_FILE = "plugins/welcome.db"

# Premium emoji configuration berdasarkan data UTF-16 yang valid
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},  # UTF-16 length: 2
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},  # UTF-16 length: 1
    'adder2': {'id': '5793913811471700779', 'char': '✅'}, # UTF-16 length: 1
    'adder3': {'id': '5321412209992033736', 'char': '👽'}, # UTF-16 length: 2
    'adder4': {'id': '5793973133559993740', 'char': '✈️'}, # UTF-16 length: 2
    'adder5': {'id': '5357404860566235955', 'char': '😈'}, # UTF-16 length: 2
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'} # UTF-16 length: 2
}

# Font conversion maps
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
client = None
logger = None
premium_status = False

def setup_logger():
    """Setup logger untuk welcome plugin"""
    global logger
    logger = logging.getLogger("welcome_plugin")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

async def check_premium_status():
    """Check if user has Telegram Premium"""
    global premium_status
    try:
        if client:
            me = await client.get_me()
            premium_status = getattr(me, 'premium', False)
            if logger:
                logger.info(f"[Welcome] Premium status: {premium_status}")
        return premium_status
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Error checking premium status: {e}")
        premium_status = False
        return False

def load_json(path, default=None):
    """Load JSON file dengan error handling"""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Error loading JSON {path}: {e}")
    return default or {}

def get_emoji(name):
    """Get emoji dengan premium support dan fallback"""
    # Try premium emojis first
    if name in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[name]['char']
    
    # Try JSON file
    emoji_map = load_json(EMOJI_JSON, {
        "main": "🤩",
        "check": "⚙️",
        "welcome": "👋",
        "user": "👤",
        "star": "⭐"
    })
    
    return emoji_map.get(name, "🤩")

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def create_premium_entities(text):
    """Create MessageEntityCustomEmoji for premium emojis in text"""
    entities = []
    
    if not premium_status:
        return entities
    
    try:
        current_offset = 0
        i = 0
        
        while i < len(text):
            found_emoji = False
            
            # Check for premium emojis at current position
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        # Calculate proper UTF-16 length
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        # Create entity
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        # Skip the emoji characters
                        i += len(emoji_char)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception as e:
                        if logger:
                            logger.error(f"[Welcome] Error creating entity for {emoji_type}: {e}")
                        break
            
            if not found_emoji:
                # Regular character
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        if logger:
            logger.debug(f"[Welcome] Created {len(entities)} premium emoji entities")
        
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Error in create_premium_entities: {e}")
        return []
    
    return entities

def render_emoji_in_text(text):
    """Replace {emoji:name} and {font:type:text} with corresponding emojis and fonts"""
    import re
    
    # Replace emoji placeholders
    def emoji_repl(m):
        return get_emoji(m.group(1))
    text = re.sub(r"{emoji:([a-zA-Z0-9_]+)}", emoji_repl, text)
    
    # Replace font placeholders
    def font_repl(m):
        font_type = m.group(1)
        font_text = m.group(2)
        return convert_font(font_text, font_type)
    text = re.sub(r"{font:([a-zA-Z]+):([^}]+)}", font_repl, text)
    
    return text

def get_db_conn():
    """Get database connection"""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS welcome (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 1,
                message TEXT DEFAULT '',
                use_premium INTEGER DEFAULT 1,
                updated_at TEXT
            );
        """)
        conn.commit()
        return conn
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Database error: {e}")
        return None

def set_welcome(chat_id, message=None, enabled=None, use_premium=None):
    """Set welcome configuration"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
            
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if exists
        cur = conn.execute("SELECT * FROM welcome WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        
        if row:
            msg = message if message is not None else row['message']
            en = enabled if enabled is not None else row['enabled']
            up = use_premium if use_premium is not None else row.get('use_premium', 1)
            conn.execute("UPDATE welcome SET message=?, enabled=?, use_premium=?, updated_at=? WHERE chat_id=?",
                         (msg, en, up, now, chat_id))
        else:
            msg = message if message is not None else ''
            en = enabled if enabled is not None else 1
            up = use_premium if use_premium is not None else 1
            conn.execute("INSERT INTO welcome (chat_id, enabled, message, use_premium, updated_at) VALUES (?, ?, ?, ?, ?)",
                         (chat_id, en, msg, up, now))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Error setting welcome: {e}")
        return False

def get_welcome(chat_id):
    """Get welcome configuration"""
    try:
        conn = get_db_conn()
        if not conn:
            return None
            
        cur = conn.execute("SELECT * FROM welcome WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        conn.close()
        return row
        
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Error getting welcome: {e}")
        return None

async def safe_send_message(event, text, use_premium=True):
    """Send message with premium emoji support"""
    try:
        if use_premium and premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                if logger:
                    logger.debug(f"[Welcome] Sent message with {len(entities)} premium entities")
                return
        
        # Fallback to standard message
        await event.reply(text)
        
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Error sending message: {e}")
        # Final fallback
        try:
            await event.reply(text)
        except Exception as e2:
            if logger:
                logger.error(f"[Welcome] Fallback send failed: {e2}")

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        OWNER_ID = os.getenv('OWNER_ID')
        if OWNER_ID:
            return user_id == int(OWNER_ID)
        # Fallback to client self-check
        if client:
            me = await client.get_me()
            return user_id == me.id
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Owner check error: {e}")
    return False

async def welcome_cmd_handler(event):
    """Handle welcome command"""
    try:
        # Owner check first
        if not await is_owner_check(event.sender_id):
            return
        
        chat = await event.get_chat()
        chat_id = chat.id
        
        # Only work in groups/supergroups
        if not hasattr(chat, 'megagroup') and not hasattr(chat, 'broadcast'):
            await safe_send_message(event, f"{get_emoji('main')} {convert_font('This command only works in groups!', 'bold')}")
            return
            
        args = event.text.split(maxsplit=2)
        
        if len(args) == 1:
            help_text = f"""
{get_emoji('main')} {convert_font('WELCOME PLUGIN HELP', 'mono')}

{get_emoji('check')} {convert_font('Commands:', 'bold')}
• {convert_font('.welcome set <message>', 'mono')} - Set welcome message
• {convert_font('.welcome show', 'mono')} - Show current welcome
• {convert_font('.welcome on', 'mono')} - Enable welcome
• {convert_font('.welcome off', 'mono')} - Disable welcome

{get_emoji('adder1')} {convert_font('Variables:', 'bold')}
• {convert_font('{name}', 'mono')} - User's first name
• {convert_font('{emoji:name}', 'mono')} - Insert emoji
• {convert_font('{font:bold:text}', 'mono')} - Bold font
• {convert_font('{font:mono:text}', 'mono')} - Monospace font

{get_emoji('adder2')} {convert_font('Example:', 'bold')}
{convert_font('.welcome set {emoji:main} Welcome {font:bold:{name}}! {emoji:check}', 'mono')}

{get_emoji('adder3')} {convert_font('Premium Status:', 'bold')} {'Active' if premium_status else 'Standard'}
            """.strip()
            
            await safe_send_message(event, help_text)
            return
        
        cmd = args[1].lower()
        
        if cmd == "set":
            if len(args) < 3:
                await safe_send_message(event, f"{get_emoji('main')} Format: {convert_font('.welcome set <message>', 'mono')}")
                return
            
            msg = args[2]
            success = set_welcome(chat_id, message=msg)
            
            if success:
                rendered_msg = render_emoji_in_text(msg)
                response = f"""
{get_emoji('main')} {convert_font('WELCOME MESSAGE SET!', 'mono')}

{get_emoji('check')} {convert_font('Preview:', 'bold')}
{rendered_msg}

{get_emoji('adder2')} {convert_font('Premium Features:', 'bold')} {'Enabled' if premium_status else 'Disabled'}
                """.strip()
                await safe_send_message(event, response)
            else:
                await safe_send_message(event, f"{get_emoji('main')} Error setting welcome message!")
        
        elif cmd == "show":
            row = get_welcome(chat_id)
            if row and row['message']:
                status = "Active" if row['enabled'] else "Inactive"
                premium_setting = "Enabled" if row.get('use_premium', 1) else "Disabled"
                
                response = f"""
{get_emoji('main')} {convert_font('WELCOME STATUS', 'mono')}

{get_emoji('check')} {convert_font('Status:', 'bold')} {status}
{get_emoji('adder1')} {convert_font('Premium:', 'bold')} {premium_setting}

{get_emoji('adder2')} {convert_font('Current Message:', 'bold')}
{render_emoji_in_text(row['message'])}
                """.strip()
                
                await safe_send_message(event, response)
            else:
                await safe_send_message(event, f"{get_emoji('main')} Welcome message not set yet.")
        
        elif cmd == "on":
            success = set_welcome(chat_id, enabled=1)
            if success:
                await safe_send_message(event, f"{get_emoji('check')} {convert_font('Welcome activated for this chat!', 'bold')}")
            else:
                await safe_send_message(event, f"{get_emoji('main')} Error activating welcome!")
        
        elif cmd == "off":
            success = set_welcome(chat_id, enabled=0)
            if success:
                await safe_send_message(event, f"{get_emoji('adder1')} {convert_font('Welcome deactivated for this chat.', 'bold')}")
            else:
                await safe_send_message(event, f"{get_emoji('main')} Error deactivating welcome!")
        
        else:
            await safe_send_message(event, "Invalid command. Use: .welcome set/show/on/off")
    
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Command handler error: {e}")
        await safe_send_message(event, f"{get_emoji('main')} Command error occurred!")

async def member_join_handler(event):
    """Handle new member joins"""
    try:
        # Check if this is a user join event
        if not (hasattr(event, "user_joined") and event.user_joined):
            return
        
        chat = await event.get_chat()
        chat_id = chat.id
        row = get_welcome(chat_id)
        
        if row and row['enabled'] and row['message']:
            # Get user info
            user = event.user_joined
            name = getattr(user, 'first_name', 'User') or 'User'
            
            # Replace variables
            msg = row['message'].replace("{name}", name)
            rendered_msg = render_emoji_in_text(msg)
            
            # Send welcome message with premium support
            use_premium = row.get('use_premium', 1) and premium_status
            await safe_send_message(event, rendered_msg, use_premium=use_premium)
            
            if logger:
                logger.info(f"[Welcome] Sent welcome to {name} in chat {chat_id}")
    
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Member join handler error: {e}")

def get_plugin_info():
    """Return plugin information"""
    return PLUGIN_INFO

def setup(telegram_client):
    """Setup welcome plugin"""
    global client
    
    # Setup logger
    setup_logger()
    
    try:
        # Store client reference
        client = telegram_client
        
        # Check premium status
        import asyncio
        if hasattr(asyncio, 'create_task'):
            asyncio.create_task(check_premium_status())
        
        # Register event handlers
        client.add_event_handler(welcome_cmd_handler, events.NewMessage(pattern=r"\.welcome"))
        client.add_event_handler(member_join_handler, 
                                events.ChatAction(func=lambda e: getattr(e, "user_joined", None) is not None))
        
        if logger:
            logger.info("[Welcome] Plugin setup completed successfully")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        if logger:
            logger.info("[Welcome] Plugin cleanup initiated")
        client = None
        if logger:
            logger.info("[Welcome] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[Welcome] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'is_owner_check', 'get_emoji', 'convert_font', 'PREMIUM_EMOJIS']