"""
Spam Bypass Plugin for Vzoel Assistant - Anti-Spam Bot Interaction
Fitur: Bypass spam bot limits, custom response modification, premium emoji support
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Spam Bot Interaction & Response Customization
"""

import os
import re
import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, User
from telethon.errors import FloodWaitError

# Plugin Info
PLUGIN_INFO = {
    "name": "spam_bypass",
    "version": "1.0.0",
    "description": "Bypass spam bot limits dan custom response dengan premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".spambypass", ".antispam", ".checkspam", ".setresponse", ".limit"],
    "features": ["spam bot bypass", "response customization", "premium emoji", "auto-interaction"]
}

# Global variables
client = None
logger = None
DB_FILE = "plugins/spam_bypass.db"

# Cache untuk mengurangi API calls
sender_cache = {}
cache_expiry = {}
CACHE_DURATION = timedelta(hours=1)  # Cache sender info untuk 1 jam
last_flood_wait = None
flood_wait_until = None

# Premium Emoji Mapping (Independent)
PREMIUM_EMOJIS = {
    'main':     {'id': '6156784006194009426', 'char': '🤩'},
    'check':    {'id': '5794353925360457382', 'char': '⚙️'},
    'shield':   {'id': '5794407002566300853', 'char': '⛈'},
    'success':  {'id': '5793913811471700779', 'char': '✅'},
    'security': {'id': '5321412209992033736', 'char': '👽'},
    'bypass':   {'id': '5793973133559993740', 'char': '✈️'},
    'danger':   {'id': '5357404860566235955', 'char': '😈'},
    'monitor':  {'id': '5794323465452394551', 'char': '🎚️'}
}

def setup_logger():
    """Setup dedicated logger"""
    global logger
    logger = logging.getLogger("spam_bypass_plugin")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

def get_emoji(emoji_type):
    """Get premium emoji dari mapping independent"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
            '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
        }
        return ''.join([bold_map.get(c, c) for c in text])
    elif font_type == 'mono':
        mono_map = {
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
            'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
            's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
            'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
            'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉'
        }
        return ''.join([mono_map.get(c, c) for c in text])
    return text

def create_premium_entities(text):
    """Generate MessageEntityCustomEmoji entities for premium emojis"""
    entities = []
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
                            logger.error(f"[SpamBypass] Error creating entity for {emoji_type}: {e}")
                        break
            
            if not found_emoji:
                # Regular character
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
                
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error in create_premium_entities: {e}")
        return []
    
    return entities

async def is_owner_check(user_id):
    """Check if user is owner dengan caching"""
    try:
        OWNER_ID = os.getenv('OWNER_ID')
        if OWNER_ID:
            return user_id == int(OWNER_ID)
        if client:
            # Simple owner check without extra API calls
            return user_id == 7847025168  # Static owner ID
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Owner check error: {e}")
    return False

def get_db_conn():
    """Get database connection"""
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spam_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT UNIQUE,
                custom_text TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS spam_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_username TEXT UNIQUE,
                bot_id INTEGER,
                bypass_enabled INTEGER DEFAULT 1,
                response_delay REAL DEFAULT 2.0,
                created_at TEXT
            );
        """)
        conn.commit()
        return conn
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Database error: {e}")
        return None

async def safe_send_message(event, text, use_premium=True):
    """Send message with premium emoji support"""
    try:
        if use_premium:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                if logger:
                    logger.debug(f"[SpamBypass] Sent message with {len(entities)} premium entities")
                return
        
        # Fallback to standard message
        await event.reply(text)
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error sending message: {e}")
        try:
            await event.reply(text)
        except Exception as e2:
            if logger:
                logger.error(f"[SpamBypass] Fallback send failed: {e2}")

def save_custom_response(original_text, custom_text):
    """Save custom response mapping"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if exists
        cur = conn.execute("SELECT id FROM spam_responses WHERE original_text = ?", (original_text,))
        row = cur.fetchone()
        
        if row:
            conn.execute("UPDATE spam_responses SET custom_text=?, updated_at=? WHERE original_text=?",
                         (custom_text, now, original_text))
        else:
            conn.execute("INSERT INTO spam_responses (original_text, custom_text, created_at, updated_at) VALUES (?, ?, ?, ?)",
                         (original_text, custom_text, now, now))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error saving custom response: {e}")
        return False

def get_custom_response(original_text):
    """Get custom response for original text"""
    try:
        conn = get_db_conn()
        if not conn:
            return None
        
        cur = conn.execute("SELECT custom_text FROM spam_responses WHERE original_text = ? AND enabled = 1", (original_text,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return row['custom_text']
        return None
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error getting custom response: {e}")
        return None

def set_response_delay(delay_seconds):
    """Set global response delay for spam bypass"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update or insert default bot setting
        conn.execute("""
            INSERT OR REPLACE INTO spam_bots 
            (bot_username, response_delay, created_at) 
            VALUES ('default', ?, ?)
        """, (delay_seconds, now))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error setting response delay: {e}")
        return False

