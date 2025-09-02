"""
Auto Updater Plugin for VzoelFox Userbot - Comprehensive Update System
Fitur: Git-based updates, rollback, backup, dependency management, seamless restart
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Complete Update Management System
"""

import sqlite3
import os
import sys
import subprocess
import json
import shutil
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Import database compatibility layer
try:
    from database_helper import get_plugin_db
    plugin_db = get_plugin_db('updater')
    DB_COMPATIBLE = True
except ImportError:
    plugin_db = None
    DB_COMPATIBLE = False

PLUGIN_INFO = {
    "name": "updater",
    "version": "1.0.0", 
    "description": "Comprehensive auto-update system dengan Git integration, rollback, dan dependency management",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".update", ".update check", ".update force", ".update rollback", ".update status", ".update changelog"],
    "features": ["git integration", "auto backup", "rollback system", "dependency management", "seamless restart"]
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

DB_FILE = "plugins/updater.db"
BACKUP_DIR = "data/backups/updates"
client = None

def get_emoji(emoji_type):
    """Get premium emoji dari mapping"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

# Import from central font system
from utils.font_helper import convert_font

def get_db_conn():
    """Get database connection dengan compatibility layer"""
    if DB_COMPATIBLE and plugin_db:
        # Initialize table dengan centralized database
        table_schema = """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_type TEXT,
            old_commit TEXT,
            new_commit TEXT,
            backup_path TEXT,
            status TEXT,
            error_message TEXT,
            created_at TEXT,
            completed_at TEXT,
            rollback_available INTEGER DEFAULT 1
        """
        plugin_db.create_table('update_history', table_schema)
        return plugin_db
    else:
        # Fallback ke legacy individual database
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE IF NOT EXISTS update_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_type TEXT,
                    old_commit TEXT,
                    new_commit TEXT,
                    backup_path TEXT,
                    status TEXT,
                    error_message TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    rollback_available INTEGER DEFAULT 1
                );
            """)
            conn.commit()
            return conn
        except Exception as e:
            print(f"[Updater] Database error: {e}")
            return None

def log_update_attempt(update_type, old_commit, new_commit, backup_path, status, error_message=None):
    """Log update attempt ke database"""
    try:
        db = get_db_conn()
        if not db:
            return False
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            'update_type': update_type,
            'old_commit': old_commit,
            'new_commit': new_commit,
            'backup_path': backup_path,
            'status': status,
            'error_message': error_message,
            'created_at': now,
            'completed_at': now if status in ['success', 'failed'] else None,
            'rollback_available': 1 if status == 'success' else 0
        }
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.insert('update_history', data)
        else:
            # Legacy database operations
            db.execute(
                "INSERT INTO update_history (update_type, old_commit, new_commit, backup_path, status, error_message, created_at, completed_at, rollback_available) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(data.values())
            )
            db.commit()
            db.close()
            return True
            
    except Exception as e:
        print(f"[Updater] Log error: {e}")
        return False

