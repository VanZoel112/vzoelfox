#!/usr/bin/env python3
"""
🔄 AUTO UPDATER PLUGIN - Automatic Git Pull & Update System
Fitur: Auto git pull saat restart, update checker, dan version manager
Author: Vzoel Fox's (Enhanced by Morgan)  
Version: 1.0.0 - Auto Update Edition
"""

import asyncio
import subprocess
import json
import os
import time
import requests
from datetime import datetime, timedelta
from telethon import events
import sqlite3
import threading

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "auto_updater", 
    "version": "1.0.0",
    "description": "🔄 Auto update system dengan git pull otomatis saat restart",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".update", ".updatecheck", ".updateauto", ".updatelog", 
        ".updatesetting", ".gitpull", ".gitinfo", ".rollback"
    ],
    "features": [
        "Auto git pull on restart", "Update checker", "Version tracking",
        "Rollback system", "Update notifications", "Git status monitoring"
    ]
}

# ===== CONFIGURATION =====
UPDATE_CONFIG_FILE = "auto_update_config.json"
UPDATE_DB = "auto_update.db"
GIT_REPO_PATH = os.getcwd()
UPDATE_LOG_FILE = "update_log.txt"

# Premium emoji configuration
PREMIUM_EMOJIS = {
    'update': {'id': '5794353925360457382', 'char': '🔄'},
    'check': {'id': '5794407002566300853', 'char': '✅'},
    'git': {'id': '5793913811471700779', 'char': '🌿'},
    'download': {'id': '5321412209992033736', 'char': '📥'},
    'version': {'id': '5793973133559993740', 'char': '📋'},
    'warning': {'id': '5357404860566235955', 'char': '⚠️'}
}

def create_premium_message(emoji_key, text):
    emoji = PREMIUM_EMOJIS.get(emoji_key, {'char': '🔄'})
    return f"<emoji id='{emoji['id']}'>{emoji['char']}</emoji> {text}"

