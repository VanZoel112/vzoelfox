#!/usr/bin/env python3
"""
Database Compatibility Helper for VZoel Fox Plugins
File: plugins/database_helper.py
Author: Morgan (Enhanced by Claude)
Description: Centralized database compatibility layer untuk semua plugins
"""

import os
import sys
import sqlite3
import logging
from typing import Any, Dict, List, Optional, Union

# Add parent directory to path untuk import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import DatabaseManager
    CENTRALIZED_DB_AVAILABLE = True
except ImportError:
    CENTRALIZED_DB_AVAILABLE = False

logger = logging.getLogger(__name__)

class PluginDatabaseManager:
    """
    Database compatibility layer untuk plugins
    Provides seamless migration dari individual databases ke centralized system
    """
    
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.db_manager = None
        self.legacy_db_path = f"plugins/{plugin_name}.db"
        
        # Initialize centralized database if available
        if CENTRALIZED_DB_AVAILABLE:
            try:
                self.db_manager = DatabaseManager()
                logger.info(f"✅ {plugin_name}: Using centralized database")
            except Exception as e:
                logger.warning(f"⚠️ {plugin_name}: Centralized DB failed, using legacy: {e}")
                self.db_manager = None
        
        # Migration check
        self._check_migration_needed()
    
    def _check_migration_needed(self):
        """Check if legacy database needs migration to centralized system"""
        if os.path.exists(self.legacy_db_path) and self.db_manager:
            logger.info(f"📦 {self.plugin_name}: Legacy database detected, migration available")
    
    def create_table(self, table_name: str, schema: str, auto_migrate: bool = True):
        """Create table dengan compatibility untuk legacy dan centralized"""
        try:
            if self.db_manager:
                # Use centralized database
                return self.db_manager.create_table(table_name, schema, self.plugin_name)
            else:
                # Fallback to legacy individual database
                return self._create_table_legacy(table_name, schema)
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Table creation failed: {e}")
            return False
    
    def _create_table_legacy(self, table_name: str, schema: str):
        """Legacy table creation for backward compatibility"""
        try:
            os.makedirs("plugins", exist_ok=True)
            conn = sqlite3.connect(self.legacy_db_path)
            cursor = conn.cursor()
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
            conn.commit()
            conn.close()
            logger.info(f"📄 {self.plugin_name}: Legacy table {table_name} created")
            return True
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Legacy table creation failed: {e}")
            return False
    
    def insert(self, table_name: str, data: Dict[str, Any]):
        """Insert data dengan compatibility layer"""
        try:
            if self.db_manager:
                return self.db_manager.insert(table_name, data, self.plugin_name)
            else:
                return self._insert_legacy(table_name, data)
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Insert failed: {e}")
            return False
    
    def _insert_legacy(self, table_name: str, data: Dict[str, Any]):
        """Legacy insert for backward compatibility"""
        try:
            conn = sqlite3.connect(self.legacy_db_path)
            cursor = conn.cursor()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())
            
            cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Legacy insert failed: {e}")
            return False
    
    def select(self, table_name: str, where_clause: Optional[str] = None, params: Optional[tuple] = None):
        """Select data dengan compatibility layer"""
        try:
            if self.db_manager:
                # Use proper database method signature: select(table, columns, where, where_params, order_by, limit, db_name)
                return self.db_manager.select(table_name, "*", where_clause, params, None, None, self.plugin_name)
            else:
                return self._select_legacy(table_name, where_clause, params)
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Select failed: {e}")
            return []
    
    def _select_legacy(self, table_name: str, where_clause: Optional[str] = None, params: Optional[tuple] = None):
        """Legacy select for backward compatibility"""
        try:
            if not os.path.exists(self.legacy_db_path):
                return []
                
            conn = sqlite3.connect(self.legacy_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if where_clause:
                cursor.execute(f"SELECT * FROM {table_name} WHERE {where_clause}", params or ())
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Legacy select failed: {e}")
            return []
    
    def update(self, table_name: str, data: Dict[str, Any], where_clause: str, params: Optional[tuple] = None):
        """Update data dengan compatibility layer"""
        try:
            if self.db_manager:
                # Use proper database method signature: update(table, data, where, where_params, db_name)
                return self.db_manager.update(table_name, data, where_clause, params or (), self.plugin_name)
            else:
                return self._update_legacy(table_name, data, where_clause, params)
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Update failed: {e}")
            return False
    
    def _update_legacy(self, table_name: str, data: Dict[str, Any], where_clause: str, params: Optional[tuple] = None):
        """Legacy update for backward compatibility"""
        try:
            conn = sqlite3.connect(self.legacy_db_path)
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            values = list(data.values()) + list(params or ())
            
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}", values)
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return affected > 0
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Legacy update failed: {e}")
            return False
    
    def delete(self, table_name: str, where_clause: str, params: Optional[tuple] = None):
        """Delete data dengan compatibility layer"""
        try:
            if self.db_manager:
                # Use proper database method signature: delete(table, where, where_params, db_name)
                return self.db_manager.delete(table_name, where_clause, params or (), self.plugin_name)
            else:
                return self._delete_legacy(table_name, where_clause, params)
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Delete failed: {e}")
            return False
    
    def _delete_legacy(self, table_name: str, where_clause: str, params: Optional[tuple] = None):
        """Legacy delete for backward compatibility"""
        try:
            conn = sqlite3.connect(self.legacy_db_path)
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}", params or ())
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return affected > 0
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Legacy delete failed: {e}")
            return False
    
    def migrate_to_centralized(self, table_mappings: Optional[Dict[str, str]] = None):
        """
        Migrate legacy database to centralized system
        table_mappings: Dict mapping old table names to new ones if different
        """
        if not self.db_manager or not os.path.exists(self.legacy_db_path):
            return False
        
        try:
            logger.info(f"🔄 {self.plugin_name}: Starting migration to centralized database")
            
            # Backup legacy database
            backup_path = f"{self.legacy_db_path}.migrated_backup"
            import shutil
            shutil.copy2(self.legacy_db_path, backup_path)
            
            # Get legacy tables
            conn = sqlite3.connect(self.legacy_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]
            
            migrated_count = 0
            for table_name in tables:
                if table_name == 'sqlite_sequence':
                    continue
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                
                # Create schema string
                schema_parts = []
                for col in columns_info:
                    col_def = f"{col['name']} {col['type']}"
                    if col['notnull']:
                        col_def += " NOT NULL"
                    if col['dflt_value']:
                        col_def += f" DEFAULT {col['dflt_value']}"
                    if col['pk']:
                        col_def += " PRIMARY KEY"
                    schema_parts.append(col_def)
                
                schema = ', '.join(schema_parts)
                
                # Map table name if needed
                new_table_name = table_mappings.get(table_name, table_name) if table_mappings else table_name
                
                # Create table in centralized database
                self.db_manager.create_table(new_table_name, schema, self.plugin_name)
                
                # Migrate data
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    self.db_manager.insert(new_table_name, row_dict, self.plugin_name)
                
                migrated_count += 1
                logger.info(f"✅ {self.plugin_name}: Migrated table {table_name} ({len(rows)} rows)")
            
            conn.close()
            
            # Mark as migrated
            migration_info = {
                'plugin_name': self.plugin_name,
                'migrated_at': sqlite3.datetime.datetime.now().isoformat(),
                'tables_migrated': migrated_count,
                'backup_path': backup_path
            }
            
            self.db_manager.insert('migration_log', migration_info, 'vzoel_assistant')
            
            logger.info(f"🎉 {self.plugin_name}: Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Migration failed: {e}")
            return False
    
    def get_stats(self):
        """Get database statistics for plugin"""
        stats = {
            'plugin_name': self.plugin_name,
            'using_centralized': self.db_manager is not None,
            'legacy_db_exists': os.path.exists(self.legacy_db_path),
            'legacy_db_size': 0,
            'tables_count': 0
        }
        
        try:
            if os.path.exists(self.legacy_db_path):
                stats['legacy_db_size'] = os.path.getsize(self.legacy_db_path)
                
                conn = sqlite3.connect(self.legacy_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table'")
                stats['tables_count'] = cursor.fetchone()[0]
                conn.close()
        except Exception as e:
            logger.error(f"❌ {self.plugin_name}: Stats failed: {e}")
        
        return stats

# Convenience functions for quick plugin integration
def get_plugin_db(plugin_name: str) -> PluginDatabaseManager:
    """Get database manager for plugin"""
    return PluginDatabaseManager(plugin_name)

def create_plugin_table(plugin_name: str, table_name: str, schema: str):
    """Quick table creation for plugin"""
    db = get_plugin_db(plugin_name)
    return db.create_table(table_name, schema)

def log_plugin_data(plugin_name: str, table_name: str, data: Dict[str, Any]):
    """Quick data logging for plugin"""
    db = get_plugin_db(plugin_name)
    return db.insert(table_name, data)

def get_plugin_data(plugin_name: str, table_name: str, where_clause: Optional[str] = None, params: Optional[tuple] = None):
    """Quick data retrieval for plugin"""
    db = get_plugin_db(plugin_name)
    return db.select(table_name, where_clause, params)

print("🗄️ Plugin Database Compatibility Layer loaded successfully!")
print("Features: Centralized DB integration, Legacy compatibility, Auto-migration")