#!/usr/bin/env python3
"""
Data Folder Initialization
Handles data storage, file management, and database operations
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ============= DATA DIRECTORY SETUP =============

# Get data directory path
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(DATA_DIR)

# Data file paths
CUSTOM_WORDS_FILE = os.path.join(DATA_DIR, "custom_words.json")
USER_DATA_FILE = os.path.join(DATA_DIR, "user_data.json") 
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
DATABASE_FILE = os.path.join(DATA_DIR, "userbot.db")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
TEMP_DIR = os.path.join(DATA_DIR, "temp")
DOWNLOADS_DIR = os.path.join(DATA_DIR, "downloads")

# ============= DATA MANAGER CLASS =============

class DataManager:
    """Centralized data management system"""
    
    def __init__(self):
        self.ensure_directories()
        self.initialize_files()
    
    def ensure_directories(self):
        """Create necessary directories"""
        directories = [DATA_DIR, LOGS_DIR, TEMP_DIR, DOWNLOADS_DIR]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o700)  # Secure permissions
                logger.info(f"📁 Created directory: {directory}")
    
    def initialize_files(self):
        """Initialize default data files"""
        self._init_custom_words()
        self._init_settings()
        self._init_user_data()
        self._init_database()
    
    def _init_custom_words(self):
        """Initialize custom words file"""
        if not os.path.exists(CUSTOM_WORDS_FILE):
            default_words = {
                "hello": ["hai bos", "halo gan", "selamat datang", "apa kabar"],
                "hi": ["hai", "halo", "hey", "woy"],
                "good morning": ["selamat pagi", "pagi bos", "morning gan"],
                "good night": ["selamat malam", "malam bos", "oyasumi"],
                "thanks": ["makasih", "terima kasih", "thx gan", "thanks bro"],
                "sorry": ["maaf", "sorry gan", "my bad", "sori"],
                "yes": ["iya", "yep", "betul", "bener"],
                "no": ["tidak", "nope", "engga", "ga"],
                "info": ["informasi", "kabar", "update", "berita"],
                "update": ["kabar terbaru", "info terkini", "update-an", "berita baru"],
                "group": ["grup", "gc", "grub", "komunitas"],
                "admin": ["admin", "mimin", "pengelola", "moderator"],
                "cool": ["keren", "mantap", "bagus", "oke"],
                "nice": ["bagus", "keren", "mantap", "oke banget"],
                "awesome": ["keren banget", "mantap jiwa", "luar biasa", "incredible"],
                "please": ["tolong", "mohon", "please", "minta"],
                "now": ["sekarang", "saat ini", "skrg", "now"],
                "today": ["hari ini", "today", "skrg", "saat ini"],
                "tomorrow": ["besok", "tomorrow", "esok hari"],
                "join": ["gabung", "ikut", "masuk", "join"],
                "leave": ["keluar", "pergi", "cabut", "leave"],
                "help": ["bantuan", "tolong", "help", "bantu"],
                "check": ["cek", "lihat", "periksa", "check"],
                "free": ["gratis", "cuma-cuma", "bebas biaya", "tanpa bayar"],
                "money": ["duit", "uang", "cuan", "recehan"],
                "business": ["bisnis", "usaha", "dagang", "kerja"],
                "opportunity": ["kesempatan", "peluang", "chance", "momentum"],
                "success": ["sukses", "berhasil", "jadi", "tembus"],
                "easy": ["gampang", "mudah", "simple", "santai"],
                "fast": ["cepet", "kilat", "express", "langsung"],
                "special": ["spesial", "khusus", "istimewa", "eksklusif"],
                "limited": ["terbatas", "limited", "langka", "sedikit"],
                "discount": ["diskon", "potongan harga", "murah", "hemat"],
                "promo": ["promo", "penawaran", "diskon", "sale"]
            }
            
            self.save_json(CUSTOM_WORDS_FILE, default_words)
            logger.info(f"✅ Initialized custom words with {len(default_words)} entries")
    
    def _init_settings(self):
        """Initialize settings file"""
        if not os.path.exists(SETTINGS_FILE):
            default_settings = {
                "version": "1.0.0",
                "initialized_at": datetime.now().isoformat(),
                "gcast": {
                    "delay_min": 2,
                    "delay_max": 5,
                    "batch_size": 10,
                    "batch_delay": 30,
                    "replacement_intensity": 0.8,
                    "blacklisted_chats": []
                },
                "word_replacer": {
                    "enabled": True,
                    "case_sensitive": False,
                    "max_replacements_per_word": 10
                },
                "logging": {
                    "max_log_size": 10485760,  # 10MB
                    "max_log_files": 5,
                    "cleanup_interval": 86400  # 24 hours
                },
                "security": {
                    "file_permissions": "600",
                    "backup_encryption": False,
                    "audit_commands": True
                }
            }
            
            self.save_json(SETTINGS_FILE, default_settings)
            logger.info("✅ Initialized default settings")
    
    def _init_user_data(self):
        """Initialize user data file"""
        if not os.path.exists(USER_DATA_FILE):
            default_user_data = {
                "statistics": {
                    "commands_used": 0,
                    "gcast_sent": 0,
                    "words_replaced": 0,
                    "uptime_total": 0,
                    "last_restart": None
                },
                "preferences": {
                    "timezone": "Asia/Jakarta",
                    "date_format": "%Y-%m-%d %H:%M:%S",
                    "notification_enabled": True
                },
                "cache": {
                    "last_chat_list": [],
                    "last_word_sync": None,
                    "performance_metrics": {}
                }
            }
            
            self.save_json(USER_DATA_FILE, default_user_data)
            logger.info("✅ Initialized user data")
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Create tables
            cursor.executescript('''
                -- Command usage log
                CREATE TABLE IF NOT EXISTS command_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    username TEXT,
                    command TEXT,
                    chat_id INTEGER,
                    chat_title TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                );
                
                -- Gcast history
                CREATE TABLE IF NOT EXISTS gcast_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message TEXT,
                    target_type TEXT,
                    total_chats INTEGER,
                    sent_count INTEGER,
                    failed_count INTEGER,
                    duration_seconds INTEGER,
                    word_replacements INTEGER
                );
                
                -- Word replacement stats
                CREATE TABLE IF NOT EXISTS word_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    word TEXT,
                    replacement TEXT,
                    usage_count INTEGER DEFAULT 0,
                    context TEXT DEFAULT 'general'
                );
                
                -- Chat blacklist
                CREATE TABLE IF NOT EXISTS chat_blacklist (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    reason TEXT,
                    blacklisted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    blacklisted_by INTEGER
                );
                
                -- Performance metrics
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT,
                    metric_value REAL,
                    details TEXT
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_command_logs_timestamp ON command_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_command_logs_user ON command_logs(user_id);
                CREATE INDEX IF NOT EXISTS idx_gcast_timestamp ON gcast_history(timestamp);
                CREATE INDEX IF NOT EXISTS idx_word_stats_date ON word_stats(date);
                CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp);
            ''')
            
            conn.commit()
            conn.close()
            
            # Set secure permissions for database
            os.chmod(DATABASE_FILE, 0o600)
            logger.info("✅ Initialized SQLite database")
            
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
    
    # ============= JSON FILE OPERATIONS =============
    
    def load_json(self, file_path: str, default: Any = None) -> Any:
        """Load data from JSON file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            return default
    
    def save_json(self, file_path: str, data: Any) -> bool:
        """Save data to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Set secure permissions
            os.chmod(file_path, 0o600)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False
    
    # ============= SETTINGS MANAGEMENT =============
    
    def get_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.load_json(SETTINGS_FILE, {})
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get specific setting"""
        settings = self.get_settings()
        keys = key.split('.')
        
        current = settings
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set specific setting"""
        settings = self.get_settings()
        keys = key.split('.')
        
        current = settings
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        return self.save_json(SETTINGS_FILE, settings)
    
    # ============= DATABASE OPERATIONS =============
    
    def execute_db(self, query: str, params: tuple = (), fetch: bool = False):
        """Execute database query"""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
                conn.close()
                return result
            else:
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Database error: {e}")
            return None
    
    def log_command(self, user_id: int, username: str, command: str, 
                   chat_id: int, chat_title: str, success: bool = True, 
                   error: str = None):
        """Log command usage"""
        self.execute_db('''
            INSERT INTO command_logs 
            (user_id, username, command, chat_id, chat_title, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, command, chat_id, chat_title, success, error))
    
    def log_gcast(self, message: str, target_type: str, total: int, 
                 sent: int, failed: int, duration: int, replacements: int):
        """Log gcast activity"""
        self.execute_db('''
            INSERT INTO gcast_history 
            (message, target_type, total_chats, sent_count, failed_count, duration_seconds, word_replacements)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (message[:100], target_type, total, sent, failed, duration, replacements))
    
    # ============= CLEANUP & MAINTENANCE =============
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(TEMP_DIR):
                for file in os.listdir(TEMP_DIR):
                    file_path = os.path.join(TEMP_DIR, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                logger.info("🧹 Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
    
    def cleanup_old_logs(self, days: int = 7):
        """Clean up old database logs"""
        try:
            self.execute_db('''
                DELETE FROM command_logs 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            self.execute_db('''
                DELETE FROM gcast_history 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            
            logger.info(f"🧹 Cleaned up logs older than {days} days")
        except Exception as e:
            logger.error(f"Error cleaning old logs: {e}")
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Get data directory statistics"""
        try:
            stats = {
                "directories": {
                    "data": os.path.exists(DATA_DIR),
                    "logs": os.path.exists(LOGS_DIR),
                    "temp": os.path.exists(TEMP_DIR),
                    "downloads": os.path.exists(DOWNLOADS_DIR)
                },
                "files": {
                    "custom_words": os.path.exists(CUSTOM_WORDS_FILE),
                    "settings": os.path.exists(SETTINGS_FILE),
                    "user_data": os.path.exists(USER_DATA_FILE),
                    "database": os.path.exists(DATABASE_FILE)
                },
                "sizes": {}
            }
            
            # Get file sizes
            files_to_check = [
                ("custom_words", CUSTOM_WORDS_FILE),
                ("settings", SETTINGS_FILE),
                ("user_data", USER_DATA_FILE),
                ("database", DATABASE_FILE)
            ]
            
            for name, path in files_to_check:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    stats["sizes"][name] = {
                        "bytes": size,
                        "human": self._format_size(size)
                    }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting data stats: {e}")
            return {}
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

