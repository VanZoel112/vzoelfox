"""
Grup Otomatisasi & Blacklist Manager with Log Group Integration
- Otomatis simpan daftar grup dari log.py
- Blacklist grup agar tidak kena gcast
- Cek di mana kamu diban/keluar
- Forward blacklist activities ke log group
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Log Group Integration
"""

import sqlite3
import os
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('grub')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

PLUGIN_INFO = {
    "name": "grup",
    "version": "2.0.0",
    "description": "Manajemen grup, blacklist, banlist, sinkron log.py dengan log group integration.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".grup log",
        ".grup blacklist <id>",
        ".grup unblacklist <id>",
        ".grup blacklistlist",
        ".grup banlist",
        ".grup loggroup"
    ],
    "features": [
        "auto grup log",
        "blacklist id grup", 
        "banlist monitoring",
        "log group integration",
        "centralized database"
    ]
}

DB_FILE = "plugins/grup.db"
client = None

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
        # Initialize tables dengan centralized database
        blacklist_schema = """
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            added_at TEXT,
            reason TEXT,
            added_by TEXT
        """
        banlist_schema = """
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            banned_at TEXT,
            ban_reason TEXT,
            auto_detected INTEGER DEFAULT 1
        """
        plugin_db.create_table('grup_blacklist', blacklist_schema)
        plugin_db.create_table('grup_banlist', banlist_schema)
        return plugin_db
    else:
        # Fallback ke legacy individual database
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS grup_blacklist (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    added_at TEXT,
                    reason TEXT,
                    added_by TEXT
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS grup_banlist (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    banned_at TEXT,
                    ban_reason TEXT,
                    auto_detected INTEGER DEFAULT 1
                );
            """)
            conn.commit()
            return conn
        except Exception as e:
            print(f"[Grub] Database error: {e}")
            return None

async def send_to_log_group(message):
    """Send message ke log group jika tersedia"""
    try:
        log_group_id = os.getenv('LOG_GROUP_ID')
        if log_group_id and client:
            await client.send_message(int(log_group_id), message)
    except Exception as e:
        print(f"[Grub] Log group send error: {e}")

async def add_blacklist(chat_id, reason=None, added_by="manual"):
    """Add grup ke blacklist dengan database compatibility dan log group integration"""
    try:
        db = get_db_conn()
        if not db:
            return False
        
        # Get chat info jika memungkinkan
        chat_title = f"Chat_{chat_id}"
        try:
            if client:
                entity = await client.get_entity(chat_id)
                chat_title = getattr(entity, 'title', chat_title)
        except Exception:
            pass
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            'chat_id': chat_id,
            'chat_title': chat_title,
            'added_at': now,
            'reason': reason or 'No reason provided',
            'added_by': added_by
        }
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            result = db.insert('grup_blacklist', data)
        else:
            # Legacy database operations
            db.execute("INSERT OR REPLACE INTO grup_blacklist (chat_id, chat_title, added_at, reason, added_by) VALUES (?, ?, ?, ?, ?)",
                       tuple(data.values()))
            db.commit()
            db.close()
            result = True
        
        # Send ke log group
        if result:
            log_message = f"""
{get_emoji('adder5')} {convert_font('BLACKLIST ADDED', 'bold')}

{get_emoji('check')} {convert_font('Chat ID:', 'mono')} {chat_id}
{get_emoji('adder2')} {convert_font('Title:', 'mono')} {chat_title}
{get_emoji('adder3')} {convert_font('Reason:', 'mono')} {reason or 'Manual add'}
{get_emoji('adder4')} {convert_font('Added by:', 'mono')} {added_by}
{get_emoji('adder6')} {convert_font('Time:', 'mono')} {now}

{get_emoji('main')} Grup ini akan diabaikan dari gcast operations.
            """.strip()
            await send_to_log_group(log_message)
            
        return result
        
    except Exception as e:
        print(f"[Grub] Add blacklist error: {e}")
        return False

async def remove_blacklist(chat_id):
    """Remove grup dari blacklist dengan database compatibility dan log group integration"""
    try:
        db = get_db_conn()
        if not db:
            return False
        
        # Get existing data untuk log
        existing = None
        if DB_COMPATIBLE and plugin_db:
            existing_list = db.select('grup_blacklist', 'chat_id = ?', (chat_id,))
            existing = existing_list[0] if existing_list else None
            result = db.delete('grup_blacklist', 'chat_id = ?', (chat_id,))
        else:
            cur = db.execute("SELECT * FROM grup_blacklist WHERE chat_id=?", (chat_id,))
            existing = cur.fetchone()
            db.execute("DELETE FROM grup_blacklist WHERE chat_id=?", (chat_id,))
            db.commit()
            db.close()
            result = True
        
        # Send ke log group
        if result and existing:
            log_message = f"""
{get_emoji('adder2')} {convert_font('BLACKLIST REMOVED', 'bold')}

{get_emoji('check')} {convert_font('Chat ID:', 'mono')} {chat_id}
{get_emoji('adder3')} {convert_font('Title:', 'mono')} {existing.get('chat_title', f'Chat_{chat_id}')}
{get_emoji('adder6')} {convert_font('Removed at:', 'mono')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{get_emoji('main')} Grup ini sekarang dapat menerima gcast lagi.
            """.strip()
            await send_to_log_group(log_message)
            
        return result
        
    except Exception as e:
        print(f"[Grub] Remove blacklist error: {e}")
        return False

def get_blacklisted_groups():
    """Get all blacklisted group IDs for gcast integration"""
    try:
        db = get_db_conn()
        if not db:
            return set()
        
        blacklisted_ids = set()
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            rows = db.select('grup_blacklist', columns=['chat_id'])
            blacklisted_ids = {row['chat_id'] for row in rows}
        else:
            # Legacy database operations
            cursor = db.execute("SELECT chat_id FROM grup_blacklist")
            blacklisted_ids = {row[0] for row in cursor.fetchall()}
            db.close()
        
        return blacklisted_ids
    except Exception as e:
        print(f"[Grub] Get blacklist error: {e}")
        return set()

def is_blacklisted(chat_id):
    """Check if chat_id is blacklisted"""
    try:
        blacklisted_ids = get_blacklisted_groups()
        return chat_id in blacklisted_ids
    except Exception as e:
        print(f"[Grub] Check blacklist error: {e}")
        return False

def get_blacklist():
    """Get blacklist dengan database compatibility"""
    try:
        db = get_db_conn()
        if not db:
            return []
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.select('grup_blacklist', 'TRUE ORDER BY added_at DESC')
        else:
            # Legacy database operations
            cur = db.execute("SELECT * FROM grup_blacklist ORDER BY added_at DESC")
            rows = cur.fetchall()
            db.close()
            return rows
            
    except Exception as e:
        print(f"[Grub] Get blacklist error: {e}")
        return []

async def add_banlist(chat_id, reason=None):
    """Add grup ke banlist dengan database compatibility dan log group integration"""
    try:
        db = get_db_conn()
        if not db:
            return False
        
        # Get chat info jika memungkinkan
        chat_title = f"Chat_{chat_id}"
        try:
            if client:
                entity = await client.get_entity(chat_id)
                chat_title = getattr(entity, 'title', chat_title)
        except Exception:
            pass
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            'chat_id': chat_id,
            'chat_title': chat_title,
            'banned_at': now,
            'ban_reason': reason or 'Auto-detected ban/kick',
            'auto_detected': 1
        }
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            result = db.insert('grup_banlist', data)
        else:
            # Legacy database operations
            db.execute("INSERT OR REPLACE INTO grup_banlist (chat_id, chat_title, banned_at, ban_reason, auto_detected) VALUES (?, ?, ?, ?, ?)",
                       tuple(data.values()))
            db.commit()
            db.close()
            result = True
        
        # Send ke log group
        if result:
            log_message = f"""
{get_emoji('adder5')} {convert_font('BAN DETECTED', 'bold')}

{get_emoji('adder3')} {convert_font('Chat ID:', 'mono')} {chat_id}
{get_emoji('check')} {convert_font('Title:', 'mono')} {chat_title}
{get_emoji('adder4')} {convert_font('Reason:', 'mono')} {reason or 'Auto-detected'}
{get_emoji('adder6')} {convert_font('Detected at:', 'mono')} {now}

{get_emoji('main')} Userbot telah di-ban/kick dari grup ini.
            """.strip()
            await send_to_log_group(log_message)
            
        return result
        
    except Exception as e:
        print(f"[Grub] Add banlist error: {e}")
        return False

def get_banlist():
    try:
        conn = get_db_conn()
        if not conn: return []
        cur = conn.execute("SELECT chat_id, banned_at FROM grup_banlist ORDER BY banned_at DESC")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

# Otomatis grup log dari log.py
def get_grup_from_log():
    try:
        LOGDB = "plugins/log.db"
        if not os.path.exists(LOGDB):
            return []
        conn = sqlite3.connect(LOGDB)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT DISTINCT chat_id FROM log_message WHERE chat_id IS NOT NULL")
        ids = [row["chat_id"] for row in cur.fetchall() if row["chat_id"]]
        conn.close()
        return ids
    except Exception:
        return []

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

async def grup_cmd_handler(event):
    """Enhanced grup command handler dengan log group integration"""
    try:
        # Owner check
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split()
        chat = await event.get_chat()
        chat_id = chat.id
        
        if len(args) == 1:
            # Show help
            help_text = f"""
{get_emoji('main')} {convert_font('GRUP MANAGER v2.0', 'bold')}

{get_emoji('check')} {convert_font('Commands:', 'bold')}
• {convert_font('.grup log', 'mono')} - Show grup dari log
• {convert_font('.grup blacklist <id>', 'mono')} - Add grup ke blacklist
• {convert_font('.grup unblacklist <id>', 'mono')} - Remove dari blacklist  
• {convert_font('.grup blacklistlist', 'mono')} - Show blacklist
• {convert_font('.grup banlist', 'mono')} - Show banlist
• {convert_font('.grup loggroup', 'mono')} - Show log group info

{get_emoji('adder2')} {convert_font('Features:', 'bold')}
• Centralized database
• Log group integration  
• Auto ban detection
• Blacklist forwarding

{get_emoji('adder4')} {convert_font('Log Group:', 'bold')} {'Active' if os.getenv('LOG_GROUP_ID') else 'Not Set'}
            """.strip()
            await event.reply(help_text)
            return
        
        if len(args) == 2 and args[1] == "log":
            # Tampilkan semua grup dari log
            grup_ids = get_grup_from_log()
            if grup_ids:
                txt = f"{get_emoji('main')} {convert_font('Grup dari log.py:', 'bold')}\\n\\n"
                for gid in grup_ids[:20]:  # Limit to 20
                    txt += f"{get_emoji('check')} {convert_font(str(gid), 'mono')}\\n"
                if len(grup_ids) > 20:
                    txt += f"\\n{get_emoji('adder3')} ... dan {len(grup_ids) - 20} grup lainnya"
            else:
                txt = f"{get_emoji('adder3')} Belum ada grup di log.py."
            await event.reply(txt)
            
        elif len(args) >= 3 and args[1] == "blacklist":
            try:
                target_id = int(args[2])
                reason = " ".join(args[3:]) if len(args) > 3 else None
                success = await add_blacklist(target_id, reason, "manual")
                
                if success:
                    response = f"""
{get_emoji('adder2')} {convert_font('Blacklist Added!', 'bold')}

{get_emoji('check')} {convert_font('Group ID:', 'mono')} {target_id}
{get_emoji('adder3')} {convert_font('Reason:', 'mono')} {reason or 'Manual add'}
{get_emoji('adder6')} {convert_font('Log Group:', 'mono')} {'Notified' if os.getenv('LOG_GROUP_ID') else 'Not Set'}
                    """.strip()
                else:
                    response = f"{get_emoji('adder5')} Failed to add grup {target_id} to blacklist."
                    
                await event.reply(response)
            except ValueError:
                await event.reply(f"{get_emoji('adder3')} Format: {convert_font('.grup blacklist <id> [reason]', 'mono')}")
            except Exception as e:
                await event.reply(f"{get_emoji('adder5')} Error: {str(e)}")
                
        elif len(args) == 3 and args[1] == "unblacklist":
            try:
                target_id = int(args[2])
                success = await remove_blacklist(target_id)
                
                if success:
                    response = f"""
{get_emoji('adder2')} {convert_font('Blacklist Removed!', 'bold')}

{get_emoji('check')} {convert_font('Group ID:', 'mono')} {target_id}
{get_emoji('adder6')} {convert_font('Log Group:', 'mono')} {'Notified' if os.getenv('LOG_GROUP_ID') else 'Not Set'}
                    """.strip()
                else:
                    response = f"{get_emoji('adder5')} Failed to remove grup {target_id} from blacklist."
                    
                await event.reply(response)
            except ValueError:
                await event.reply(f"{get_emoji('adder3')} Format: {convert_font('.grup unblacklist <id>', 'mono')}")
            except Exception as e:
                await event.reply(f"{get_emoji('adder5')} Error: {str(e)}")
                
        elif len(args) == 2 and args[1] == "blacklistlist":
            rows = get_blacklist()
            if rows:
                txt = f"{get_emoji('adder5')} {convert_font('GRUP BLACKLIST', 'bold')}\\n\\n"
                for r in rows[:15]:  # Limit to 15
                    chat_id = r.get('chat_id', r.get('chat_id'))
                    chat_title = r.get('chat_title', f'Chat_{chat_id}')
                    added_at = r.get('added_at', 'Unknown')
                    reason = r.get('reason', 'No reason')
                    
                    txt += f"{get_emoji('check')} {convert_font(str(chat_id), 'mono')}\\n"
                    txt += f"   {convert_font('Title:', 'mono')} {chat_title}\\n"
                    txt += f"   {convert_font('Reason:', 'mono')} {reason}\\n"
                    txt += f"   {convert_font('Added:', 'mono')} {added_at}\\n\\n"
                    
                if len(rows) > 15:
                    txt += f"{get_emoji('adder3')} ... dan {len(rows) - 15} grup lainnya"
            else:
                txt = f"{get_emoji('check')} Belum ada grup blacklist."
            await event.reply(txt)
            
        elif len(args) == 2 and args[1] == "banlist":
            rows = get_banlist()
            if rows:
                txt = f"{get_emoji('adder3')} {convert_font('GRUP BANLIST', 'bold')}\\n\\n"
                for r in rows[:10]:  # Limit to 10
                    chat_id = r.get('chat_id', r.get('chat_id'))
                    chat_title = r.get('chat_title', f'Chat_{chat_id}')
                    banned_at = r.get('banned_at', 'Unknown')
                    ban_reason = r.get('ban_reason', 'Auto-detected')
                    
                    txt += f"{get_emoji('adder5')} {convert_font(str(chat_id), 'mono')}\\n"
                    txt += f"   {convert_font('Title:', 'mono')} {chat_title}\\n"
                    txt += f"   {convert_font('Reason:', 'mono')} {ban_reason}\\n"
                    txt += f"   {convert_font('Banned:', 'mono')} {banned_at}\\n\\n"
                    
                if len(rows) > 10:
                    txt += f"{get_emoji('adder4')} ... dan {len(rows) - 10} grup lainnya"
            else:
                txt = f"{get_emoji('check')} Belum ada grup banlist."
            await event.reply(txt)
            
        elif len(args) == 2 and args[1] == "loggroup":
            # Show log group information
            log_group_id = os.getenv('LOG_GROUP_ID')
            log_group_updated = os.getenv('LOG_GROUP_UPDATED')
            
            if log_group_id:
                try:
                    entity = await client.get_entity(int(log_group_id))
                    group_title = getattr(entity, 'title', 'Unknown')
                    
                    response = f"""
{get_emoji('main')} {convert_font('LOG GROUP INFO', 'bold')}

{get_emoji('check')} {convert_font('Group ID:', 'mono')} {log_group_id}
{get_emoji('adder2')} {convert_font('Title:', 'mono')} {group_title}
{get_emoji('adder4')} {convert_font('Updated:', 'mono')} {log_group_updated or 'Unknown'}
{get_emoji('adder6')} {convert_font('Status:', 'mono')} Active

{get_emoji('adder3')} All blacklist activities akan dikirim ke grup ini.
                    """.strip()
                except Exception as e:
                    response = f"""
{get_emoji('adder5')} {convert_font('LOG GROUP ERROR', 'bold')}

{get_emoji('check')} {convert_font('Group ID:', 'mono')} {log_group_id}
{get_emoji('adder3')} {convert_font('Error:', 'mono')} {str(e)}

{get_emoji('adder4')} Use {convert_font('.loggroup create', 'mono')} to create new log group.
                    """.strip()
            else:
                response = f"""
{get_emoji('adder3')} {convert_font('No Log Group Set', 'bold')}

{get_emoji('check')} Use {convert_font('.loggroup create', 'mono')} to create log group.
{get_emoji('adder2')} Log group akan menerima semua blacklist notifications.
                """.strip()
            
            await event.reply(response)
            
        else:
            await event.reply(f"{get_emoji('adder3')} Unknown command. Use {convert_font('.grup', 'mono')} for help.")
            
    except Exception as e:
        print(f"[Grub] Command handler error: {e}")
        await event.reply(f"{get_emoji('adder5')} Command error occurred")

async def ban_monitor_handler(event):
    """Monitor jika userbot diban/kick dari grup dengan enhanced logging"""
    try:
        # Check if this involves our userbot
        if getattr(event, "user_left", None) or getattr(event, "user_kicked", None):
            chat = await event.get_chat()
            chat_id = chat.id
            
            # Get our user ID
            if client:
                me = await client.get_me()
                our_id = me.id
                
                # Check if it's us who got kicked/left
                if hasattr(event, 'user_id') and event.user_id == our_id:
                    reason = "Auto-detected: User kicked" if getattr(event, "user_kicked", None) else "Auto-detected: User left"
                    await add_banlist(chat_id, reason)
                elif getattr(event, "user_kicked", None) and event.user_kicked.id == our_id:
                    await add_banlist(chat_id, "Auto-detected: Userbot was kicked")
                    
    except Exception as e:
        print(f"[Grub] Ban monitor error: {e}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    """Setup grup manager dengan log group integration"""
    global client
    client = telegram_client
    
    try:
        # Register event handlers
        client.add_event_handler(grup_cmd_handler, events.NewMessage(pattern=r"\.grup"))
        client.add_event_handler(ban_monitor_handler, events.ChatAction(func=lambda e: getattr(e, "user_left", None) or getattr(e, "user_kicked", None)))
        
        print("[Grub] Plugin loaded successfully with log group integration")
        return True
        
    except Exception as e:
        print(f"[Grub] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Grub] Plugin cleanup initiated")
        client = None
        print("[Grub] Plugin cleanup completed")
    except Exception as e:
        print(f"[Grub] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'add_blacklist', 'remove_blacklist', 'get_blacklist', 'add_banlist', 'get_banlist']