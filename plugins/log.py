"""
Enhanced Activity Logger Plugin - Comprehensive Userbot Monitoring
Fitur: Monitor semua aktivitas userbot, outgoing/incoming messages, commands, statistics
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 2.0.0 - Complete Activity Monitoring
"""

import sqlite3
import os
import json
from datetime import datetime
from telethon import events
from telethon.tl.types import Channel, Chat

# Import assetjson environment
try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None
client = None

PLUGIN_INFO = {
    "name": "log",
    "version": "2.0.0",
    "description": "Comprehensive userbot activity monitoring dengan real-time statistics",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".log show", ".log query <keyword>", ".log clear", ".log stats", ".log activity", ".log monitor"],
    "features": ["activity logging", "userbot monitoring", "statistics", "premium emoji", "real-time tracking"]
}

DB_FILE = "plugins/log.db"

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        
        # Enhanced message logging table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                user_id INTEGER,
                chat_id INTEGER,
                chat_title TEXT,
                username TEXT,
                message_text TEXT,
                command TEXT,
                is_outgoing INTEGER DEFAULT 0,
                message_id INTEGER,
                reply_to_id INTEGER,
                media_type TEXT,
                file_name TEXT,
                additional_data TEXT,
                created_at TEXT,
                timestamp INTEGER
            );
        """)
        
        # Activity statistics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                messages_sent INTEGER DEFAULT 0,
                messages_received INTEGER DEFAULT 0,
                commands_executed INTEGER DEFAULT 0,
                chats_active INTEGER DEFAULT 0,
                media_sent INTEGER DEFAULT 0,
                updated_at TEXT
            );
        """)
        
        # Chat monitoring table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER UNIQUE,
                chat_title TEXT,
                chat_type TEXT,
                monitoring_enabled INTEGER DEFAULT 1,
                log_level TEXT DEFAULT 'all',
                last_activity TEXT,
                message_count INTEGER DEFAULT 0,
                created_at TEXT
            );
        """)
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"[ActivityLog] Database error: {e}")
        return None

# Helper functions for enhanced logging
async def safe_send_message(event, text):
    """Send message with env integration"""
    if env and 'safe_send_with_entities' in env:
        await env['safe_send_with_entities'](event, text)
    else:
        await event.reply(text)

def safe_get_emoji(emoji_type):
    """Get emoji with fallback"""
    if env and 'get_emoji' in env:
        return env['get_emoji'](emoji_type)
    emoji_fallbacks = {
        'main': '🤩', 'check': '⚙️', 'adder1': '⛈', 'adder2': '✅', 
        'adder3': '👽', 'adder4': '✈️', 'adder5': '😈', 'adder6': '🎚️'
    }
    return emoji_fallbacks.get(emoji_type, '📝')

def safe_convert_font(text, font_type='bold'):
    """Convert font with fallback"""
    if env and 'convert_font' in env:
        return env['convert_font'](text, font_type)
    return text

async def get_chat_info(chat):
    """Get detailed chat information"""
    try:
        if isinstance(chat, Channel):
            chat_type = "Channel" if chat.broadcast else "Supergroup"
            title = chat.title
        elif isinstance(chat, Chat):
            chat_type = "Group"
            title = chat.title
        else:
            chat_type = "Private"
            title = f"User_{chat.id}"
        
        return {
            'title': title,
            'type': chat_type,
            'id': chat.id
        }
    except Exception:
        return {
            'title': f"Chat_{chat.id if hasattr(chat, 'id') else 'Unknown'}",
            'type': "Unknown",
            'id': chat.id if hasattr(chat, 'id') else 0
        }

def log_activity(activity_type, user_id=None, chat_id=None, chat_title=None, 
                username=None, message_text=None, command=None, is_outgoing=False, 
                message_id=None, reply_to_id=None, media_type=None, file_name=None, 
                additional_data=None):
    """Enhanced activity logging function"""
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        now = datetime.now()
        timestamp = int(now.timestamp())
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Store additional data as JSON if it's a dict
        if isinstance(additional_data, dict):
            additional_data = json.dumps(additional_data)
        
        conn.execute("""
            INSERT INTO activity_log 
            (activity_type, user_id, chat_id, chat_title, username, message_text, 
             command, is_outgoing, message_id, reply_to_id, media_type, file_name, 
             additional_data, created_at, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_type, user_id, chat_id, chat_title, username, message_text,
            command, 1 if is_outgoing else 0, message_id, reply_to_id, media_type,
            file_name, additional_data, created_at, timestamp
        ))
        
        conn.commit()
        conn.close()
        
        # Update statistics
        update_daily_stats(activity_type, is_outgoing)
        return True
        
    except Exception as e:
        print(f"[ActivityLog] Log error: {e}")
        return False

