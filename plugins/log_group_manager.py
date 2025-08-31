"""
Log Group Manager Plugin for VzoelFox - Permanent Group Creator & Environment Manager
Fitur: Membuat grup log permanen, simpan ID ke environment, kelola semua aktivitas userbot
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Permanent Log Group Management
"""

import sqlite3
import os
import json
from datetime import datetime
from telethon import events, functions, types
from telethon.errors import ChatAdminRequiredError, FloodWaitError, PeerIdInvalidError

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('log_group_manager')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

PLUGIN_INFO = {
    "name": "log_group_manager", 
    "version": "1.0.0",
    "description": "Permanent log group creator & environment manager untuk menyimpan semua aktivitas userbot",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".loggroup create", ".loggroup status", ".loggroup set <id>", ".loggroup test"],
    "features": ["permanent log group", "environment integration", "auto blacklist sync", "activity forwarding"]
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

DB_FILE = "plugins/log_group_manager.db"
ENV_FILE = ".env"
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
            log_group_id INTEGER UNIQUE,
            group_title TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'active',
            environment_updated TEXT,
            additional_data TEXT
        """
        plugin_db.create_table('log_groups', table_schema)
        return plugin_db
    else:
        # Fallback ke legacy individual database
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_group_id INTEGER UNIQUE,
                    group_title TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'active',
                    environment_updated TEXT,
                    additional_data TEXT
                );
            """)
            conn.commit()
            return conn
        except Exception as e:
            print(f"[LogGroupManager] Database error: {e}")
            return None

def save_log_group(group_id, title, additional_data=None):
    """Save log group information"""
    try:
        db = get_db_conn()
        if not db:
            return False
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            'log_group_id': group_id,
            'group_title': title,
            'created_at': now,
            'status': 'active',
            'environment_updated': now,
            'additional_data': json.dumps(additional_data) if additional_data else None
        }
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.insert('log_groups', data)
        else:
            # Legacy database operations
            db.execute(
                "INSERT OR REPLACE INTO log_groups (log_group_id, group_title, created_at, status, environment_updated, additional_data) VALUES (?, ?, ?, ?, ?, ?)",
                tuple(data.values())
            )
            db.commit()
            db.close()
            return True
            
    except Exception as e:
        print(f"[LogGroupManager] Save error: {e}")
        return False

def get_log_group():
    """Get current log group information"""
    try:
        db = get_db_conn()
        if not db:
            return None
            
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            results = db.select('log_groups', 'status = ?', ('active',))
            return results[0] if results else None
        else:
            # Legacy database operations
            cur = db.execute("SELECT * FROM log_groups WHERE status = 'active' ORDER BY created_at DESC LIMIT 1")
            result = cur.fetchone()
            db.close()
            return result
            
    except Exception as e:
        print(f"[LogGroupManager] Get error: {e}")
        return None

