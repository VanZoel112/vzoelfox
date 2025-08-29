"""
Database Helper - Centralized database management
File: database.py
Author: Morgan (Vzoel Fox's Assistant)
Version: 1.0.0
Description: Unified SQLite database operations for all plugins
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database management for all plugins"""
    
    def __init__(self, db_dir: str = "data"):
        self.db_dir = os.path.abspath(db_dir)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))  # vzoelfox directory
        os.makedirs(self.db_dir, exist_ok=True)
        self._connections = threading.local()
        
        # Initialize config table on startup
        self._init_config_table()
    
    def _init_config_table(self):
        """Initialize bot configuration table"""
        try:
            # Create config table in vzoel_assistant.db
            config_schema = """
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
            self.create_table('bot_config', config_schema, 'vzoel_assistant')
            
            # Set default configs if not exists
            self._set_default_configs()
            
        except Exception as e:
            logger.error(f"Error initializing config table: {e}")
    
    def _set_default_configs(self):
        """Set default configuration values"""
        default_configs = [
            {
                'config_key': 'owner_id',
                'config_value': '0',
                'config_type': 'integer',
                'description': 'Bot owner user ID'
            },
            {
                'config_key': 'log_channel_id',
                'config_value': '-1002975804142',
                'config_type': 'integer', 
                'description': 'Default logging channel ID'
            },
            {
                'config_key': 'bot_name',
                'config_value': 'VzoelFox Assistant',
                'config_type': 'string',
                'description': 'Bot display name'
            },
            {
                'config_key': 'blacklist_enabled',
                'config_value': 'true',
                'config_type': 'boolean',
                'description': 'Enable blacklist system'
            }
        ]
        
        try:
            for config in default_configs:
                # Check if config already exists
                existing = self.select_one('bot_config', where='config_key = ?', 
                                         where_params=(config['config_key'],), 
                                         db_name='vzoel_assistant')
                if not existing:
                    self.insert('bot_config', config, 'vzoel_assistant')
        except Exception as e:
            logger.error(f"Error setting default configs: {e}")
        
    def get_db_path(self, db_name: str) -> str:
        """Get full path for database file"""
        if not db_name.endswith('.db'):
            db_name += '.db'
            
        # Handle special vzoel databases in base directory
        if db_name in ['vzoel.db', 'vzoelfox.db', 'vzoel_assistant.db']:
            return os.path.join(self.base_dir, db_name)
        
        # Use data directory for other databases
        return os.path.join(self.db_dir, db_name)
    
    @contextmanager
    def get_connection(self, db_name: str = "main"):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            db_path = self.get_db_path(db_name)
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        except Exception as e:
            logger.error(f"Database connection error for {db_name}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = (), db_name: str = "main", 
                     fetch: str = None) -> Union[List[sqlite3.Row], sqlite3.Row, int, None]:
        """Execute SQL query with automatic connection management"""
        try:
            with self.get_connection(db_name) as conn:
                cursor = conn.execute(query, params)
                
                if fetch == "all":
                    return cursor.fetchall()
                elif fetch == "one":
                    return cursor.fetchone()
                elif query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    return cursor.rowcount
                else:
                    conn.commit()
                    return cursor.fetchall()
                    
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return None
    
    def create_table(self, table_name: str, schema: str, db_name: str = "main") -> bool:
        """Create table if not exists"""
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        try:
            result = self.execute_query(query, db_name=db_name)
            logger.info(f"Table {table_name} created/verified in {db_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return False
    
    def insert(self, table: str, data: Dict[str, Any], db_name: str = "main") -> Optional[int]:
        """Insert data into table"""
        if not data:
            return None
            
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            with self.get_connection(db_name) as conn:
                cursor = conn.execute(query, tuple(data.values()))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Insert error for table {table}: {e}")
            return None
    
    def update(self, table: str, data: Dict[str, Any], where: str, 
              where_params: tuple = (), db_name: str = "main") -> int:
        """Update data in table"""
        if not data:
            return 0
            
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params
        
        result = self.execute_query(query, params, db_name)
        return result if result is not None else 0
    
    def select(self, table: str, columns: str = "*", where: str = None, 
              where_params: tuple = (), order_by: str = None, limit: int = None,
              db_name: str = "main") -> List[sqlite3.Row]:
        """Select data from table"""
        query = f"SELECT {columns} FROM {table}"
        
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
            
        result = self.execute_query(query, where_params, db_name, fetch="all")
        return result if result is not None else []
    
    def select_one(self, table: str, columns: str = "*", where: str = None,
                  where_params: tuple = (), db_name: str = "main") -> Optional[sqlite3.Row]:
        """Select single row from table"""
        query = f"SELECT {columns} FROM {table}"
        if where:
            query += f" WHERE {where}"
        query += " LIMIT 1"
        
        result = self.execute_query(query, where_params, db_name, fetch="one")
        return result
    
    def delete(self, table: str, where: str, where_params: tuple = (), 
              db_name: str = "main") -> int:
        """Delete data from table"""
        query = f"DELETE FROM {table} WHERE {where}"
        result = self.execute_query(query, where_params, db_name)
        return result if result is not None else 0
    
    def count(self, table: str, where: str = None, where_params: tuple = (),
             db_name: str = "main") -> int:
        """Count rows in table"""
        query = f"SELECT COUNT(*) FROM {table}"
        if where:
            query += f" WHERE {where}"
            
        result = self.execute_query(query, where_params, db_name, fetch="one")
        return result[0] if result else 0
    
    def table_exists(self, table_name: str, db_name: str = "main") -> bool:
        """Check if table exists"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(query, (table_name,), db_name, fetch="one")
        return result is not None
    
    def get_table_info(self, table_name: str, db_name: str = "main") -> List[sqlite3.Row]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query, db_name=db_name, fetch="all") or []
    
    def backup_database(self, db_name: str = "main", backup_suffix: str = None) -> str:
        """Create database backup"""
        if not backup_suffix:
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        source_path = self.get_db_path(db_name)
        backup_path = self.get_db_path(f"{db_name}_backup_{backup_suffix}")
        
        try:
            with self.get_connection(db_name) as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