def get_response_delay():
    """Get current response delay setting"""
    try:
        conn = get_db_conn()
        if not conn:
            return 1.0  # Default delay
        
        cur = conn.execute("SELECT response_delay FROM spam_bots WHERE bot_username = 'default'")
        row = cur.fetchone()
        conn.close()
        
        if row:
            return float(row['response_delay'])
        return 1.0  # Default delay
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error getting response delay: {e}")
        return 1.0

async def get_sender_safe(event):
    """Get sender with caching and flood wait handling"""
    global last_flood_wait, flood_wait_until, sender_cache, cache_expiry
    
    try:
        # Check flood wait status
        if flood_wait_until and datetime.now() < flood_wait_until:
            return None  # Still in flood wait period
        
        sender_id = event.sender_id
        if not sender_id:
            return None
            
        # Check cache first
        now = datetime.now()
        if sender_id in sender_cache and sender_id in cache_expiry:
            if now < cache_expiry[sender_id]:
                return sender_cache[sender_id]
            else:
                # Clean expired cache
                del sender_cache[sender_id]
                del cache_expiry[sender_id]
        
        # Get sender with flood wait handling
        try:
            sender = await event.get_sender()
            
            # Cache the result
            sender_cache[sender_id] = sender
            cache_expiry[sender_id] = now + CACHE_DURATION
            
            # Clean old cache entries (max 100 entries)
            if len(sender_cache) > 100:
                oldest_key = min(cache_expiry.keys(), key=lambda k: cache_expiry[k])
                del sender_cache[oldest_key]
                del cache_expiry[oldest_key]
            
            return sender
            
        except FloodWaitError as e:
            # Set flood wait period
            flood_wait_until = datetime.now() + timedelta(seconds=e.seconds + 5)  # Add 5s buffer
            last_flood_wait = datetime.now()
            
            if logger:
                logger.warning(f"[SpamBypass] FloodWait {e.seconds}s - suspending sender checks until {flood_wait_until}")
            return None
            
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error getting sender safely: {e}")
        return None

async def detect_spam_bot_response(event):
    """Detect and handle spam bot responses with flood protection"""
    global flood_wait_until
    try:
        # Skip if we're in flood wait period
        if flood_wait_until and datetime.now() < flood_wait_until:
            return False
        
        # Get sender safely
        sender = await get_sender_safe(event)
        if not sender:
            return False  # Could not get sender or in flood wait
            
        # Skip if not from a bot
        if not (hasattr(sender, 'bot') and sender.bot):
            return False
        
        message_text = event.message.text or ""
        
        # Common spam bot response patterns
        spam_patterns = [
            r"baik akun anda bebas",
            r"akun anda aman",
            r"account is safe",
            r"no spam detected",
            r"clear account",
            r"verified account"
        ]
        
        # Check if message matches spam bot patterns
        for pattern in spam_patterns:
            if re.search(pattern, message_text, re.IGNORECASE):
                # Get custom response
                custom_text = get_custom_response(message_text.strip())
                
                if not custom_text:
                    # Default vzoel response with premium emojis
                    custom_text = f"{get_emoji('success')} {convert_font('akun vzoel aman', 'bold')} {get_emoji('security')}"
                
                # Delete original message if possible
                try:
                    await event.message.delete()
                    if logger:
                        logger.info(f"[SpamBypass] Deleted spam bot message: {message_text[:50]}...")
                except Exception as e:
                    if logger:
                        logger.warning(f"[SpamBypass] Could not delete message: {e}")
                
                # Send custom response with configured delay
                delay = get_response_delay()
                await asyncio.sleep(delay)
                await safe_send_message(event, custom_text)
                
                if logger:
                    logger.info(f"[SpamBypass] Replaced spam response from @{sender.username}")
                
                return True
        
        return False
        
    except FloodWaitError as e:
        # Handle flood wait in main detection function too  
        flood_wait_until = datetime.now() + timedelta(seconds=e.seconds + 5)
        if logger:
            logger.warning(f"[SpamBypass] FloodWait in detection: {e.seconds}s - suspending until {flood_wait_until}")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Error in spam bot detection: {e}")
        return False