def update_environment_file(group_id):
    """Update .env file dengan LOG_GROUP_ID"""
    try:
        env_path = os.path.join(os.getcwd(), ENV_FILE)
        env_vars = {}
        
        # Read existing .env file
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Update LOG_GROUP_ID
        env_vars['LOG_GROUP_ID'] = str(group_id)
        env_vars['LOG_GROUP_UPDATED'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write updated .env file
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# VzoelFox Userbot Environment Variables\n")
            f.write("# Generated automatically - Do not edit LOG_GROUP_ID manually\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Also update os.environ for current session
        os.environ['LOG_GROUP_ID'] = str(group_id)
        os.environ['LOG_GROUP_UPDATED'] = env_vars['LOG_GROUP_UPDATED']
        
        print(f"[LogGroupManager] Environment updated: LOG_GROUP_ID={group_id}")
        return True
        
    except Exception as e:
        print(f"[LogGroupManager] Environment update error: {e}")
        return False

async def create_log_group():
    """Create permanent log group for userbot"""
    try:
        if not client:
            return None, "Client not available"
        
        # Get userbot info
        me = await client.get_me()
        username = me.username or f"User_{me.id}"
        
        # Create group
        group_title = f"📊 {username} VzoelFox Logs"
        
        result = await client(functions.messages.CreateChatRequest(
            users=[me.id],
            title=group_title
        ))
        
        # Get the chat object
        chat_id = None
        if hasattr(result, 'chats') and result.chats:
            chat_id = result.chats[0].id
            # Convert to negative for supergroups
            if hasattr(result.chats[0], 'megagroup'):
                chat_id = -chat_id
        
        if not chat_id:
            return None, "Failed to get group ID"
        
        # Set group description
        description = f"""
🤖 VzoelFox Userbot Log Group
📊 Automatic logging untuk semua aktivitas userbot
🔒 Private group - Jangan bagikan atau invite orang lain
⚙️ Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📋 Fitur Logging:
• Blacklist notifications
• Command executions
• Error reports
• Activity summaries
• Auto backup logs

🚫 DO NOT DELETE THIS GROUP - Required untuk userbot operations
        """.strip()
        
        try:
            await client(functions.messages.EditChatAboutRequest(
                peer=chat_id,
                about=description
            ))
        except Exception as e:
            print(f"[LogGroupManager] Description update failed: {e}")
        
        # Save to database
        additional_data = {
            'creator_id': me.id,
            'creator_username': username,
            'auto_created': True,
            'permanent': True
        }
        
        save_success = save_log_group(chat_id, group_title, additional_data)
        env_success = update_environment_file(chat_id)
        
        if save_success and env_success:
            return chat_id, f"Log group created successfully: {chat_id}"
        else:
            return chat_id, f"Group created but database/env update failed"
            
    except FloodWaitError as e:
        return None, f"Rate limited. Please wait {e.seconds} seconds"
    except ChatAdminRequiredError:
        return None, "Admin rights required to create group"
    except Exception as e:
        return None, f"Creation failed: {str(e)}"

async def test_log_group(group_id):
    """Test log group by sending a test message"""
    try:
        if not client:
            return False, "Client not available"
        
        test_message = f"""
{get_emoji('main')} {convert_font('LOG GROUP TEST', 'bold')}

{get_emoji('check')} {convert_font('Status:', 'bold')} Active
{get_emoji('adder2')} {convert_font('Group ID:', 'mono')} {group_id}
{get_emoji('adder4')} {convert_font('Time:', 'mono')} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{get_emoji('adder3')} {convert_font('Test Result:', 'bold')} Log group working perfectly!
{get_emoji('adder5')} {convert_font('Integration:', 'bold')} Environment variables updated

{get_emoji('adder6')} This group akan menerima semua log dari userbot activities.
        """.strip()
        
        await client.send_message(group_id, test_message)
        return True, "Test message sent successfully"
        
    except PeerIdInvalidError:
        return False, "Invalid group ID - group might not exist"
    except Exception as e:
        return False, f"Test failed: {str(e)}"

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

async def loggroup_handler(event):
    """Handle log group management commands"""
    try:
        # Owner check
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split()
        
        if len(args) == 1:
            # Show help
            help_text = f"""
{get_emoji('main')} {convert_font('LOG GROUP MANAGER', 'bold')}

{get_emoji('check')} {convert_font('Commands:', 'bold')}
• {convert_font('.loggroup create', 'mono')} - Create permanent log group
• {convert_font('.loggroup status', 'mono')} - Show current log group status
• {convert_font('.loggroup set <id>', 'mono')} - Set existing group as log group
• {convert_font('.loggroup test', 'mono')} - Test current log group

{get_emoji('adder2')} {convert_font('Features:', 'bold')}
• Permanent log storage
• Environment integration
• Auto blacklist sync
• Activity forwarding

{get_emoji('adder4')} {convert_font('Note:', 'bold')}
Hanya 1 log group yang diizinkan per userbot untuk keamanan.
            """.strip()
            
            await event.reply(help_text)
            return
            
        command = args[1]
        
        if command == "create":
            # Create new log group
            current_group = get_log_group()
            if current_group:
                response = f"""
{get_emoji('adder3')} {convert_font('Log Group Already Exists!', 'bold')}

{get_emoji('check')} {convert_font('Current Group:', 'bold')}
• ID: {convert_font(str(current_group.get('log_group_id', 'Unknown')), 'mono')}
• Title: {current_group.get('group_title', 'Unknown')}
• Created: {current_group.get('created_at', 'Unknown')}

{get_emoji('adder5')} Use {convert_font('.loggroup test', 'mono')} to verify it's working.
                """.strip()
                await event.reply(response)
                return
            
            await event.reply(f"{get_emoji('adder4')} {convert_font('Creating log group...', 'mono')}")
            
            group_id, message = await create_log_group()
            
            if group_id:
                response = f"""
{get_emoji('main')} {convert_font('LOG GROUP CREATED!', 'bold')}

{get_emoji('adder2')} {convert_font('Group ID:', 'mono')} {group_id}
{get_emoji('check')} {convert_font('Environment:', 'mono')} Updated
{get_emoji('adder4')} {convert_font('Status:', 'mono')} Active

{get_emoji('adder6')} {convert_font('Important:', 'bold')}
• Group ID saved to .env file
• Available as LOG_GROUP_ID environment variable
• DO NOT delete this group!

{get_emoji('adder5')} {message}
                """.strip()
            else:
                response = f"{get_emoji('adder3')} {convert_font('Creation Failed:', 'bold')} {message}"
            
            await event.reply(response)
            
        elif command == "status":
            # Show current log group status
            current_group = get_log_group()
            env_group_id = os.getenv('LOG_GROUP_ID')
            
            if current_group:
                response = f"""
{get_emoji('main')} {convert_font('LOG GROUP STATUS', 'bold')}

{get_emoji('adder2')} {convert_font('Database:', 'bold')}
• ID: {convert_font(str(current_group.get('log_group_id', 'Unknown')), 'mono')}
• Title: {current_group.get('group_title', 'Unknown')}
• Status: {current_group.get('status', 'Unknown')}
• Created: {current_group.get('created_at', 'Unknown')}

{get_emoji('check')} {convert_font('Environment:', 'bold')}
• LOG_GROUP_ID: {convert_font(env_group_id or 'Not Set', 'mono')}
• Updated: {os.getenv('LOG_GROUP_UPDATED', 'Unknown')}

{get_emoji('adder4')} {convert_font('Sync Status:', 'bold')} {'✅ Synced' if str(current_group.get('log_group_id')) == env_group_id else '❌ Out of Sync'}
                """.strip()
            else:
                response = f"""
{get_emoji('adder3')} {convert_font('No Log Group Found', 'bold')}

{get_emoji('check')} {convert_font('Environment LOG_GROUP_ID:', 'mono')} {env_group_id or 'Not Set'}

{get_emoji('adder5')} Use {convert_font('.loggroup create', 'mono')} to create a new log group.
                """.strip()
            
            await event.reply(response)
            
        elif command == "set" and len(args) >= 3:
            # Set existing group as log group
            try:
                group_id = int(args[2])
                
                # Test if group exists and accessible
                try:
                    entity = await client.get_entity(group_id)
                    title = getattr(entity, 'title', f"Group_{group_id}")
                except Exception as e:
                    await event.reply(f"{get_emoji('adder3')} {convert_font('Invalid Group ID:', 'bold')} {str(e)}")
                    return
                
                # Save to database and environment
                save_success = save_log_group(group_id, title)
                env_success = update_environment_file(group_id)
                
                if save_success and env_success:
                    response = f"""
{get_emoji('adder2')} {convert_font('Log Group Set Successfully!', 'bold')}

{get_emoji('check')} {convert_font('Group ID:', 'mono')} {group_id}
{get_emoji('adder4')} {convert_font('Title:', 'mono')} {title}
{get_emoji('main')} {convert_font('Environment:', 'mono')} Updated

{get_emoji('adder6')} Use {convert_font('.loggroup test', 'mono')} to verify functionality.
                    """.strip()
                else:
                    response = f"{get_emoji('adder3')} {convert_font('Failed to save log group settings', 'bold')}"
                    
                await event.reply(response)
                
            except ValueError:
                await event.reply(f"{get_emoji('adder3')} Invalid group ID format. Use: {convert_font('.loggroup set <numeric_id>', 'mono')}")
                
        elif command == "test":
            # Test current log group
            current_group = get_log_group()
            if not current_group:
                await event.reply(f"{get_emoji('adder3')} {convert_font('No log group configured. Use', 'bold')} {convert_font('.loggroup create', 'mono')} {convert_font('first.', 'bold')}")
                return
                
            group_id = current_group.get('log_group_id')
            if not group_id:
                await event.reply(f"{get_emoji('adder3')} {convert_font('Invalid log group configuration', 'bold')}")
                return
                
            await event.reply(f"{get_emoji('adder4')} {convert_font('Testing log group...', 'mono')}")
            
            success, message = await test_log_group(group_id)
            
            if success:
                response = f"""
{get_emoji('main')} {convert_font('LOG GROUP TEST PASSED!', 'bold')}

{get_emoji('adder2')} {convert_font('Group ID:', 'mono')} {group_id}
{get_emoji('check')} {convert_font('Status:', 'mono')} Active
{get_emoji('adder4')} {convert_font('Result:', 'mono')} {message}

{get_emoji('adder6')} Log group siap menerima aktivitas userbot!
                """.strip()
            else:
                response = f"""
{get_emoji('adder3')} {convert_font('LOG GROUP TEST FAILED!', 'bold')}

{get_emoji('adder5')} {convert_font('Error:', 'mono')} {message}

{get_emoji('check')} Try {convert_font('.loggroup create', 'mono')} to create a new log group.
                """.strip()
                
            await event.reply(response)
            
        else:
            await event.reply(f"{get_emoji('adder3')} Unknown command. Use {convert_font('.loggroup', 'mono')} for help.")
            
    except Exception as e:
        print(f"[LogGroupManager] Handler error: {e}")
        await event.reply(f"{get_emoji('adder3')} {convert_font('Command error occurred', 'bold')}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    """Setup log group manager plugin"""
    global client
    client = telegram_client
    
    try:
        # Register event handler
        client.add_event_handler(loggroup_handler, events.NewMessage(pattern=r"\.loggroup"))
        
        print("[LogGroupManager] Plugin loaded successfully")
        return True
        
    except Exception as e:
        print(f"[LogGroupManager] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[LogGroupManager] Plugin cleanup initiated")
        client = None
        print("[LogGroupManager] Plugin cleanup completed")
    except Exception as e:
        print(f"[LogGroupManager] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'create_log_group', 'get_log_group', 'update_environment_file']