# Global instance
db_manager = DatabaseManager()

# Convenience functions for common operations
def get_connection(db_name: str = "main"):
    """Get database connection"""
    return db_manager.get_connection(db_name)

def execute_query(query: str, params: tuple = (), db_name: str = "main", fetch: str = None):
    """Execute SQL query"""
    return db_manager.execute_query(query, params, db_name, fetch)

def create_table(table_name: str, schema: str, db_name: str = "main") -> bool:
    """Create table"""
    return db_manager.create_table(table_name, schema, db_name)

def insert(table: str, data: Dict[str, Any], db_name: str = "main") -> Optional[int]:
    """Insert data"""
    return db_manager.insert(table, data, db_name)

def update(table: str, data: Dict[str, Any], where: str, where_params: tuple = (), db_name: str = "main") -> int:
    """Update data"""
    return db_manager.update(table, data, where, where_params, db_name)

def select(table: str, columns: str = "*", where: str = None, where_params: tuple = (), 
          order_by: str = None, limit: int = None, db_name: str = "main") -> List[sqlite3.Row]:
    """Select data"""
    return db_manager.select(table, columns, where, where_params, order_by, limit, db_name)

def select_one(table: str, columns: str = "*", where: str = None, where_params: tuple = (), 
              db_name: str = "main") -> Optional[sqlite3.Row]:
    """Select single row"""
    return db_manager.select_one(table, columns, where, where_params, db_name)

def delete(table: str, where: str, where_params: tuple = (), db_name: str = "main") -> int:
    """Delete data"""
    return db_manager.delete(table, where, where_params, db_name)

def count(table: str, where: str = None, where_params: tuple = (), db_name: str = "main") -> int:
    """Count rows"""
    return db_manager.count(table, where, where_params, db_name)

# ID Management Utilities
class IDManager:
    """Utilities for managing various ID types"""
    
    @staticmethod
    def extract_user_id(event) -> Optional[int]:
        """Extract user ID from event"""
        try:
            return event.sender_id
        except AttributeError:
            return None
    
    @staticmethod
    def extract_chat_id(event) -> Optional[int]:
        """Extract chat ID from event"""
        try:
            return event.chat_id
        except AttributeError:
            return None
    
    @staticmethod
    def extract_message_id(event) -> Optional[int]:
        """Extract message ID from event"""
        try:
            return event.message.id
        except AttributeError:
            return None
    
    @staticmethod
    def is_valid_id(id_value: Any) -> bool:
        """Check if ID is valid"""
        try:
            return isinstance(id_value, int) and id_value != 0
        except:
            return False