# ============= GLOBAL INSTANCE =============

# Create global data manager instance
data_manager = DataManager()

# ============= CONVENIENCE FUNCTIONS =============

def get_custom_words() -> Dict[str, Any]:
    """Get custom words dictionary"""
    return data_manager.load_json(CUSTOM_WORDS_FILE, {})

def save_custom_words(words: Dict[str, Any]) -> bool:
    """Save custom words dictionary"""
    return data_manager.save_json(CUSTOM_WORDS_FILE, words)

def get_settings() -> Dict[str, Any]:
    """Get all settings"""
    return data_manager.get_settings()

def get_setting(key: str, default: Any = None) -> Any:
    """Get specific setting"""
    return data_manager.get_setting(key, default)

def set_setting(key: str, value: Any) -> bool:
    """Set specific setting"""
    return data_manager.set_setting(key, value)

# ============= EXPORTS =============

__all__ = [
    'DataManager',
    'data_manager',
    'get_custom_words',
    'save_custom_words', 
    'get_settings',
    'get_setting',
    'set_setting',
    'DATA_DIR',
    'CUSTOM_WORDS_FILE',
    'SETTINGS_FILE',
    'USER_DATA_FILE',
    'DATABASE_FILE',
    'LOGS_DIR',
    'TEMP_DIR',
    'DOWNLOADS_DIR'
]

# ============= INITIALIZATION MESSAGE =============

logger.info("📁 Data management system initialized")
logger.info(f"📍 Data directory: {DATA_DIR}")
logger.info(f"🔧 Settings file: {os.path.basename(SETTINGS_FILE)}")
logger.info(f"💾 Database: {os.path.basename(DATABASE_FILE)}")
logger.info(f"📝 Custom words: {len(get_custom_words())} entries")