async def spambypass_handler(event):
    """Handle .spambypass command"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split(maxsplit=1)
        
        if len(args) == 1:
            help_text = f"""
{get_emoji('shield')} {convert_font('SPAM BYPASS PLUGIN', 'bold')}

{get_emoji('check')} {convert_font('Commands:', 'bold')}
• {convert_font('.spambypass', 'mono')} - Show this help
• {convert_font('.antispam on/off', 'mono')} - Toggle auto-bypass  
• {convert_font('.checkspam', 'mono')} - Check spam bot status
• {convert_font('.setresponse <original> | <custom>', 'mono')} - Set custom response
• {convert_font('.limit <seconds>', 'mono')} - Set response delay (0.5-10.0s)

{get_emoji('bypass')} {convert_font('Features:', 'bold')}
• Auto-replace spam bot responses
• Custom response mapping
• Premium emoji support
• Message deletion & replacement

{get_emoji('security')} {convert_font('Default Response:', 'bold')}
{get_emoji('success')} {convert_font('akun vzoel aman', 'bold')} {get_emoji('security')}

{get_emoji('monitor')} {convert_font('Status:', 'bold')} Auto-bypass is Active
            """.strip()
            
            await safe_send_message(event, help_text)
            return
        
        await safe_send_message(event, f"{get_emoji('check')} {convert_font('Spam bypass is active!', 'bold')}")
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Command handler error: {e}")
        await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Command error!', 'bold')}")

async def setresponse_handler(event):
    """Handle .setresponse command"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split(maxsplit=1)
        
        if len(args) < 2 or '|' not in args[1]:
            await safe_send_message(event, 
                f"{get_emoji('shield')} {convert_font('Format:', 'mono')} .setresponse <original> | <custom>\n\n"
                f"{get_emoji('check')} {convert_font('Example:', 'bold')}\n"
                f"{convert_font('.setresponse baik akun anda bebas | ', 'mono')}{get_emoji('success')} {convert_font('akun vzoel aman', 'bold')} {get_emoji('security')}")
            return
        
        parts = args[1].split('|', 1)
        original = parts[0].strip()
        custom = parts[1].strip()
        
        if save_custom_response(original, custom):
            response_text = f"""
{get_emoji('success')} {convert_font('CUSTOM RESPONSE SET!', 'bold')}

{get_emoji('check')} {convert_font('Original:', 'bold')} {convert_font(original, 'mono')}
{get_emoji('bypass')} {convert_font('Custom:', 'bold')} {custom}

{get_emoji('monitor')} {convert_font('Response will replace spam bot messages automatically', 'mono')}
            """.strip()
            
            await safe_send_message(event, response_text)
        else:
            await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Failed to save custom response!', 'bold')}")
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Set response handler error: {e}")
        await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Set response error!', 'bold')}")

async def checkspam_handler(event):
    """Handle .checkspam command"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        # Get statistics
        conn = get_db_conn()
        if conn:
            cur = conn.execute("SELECT COUNT(*) as count FROM spam_responses WHERE enabled = 1")
            response_count = cur.fetchone()['count']
            
            cur = conn.execute("SELECT original_text, custom_text FROM spam_responses WHERE enabled = 1 LIMIT 5")
            responses = cur.fetchall()
            conn.close()
        else:
            response_count = 0
            responses = []
        
        # Flood wait status
        flood_status = "Active"
        if flood_wait_until and datetime.now() < flood_wait_until:
            remaining = (flood_wait_until - datetime.now()).seconds
            flood_status = f"Suspended ({remaining}s remaining)"
        
        status_text = f"""
{get_emoji('security')} {convert_font('SPAM BYPASS STATUS', 'bold')}

{get_emoji('check')} {convert_font('Auto-Bypass:', 'bold')} {flood_status}
{get_emoji('monitor')} {convert_font('Custom Responses:', 'bold')} {response_count}
{get_emoji('shield')} {convert_font('Cached Senders:', 'bold')} {len(sender_cache)}

{get_emoji('bypass')} {convert_font('Default Response:', 'bold')}
{get_emoji('success')} {convert_font('akun vzoel aman', 'bold')} {get_emoji('security')}

