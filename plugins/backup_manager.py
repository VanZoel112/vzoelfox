"""
Database Backup Manager Plugin with Premium Emojis
File: plugins/backup_manager.py
Author: Morgan (Vzoel Fox's Assistant)
Version: 1.0.0
Fitur: Backup database dengan premium emoji mapping sendiri
"""

import os
import shutil
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Import database helper
try:
    from database import backup_database, select, get_owner_id
except ImportError:
    print("[Backup Manager] Database helper not found")
    backup_database = None
    select = None
    get_owner_id = lambda: 0

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "backup_manager",
    "version": "1.0.0",
    "description": "Database backup manager with premium emojis",
    "author": "Morgan (Vzoel Fox's Assistant)",
    "commands": [".backup", ".listbackups", ".dbstatus"],
    "features": ["database backup", "premium emojis", "backup listing", "db status"]
}

# ===== PREMIUM EMOJI CONFIGURATION =====
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

async def backup_handler(event):
    """Backup database handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        msg = await safe_send_premium(event, f"{get_emoji('adder1')} **Starting database backup...**")
        
        # Get all database files
        db_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.db') and not file.startswith('backup_'):
                    db_path = os.path.join(root, file)
                    db_files.append(db_path)
        
        if not db_files:
            await msg.edit(f"{get_emoji('adder5')} **No database files found!**")
            return
        
        # Create backup directory
        backup_dir = f"backups_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        backed_up = 0
        failed = 0
        
        for db_file in db_files:
            try:
                # Copy database file to backup directory
                filename = os.path.basename(db_file)
                backup_path = os.path.join(backup_dir, f"backup_{filename}")
                shutil.copy2(db_file, backup_path)
                backed_up += 1
            except Exception as e:
                print(f"[Backup Manager] Error backing up {db_file}: {e}")
                failed += 1
        
        # Create backup info file
        info_file = os.path.join(backup_dir, "backup_info.txt")
        with open(info_file, 'w') as f:
            f.write(f"Database Backup Created\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Files backed up: {backed_up}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Backup directory: {backup_dir}\n\n")
            f.write("Files included:\n")
            for db_file in db_files:
                size = os.path.getsize(db_file)
                f.write(f"- {db_file} ({size} bytes)\n")
        
        backup_size = sum(os.path.getsize(os.path.join(backup_dir, f)) 
                         for f in os.listdir(backup_dir))
        
        report = f"""
{get_emoji('main')} **Database Backup Complete!**

{get_emoji('check')} **Backup Summary:**
• Directory: `{backup_dir}`
• Files backed up: `{backed_up}`
• Failed: `{failed}`
• Total size: `{backup_size:,} bytes`

{get_emoji('adder2')} **Backup created successfully!**
{get_emoji('adder4')} Use `.listbackups` to see all backups
        """.strip()
        
        await msg.edit(report)
        
    except Exception as e:
        report = f"{get_emoji('adder5')} **Backup error:** {str(e)}"
        await safe_send_premium(event, report)

async def list_backups_handler(event):
    """List all backups handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        # Find all backup directories
        backup_dirs = []
        for item in os.listdir('.'):
            if os.path.isdir(item) and item.startswith('backups_'):
                backup_dirs.append(item)
        
        if not backup_dirs:
            await safe_send_premium(event, f"{get_emoji('adder5')} **No backups found!**")
            return
        
        # Sort by creation time (newest first)
        backup_dirs.sort(reverse=True)
        
        report_lines = [f"{get_emoji('main')} **Available Backups**", ""]
        
        for i, backup_dir in enumerate(backup_dirs[:10], 1):  # Show max 10
            # Get backup info
            info_file = os.path.join(backup_dir, "backup_info.txt")
            if os.path.exists(info_file):
                with open(info_file, 'r') as f:
                    content = f.read()
                    timestamp_line = [line for line in content.split('\n') if 'Timestamp:' in line]
                    files_line = [line for line in content.split('\n') if 'Files backed up:' in line]
                    
                    timestamp = timestamp_line[0].split(': ')[1] if timestamp_line else "Unknown"
                    files_count = files_line[0].split(': ')[1] if files_line else "0"
            else:
                timestamp = "Unknown"
                files_count = "0"
            
            # Get directory size
            dir_size = sum(os.path.getsize(os.path.join(backup_dir, f)) 
                          for f in os.listdir(backup_dir))
            
            report_lines.append(f"{get_emoji('adder2')} **Backup #{i}**")
            report_lines.append(f"• Directory: `{backup_dir}`")
            report_lines.append(f"• Created: `{timestamp}`")
            report_lines.append(f"• Files: `{files_count}`")
            report_lines.append(f"• Size: `{dir_size:,} bytes`")
            report_lines.append("")
        
        if len(backup_dirs) > 10:
            report_lines.append(f"{get_emoji('adder6')} *Showing 10 most recent backups*")
        
        report_lines.append(f"{get_emoji('adder4')} **Total backups:** `{len(backup_dirs)}`")
        
        report = "\n".join(report_lines)
        await safe_send_premium(event, report)
        
    except Exception as e:
        report = f"{get_emoji('adder5')} **List backups error:** {str(e)}"
        await safe_send_premium(event, report)

async def db_status_handler(event):
    """Database status handler"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        # Get all database files
        db_files = []
        total_size = 0
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.db'):
                    db_path = os.path.join(root, file)
                    size = os.path.getsize(db_path)
                    db_files.append((db_path, size))
                    total_size += size
        
        # Sort by size (largest first)
        db_files.sort(key=lambda x: x[1], reverse=True)
        
        report_lines = [
            f"{get_emoji('main')} **Database Status**",
            "",
            f"{get_emoji('check')} **Summary:**",
            f"• Total databases: `{len(db_files)}`",
            f"• Total size: `{total_size:,} bytes`",
            f"• Largest: `{db_files[0][0]}` ({db_files[0][1]:,} bytes)" if db_files else "• No databases",
            ""
        ]
        
        if db_files:
            report_lines.append(f"{get_emoji('adder4')} **Database Files:**")
            for db_path, size in db_files[:8]:  # Show max 8
                size_mb = size / 1024 / 1024
                if size_mb >= 1:
                    size_str = f"{size_mb:.1f} MB"
                elif size >= 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} bytes"
                
                report_lines.append(f"• `{db_path}`: {size_str}")
            
            if len(db_files) > 8:
                report_lines.append(f"• *...and {len(db_files)-8} more*")
        
        report_lines.append("")
        report_lines.append(f"{get_emoji('adder2')} Use `.backup` to create backup")
        
        report = "\n".join(report_lines)
        await safe_send_premium(event, report)
        
    except Exception as e:
        report = f"{get_emoji('adder5')} **DB status error:** {str(e)}"
        await safe_send_premium(event, report)

def get_plugin_info():
    return PLUGIN_INFO

async def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    client.add_event_handler(backup_handler, events.NewMessage(pattern=r"\.backup$"))
    client.add_event_handler(list_backups_handler, events.NewMessage(pattern=r"\.listbackups$"))
    client.add_event_handler(db_status_handler, events.NewMessage(pattern=r"\.dbstatus$"))
    
    print(f"✅ [Backup Manager] Plugin loaded - Database backup with premium emojis v{PLUGIN_INFO['version']}")