# Global ID manager instance
id_manager = IDManager()

# Configuration Management Functions
class ConfigManager:
    """Manage bot configuration in database"""
    
    @staticmethod
    def get_config(key: str, default: Any = None, config_type: str = None) -> Any:
        """Get configuration value"""
        try:
            result = db_manager.select_one('bot_config', 
                                         where='config_key = ?', 
                                         where_params=(key,),
                                         db_name='vzoel_assistant')
            if result:
                value = result['config_value']
                value_type = result['config_type'] if config_type is None else config_type
                
                # Convert value based on type
                if value_type == 'integer':
                    return int(value)
                elif value_type == 'float':
                    return float(value)
                elif value_type == 'boolean':
                    return value.lower() in ['true', '1', 'yes', 'on']
                else:
                    return value
            return default
        except Exception as e:
            logger.error(f"Error getting config {key}: {e}")
            return default
    
    @staticmethod
    def set_config(key: str, value: Any, config_type: str = 'string', description: str = None) -> bool:
        """Set configuration value"""
        try:
            # Convert value to string for storage
            str_value = str(value)
            
            # Check if config exists
            existing = db_manager.select_one('bot_config', 
                                           where='config_key = ?',
                                           where_params=(key,),
                                           db_name='vzoel_assistant')
            
            if existing:
                # Update existing
                update_data = {
                    'config_value': str_value,
                    'config_type': config_type,
                    'updated_at': 'CURRENT_TIMESTAMP'
                }
                if description:
                    update_data['description'] = description
                    
                result = db_manager.update('bot_config', 
                                         update_data,
                                         'config_key = ?',
                                         (key,),
                                         'vzoel_assistant')
                return result > 0
            else:
                # Insert new
                insert_data = {
                    'config_key': key,
                    'config_value': str_value,
                    'config_type': config_type
                }
                if description:
                    insert_data['description'] = description
                    
                result = db_manager.insert('bot_config', insert_data, 'vzoel_assistant')
                return result is not None
                
        except Exception as e:
            logger.error(f"Error setting config {key}: {e}")
            return False
    
    @staticmethod
    def get_owner_id() -> int:
        """Get bot owner ID"""
        return ConfigManager.get_config('owner_id', 0, 'integer')
    
    @staticmethod
    def set_owner_id(owner_id: int) -> bool:
        """Set bot owner ID"""
        return ConfigManager.set_config('owner_id', owner_id, 'integer', 'Bot owner user ID')
    
    @staticmethod
    def get_log_channel_id() -> int:
        """Get logging channel ID"""
        return ConfigManager.get_config('log_channel_id', -1002975804142, 'integer')
    
    @staticmethod
    def set_log_channel_id(channel_id: int) -> bool:
        """Set logging channel ID"""
        return ConfigManager.set_config('log_channel_id', channel_id, 'integer', 'Default logging channel ID')
    
    @staticmethod
    def get_all_configs() -> List[Dict]:
        """Get all configuration values"""
        try:
            rows = db_manager.select('bot_config', 
                                   order_by='config_key',
                                   db_name='vzoel_assistant')
            return [dict(row) for row in rows] if rows else []
        except Exception as e:
            logger.error(f"Error getting all configs: {e}")
            return []

# Global config manager instance
config_manager = ConfigManager()

# Convenience functions for config management
def get_config(key: str, default: Any = None, config_type: str = None) -> Any:
    """Get configuration value"""
    return config_manager.get_config(key, default, config_type)

def set_config(key: str, value: Any, config_type: str = 'string', description: str = None) -> bool:
    """Set configuration value"""
    return config_manager.set_config(key, value, config_type, description)

def get_owner_id() -> int:
    """Get bot owner ID"""
    return config_manager.get_owner_id()

def set_owner_id(owner_id: int) -> bool:
    """Set bot owner ID"""
    return config_manager.set_owner_id(owner_id)

def get_log_channel_id() -> int:
    """Get logging channel ID"""
    return config_manager.get_log_channel_id()

def set_log_channel_id(channel_id: int) -> bool:
    """Set logging channel ID"""
    return config_manager.set_log_channel_id(channel_id)