#!/usr/bin/env python3
"""
🧹 FILE CLEANER PLUGIN - Repository Cleanup System
Fitur: Cleanup file tidak perlu, manage temporary files, optimize disk space
Author: Vzoel Fox's (Enhanced by Morgan)  
Version: 1.0.0 - File Cleaner Edition
"""

import asyncio
import os
import shutil
import glob
import json
import time
from datetime import datetime, timedelta
from telethon import events
import sqlite3

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "file_cleaner", 
    "version": "1.0.0",
    "description": "🧹 Repository cleanup system untuk hapus file tidak perlu",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".cleanup", ".cleantemp", ".cleanlog", ".cleanbackup", 
        ".diskusage", ".cleanup auto", ".cleansetting"
    ],
    "features": [
        "Auto cleanup temporary files", "Log rotation", "Backup cleanup",
        "Disk usage monitor", "Safe file removal", "Cleanup scheduling"
    ]
}

# ===== CONFIGURATION =====
CLEANUP_CONFIG = {
    # Files to clean (extensions)
    "temp_extensions": [".tmp", ".temp", ".log", ".cache", ".bak", ".old"],
    "backup_extensions": [".backup", ".bkp"],
    "log_extensions": [".log"],
    
    # Directories to clean
    "temp_directories": [
        "temp", "__pycache__", ".pytest_cache", "temp_audio", 
        "downloads", "cache", ".cache", "logs"
    ],
    
    # Files to keep (whitelist)
    "keep_files": [
        "main.py", "plugin_loader.py", "client.py", "requirements.txt",
        "userbot_custom_messages.json", "voice_clone_config.json", 
        "auto_update_config.json", ".env", "README.md"
    ],
    
    # Age limits (in days)
    "temp_file_age": 7,    # Delete temp files older than 7 days
    "log_file_age": 30,    # Delete log files older than 30 days  
    "backup_age": 14,      # Delete backups older than 14 days
    
    # Size limits (in MB)
    "max_log_size": 50,    # Rotate logs larger than 50MB
    "max_temp_size": 100   # Clean temp if total size > 100MB
}

# Premium emoji configuration
PREMIUM_EMOJIS = {
    'clean': {'id': '5794353925360457382', 'char': '🧹'},
    'check': {'id': '5794407002566300853', 'char': '✅'},
    'delete': {'id': '5357404860566235955', 'char': '🗑️'},
    'disk': {'id': '5321412209992033736', 'char': '💾'},
    'warning': {'id': '5793973133559993740', 'char': '⚠️'},
    'folder': {'id': '5793913811471700779', 'char': '📁'}
}

def create_premium_message(emoji_key, text):
    emoji = PREMIUM_EMOJIS.get(emoji_key, {'char': '🧹'})
    return f"<emoji id='{emoji['id']}'>{emoji['char']}</emoji> {text}"

# ===== UTILITY FUNCTIONS =====
def get_file_size(filepath):
    """Get file size in MB"""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

def get_directory_size(directory):
    """Get directory size in MB"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    continue
        return total_size / (1024 * 1024)
    except:
        return 0

def is_file_old(filepath, days):
    """Check if file is older than specified days"""
    try:
        file_time = os.path.getmtime(filepath)
        file_age = time.time() - file_time
        return file_age > (days * 24 * 3600)
    except:
        return False

def safe_delete(path):
    """Safely delete file or directory"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return True
    except Exception as e:
        print(f"Error deleting {path}: {e}")
    return False

# ===== CLEANUP FUNCTIONS =====
def cleanup_temp_files():
    """Clean temporary files"""
    cleaned_files = []
    total_size_freed = 0
    
    # Clean by extension
    for ext in CLEANUP_CONFIG["temp_extensions"]:
        pattern = f"**/*{ext}"
        files = glob.glob(pattern, recursive=True)
        
        for file_path in files:
            if os.path.basename(file_path) not in CLEANUP_CONFIG["keep_files"]:
                if is_file_old(file_path, CLEANUP_CONFIG["temp_file_age"]):
                    size = get_file_size(file_path)
                    if safe_delete(file_path):
                        cleaned_files.append(file_path)
                        total_size_freed += size
    
    # Clean temp directories
    for temp_dir in CLEANUP_CONFIG["temp_directories"]:
        if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
            if is_file_old(temp_dir, CLEANUP_CONFIG["temp_file_age"]):
                size = get_directory_size(temp_dir)
                if safe_delete(temp_dir):
                    cleaned_files.append(temp_dir)
                    total_size_freed += size
    
    return {
        'files_cleaned': len(cleaned_files),
        'size_freed': total_size_freed,
        'files_list': cleaned_files[:10]  # First 10 for display
    }