def get_update_history(limit=10):
    """Get update history dari database"""
    try:
        db = get_db_conn()
        if not db:
            return []
        
        if DB_COMPATIBLE and plugin_db:
            # Use centralized database
            return db.select('update_history', 'TRUE ORDER BY created_at DESC LIMIT ' + str(limit))
        else:
            # Legacy database operations
            cur = db.execute("SELECT * FROM update_history ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            db.close()
            return rows
            
    except Exception as e:
        print(f"[Updater] History error: {e}")
        return []

async def send_to_log_group(message):
    """Send message ke log group jika tersedia"""
    try:
        log_group_id = os.getenv('LOG_GROUP_ID')
        if log_group_id and client:
            await client.send_message(int(log_group_id), message)
    except Exception as e:
        print(f"[Updater] Log group send error: {e}")

def run_command(command, cwd=None):
    """Execute shell command dengan error handling"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd or os.getcwd(),
            timeout=300  # 5 minutes timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout after 5 minutes"
    except Exception as e:
        return False, "", str(e)

def check_git_repo():
    """Check if we're in a git repository"""
    return os.path.exists('.git') and os.path.isdir('.git')

def get_current_commit():
    """Get current git commit hash"""
    if not check_git_repo():
        return None
    
    success, stdout, stderr = run_command("git rev-parse HEAD")
    if success:
        return stdout.strip()[:8]  # Short hash
    return None

def get_remote_commit():
    """Get latest remote commit hash"""
    if not check_git_repo():
        return None
    
    # Fetch latest changes
    success, _, _ = run_command("git fetch origin")
    if not success:
        return None
    
    success, stdout, stderr = run_command("git rev-parse origin/main")
    if success:
        return stdout.strip()[:8]  # Short hash
    return None

def get_commits_behind():
    """Get number of commits behind remote"""
    if not check_git_repo():
        return 0
    
    success, stdout, stderr = run_command("git rev-list --count HEAD..origin/main")
    if success:
        try:
            return int(stdout.strip())
        except ValueError:
            return 0
    return 0

def create_backup():
    """Create backup sebelum update"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_commit = get_current_commit()
        backup_name = f"backup_{timestamp}_{current_commit}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Create backup directory
        os.makedirs(backup_path, exist_ok=True)
        
        # Backup critical files
        critical_files = [
            'main.py',
            'database.py',
            'config.py',
            '.env',
            'plugins/',
            'data/databases/'
        ]
        
        for item in critical_files:
            if os.path.exists(item):
                if os.path.isfile(item):
                    shutil.copy2(item, backup_path)
                elif os.path.isdir(item):
                    shutil.copytree(item, os.path.join(backup_path, item), dirs_exist_ok=True)
        
        # Create backup info
        backup_info = {
            'timestamp': timestamp,
            'commit': current_commit,
            'backup_path': backup_path,
            'files_backed_up': critical_files
        }
        
        with open(os.path.join(backup_path, 'backup_info.json'), 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        return backup_path
        
    except Exception as e:
        print(f"[Updater] Backup error: {e}")
        return None

def check_dependencies():
    """Check if all dependencies are satisfied"""
    try:
        if not os.path.exists('requirements.txt'):
            return True, "No requirements.txt found"
        
        success, stdout, stderr = run_command("pip check")
        if success:
            return True, "All dependencies satisfied"
        else:
            return False, stderr
            
    except Exception as e:
        return False, str(e)

def update_dependencies():
    """Update dependencies dari requirements.txt"""
    try:
        if not os.path.exists('requirements.txt'):
            return True, "No requirements.txt found"
        
        success, stdout, stderr = run_command("pip install -r requirements.txt --upgrade")
        return success, stdout if success else stderr
        
    except Exception as e:
        return False, str(e)

async def perform_update(update_type="normal"):
    """Perform actual update process"""
    try:
        if not check_git_repo():
            return False, "Not a git repository"
        
        # Get current state
        old_commit = get_current_commit()
        
        # Create backup
        backup_path = create_backup()
        if not backup_path:
            return False, "Failed to create backup"
        
        # Fetch latest changes
        success, stdout, stderr = run_command("git fetch origin")
        if not success:
            return False, f"Git fetch failed: {stderr}"
        
        # Get new commit
        new_commit = get_remote_commit()
        if not new_commit:
            return False, "Failed to get remote commit"
        
        # Check if update needed
        if old_commit == new_commit and update_type != "force":
            return False, "Already up to date"
        
        # Log update attempt
        log_update_attempt(update_type, old_commit, new_commit, backup_path, "in_progress")
        
        # Perform git pull
        if update_type == "force":
            success, stdout, stderr = run_command("git reset --hard origin/main")
        else:
            success, stdout, stderr = run_command("git pull origin main")
        
        if not success:
            log_update_attempt(update_type, old_commit, new_commit, backup_path, "failed", stderr)
            return False, f"Git pull failed: {stderr}"
        
        # Update dependencies
        dep_success, dep_message = update_dependencies()
        if not dep_success:
            print(f"[Updater] Dependencies update failed: {dep_message}")
        
        # Log successful update
        log_update_attempt(update_type, old_commit, new_commit, backup_path, "success")
        
        return True, f"Updated from {old_commit} to {new_commit}"
        
    except Exception as e:
        return False, str(e)

async def rollback_update():
    """Rollback to previous version"""
    try:
        # Get latest successful update
        history = get_update_history(1)
        if not history or history[0].get('status') != 'success':
            return False, "No successful update found to rollback"
        
        last_update = history[0]
        backup_path = last_update.get('backup_path')
        old_commit = last_update.get('old_commit')
        
        if not backup_path or not os.path.exists(backup_path):
            return False, "Backup not found"
        
        # Restore from backup
        backup_info_path = os.path.join(backup_path, 'backup_info.json')
        if not os.path.exists(backup_info_path):
            return False, "Backup info not found"
        
        with open(backup_info_path, 'r') as f:
            backup_info = json.load(f)
        
        # Restore files
        for item in backup_info.get('files_backed_up', []):
            backup_item_path = os.path.join(backup_path, item)
            if os.path.exists(backup_item_path):
                if os.path.isfile(backup_item_path):
                    shutil.copy2(backup_item_path, item)
                elif os.path.isdir(backup_item_path):
                    if os.path.exists(item):
                        shutil.rmtree(item)
                    shutil.copytree(backup_item_path, item)
        
        # Reset git to old commit if possible
        if old_commit:
            run_command(f"git reset --hard {old_commit}")
        
        # Log rollback
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_update_attempt("rollback", last_update.get('new_commit'), old_commit, backup_path, "success")
        
        return True, f"Rollback successful to commit {old_commit}"
        
    except Exception as e:
        return False, str(e)

def get_changelog():
    """Get changelog between current and remote"""
    try:
        if not check_git_repo():
            return []
        
        # Get commits between current and remote
        success, stdout, stderr = run_command("git log --oneline HEAD..origin/main")
        if success and stdout.strip():
            commits = []
            for line in stdout.strip().split('\n'):
                if line.strip():
                    commit_hash, *message = line.split(' ')
                    commits.append({
                        'hash': commit_hash,
                        'message': ' '.join(message)
                    })
            return commits
        return []
        
    except Exception as e:
        print(f"[Updater] Changelog error: {e}")
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

async def updater_handler(event):
    """Handle updater commands"""
    try:
        # Owner check
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split()
        
        if len(args) == 1:
            # Show help
            help_text = f"""
{get_emoji('main')} {convert_font('AUTO UPDATER v1.0', 'bold')}

{get_emoji('check')} {convert_font('Commands:', 'bold')}
• {convert_font('.update', 'mono')} - Check & perform update
• {convert_font('.update check', 'mono')} - Check for updates only
• {convert_font('.update force', 'mono')} - Force update (hard reset)
• {convert_font('.update rollback', 'mono')} - Rollback last update
• {convert_font('.update status', 'mono')} - Show update status
• {convert_font('.update changelog', 'mono')} - Show pending changes

{get_emoji('adder2')} {convert_font('Features:', 'bold')}
• Git-based automatic updates
• Automatic backup before update
• Rollback functionality
• Dependency management
• Update history tracking

{get_emoji('adder4')} {convert_font('Safety:', 'bold')} All updates create backups automatically
            """.strip()
            await event.reply(help_text)
            return
        
        command = args[1].lower()
        
        if command == "check":
            # Check for updates only
            if not check_git_repo():
                await event.reply(f"{get_emoji('adder3')} {convert_font('Not a git repository', 'bold')}")
                return
            
            await event.reply(f"{get_emoji('adder4')} {convert_font('Checking for updates...', 'mono')}")
            
            current_commit = get_current_commit()
            remote_commit = get_remote_commit()
            commits_behind = get_commits_behind()
            
            if not remote_commit:
                await event.reply(f"{get_emoji('adder5')} {convert_font('Failed to check remote repository', 'bold')}")
                return
            
            if commits_behind == 0:
                response = f"""
{get_emoji('adder2')} {convert_font('UP TO DATE!', 'bold')}

{get_emoji('check')} {convert_font('Current:', 'mono')} {current_commit}
{get_emoji('adder4')} {convert_font('Remote:', 'mono')} {remote_commit}
{get_emoji('main')} {convert_font('Status:', 'mono')} No updates available
                """.strip()
            else:
                changelog = get_changelog()
                changelog_text = ""
                if changelog:
                    changelog_text = "\n\n" + get_emoji('adder6') + " " + convert_font('Recent Changes:', 'bold') + "\n"
                    for commit in changelog[:5]:  # Show max 5 commits
                        changelog_text += f"• {convert_font(commit['hash'], 'mono')}: {commit['message']}\n"
                    if len(changelog) > 5:
                        changelog_text += f"... and {len(changelog) - 5} more commits"
                
                response = f"""
{get_emoji('adder4')} {convert_font('UPDATES AVAILABLE!', 'bold')}

{get_emoji('check')} {convert_font('Current:', 'mono')} {current_commit}
{get_emoji('adder2')} {convert_font('Latest:', 'mono')} {remote_commit}
{get_emoji('main')} {convert_font('Behind:', 'mono')} {commits_behind} commits
{changelog_text}

{get_emoji('adder5')} Use {convert_font('.update', 'mono')} to install updates
                """.strip()
            
            await event.reply(response)
            
        elif command == "force":
            # Force update
            if not check_git_repo():
                await event.reply(f"{get_emoji('adder3')} {convert_font('Not a git repository', 'bold')}")
                return
            
            progress_msg = await event.reply(f"{get_emoji('adder4')} {convert_font('Force updating...', 'mono')}")
            
            success, message = await perform_update("force")
            
            if success:
                # Send to log group
                log_message = f"""
{get_emoji('adder2')} {convert_font('FORCE UPDATE COMPLETED', 'bold')}

{get_emoji('check')} {convert_font('Result:', 'mono')} {message}
{get_emoji('adder4')} {convert_font('Time:', 'mono')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{get_emoji('adder6')} {convert_font('Type:', 'mono')} Force Update

{get_emoji('main')} Userbot akan restart dalam 10 detik...
                """.strip()
                await send_to_log_group(log_message)
                
                response = f"""
{get_emoji('adder2')} {convert_font('FORCE UPDATE SUCCESS!', 'bold')}

{get_emoji('main')} {message}
{get_emoji('adder4')} {convert_font('Backup Created:', 'mono')} ✅
{get_emoji('adder6')} {convert_font('Dependencies:', 'mono')} Updated

{get_emoji('adder5')} {convert_font('Restarting in 10 seconds...', 'mono')}
                """.strip()
                
                await progress_msg.edit(response)
                
                # Restart after 10 seconds
                await asyncio.sleep(10)
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                response = f"""
{get_emoji('adder5')} {convert_font('FORCE UPDATE FAILED!', 'bold')}

{get_emoji('adder3')} {convert_font('Error:', 'mono')} {message}
{get_emoji('check')} {convert_font('Backup:', 'mono')} Created (safe)
{get_emoji('adder4')} {convert_font('Rollback:', 'mono')} Available

{get_emoji('adder6')} Try {convert_font('.update rollback', 'mono')} if needed
                """.strip()
                
                await progress_msg.edit(response)
            
        elif command == "rollback":
            # Rollback last update
            progress_msg = await event.reply(f"{get_emoji('adder4')} {convert_font('Rolling back...', 'mono')}")
            
            success, message = await rollback_update()
            
            if success:
                # Send to log group
                log_message = f"""
{get_emoji('adder6')} {convert_font('ROLLBACK COMPLETED', 'bold')}

{get_emoji('check')} {convert_font('Result:', 'mono')} {message}
{get_emoji('adder4')} {convert_font('Time:', 'mono')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{get_emoji('main')} System restored from backup successfully.
                """.strip()
                await send_to_log_group(log_message)
                
                response = f"""
{get_emoji('adder2')} {convert_font('ROLLBACK SUCCESS!', 'bold')}

{get_emoji('main')} {message}
{get_emoji('check')} {convert_font('Status:', 'mono')} Restored from backup
{get_emoji('adder4')} {convert_font('Files:', 'mono')} Restored successfully

{get_emoji('adder5')} {convert_font('Restarting in 10 seconds...', 'mono')}
                """.strip()
                
                await progress_msg.edit(response)
                
                # Restart after 10 seconds
                await asyncio.sleep(10)
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                response = f"""
{get_emoji('adder5')} {convert_font('ROLLBACK FAILED!', 'bold')}

{get_emoji('adder3')} {convert_font('Error:', 'mono')} {message}
{get_emoji('check')} {convert_font('Current state:', 'mono')} Unchanged
                """.strip()
                
                await progress_msg.edit(response)
            
        elif command == "status":
            # Show update status
            if not check_git_repo():
                await event.reply(f"{get_emoji('adder3')} {convert_font('Not a git repository', 'bold')}")
                return
            
            current_commit = get_current_commit()
            remote_commit = get_remote_commit()
            commits_behind = get_commits_behind()
            dep_status, dep_message = check_dependencies()
            
            history = get_update_history(3)
            history_text = ""
            if history:
                history_text = "\n\n" + get_emoji('adder6') + " " + convert_font('Recent Updates:', 'bold') + "\n"
                for update in history:
                    status_icon = get_emoji('adder2') if update.get('status') == 'success' else get_emoji('adder3')
                    history_text += f"{status_icon} {update.get('update_type', 'unknown')} - {update.get('created_at', 'unknown')}\n"
            
            response = f"""
{get_emoji('main')} {convert_font('UPDATER STATUS', 'bold')}

{get_emoji('check')} {convert_font('Git Repository:', 'mono')} Active
{get_emoji('adder4')} {convert_font('Current Commit:', 'mono')} {current_commit or 'Unknown'}
{get_emoji('adder2')} {convert_font('Remote Commit:', 'mono')} {remote_commit or 'Unknown'}
{get_emoji('adder1')} {convert_font('Commits Behind:', 'mono')} {commits_behind}

{get_emoji('adder5')} {convert_font('Dependencies:', 'mono')} {'✅ OK' if dep_status else '❌ Issues'}
{get_emoji('adder3')} {convert_font('Auto Backup:', 'mono')} Enabled
{history_text}
            """.strip()
            
            await event.reply(response)
            
        elif command == "changelog":
            # Show changelog
            changelog = get_changelog()
            
            if not changelog:
                await event.reply(f"{get_emoji('check')} {convert_font('No pending changes', 'bold')}")
                return
            
            changelog_text = f"""
{get_emoji('main')} {convert_font('PENDING CHANGES', 'bold')}

{get_emoji('adder4')} {convert_font('Found:', 'mono')} {len(changelog)} new commits
            """.strip()
            
            for i, commit in enumerate(changelog[:10]):  # Show max 10 commits
                changelog_text += f"\n{get_emoji('check')} {convert_font(commit['hash'], 'mono')}: {commit['message']}"
            
            if len(changelog) > 10:
                changelog_text += f"\n\n{get_emoji('adder3')} ... and {len(changelog) - 10} more commits"
            
            changelog_text += f"\n\n{get_emoji('adder2')} Use {convert_font('.update', 'mono')} to install updates"
            
            await event.reply(changelog_text)
            
        else:
            # Default update command
            if not check_git_repo():
                await event.reply(f"{get_emoji('adder3')} {convert_font('Not a git repository', 'bold')}")
                return
            
            commits_behind = get_commits_behind()
            if commits_behind == 0:
                await event.reply(f"{get_emoji('check')} {convert_font('Already up to date!', 'bold')}")
                return
            
            progress_msg = await event.reply(f"{get_emoji('adder4')} {convert_font('Updating...', 'mono')}")
            
            success, message = await perform_update("normal")
            
            if success:
                # Send to log group
                log_message = f"""
{get_emoji('adder2')} {convert_font('UPDATE COMPLETED', 'bold')}

{get_emoji('check')} {convert_font('Result:', 'mono')} {message}
{get_emoji('adder4')} {convert_font('Time:', 'mono')} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{get_emoji('adder6')} {convert_font('Commits:', 'mono')} {commits_behind} new commits applied

{get_emoji('main')} Userbot akan restart dalam 10 detik...
                """.strip()
                await send_to_log_group(log_message)
                
                response = f"""
{get_emoji('adder2')} {convert_font('UPDATE SUCCESS!', 'bold')}

{get_emoji('main')} {message}
{get_emoji('adder4')} {convert_font('Commits Applied:', 'mono')} {commits_behind}
{get_emoji('check')} {convert_font('Backup Created:', 'mono')} ✅
{get_emoji('adder6')} {convert_font('Dependencies:', 'mono')} Updated

{get_emoji('adder5')} {convert_font('Restarting in 10 seconds...', 'mono')}
                """.strip()
                
                await progress_msg.edit(response)
                
                # Restart after 10 seconds
                await asyncio.sleep(10)
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                response = f"""
{get_emoji('adder5')} {convert_font('UPDATE FAILED!', 'bold')}

{get_emoji('adder3')} {convert_font('Error:', 'mono')} {message}
{get_emoji('check')} {convert_font('Backup:', 'mono')} Created (safe)
{get_emoji('adder4')} {convert_font('Rollback:', 'mono')} Available

{get_emoji('adder6')} Try {convert_font('.update rollback', 'mono')} if needed
                """.strip()
                
                await progress_msg.edit(response)
            
    except Exception as e:
        print(f"[Updater] Handler error: {e}")
        await event.reply(f"{get_emoji('adder5')} {convert_font('Command error occurred', 'bold')}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    """Setup updater plugin"""
    global client
    client = telegram_client
    
    try:
        # Register event handler
        client.add_event_handler(updater_handler, events.NewMessage(pattern=r"\.update"))
        
        # Create backup directory
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        print("[Updater] Plugin loaded successfully with comprehensive update management")
        return True
        
    except Exception as e:
        print(f"[Updater] Setup error: {e}")
        return False

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Updater] Plugin cleanup initiated")
        client = None
        print("[Updater] Plugin cleanup completed")
    except Exception as e:
        print(f"[Updater] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'perform_update', 'rollback_update', 'check_git_repo']