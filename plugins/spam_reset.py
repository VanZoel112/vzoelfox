"""
Spam Limit Reset Plugin for VzoelFox Userbot - Telegram SpamBot Integration
Fitur: Reset batasan Telegram melalui SpamBot, check status limit, auto-apply untuk unban
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Complete Spam Limit Management
"""

import sqlite3
import os
import asyncio
from datetime import datetime, timedelta
from telethon import events, functions, types
from telethon.errors import UserIsBlockedError, PeerFloodError, FloodWaitError

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('spam_reset')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

PLUGIN_INFO = {
    "name": "spam_reset",
    "version": "1.0.0",
    "description": "Reset batasan Telegram melalui SpamBot integration dengan automatic limit checking",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".spamreset", ".spamcheck", ".spamstatus", ".spambot", ".antispam"],
    "features": ["spambot integration", "auto limit reset", "status monitoring", "flood protection", "centralized database"]
}

# Premium Emoji Mapping
PREMIUM_EMOJIS = {
    "main": {"emoji": "🤩", "custom_emoji_id": "6156784006194009426"},
    "check": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "adder1": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6": {"emoji": "🎚️", "custom_emoji_id": "5794323465452394551"}
}

# SpamBot usernames (official Telegram bots)
SPAMBOTS = [
    "@SpamBot",
    "@NotifyBot", 
    "@BotFather"  # Backup option
]

DB_FILE = "plugins/spam_reset.db"
client = None