def cleanup_logs():
    """Clean and rotate log files"""
    cleaned_files = []
    total_size_freed = 0
    
    # Find log files
    log_patterns = ["*.log", "logs/*.log", "**/*.log"]
    
    for pattern in log_patterns:
        log_files = glob.glob(pattern, recursive=True)
        
        for log_file in log_files:
            file_size = get_file_size(log_file)
            
            # Delete old logs
            if is_file_old(log_file, CLEANUP_CONFIG["log_file_age"]):
                if safe_delete(log_file):
                    cleaned_files.append(f"Deleted: {log_file}")
                    total_size_freed += file_size
            
            # Rotate large logs
            elif file_size > CLEANUP_CONFIG["max_log_size"]:
                try:
                    # Create rotated filename
                    base_name = os.path.splitext(log_file)[0]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    rotated_name = f"{base_name}_{timestamp}.log.old"
                    
                    # Move current log to rotated name
                    shutil.move(log_file, rotated_name)
                    
                    # Create new empty log file
                    open(log_file, 'a').close()
                    
                    cleaned_files.append(f"Rotated: {log_file}")
                    
                except Exception as e:
                    print(f"Error rotating {log_file}: {e}")
    
    return {
        'files_processed': len(cleaned_files),
        'size_freed': total_size_freed,
        'actions': cleaned_files[:10]
    }

def cleanup_backups():
    """Clean old backup files"""
    cleaned_files = []
    total_size_freed = 0
    
    # Find backup directories
    backup_dirs = ["backups", "voice_clone_backups", "message_backups"]
    
    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if is_file_old(file_path, CLEANUP_CONFIG["backup_age"]):
                        size = get_file_size(file_path)
                        if safe_delete(file_path):
                            cleaned_files.append(file_path)
                            total_size_freed += size
    
    # Clean backup files by extension
    for ext in CLEANUP_CONFIG["backup_extensions"]:
        pattern = f"**/*{ext}"
        files = glob.glob(pattern, recursive=True)
        
        for file_path in files:
            if is_file_old(file_path, CLEANUP_CONFIG["backup_age"]):
                size = get_file_size(file_path)
                if safe_delete(file_path):
                    cleaned_files.append(file_path)
                    total_size_freed += size
    
    return {
        'files_cleaned': len(cleaned_files),
        'size_freed': total_size_freed,
        'files_list': cleaned_files[:10]
    }