{get_emoji('shield')} {convert_font('Protected Patterns:', 'bold')}
• baik akun anda bebas → akun vzoel aman
• account is safe → akun vzoel aman  
• no spam detected → akun vzoel aman
        """.strip()
        
        if responses:
            status_text += f"\n\n{get_emoji('check')} {convert_font('Custom Mappings:', 'bold')}"
            for resp in responses[:3]:
                orig_short = resp['original_text'][:30] + "..." if len(resp['original_text']) > 30 else resp['original_text']
                custom_short = resp['custom_text'][:30] + "..." if len(resp['custom_text']) > 30 else resp['custom_text']
                status_text += f"\n• {convert_font(orig_short, 'mono')} → {custom_short}"
        
        await safe_send_message(event, status_text)
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Check spam handler error: {e}")
        await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Status check error!', 'bold')}")

async def limit_handler(event):
    """Handle .limit command to set response delay"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split(maxsplit=1)
        
        if len(args) == 1:
            # Show current delay
            current_delay = get_response_delay()
            delay_text = f"""
{get_emoji('monitor')} {convert_font('RESPONSE DELAY SETTINGS', 'bold')}

{get_emoji('check')} {convert_font('Current Delay:', 'bold')} {current_delay} seconds
{get_emoji('bypass')} {convert_font('Range:', 'bold')} 0.5 - 10.0 seconds

{get_emoji('shield')} {convert_font('Usage:', 'bold')}
• {convert_font('.limit <seconds>', 'mono')} - Set delay (e.g., .limit 2.5)
• {convert_font('.limit', 'mono')} - Show current setting

{get_emoji('security')} {convert_font('Purpose:', 'bold')}
Delay before sending bypass response to avoid spam detection
            """.strip()
            
            await safe_send_message(event, delay_text)
            return
        
        try:
            delay_value = float(args[1])
            
            # Validate delay range
            if delay_value < 0.5:
                await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Minimum delay is 0.5 seconds', 'bold')}")
                return
            elif delay_value > 10.0:
                await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Maximum delay is 10.0 seconds', 'bold')}")
                return
            
            # Set the delay
            if set_response_delay(delay_value):
                success_text = f"""
{get_emoji('success')} {convert_font('DELAY UPDATED!', 'bold')}

{get_emoji('monitor')} {convert_font('New Delay:', 'bold')} {delay_value} seconds
{get_emoji('bypass')} {convert_font('Applied to:', 'bold')} All spam bypass responses
{get_emoji('security')} {convert_font('Status:', 'bold')} Active immediately

{get_emoji('shield')} {convert_font('Next spam response will wait', 'mono')} {delay_value}s {convert_font('before replying', 'mono')}
                """.strip()
                
                await safe_send_message(event, success_text)
            else:
                await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Failed to update delay setting!', 'bold')}")
                
        except ValueError:
            await safe_send_message(event, 
                f"{get_emoji('shield')} {convert_font('Invalid delay value!', 'bold')}\n\n"
                f"{get_emoji('check')} {convert_font('Example:', 'bold')} {convert_font('.limit 2.5', 'mono')}\n"
                f"{get_emoji('monitor')} {convert_font('Range:', 'bold')} 0.5 - 10.0 seconds")
        
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Limit handler error: {e}")
        await safe_send_message(event, f"{get_emoji('danger')} {convert_font('Limit command error!', 'bold')}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    global client, logger
    setup_logger()
    
    try:
        client = telegram_client
        if client:
            # Register command handlers
            client.add_event_handler(spambypass_handler, events.NewMessage(pattern=r'\.spambypass'))
            client.add_event_handler(setresponse_handler, events.NewMessage(pattern=r'\.setresponse'))
            client.add_event_handler(checkspam_handler, events.NewMessage(pattern=r'\.checkspam'))
            client.add_event_handler(limit_handler, events.NewMessage(pattern=r'\.limit'))
            
            # Register auto-detection for all messages dengan rate limiting
            client.add_event_handler(detect_spam_bot_response, events.NewMessage(func=lambda e: not (flood_wait_until and datetime.now() < flood_wait_until)))
            
            # Initialize default response
            save_custom_response("baik akun anda bebas", f"{get_emoji('success')} {convert_font('akun vzoel aman', 'bold')} {get_emoji('security')}")
            
            if logger:
                logger.info("[SpamBypass] Plugin setup completed - Anti-spam bypass active")
        return True
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Setup error: {e}")
        return False

def cleanup_plugin():
    global client, logger, sender_cache, cache_expiry, flood_wait_until
    try:
        if logger:
            logger.info("[SpamBypass] Plugin cleanup initiated")
        client = None
        
        # Clear caches
        sender_cache.clear()
        cache_expiry.clear()
        flood_wait_until = None
        
        if logger:
            logger.info("[SpamBypass] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[SpamBypass] Cleanup error: {e}")

__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'is_owner_check', 'get_emoji', 'convert_font', 'PREMIUM_EMOJIS', 'save_custom_response', 'get_custom_response']