def get_emoji(emoji_type):
    """Get premium emoji dari mapping"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭'
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

def get_db_conn():
    """Get database connection dengan compatibility layer"""
    if DB_COMPATIBLE and plugin_db:
        # Initialize table dengan centralized database
        table_schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT,
            spambot_used TEXT,
            status TEXT,
            response_message TEXT,
            limit_info TEXT,
            created_at TEXT,
            success INTEGER DEFAULT 0
        """
        plugin_db.create_table('spam_reset_log', table_schema)
        return plugin_db
    else:
        # Fallback ke legacy individual database
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spam_reset_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT,
                    spambot_used TEXT,
                    status TEXT,
                    response_message TEXT,
                    limit_info TEXT,
                    created_at TEXT,
                    success INTEGER DEFAULT 0
                );
            """)
            conn.commit()
            return conn
        except Exception as e:
            print(f"[SpamReset] Database error: {e}")
            return None

def log_spam_action(action_type, spambot_used, status, response_message, limit_info=None, success=False):
    """Log spam action ke database"""
    try:
        db = get_db_conn()
        if not db:
            return False
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            'action_type': action_type,
            'spambot_used': spambot_used,
            'status': status,
            'response_message': response_message,
            'limit_info': limit_info,
            'created_at': now,
            'success': 1 if success else 0
        }
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.insert('spam_reset_log', data)
        else:
            # Legacy database operations
            db.execute(
                "INSERT INTO spam_reset_log (action_type, spambot_used, status, response_message, limit_info, created_at, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
                tuple(data.values())
            )
            db.commit()
            db.close()
            return True
            
    except Exception as e:
        print(f"[SpamReset] Log error: {e}")
        return False

def get_spam_history(limit=10):
    """Get spam action history"""
    try:
        db = get_db_conn()
        if not db:
            return []
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.select('spam_reset_log', 'TRUE ORDER BY created_at DESC LIMIT ' + str(limit))
        else:
            # Legacy database operations
            cur = db.execute("SELECT * FROM spam_reset_log ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            db.close()
            return rows
            
    except Exception as e:
        print(f"[SpamReset] History error: {e}")
        return []

async def send_to_log_group(message):
    """Send message ke log group jika tersedia"""
    try:
        log_group_id = os.getenv('LOG_GROUP_ID')
        if log_group_id and client:
            await client.send_message(int(log_group_id), message)
    except Exception as e:
        print(f"[SpamReset] Log group send error: {e}")

async def interact_with_spambot(spambot_username, message_text):
    """Interact dengan SpamBot untuk reset limit"""
    try:
        if not client:
            return False, "Client not available"
        
        # Get SpamBot entity
        try:
            spambot = await client.get_entity(spambot_username)
        except Exception as e:
            return False, f"Failed to find {spambot_username}: {str(e)}"
        
        # Send message to SpamBot
        try:
            await client.send_message(spambot, message_text)
            
            # Wait for response (max 30 seconds)
            response = None
            for _ in range(30):  # 30 seconds timeout
                await asyncio.sleep(1)
                
                # Get recent messages from SpamBot
                async for message in client.iter_messages(spambot, limit=5):
                    if message.date > datetime.now() - timedelta(seconds=35):
                        response = message.message
                        break
                
                if response:
                    break
            
            if not response:
                return False, "No response from SpamBot (timeout)"
            
            return True, response
            
        except UserIsBlockedError:
            return False, f"You are blocked by {spambot_username}"
        except FloodWaitError as e:
            return False, f"FloodWait: Please wait {e.seconds} seconds"
        except Exception as e:
            return False, f"Failed to send message: {str(e)}"
            
    except Exception as e:
        return False, f"SpamBot interaction failed: {str(e)}"

async def check_spam_status():
    """Check current spam status via SpamBot"""
    try:
        # Try each SpamBot until one works
        for spambot in SPAMBOTS:
            success, response = await interact_with_spambot(spambot, "/start")
            
            if success:
                # Log the check
                log_spam_action("status_check", spambot, "success", response, success=True)
                
                # Parse response for limit information
                limit_info = "Unknown"
                if "limit" in response.lower() or "restricted" in response.lower():
                    limit_info = "Limits detected"
                elif "good" in response.lower() or "normal" in response.lower():
                    limit_info = "No limits"
                
                return True, response, limit_info, spambot
            else:
                # Log failed attempt
                log_spam_action("status_check", spambot, "failed", response, success=False)
        
        return False, "All SpamBots unavailable", "Unknown", None
        
    except Exception as e:
        return False, str(e), "Error", None

async def request_limit_reset():
    """Request limit reset dari SpamBot"""
    try:
        reset_messages = [
            "Hello, I think my account has been limited. Can you help me reset the limits?",
            "/start",
            "I'm experiencing sending limits, please help reset my account",
            "My account seems to be restricted, can you check and reset it?"
        ]
        
        success_count = 0
        responses = []
        
        # Try each SpamBot with different messages
        for spambot in SPAMBOTS:
            for message in reset_messages:
                try:
                    success, response = await interact_with_spambot(spambot, message)
                    
                    if success:
                        success_count += 1
                        responses.append(f"{spambot}: {response[:100]}...")
                        
                        # Log successful reset request
                        log_spam_action("reset_request", spambot, "success", response, success=True)
                        
                        # Wait between requests to avoid flood
                        await asyncio.sleep(5)
                        break
                    else:
                        # Log failed attempt
                        log_spam_action("reset_request", spambot, "failed", response, success=False)
                        
                except Exception as e:
                    print(f"[SpamReset] Error with {spambot}: {e}")
                    continue
                    
                # Wait between attempts
                await asyncio.sleep(3)
        
        if success_count > 0:
            return True, f"Reset requested from {success_count} SpamBots", responses
        else:
            return False, "Failed to contact any SpamBot", []
            
    except Exception as e:
        return False, str(e), []

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        if client:
            owner_id = os.getenv("OWNER_ID")
            if owner_id:
                return user_id == int(owner_id)
            me = await client.get_me()
            return user_id == me.id
    except Exception as e:
        print(f"Error checking owner: {e}")
    return False

async def spam_reset_handler(event):
    """Handle spam reset commands"""
    try:
        # Owner check
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split()
        command = args[0].lower()
        
        if command == ".spamreset":
            # Full spam reset process
            progress_msg = await event.reply(f"{get_emoji('adder4')} {convert_font('Starting spam limit reset...', 'mono')}")
            
            # Step 1: Check current status
            await progress_msg.edit(f"{get_emoji('check')} {convert_font('Step 1/3: Checking current status...', 'mono')}")
            
            status_success, status_response, limit_info, used_bot = await check_spam_status()
            
            # Step 2: Request reset
            await progress_msg.edit(f"{get_emoji('adder2')} {convert_font('Step 2/3: Requesting limit reset...', 'mono')}")
            
            reset_success, reset_message, reset_responses = await request_limit_reset()
            
            # Step 3: Final verification
            await progress_msg.edit(f"{get_emoji('adder6')} {convert_font('Step 3/3: Final verification...', 'mono')}")
            
            await asyncio.sleep(10)  # Wait for limits to be processed
            final_success, final_response, final_limit_info, final_bot = await check_spam_status()
            
            # Prepare result
            if reset_success:
                # Send to log group
                log_message = f"""
{get_emoji('adder2')} {convert_font('SPAM RESET COMPLETED', 'bold')}