def get_disk_usage():
    """Get disk usage information"""
    try:
        cwd = os.getcwd()
        
        # Get disk usage
        total, used, free = shutil.disk_usage(cwd)
        
        # Convert to GB
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)
        usage_percent = (used / total) * 100
        
        # Get repo size
        repo_size = get_directory_size(".")
        
        # Count files by type
        file_counts = {}
        total_files = 0
        
        for root, dirs, files in os.walk("."):
            for file in files:
                total_files += 1
                ext = os.path.splitext(file)[1] or "no_ext"
                file_counts[ext] = file_counts.get(ext, 0) + 1
        
        return {
            'disk': {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'usage_percent': round(usage_percent, 2)
            },
            'repo': {
                'size_mb': round(repo_size, 2),
                'total_files': total_files,
                'file_types': dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        }
        
    except Exception as e:
        return {'error': str(e)}

# ===== EVENT HANDLERS =====
@client.on(events.NewMessage(pattern=r'^\.cleanup$'))
async def full_cleanup(event):
    """Perform full repository cleanup"""
    try:
        msg = await event.respond(create_premium_message('clean', '**🧹 Starting full cleanup...**'))
        
        # Step 1: Cleanup temp files
        await msg.edit(create_premium_message('clean', '**🧹 Cleaning temporary files...**'))
        temp_result = cleanup_temp_files()
        
        # Step 2: Cleanup logs
        await msg.edit(create_premium_message('clean', '**📄 Processing log files...**'))
        log_result = cleanup_logs()
        
        # Step 3: Cleanup backups
        await msg.edit(create_premium_message('clean', '**💾 Cleaning old backups...**'))
        backup_result = cleanup_backups()
        
        # Calculate totals
        total_files = temp_result['files_cleaned'] + log_result['files_processed'] + backup_result['files_cleaned']
        total_size = temp_result['size_freed'] + log_result['size_freed'] + backup_result['size_freed']
        
        # Get disk usage
        await msg.edit(create_premium_message('disk', '**💾 Calculating disk usage...**'))
        disk_info = get_disk_usage()
        
        result_text = f"""**✅ Cleanup Complete!**

**📊 Files Processed:**
• Temp files: {temp_result['files_cleaned']}
• Log files: {log_result['files_processed']}
• Backups: {backup_result['files_cleaned']}
• **Total: {total_files} files**

**💾 Space Freed:** {total_size:.2f} MB

**📈 Disk Status:**
• Repository: {disk_info['repo']['size_mb']:.1f} MB
• Disk usage: {disk_info['disk']['usage_percent']:.1f}%
• Free space: {disk_info['disk']['free_gb']:.1f} GB

**🔧 Next Steps:**
• `.diskusage` - Detailed disk info
• `.cleanup auto` - Enable auto cleanup"""
        
        await msg.edit(create_premium_message('check', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Cleanup error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.cleantemp$'))
async def clean_temp_only(event):
    """Clean only temporary files"""
    try:
        msg = await event.respond(create_premium_message('clean', '**🧹 Cleaning temporary files...**'))
        
        result = cleanup_temp_files()
        
        if result['files_cleaned'] > 0:
            files_preview = "\n".join(f"• {os.path.basename(f)}" for f in result['files_list'])
            
            result_text = f"""**🗑️ Temp Cleanup Complete!**

**📊 Results:**
• Files cleaned: {result['files_cleaned']}
• Space freed: {result['size_freed']:.2f} MB

**🗂️ Cleaned files (preview):**
{files_preview}
{'...' if result['files_cleaned'] > 10 else ''}"""
        else:
            result_text = "**✅ No temporary files to clean!**\n\nRepository is already clean."
        
        await msg.edit(create_premium_message('check', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Temp cleanup error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.diskusage$'))
async def show_disk_usage(event):
    """Show detailed disk usage information"""
    try:
        msg = await event.respond(create_premium_message('disk', '**📊 Analyzing disk usage...**'))
        
        disk_info = get_disk_usage()
        
        if 'error' in disk_info:
            await msg.edit(create_premium_message('warning', f'**Disk analysis error:** {disk_info["error"]}'))
            return
        
        # Format file types
        file_types = []
        for ext, count in list(disk_info['repo']['file_types'].items())[:8]:
            file_types.append(f"• {ext if ext != 'no_ext' else 'No extension'}: {count}")
        
        result_text = f"""**💾 Disk Usage Report**

**🖥️ System Disk:**
• Total: {disk_info['disk']['total_gb']} GB
• Used: {disk_info['disk']['used_gb']} GB ({disk_info['disk']['usage_percent']}%)
• Free: {disk_info['disk']['free_gb']} GB

**📁 Repository:**
• Size: {disk_info['repo']['size_mb']} MB
• Total files: {disk_info['repo']['total_files']}

**📋 File Types:**
{chr(10).join(file_types)}

**🧹 Cleanup Commands:**
• `.cleanup` - Full cleanup
• `.cleantemp` - Clean temp files only
• `.cleanlog` - Clean log files only"""
        
        await msg.edit(create_premium_message('disk', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Disk usage error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.cleanlog$'))
async def clean_logs_only(event):
    """Clean and rotate log files only"""
    try:
        msg = await event.respond(create_premium_message('clean', '**📄 Processing log files...**'))
        
        result = cleanup_logs()
        
        if result['files_processed'] > 0:
            actions_preview = "\n".join(f"• {action}" for action in result['actions'])
            
            result_text = f"""**📄 Log Cleanup Complete!**

**📊 Results:**
• Files processed: {result['files_processed']}
• Space freed: {result['size_freed']:.2f} MB

**🔧 Actions taken:**
{actions_preview}
{'...' if result['files_processed'] > 10 else ''}"""
        else:
            result_text = "**✅ No log files to process!**\n\nAll logs are current and within size limits."
        
        await msg.edit(create_premium_message('check', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Log cleanup error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.cleanup auto$'))
async def setup_auto_cleanup(event):
    """Setup automatic cleanup (placeholder for future implementation)"""
    try:
        result_text = f"""**🤖 Auto Cleanup Setup**

**⚙️ Auto Cleanup Features:**
• Scheduled temp file cleanup
• Automatic log rotation
• Background disk monitoring
• Smart file aging

**🔧 Configuration:**
• Temp files: Clean after {CLEANUP_CONFIG['temp_file_age']} days
• Log files: Clean after {CLEANUP_CONFIG['log_file_age']} days  
• Backups: Clean after {CLEANUP_CONFIG['backup_age']} days
• Log rotation: At {CLEANUP_CONFIG['max_log_size']} MB

**📝 Status:** Manual cleanup available
**🔮 Coming Soon:** Automated scheduling

**💡 For now, use:**
• `.cleanup` - Manual full cleanup
• `.cleantemp` - Quick temp cleanup"""
        
        await event.respond(create_premium_message('check', result_text))
        
    except Exception as e:
        await event.respond(create_premium_message('warning', f'**Auto cleanup error:** {str(e)}'))

# ===== INITIALIZATION =====
def setup():
    """Plugin setup function"""
    print("🧹 File Cleaner Plugin loaded!")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    return True

if __name__ == "__main__":
    setup()