# ===== DATABASE FUNCTIONS =====
def init_update_db():
    """Initialize update database"""
    try:
        conn = sqlite3.connect(UPDATE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_type TEXT NOT NULL,
                old_version TEXT,
                new_version TEXT,
                files_changed INTEGER,
                success BOOLEAN,
                error_message TEXT,
                duration REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS version_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                commit_hash TEXT NOT NULL,
                commit_message TEXT,
                author TEXT,
                files_modified TEXT,
                backup_path TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_settings (
                id INTEGER PRIMARY KEY,
                auto_update_on_restart BOOLEAN DEFAULT 1,
                check_updates_interval INTEGER DEFAULT 3600,
                backup_before_update BOOLEAN DEFAULT 1,
                notify_updates BOOLEAN DEFAULT 1,
                last_check TIMESTAMP,
                update_channel TEXT
            )
        ''')
        
        # Insert default settings if not exists
        cursor.execute('SELECT COUNT(*) FROM update_settings WHERE id = 1')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO update_settings (
                    id, auto_update_on_restart, check_updates_interval, 
                    backup_before_update, notify_updates
                ) VALUES (1, 1, 3600, 1, 1)
            ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Update DB init error: {e}")
        return False

def log_update(update_type, old_version, new_version, files_changed, success, error_message=None, duration=0):
    """Log update activity"""
    try:
        conn = sqlite3.connect(UPDATE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO update_log (
                update_type, old_version, new_version, files_changed, 
                success, error_message, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (update_type, old_version, new_version, files_changed, success, error_message, duration))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Log update error: {e}")
        return False

# ===== GIT FUNCTIONS =====
def run_git_command(command, timeout=30):
    """Run git command safely"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=GIT_REPO_PATH
        )
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timeout', 'output': '', 'returncode': -1}
    except Exception as e:
        return {'success': False, 'error': str(e), 'output': '', 'returncode': -1}

def check_git_status():
    """Check current git status"""
    try:
        # Check if we're in a git repository
        git_check = run_git_command("git rev-parse --git-dir")
        if not git_check['success']:
            return {'status': 'not_git_repo', 'message': 'Not a git repository'}
        
        # Get current branch
        branch_result = run_git_command("git branch --show-current")
        current_branch = branch_result['output'] if branch_result['success'] else 'unknown'
        
        # Get current commit
        commit_result = run_git_command("git rev-parse HEAD")
        current_commit = commit_result['output'][:8] if commit_result['success'] else 'unknown'
        
        # Get remote URL
        remote_result = run_git_command("git config --get remote.origin.url")
        remote_url = remote_result['output'] if remote_result['success'] else 'No remote'
        
        # Check for changes
        status_result = run_git_command("git status --porcelain")
        has_changes = len(status_result['output']) > 0 if status_result['success'] else False
        
        # Check if behind remote
        fetch_result = run_git_command("git fetch origin")
        behind_result = run_git_command(f"git rev-list HEAD..origin/{current_branch} --count")
        commits_behind = int(behind_result['output']) if behind_result['success'] else 0
        
        return {
            'status': 'ok',
            'branch': current_branch,
            'commit': current_commit,
            'remote': remote_url,
            'has_changes': has_changes,
            'commits_behind': commits_behind,
            'needs_update': commits_behind > 0
        }
        
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def perform_git_pull():
    """Perform git pull with proper error handling"""
    start_time = time.time()
    
    try:
        # Get current status
        status = check_git_status()
        if status['status'] != 'ok':
            return {'success': False, 'error': status.get('message', 'Git status check failed')}
        
        old_commit = status['commit']
        
        # Stash changes if any
        if status['has_changes']:
            stash_result = run_git_command("git stash push -m 'Auto-stash before update'")
            if not stash_result['success']:
                return {'success': False, 'error': f'Failed to stash changes: {stash_result["error"]}'}
        
        # Perform git pull
        pull_result = run_git_command("git pull origin main")
        
        if not pull_result['success']:
            return {
                'success': False, 
                'error': f'Git pull failed: {pull_result["error"]}',
                'output': pull_result['output']
            }
        
        # Get new commit
        new_status = check_git_status()
        new_commit = new_status['commit'] if new_status['status'] == 'ok' else 'unknown'
        
        # Check what changed
        if old_commit != new_commit:
            diff_result = run_git_command(f"git diff --name-only {old_commit} {new_commit}")
            changed_files = diff_result['output'].split('\n') if diff_result['success'] else []
            files_count = len([f for f in changed_files if f.strip()])
        else:
            files_count = 0
        
        duration = time.time() - start_time
        
        # Log the update
        log_update('git_pull', old_commit, new_commit, files_count, True, None, duration)
        
        return {
            'success': True,
            'old_commit': old_commit,
            'new_commit': new_commit,
            'files_changed': files_count,
            'duration': duration,
            'output': pull_result['output'],
            'updated': old_commit != new_commit
        }
        
    except Exception as e:
        duration = time.time() - start_time
        log_update('git_pull', '', '', 0, False, str(e), duration)
        return {'success': False, 'error': str(e)}

def create_backup():
    """Create backup before update"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/backup_{timestamp}"
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy important files
        important_files = [
            "main.py", "plugin_loader.py", "client.py",
            "userbot_custom_messages.json", "voice_clone_config.json",
            "auto_update_config.json"
        ]
        
        copied_files = []
        for file in important_files:
            if os.path.exists(file):
                import shutil
                shutil.copy2(file, os.path.join(backup_dir, file))
                copied_files.append(file)
        
        # Copy plugins directory
        if os.path.exists("plugins"):
            import shutil
            shutil.copytree("plugins", os.path.join(backup_dir, "plugins"), dirs_exist_ok=True)
        
        return {
            'success': True,
            'backup_path': backup_dir,
            'files_backed_up': len(copied_files)
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ===== AUTO UPDATE ON STARTUP =====
async def auto_update_on_startup():
    """Perform auto update when bot starts"""
    try:
        # Load settings
        conn = sqlite3.connect(UPDATE_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT auto_update_on_restart, backup_before_update FROM update_settings WHERE id = 1')
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:  # Auto update disabled
            print("🔄 Auto update disabled")
            return
        
        print("🔄 Starting auto update on startup...")
        
        # Check git status first
        status = check_git_status()
        if status['status'] != 'ok':
            print(f"❌ Git status error: {status.get('message', 'Unknown error')}")
            return
        
        if not status['needs_update']:
            print("✅ Already up to date")
            return
        
        print(f"📥 {status['commits_behind']} commits behind, updating...")
        
        # Create backup if enabled
        if result[1]:  # backup_before_update enabled
            backup_result = create_backup()
            if backup_result['success']:
                print(f"💾 Backup created: {backup_result['backup_path']}")
            else:
                print(f"⚠️ Backup failed: {backup_result['error']}")
        
        # Perform git pull
        update_result = perform_git_pull()
        
        if update_result['success']:
            if update_result['updated']:
                print(f"✅ Update successful: {update_result['old_commit']} → {update_result['new_commit']}")
                print(f"📊 Files changed: {update_result['files_changed']}")
                
                # Write update log to file
                with open(UPDATE_LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"\n[{datetime.now()}] AUTO UPDATE SUCCESS\n")
                    f.write(f"Old: {update_result['old_commit']} → New: {update_result['new_commit']}\n")
                    f.write(f"Files changed: {update_result['files_changed']}\n")
                    f.write("-" * 50 + "\n")
            else:
                print("✅ Already up to date")
        else:
            print(f"❌ Update failed: {update_result['error']}")
            
            # Write error log
            with open(UPDATE_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] AUTO UPDATE FAILED\n")
                f.write(f"Error: {update_result['error']}\n")
                f.write("-" * 50 + "\n")
        
    except Exception as e:
        print(f"❌ Auto update error: {e}")

# Schedule auto update on startup
def schedule_startup_update():
    """Schedule auto update to run after bot starts"""
    def delayed_update():
        time.sleep(10)  # Wait 10 seconds for bot to fully start
        asyncio.run(auto_update_on_startup())
    
    thread = threading.Thread(target=delayed_update)
    thread.daemon = True
    thread.start()

# ===== EVENT HANDLERS =====
@client.on(events.NewMessage(pattern=r'^\.update$'))
async def manual_update(event):
    """Manual update command"""
    try:
        msg = await event.respond(create_premium_message('update', '**🔄 Starting manual update...**'))
        
        # Check git status
        await msg.edit(create_premium_message('git', '**📋 Checking git status...**'))
        status = check_git_status()
        
        if status['status'] != 'ok':
            await msg.edit(create_premium_message('warning', f'**Git Error:** {status.get("message", "Unknown error")}'))
            return
        
        if not status['needs_update']:
            await msg.edit(create_premium_message('check', '**✅ Already up to date!**\n\nNo new commits available.'))
            return
        
        # Create backup
        await msg.edit(create_premium_message('download', '**💾 Creating backup...**'))
        backup_result = create_backup()
        
        # Perform update
        await msg.edit(create_premium_message('update', f'**📥 Pulling {status["commits_behind"]} new commits...**'))
        update_result = perform_git_pull()
        
        if update_result['success']:
            if update_result['updated']:
                result_text = f"""**✅ Update Successful!**

**📊 Changes:**
• Old: `{update_result['old_commit']}`
• New: `{update_result['new_commit']}`
• Files changed: {update_result['files_changed']}
• Duration: {update_result['duration']:.2f}s

**💾 Backup:** {'✅ Created' if backup_result['success'] else '❌ Failed'}

**🔄 Restart bot to apply changes**"""
            else:
                result_text = "**✅ Already up to date!**"
        else:
            result_text = f"**❌ Update Failed!**\n\n**Error:** {update_result['error']}"
        
        await msg.edit(create_premium_message('check' if update_result['success'] else 'warning', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Update error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.updatecheck$'))
async def check_updates(event):
    """Check for available updates"""
    try:
        msg = await event.respond(create_premium_message('git', '**📋 Checking for updates...**'))
        
        status = check_git_status()
        
        if status['status'] != 'ok':
            await msg.edit(create_premium_message('warning', f'**Git Error:** {status.get("message", "Unknown error")}'))
            return
        
        # Get commit info
        if status['commits_behind'] > 0:
            # Get commit messages
            log_result = run_git_command(f"git log HEAD..origin/{status['branch']} --oneline -5")
            recent_commits = log_result['output'].split('\n') if log_result['success'] else []
            
            commit_list = []
            for commit in recent_commits[:3]:  # Show max 3 commits
                if commit.strip():
                    commit_list.append(f"• `{commit.strip()}`")
            
            result_text = f"""**📥 Updates Available!**

**📊 Status:**
• Branch: `{status['branch']}`
• Current: `{status['commit']}`
• Commits behind: **{status['commits_behind']}**

**🔄 Recent Changes:**
{chr(10).join(commit_list) if commit_list else '• No commit details available'}

**Commands:**
• `.update` - Update now
• `.updateauto on` - Enable auto update"""
        else:
            result_text = f"""**✅ Up to Date!**

**📊 Status:**
• Branch: `{status['branch']}`
• Current: `{status['commit']}`
• Remote: Connected

**⚡ No updates available**"""
        
        await msg.edit(create_premium_message('check', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Update check error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.updateauto (.+)$'))
async def toggle_auto_update(event):
    """Toggle auto update settings"""
    try:
        action = event.pattern_match.group(1).strip().lower()
        
        conn = sqlite3.connect(UPDATE_DB)
        cursor = conn.cursor()
        
        if action in ['on', 'enable', '1', 'true']:
            cursor.execute('UPDATE update_settings SET auto_update_on_restart = 1 WHERE id = 1')
            status = "enabled"
        elif action in ['off', 'disable', '0', 'false']:
            cursor.execute('UPDATE update_settings SET auto_update_on_restart = 0 WHERE id = 1')
            status = "disabled"
        else:
            await event.respond(create_premium_message('warning', '**Usage:** `.updateauto on/off`'))
            conn.close()
            return
        
        conn.commit()
        conn.close()
        
        await event.respond(create_premium_message('check', f'**Auto update {status}!**\n\nBot will {"" if status == "enabled" else "not "}auto-update on restart.'))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Auto update toggle error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.updatelog$'))
async def show_update_log(event):
    """Show recent update log"""
    try:
        conn = sqlite3.connect(UPDATE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, update_type, old_version, new_version, 
                   files_changed, success, error_message
            FROM update_log 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            await event.respond(create_premium_message('version', '**No update logs found.**'))
            return
        
        log_entries = []
        for log in logs:
            timestamp, update_type, old_ver, new_ver, files, success, error = log
            dt = datetime.fromisoformat(timestamp)
            status = "✅" if success else "❌"
            
            if success:
                log_entries.append(f"{status} **{dt.strftime('%m/%d %H:%M')}** - {update_type}")
                if old_ver and new_ver:
                    log_entries.append(f"   `{old_ver[:8]}` → `{new_ver[:8]}` ({files} files)")
            else:
                log_entries.append(f"{status} **{dt.strftime('%m/%d %H:%M')}** - Failed: {error[:30]}...")
        
        result_text = f"""**📋 Update History**

{chr(10).join(log_entries)}

**Commands:**
• `.update` - Manual update
• `.updatecheck` - Check for updates"""
        
        await event.respond(create_premium_message('version', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Update log error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.gitinfo$'))
async def show_git_info(event):
    """Show detailed git information"""
    try:
        msg = await event.respond(create_premium_message('git', '**📋 Loading git information...**'))
        
        status = check_git_status()
        
        if status['status'] != 'ok':
            await msg.edit(create_premium_message('warning', f'**Git Error:** {status.get("message", "Unknown error")}'))
            return
        
        # Get additional info
        author_result = run_git_command("git log -1 --pretty=format:'%an <%ae>'")
        author = author_result['output'] if author_result['success'] else 'Unknown'
        
        date_result = run_git_command("git log -1 --pretty=format:'%cd' --date=relative")
        last_commit_date = date_result['output'] if date_result['success'] else 'Unknown'
        
        message_result = run_git_command("git log -1 --pretty=format:'%s'")
        last_message = message_result['output'] if message_result['success'] else 'No message'
        
        result_text = f"""**🌿 Git Repository Information**

**📊 Current Status:**
• Branch: `{status['branch']}`
• Commit: `{status['commit']}`
• Behind: {status['commits_behind']} commits
• Has changes: {'Yes' if status['has_changes'] else 'No'}

**📝 Last Commit:**
• Author: {author}
• Date: {last_commit_date}
• Message: "{last_message[:50]}{'...' if len(last_message) > 50 else ''}"

**🌐 Remote:**
• URL: `{status['remote']}`
• Update needed: {'Yes' if status['needs_update'] else 'No'}"""
        
        await msg.edit(create_premium_message('git', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Git info error:** {str(e)}'))

# ===== INITIALIZATION =====
def setup():
    """Plugin setup function"""
    print("🔄 Auto Updater Plugin loaded!")
    
    # Initialize database
    init_update_db()
    
    # Schedule auto update on startup
    schedule_startup_update()
    
    return True

if __name__ == "__main__":
    setup()