{get_emoji('check')} {convert_font('Initial Status:', 'mono')} {limit_info}
{get_emoji('adder4')} {convert_font('Reset Requests:', 'mono')} {len(reset_responses)} sent
{get_emoji('adder6')} {convert_font('Final Status:', 'mono')} {final_limit_info}
{get_emoji('main')} {convert_font('Time:', 'mono')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{get_emoji('adder3')} Spam limits have been processed by Telegram SpamBots.
                """.strip()
                await send_to_log_group(log_message)
                
                response = f"""
{get_emoji('main')} {convert_font('SPAM RESET COMPLETE!', 'bold')}

{get_emoji('check')} {convert_font('Initial Status:', 'bold')}
{limit_info}

{get_emoji('adder2')} {convert_font('Reset Process:', 'bold')}
• {convert_font('Requests Sent:', 'mono')} {len(reset_responses)}
• {convert_font('Success Rate:', 'mono')} {'High' if len(reset_responses) > 1 else 'Medium'}

{get_emoji('adder4')} {convert_font('Final Status:', 'bold')}
{final_limit_info}

{get_emoji('adder6')} {convert_font('SpamBots Contacted:', 'bold')}
                """.strip()
                
                for resp in reset_responses[:3]:  # Show max 3 responses
                    response += f"\n• {resp}"
                
                response += f"\n\n{get_emoji('adder5')} {convert_font('Process completed successfully!', 'mono')}"
                
            else:
                response = f"""
{get_emoji('adder5')} {convert_font('SPAM RESET FAILED!', 'bold')}

{get_emoji('adder3')} {convert_font('Error:', 'mono')} {reset_message}
{get_emoji('check')} {convert_font('Current Status:', 'mono')} {limit_info}

{get_emoji('adder4')} {convert_font('Suggestions:', 'bold')}
• Try again in a few minutes
• Check if SpamBot is available
• Use {convert_font('.spamcheck', 'mono')} to verify status
                """.strip()
            
            await progress_msg.edit(response)
            
        elif command == ".spamcheck":
            # Check spam status only
            progress_msg = await event.reply(f"{get_emoji('check')} {convert_font('Checking spam status...', 'mono')}")
            
            success, response, limit_info, used_bot = await check_spam_status()
            
            if success:
                result = f"""
{get_emoji('main')} {convert_font('SPAM STATUS CHECK', 'bold')}

{get_emoji('check')} {convert_font('SpamBot:', 'mono')} {used_bot}
{get_emoji('adder2')} {convert_font('Status:', 'mono')} {limit_info}
{get_emoji('adder4')} {convert_font('Time:', 'mono')} {datetime.now().strftime('%H:%M:%S')}

{get_emoji('adder6')} {convert_font('Response:', 'bold')}
{response[:200]}{'...' if len(response) > 200 else ''}

{get_emoji('adder3')} Use {convert_font('.spamreset', 'mono')} if limits are detected
                """.strip()
            else:
                result = f"""
{get_emoji('adder5')} {convert_font('STATUS CHECK FAILED', 'bold')}

{get_emoji('adder3')} {convert_font('Error:', 'mono')} {response}
{get_emoji('check')} {convert_font('All SpamBots:', 'mono')} Unavailable

{get_emoji('adder4')} {convert_font('Try again later or contact:', 'bold')}
• @SpamBot directly in Telegram
• @NotifyBot for alternative check
                """.strip()
            
            await progress_msg.edit(result)
            
        elif command == ".spamstatus":
            # Show spam reset history
            history = get_spam_history(5)
            
            if history:
                status_text = f"""
{get_emoji('main')} {convert_font('SPAM RESET HISTORY', 'bold')}

{get_emoji('check')} {convert_font('Recent Activities:', 'bold')}
                """.strip()
                
                for record in history:
                    action_type = record.get('action_type', 'unknown')
                    status = record.get('status', 'unknown')
                    created_at = record.get('created_at', 'unknown')
                    success = record.get('success', 0)
                    
                    status_icon = get_emoji('adder2') if success else get_emoji('adder3')
                    status_text += f"\n{status_icon} {convert_font(action_type.title(), 'mono')} - {status} ({created_at[-8:]})"
                
                status_text += f"\n\n{get_emoji('adder4')} {convert_font('Available Commands:', 'bold')}"
                status_text += f"\n• {convert_font('.spamreset', 'mono')} - Full reset process"
                status_text += f"\n• {convert_font('.spamcheck', 'mono')} - Status check only"
                
            else:
                status_text = f"""
{get_emoji('check')} {convert_font('No spam reset history found', 'bold')}

{get_emoji('adder2')} {convert_font('Available Commands:', 'bold')}
• {convert_font('.spamreset', 'mono')} - Start spam limit reset
• {convert_font('.spamcheck', 'mono')} - Check current status
                """.strip()
            
            await event.reply(status_text)
            
        elif command == ".spambot":
            # Manual SpamBot interaction
            if len(args) < 2:
                await event.reply(f"{get_emoji('adder3')} Format: {convert_font('.spambot <message>', 'mono')}")
                return
            
            message_text = " ".join(args[1:])
            
            progress_msg = await event.reply(f"{get_emoji('adder4')} {convert_font('Contacting SpamBot...', 'mono')}")
            
            # Try first available SpamBot
            success, response = await interact_with_spambot(SPAMBOTS[0], message_text)
            
            if success:
                result = f"""
{get_emoji('adder2')} {convert_font('SPAMBOT RESPONSE', 'bold')}

{get_emoji('check')} {convert_font('Bot:', 'mono')} {SPAMBOTS[0]}
{get_emoji('adder4')} {convert_font('Your Message:', 'mono')} {message_text[:50]}{'...' if len(message_text) > 50 else ''}

{get_emoji('main')} {convert_font('Response:', 'bold')}
{response}
                """.strip()
            else:
                result = f"""
{get_emoji('adder5')} {convert_font('SPAMBOT ERROR', 'bold')}

{get_emoji('adder3')} {convert_font('Error:', 'mono')} {response}
{get_emoji('check')} {convert_font('Bot:', 'mono')} {SPAMBOTS[0]}
                """.strip()
            
            await progress_msg.edit(result)
            
        elif command == ".antispam":
            # Show help and information
            help_text = f"""
{get_emoji('main')} {convert_font('SPAM RESET SYSTEM', 'bold')}

{get_emoji('check')} {convert_font('Main Commands:', 'bold')}
• {convert_font('.spamreset', 'mono')} - Complete limit reset process
• {convert_font('.spamcheck', 'mono')} - Check current spam status
• {convert_font('.spamstatus', 'mono')} - Show reset history
• {convert_font('.spambot <msg>', 'mono')} - Manual bot interaction

{get_emoji('adder2')} {convert_font('Features:', 'bold')}
• Automatic SpamBot detection
• Multi-bot reset requests
• Status verification
• Activity logging
• Log group integration

{get_emoji('adder4')} {convert_font('SpamBots Used:', 'bold')}
• @SpamBot (primary)
• @NotifyBot (secondary)
• @BotFather (backup)

{get_emoji('adder6')} {convert_font('Safety:', 'bold')}
• All interactions are logged
• Owner-only access protection
• Automatic rate limiting

{get_emoji('adder5')} {convert_font('Note:', 'mono')} Results depend on Telegram's SpamBot availability
            """.strip()
            
            await event.reply(help_text)
            
    except Exception as e:
        print(f"[SpamReset] Handler error: {e}")
        await event.reply(f"{get_emoji('adder5')} {convert_font('Command error occurred', 'bold')}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    """Setup spam reset plugin"""
    global client
    client = telegram_client
    
    try:
        # Register event handlers
        client.add_event_handler(spam_reset_handler, events.NewMessage(pattern=r"\.spam(reset|check|status|bot|anti)"))
        
        print("[SpamReset] Plugin loaded successfully with SpamBot integration")
        return True
        
    except Exception as e:
        print(f"[SpamReset] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[SpamReset] Plugin cleanup initiated")
        client = None
        print("[SpamReset] Plugin cleanup completed")
    except Exception as e:
        print(f"[SpamReset] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'interact_with_spambot', 'check_spam_status', 'request_limit_reset']