def update_daily_stats(activity_type, is_outgoing=False):
    """Update daily statistics"""
    try:
        conn = get_db_conn()
        if not conn:
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize today's stats if not exists
        conn.execute("""
            INSERT OR IGNORE INTO activity_stats (date, updated_at) VALUES (?, ?)
        """, (today, now))
        
        # Update counters based on activity type
        if activity_type == "message":
            if is_outgoing:
                conn.execute("UPDATE activity_stats SET messages_sent = messages_sent + 1, updated_at = ? WHERE date = ?", (now, today))
            else:
                conn.execute("UPDATE activity_stats SET messages_received = messages_received + 1, updated_at = ? WHERE date = ?", (now, today))
        elif activity_type == "command":
            conn.execute("UPDATE activity_stats SET commands_executed = commands_executed + 1, updated_at = ? WHERE date = ?", (now, today))
        elif activity_type == "media":
            conn.execute("UPDATE activity_stats SET media_sent = media_sent + 1, updated_at = ? WHERE date = ?", (now, today))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"[ActivityLog] Stats update error: {e}")

def log_message(user_id, chat_id, username, text):
    """Legacy function - redirects to enhanced logging"""
    return log_activity("message", user_id=user_id, chat_id=chat_id, 
                       username=username, message_text=text, is_outgoing=False)

