#!/usr/bin/env python3
"""
Enhanced Utilities for Vzoel Assistant
Backup system, plugin generators, and helper functions
"""

import os
import sys
import json
import shutil
import zipfile
import hashlib
import asyncio
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ============= BACKUP SYSTEM =============

class BackupManager:
    """Advanced backup management system"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Critical files to backup
        self.critical_files = [
            '.env',
            'main.py',
            'config.py', 
            '__init__.py',
            '*.session*',
            'requirements.txt',
            'vzoel_assistant.log',
            'command_stats.json'
        ]
        
        # Directories to backup
        self.backup_dirs = [
            'plugins/',
            'downloads/'
        ]
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create complete backup of userbot"""
        if not backup_name:
            backup_name = f"vzoel_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Backup critical files
                for pattern in self.critical_files:
                    if '*' in pattern:
                        import glob
                        for file in glob.glob(pattern):
                            if os.path.isfile(file):
                                backup_zip.write(file)
                                logger.debug(f"Backed up file: {file}")
                    else:
                        if os.path.isfile(pattern):
                            backup_zip.write(pattern)
                            logger.debug(f"Backed up file: {pattern}")
                
                # Backup directories
                for dir_path in self.backup_dirs:
                    if os.path.isdir(dir_path):
                        for root, dirs, files in os.walk(dir_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                backup_zip.write(file_path)
                                logger.debug(f"Backed up: {file_path}")
                
                # Create backup manifest
                manifest = {
                    'backup_name': backup_name,
                    'created_at': datetime.now().isoformat(),
                    'version': '2.1.0',
                    'files_count': len(backup_zip.namelist()),
                    'backup_size': 0  # Will be updated after creation
                }
                
                backup_zip.writestr('backup_manifest.json', json.dumps(manifest, indent=2))
            
            # Update manifest with file size
            backup_size = backup_path.stat().st_size
            with zipfile.ZipFile(backup_path, 'a') as backup_zip:
                # Read existing manifest
                manifest_data = backup_zip.read('backup_manifest.json').decode()
                manifest = json.loads(manifest_data)
                manifest['backup_size'] = backup_size
                
                # Remove old manifest and add updated one
                backup_zip.writestr('backup_manifest.json', json.dumps(manifest, indent=2))
            
            logger.info(f"Backup created: {backup_path} ({backup_size / 1024 / 1024:.2f}MB)")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return ""
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore from backup file"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            # Create restore directory
            restore_dir = Path(f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            restore_dir.mkdir(exist_ok=True)
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                backup_zip.extractall(restore_dir)
                
                # Read manifest
                try:
                    manifest_data = backup_zip.read('backup_manifest.json').decode()
                    manifest = json.loads(manifest_data)
                    logger.info(f"Restoring backup: {manifest['backup_name']} from {manifest['created_at']}")
                except Exception:
                    logger.warning("No manifest found in backup")
            
            logger.info(f"Backup restored to: {restore_dir}")
            logger.info("Please manually move files from restore directory to replace current files")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        
        try:
            for backup_file in self.backup_dir.glob("*.zip"):
                try:
                    stat = backup_file.stat()
                    backup_info = {
                        'name': backup_file.name,
                        'path': str(backup_file),
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_ctime)).days
                    }
                    
                    # Try to read manifest
                    try:
                        with zipfile.ZipFile(backup_file, 'r') as backup_zip:
                            if 'backup_manifest.json' in backup_zip.namelist():
                                manifest_data = backup_zip.read('backup_manifest.json').decode()
                                manifest = json.loads(manifest_data)
                                backup_info.update(manifest)
                    except Exception:
                        pass
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logger.error(f"Error reading backup {backup_file}: {e}")
            
            return sorted(backups, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """Clean up old backups"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for backup in backups[keep_count:]:  # Keep at least keep_count backups
            backup_date = datetime.fromisoformat(backup['created_at'])
            if backup_date < cutoff_date:
                try:
                    Path(backup['path']).unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup['name']}")
                except Exception as e:
                    logger.error(f"Error deleting backup {backup['name']}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups")

# ============= PLUGIN GENERATOR =============

class PluginGenerator:
    """Generate plugin templates and boilerplate code"""
    
    def __init__(self):
        self.plugins_dir = Path("plugins")
        self.templates = {
            'basic': self._basic_template,
            'advanced': self._advanced_template,
            'utility': self._utility_template,
            'fun': self._fun_template,
            'admin': self._admin_template
        }
    
    def _basic_template(self, plugin_name: str, description: str) -> str:
        """Basic plugin template"""
        return f'''#!/usr/bin/env python3
"""
{plugin_name.title()} Plugin for Enhanced Vzoel Assistant
{description}
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
from monitoring import monitor_performance
import asyncio

@events.register(events.NewMessage(pattern=rf'^{{COMMAND_PREFIX}}{plugin_name.lower()}$', outgoing=True))
@owner_only
@log_command_usage
@monitor_performance
async def {plugin_name.lower()}_handler(event):
    """{description}"""
    try:
        await event.edit(f"✅ **{plugin_name.title()}** plugin is working!")
        
        # Add your plugin logic here
        
    except Exception as e:
        await event.edit(f"❌ **Error in {plugin_name.lower()}:** `{{str(e)}}`")

# Plugin information for the management system
PLUGIN_INFO = {{
    'name': '{plugin_name.title()}',
    'description': '{description}',
    'version': '1.0.0',
    'author': 'Vzoel Assistant',
    'category': 'Basic',
    'commands': [
        f'{{COMMAND_PREFIX}}{plugin_name.lower()} - {description}'
    ]
}}

def get_plugin_info():
    return PLUGIN_INFO
'''
    
    def _advanced_template(self, plugin_name: str, description: str) -> str:
        """Advanced plugin template with multiple commands"""
        return f'''#!/usr/bin/env python3
"""
{plugin_name.title()} Plugin for Enhanced Vzoel Assistant
{description}
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
from monitoring import monitor_performance
import asyncio
import logging

logger = logging.getLogger(__name__)

class {plugin_name.title()}Handler:
    """Handler class for {plugin_name.lower()} operations"""
    
    def __init__(self):
        self.active = True
        self.stats = {{'usage_count': 0, 'last_used': None}}
    
    async def process_command(self, event, action: str = None):
        """Process {plugin_name.lower()} command"""
        try:
            self.stats['usage_count'] += 1
            self.stats['last_used'] = asyncio.get_event_loop().time()
            
            if action == 'status':
                await self._show_status(event)
            elif action == 'config':
                await self._show_config(event)
            else:
                await self._default_action(event)
                
        except Exception as e:
            logger.error(f"{plugin_name.lower()} error: {{e}}")
            await event.edit(f"❌ **{plugin_name.title()} Error:** `{{str(e)}}`")
    
    async def _default_action(self, event):
        """Default action"""
        await event.edit(f"🔥 **{plugin_name.title()}** is active!\\n💎 Use `{{COMMAND_PREFIX}}{plugin_name.lower()} status` for details")
    
    async def _show_status(self, event):
        """Show plugin status"""
        status_text = f"""
📊 **{plugin_name.title()} Status**

🔧 **Active:** `{{self.active}}`
📈 **Usage Count:** `{{self.stats['usage_count']}}`
⏰ **Last Used:** `{{self.stats['last_used'] or 'Never'}}`

💎 **Vzoel Assistant** - {plugin_name.title()} Module
        """.strip()
        
        await event.edit(status_text)
    
    async def _show_config(self, event):
        """Show plugin configuration"""
        config_text = f"""
⚙️ **{plugin_name.title()} Configuration**

📋 **Settings:**
├── Active: `{{self.active}}`
├── Version: `1.0.0`
└── Category: `Advanced`

🔧 **Available Commands:**
├── `{{COMMAND_PREFIX}}{plugin_name.lower()}` - Main command
├── `{{COMMAND_PREFIX}}{plugin_name.lower()} status` - Show status
└── `{{COMMAND_PREFIX}}{plugin_name.lower()} config` - Show config

💎 **Vzoel Fox's Enhanced Plugin System**
        '''