def query_logs(chat_id, keyword=None, limit=10):
    try:
        conn = get_db_conn()
        if not conn:
            return []
        if keyword:
            cur = conn.execute(
                "SELECT * FROM log_message WHERE chat_id=? AND text LIKE ? ORDER BY created_at DESC LIMIT ?",
                (chat_id, f"%{keyword}%", limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM log_message WHERE chat_id=? ORDER BY created_at DESC LIMIT ?",
                (chat_id, limit),
            )
        logs = cur.fetchall()
        conn.close()
        return logs
    except Exception:
        return []

def clear_logs(chat_id):
    try:
        conn = get_db_conn()
        if not conn:
            return False
        conn.execute("DELETE FROM log_message WHERE chat_id=?", (chat_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# Enhanced event handlers for comprehensive monitoring
async def incoming_message_handler(event):
    """Log all incoming messages"""
    try:
        chat = await event.get_chat()
        chat_info = await get_chat_info(chat)
        sender = await event.get_sender()
        
        username = getattr(sender, 'username', '') or f"User_{event.sender_id}"
        text = event.message.message if event.message else ""
        
        # Don't log our own .log commands to avoid spam
        if text.startswith(".log"):
            return
        
        # Check for media
        media_type = None
        file_name = None
        if event.message.media:
            media_type = type(event.message.media).__name__
            if hasattr(event.message.media, 'document') and event.message.media.document:
                if hasattr(event.message.media.document, 'attributes'):
                    for attr in event.message.media.document.attributes:
                        if hasattr(attr, 'file_name') and attr.file_name:
                            file_name = attr.file_name
                            break
        
        log_activity(
            activity_type="message",
            user_id=event.sender_id,
            chat_id=chat.id,
            chat_title=chat_info['title'],
            username=username,
            message_text=text[:500],  # Limit text length
            is_outgoing=False,
            message_id=event.message.id,
            reply_to_id=event.message.reply_to_msg_id,
            media_type=media_type,
            file_name=file_name
        )
    except Exception as e:
        print(f"[ActivityLog] Incoming handler error: {e}")

async def outgoing_message_handler(event):
    """Log all outgoing messages (userbot activities)"""
    try:
        chat = await event.get_chat()
        chat_info = await get_chat_info(chat)
        
        text = event.message.message if event.message else ""
        
        # Detect if it's a command
        is_command = text.startswith(".")
        command = None
        if is_command:
            command = text.split()[0] if text.split() else text
        
        # Check for media
        media_type = None
        file_name = None
        if event.message.media:
            media_type = type(event.message.media).__name__
            if hasattr(event.message.media, 'document') and event.message.media.document:
                if hasattr(event.message.media.document, 'attributes'):
                    for attr in event.message.media.document.attributes:
                        if hasattr(attr, 'file_name') and attr.file_name:
                            file_name = attr.file_name
                            break
        
        log_activity(
            activity_type="command" if is_command else "message",
            user_id=event.sender_id,
            chat_id=chat.id,
            chat_title=chat_info['title'],
            username="userbot",
            message_text=text[:500],  # Limit text length
            command=command,
            is_outgoing=True,
            message_id=event.message.id,
            reply_to_id=event.message.reply_to_msg_id,
            media_type=media_type,
            file_name=file_name
        )
    except Exception as e:
        print(f"[ActivityLog] Outgoing handler error: {e}")

async def message_edited_handler(event):
    """Log message edits"""
    try:
        chat = await event.get_chat()
        chat_info = await get_chat_info(chat)
        sender = await event.get_sender()
        
        username = getattr(sender, 'username', '') or f"User_{event.sender_id}"
        text = event.message.message if event.message else ""
        
        log_activity(
            activity_type="edit",
            user_id=event.sender_id,
            chat_id=chat.id,
            chat_title=chat_info['title'],
            username=username,
            message_text=f"[EDITED] {text[:450]}",
            is_outgoing=event.out,
            message_id=event.message.id,
            additional_data={"action": "message_edited"}
        )
    except Exception as e:
        print(f"[ActivityLog] Edit handler error: {e}")

async def message_deleted_handler(event):
    """Log message deletions"""
    try:
        for msg_id in event.deleted_ids:
            log_activity(
                activity_type="delete",
                chat_id=event.chat_id,
                message_id=msg_id,
                additional_data={"action": "message_deleted", "deleted_ids": event.deleted_ids}
            )
    except Exception as e:
        print(f"[ActivityLog] Delete handler error: {e}")

async def log_cmd_handler(event):
    """Enhanced log command handler with comprehensive monitoring features"""
    try:
        # Log this command execution
        chat = await event.get_chat()
        chat_info = await get_chat_info(chat)
        
        log_activity(
            activity_type="command",
            user_id=event.sender_id,
            chat_id=chat.id,
            chat_title=chat_info['title'],
            username="userbot",
            command=".log",
            message_text=event.text,
            is_outgoing=True
        )
        
        args = event.text.split(maxsplit=2)
        
        if len(args) == 1:
            # Show help
            help_text = f"""
{safe_get_emoji('main')} {safe_convert_font('ACTIVITY LOGGER v2.0', 'bold')}

{safe_get_emoji('check')} {safe_convert_font('Commands:', 'bold')}
• {safe_convert_font('.log show', 'mono')} - Show recent activity
• {safe_convert_font('.log query <keyword>', 'mono')} - Search activity
• {safe_convert_font('.log stats', 'mono')} - Show statistics  
• {safe_convert_font('.log activity', 'mono')} - Show userbot activity
• {safe_convert_font('.log monitor', 'mono')} - Monitoring status
• {safe_convert_font('.log clear', 'mono')} - Clear chat logs

{safe_get_emoji('adder2')} {safe_convert_font('Features:', 'bold')}
• Real-time userbot monitoring
• Command execution tracking
• Message statistics
• Media logging
• Edit/Delete tracking

{safe_get_emoji('adder4')} {safe_convert_font('Monitoring:', 'bold')} All userbot activities
            """.strip()
            await safe_send_message(event, help_text)
            
        elif len(args) == 2:
            command = args[1]
            
            if command == "show":
                await show_recent_activity(event, chat.id)
            elif command == "stats":
                await show_activity_stats(event)
            elif command == "activity":
                await show_userbot_activity(event, chat.id)
            elif command == "monitor":
                await show_monitoring_status(event)
            elif command == "clear":
                await clear_chat_logs(event, chat.id)
            else:
                await safe_send_message(event, f"{safe_get_emoji('adder3')} Unknown command: {command}")
                
        elif len(args) >= 3 and args[1] == "query":
            keyword = args[2]
            await search_activity(event, chat.id, keyword)
            
    except Exception as e:
        print(f"[ActivityLog] Command handler error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Command error occurred")

async def show_recent_activity(event, chat_id):
    """Show recent activity in current chat"""
    try:
        conn = get_db_conn()
        if not conn:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} Database error")
            return
            
        cur = conn.execute("""
            SELECT activity_type, username, message_text, command, is_outgoing, created_at, media_type
            FROM activity_log 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (chat_id,))
        
        activities = cur.fetchall()
        conn.close()
        
        if not activities:
            await safe_send_message(event, f"{safe_get_emoji('check')} No activity logged in this chat yet")
            return
        
        activity_text = f"{safe_get_emoji('main')} {safe_convert_font('RECENT ACTIVITY', 'bold')}\n\n"
        
        for activity in activities:
            activity_type = activity['activity_type']
            username = activity['username'] or 'Unknown'
            text = activity['message_text'][:50] + "..." if activity['message_text'] and len(activity['message_text']) > 50 else activity['message_text']
            created_at = activity['created_at']
            is_outgoing = activity['is_outgoing']
            media_type = activity['media_type']
            command = activity['command']
            
            # Format activity icon
            if activity_type == "command":
                icon = safe_get_emoji('adder4')
                action = f"CMD: {command}"
            elif activity_type == "message":
                icon = safe_get_emoji('adder2') if is_outgoing else safe_get_emoji('check')
                action = f"{'OUT' if is_outgoing else 'IN'}: {text or '[No text]'}"
            elif activity_type == "edit":
                icon = safe_get_emoji('adder6')
                action = f"EDIT: {text or '[No text]'}"
            elif activity_type == "delete":
                icon = safe_get_emoji('adder3')
                action = "DELETE"
            else:
                icon = safe_get_emoji('main')
                action = f"{activity_type.upper()}"
            
            if media_type:
                action += f" [{media_type}]"
            
            activity_text += f"{icon} {safe_convert_font(username, 'mono')} - {action}\n{safe_convert_font(created_at[-8:], 'mono')}\n\n"
        
        await safe_send_message(event, activity_text.strip())
        
    except Exception as e:
        print(f"[ActivityLog] Show activity error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Error loading activity")

async def show_activity_stats(event):
    """Show comprehensive activity statistics"""
    try:
        conn = get_db_conn()
        if not conn:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} Database error")
            return
        
        # Get today's stats
        today = datetime.now().strftime("%Y-%m-%d")
        cur = conn.execute("SELECT * FROM activity_stats WHERE date = ?", (today,))
        today_stats = cur.fetchone()
        
        # Get total activity counts
        cur = conn.execute("""
            SELECT 
                COUNT(*) as total_activities,
                SUM(CASE WHEN activity_type = 'command' THEN 1 ELSE 0 END) as total_commands,
                SUM(CASE WHEN activity_type = 'message' AND is_outgoing = 1 THEN 1 ELSE 0 END) as messages_sent,
                SUM(CASE WHEN activity_type = 'message' AND is_outgoing = 0 THEN 1 ELSE 0 END) as messages_received,
                COUNT(DISTINCT chat_id) as active_chats
            FROM activity_log
        """)
        
        total_stats = cur.fetchone()
        
        # Get recent command usage
        cur = conn.execute("""
            SELECT command, COUNT(*) as usage_count 
            FROM activity_log 
            WHERE activity_type = 'command' AND command IS NOT NULL
            GROUP BY command 
            ORDER BY usage_count DESC 
            LIMIT 5
        """)
        
        top_commands = cur.fetchall()
        conn.close()
        
        stats_text = f"""
{safe_get_emoji('main')} {safe_convert_font('USERBOT ACTIVITY STATISTICS', 'bold')}

{safe_get_emoji('adder2')} {safe_convert_font('Today:', 'bold')}
• Messages Sent: {today_stats['messages_sent'] if today_stats else 0}
• Messages Received: {today_stats['messages_received'] if today_stats else 0}
• Commands Executed: {today_stats['commands_executed'] if today_stats else 0}

{safe_get_emoji('check')} {safe_convert_font('All Time:', 'bold')}
• Total Activities: {total_stats['total_activities'] or 0}
• Commands Run: {total_stats['total_commands'] or 0}  
• Messages Sent: {total_stats['messages_sent'] or 0}
• Messages Received: {total_stats['messages_received'] or 0}
• Active Chats: {total_stats['active_chats'] or 0}

{safe_get_emoji('adder4')} {safe_convert_font('Top Commands:', 'bold')}
        """.strip()
        
        if top_commands:
            for cmd in top_commands:
                stats_text += f"\n• {safe_convert_font(cmd['command'], 'mono')}: {cmd['usage_count']}"
        else:
            stats_text += "\n• No commands logged yet"
            
        await safe_send_message(event, stats_text)
        
    except Exception as e:
        print(f"[ActivityLog] Stats error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Error loading statistics")

async def show_userbot_activity(event, chat_id):
    """Show only userbot outgoing activities"""
    try:
        conn = get_db_conn()
        if not conn:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} Database error")
            return
            
        cur = conn.execute("""
            SELECT activity_type, message_text, command, created_at, media_type
            FROM activity_log 
            WHERE chat_id = ? AND is_outgoing = 1
            ORDER BY timestamp DESC 
            LIMIT 15
        """, (chat_id,))
        
        activities = cur.fetchall()
        conn.close()
        
        if not activities:
            await safe_send_message(event, f"{safe_get_emoji('check')} No userbot activity in this chat yet")
            return
        
        activity_text = f"{safe_get_emoji('adder4')} {safe_convert_font('USERBOT ACTIVITY LOG', 'bold')}\n\n"
        
        for activity in activities:
            activity_type = activity['activity_type']
            text = activity['message_text'][:40] + "..." if activity['message_text'] and len(activity['message_text']) > 40 else activity['message_text']
            created_at = activity['created_at']
            media_type = activity['media_type']
            command = activity['command']
            
            if activity_type == "command":
                icon = safe_get_emoji('adder2')
                action = f"{safe_convert_font('CMD:', 'bold')} {safe_convert_font(command, 'mono')}"
            else:
                icon = safe_get_emoji('check')
                action = f"{safe_convert_font('MSG:', 'bold')} {text or '[No text]'}"
            
            if media_type:
                action += f" {safe_convert_font(f'[{media_type}]', 'mono')}"
            
            activity_text += f"{icon} {action}\n{safe_convert_font(created_at[-8:], 'mono')}\n\n"
        
        await safe_send_message(event, activity_text.strip())
        
    except Exception as e:
        print(f"[ActivityLog] Userbot activity error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Error loading userbot activity")

async def show_monitoring_status(event):
    """Show monitoring system status"""
    try:
        conn = get_db_conn()
        if not conn:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} Database error")
            return
        
        # Get monitoring stats
        cur = conn.execute("SELECT COUNT(*) as monitored_chats FROM chat_monitoring WHERE monitoring_enabled = 1")
        monitored = cur.fetchone()['monitored_chats']
        
        cur = conn.execute("SELECT COUNT(*) as total_activities FROM activity_log WHERE DATE(created_at) = DATE('now')")
        today_activities = cur.fetchone()['total_activities']
        
        conn.close()
        
        status_text = f"""
{safe_get_emoji('adder6')} {safe_convert_font('MONITORING SYSTEM STATUS', 'bold')}

{safe_get_emoji('adder2')} {safe_convert_font('Status:', 'bold')} Active
{safe_get_emoji('check')} {safe_convert_font('Monitored Chats:', 'bold')} {monitored}
{safe_get_emoji('main')} {safe_convert_font('Today Activities:', 'bold')} {today_activities}

{safe_get_emoji('adder4')} {safe_convert_font('Tracking:', 'bold')}
• Incoming Messages ✅
• Outgoing Messages ✅  
• Command Executions ✅
• Message Edits ✅
• Message Deletions ✅
• Media Files ✅

{safe_get_emoji('adder5')} {safe_convert_font('Database:', 'bold')} SQLite Active
{safe_get_emoji('adder3')} {safe_convert_font('Real-time Logging:', 'bold')} Enabled
        """.strip()
        
        await safe_send_message(event, status_text)
        
    except Exception as e:
        print(f"[ActivityLog] Status error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Error loading status")

async def search_activity(event, chat_id, keyword):
    """Search activity by keyword"""
    try:
        conn = get_db_conn()
        if not conn:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} Database error")
            return
            
        cur = conn.execute("""
            SELECT activity_type, username, message_text, command, is_outgoing, created_at, media_type
            FROM activity_log 
            WHERE chat_id = ? AND (message_text LIKE ? OR command LIKE ?)
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (chat_id, f"%{keyword}%", f"%{keyword}%"))
        
        results = cur.fetchall()
        conn.close()
        
        if not results:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} No results found for: {safe_convert_font(keyword, 'mono')}")
            return
        
        search_text = f"{safe_get_emoji('main')} {safe_convert_font('SEARCH RESULTS', 'bold')}\n"
        search_text += f"{safe_get_emoji('check')} {safe_convert_font('Keyword:', 'mono')} {keyword}\n\n"
        
        for result in results:
            activity_type = result['activity_type']
            username = result['username'] or 'Unknown'
            text = result['message_text'][:40] + "..." if result['message_text'] and len(result['message_text']) > 40 else result['message_text']
            created_at = result['created_at']
            is_outgoing = result['is_outgoing']
            command = result['command']
            
            if activity_type == "command":
                icon = safe_get_emoji('adder4')
                action = f"CMD: {command}"
            else:
                icon = safe_get_emoji('adder2') if is_outgoing else safe_get_emoji('check')
                action = f"{'OUT' if is_outgoing else 'IN'}: {text or '[No text]'}"
            
            search_text += f"{icon} {safe_convert_font(username, 'mono')} - {action}\n{safe_convert_font(created_at[-8:], 'mono')}\n\n"
        
        await safe_send_message(event, search_text.strip())
        
    except Exception as e:
        print(f"[ActivityLog] Search error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Search error occurred")

async def clear_chat_logs(event, chat_id):
    """Clear logs for current chat"""
    try:
        conn = get_db_conn()
        if not conn:
            await safe_send_message(event, f"{safe_get_emoji('adder3')} Database error")
            return
        
        cur = conn.execute("SELECT COUNT(*) as count FROM activity_log WHERE chat_id = ?", (chat_id,))
        count = cur.fetchone()['count']
        
        conn.execute("DELETE FROM activity_log WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        
        await safe_send_message(event, f"{safe_get_emoji('adder2')} {safe_convert_font('Logs Cleared!', 'bold')}\n{safe_get_emoji('check')} Removed {count} activity records from this chat")
        
    except Exception as e:
        print(f"[ActivityLog] Clear error: {e}")
        await safe_send_message(event, f"{safe_get_emoji('adder3')} Error clearing logs")

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Enhanced setup function with comprehensive userbot monitoring"""
    global client, env
    client = client_instance
    
    try:
        # Create plugin environment
        env = create_plugin_environment(client)
        
        # Register comprehensive event handlers
        
        # 1. Incoming messages (from others)
        client.add_event_handler(
            incoming_message_handler, 
            events.NewMessage(incoming=True, func=lambda e: not (e.text and e.text.startswith(".log")))
        )
        
        # 2. Outgoing messages (userbot activities) - THIS IS THE KEY IMPROVEMENT
        client.add_event_handler(
            outgoing_message_handler,
            events.NewMessage(outgoing=True)
        )
        
        # 3. Message edits
        client.add_event_handler(
            message_edited_handler,
            events.MessageEdited()
        )
        
        # 4. Message deletions
        client.add_event_handler(
            message_deleted_handler,
            events.MessageDeleted()
        )
        
        # 5. Command handler
        client.add_event_handler(
            log_cmd_handler, 
            events.NewMessage(pattern=r"\.log")
        )
        
        print(f"✅ [ActivityLog] Enhanced monitoring v{PLUGIN_INFO['version']} - Comprehensive userbot tracking active")
        
        if env and 'logger' in env:
            env['logger'].info("[ActivityLog] Comprehensive userbot activity monitoring initialized")
            
    except Exception as e:
        print(f"[ActivityLog] Setup error: {e}")
        return False
        
    return True