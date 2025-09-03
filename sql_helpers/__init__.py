"""
SQL Helpers Module for VzoelFox Userbot
Database management dengan SQLAlchemy untuk persistent data storage
Author: Vzoel Fox's Enhanced by Claude
"""

import os
import threading
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Database configuration
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///vzoel_userbot.db')

# Handle different database types
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql://', 1)

# Create engine dengan proper configuration
if DB_URL.startswith('sqlite'):
    engine = create_engine(
        DB_URL,
        poolclass=StaticPool,
        connect_args={
            'check_same_thread': False,
            'timeout': 20,
            'isolation_level': None
        },
        echo=False
    )
else:
    engine = create_engine(DB_URL, echo=False)

# Create base dan session
BASE = declarative_base()
SESSION = scoped_session(sessionmaker(bind=engine, autoflush=False))

# Thread lock untuk database operations
DB_LOCK = threading.RLock()

def start_db():
    """Initialize database tables"""
    try:
        BASE.metadata.create_all(engine)
        print("✅ [SQL] Database initialized successfully")
        
        # Initialize module-specific data loading
        try:
            from sql_helpers.anti_floodwait import __load_flood_settings
            __load_flood_settings()
        except ImportError:
            pass
            
        try:
            from sql_helpers.broadcast_sql import __load_chat_broadcastlists
            __load_chat_broadcastlists()
        except ImportError:
            pass
        
        return True
    except Exception as e:
        print(f"❌ [SQL] Database initialization failed: {e}")
        return False

def close_db():
    """Close database connections"""
    try:
        SESSION.remove()
        engine.dispose()
        print("✅ [SQL] Database connections closed")
    except Exception as e:
        print(f"❌ [SQL] Error closing database: {e}")

# Auto-initialize database
start_db()

__all__ = ['BASE', 'SESSION', 'DB_LOCK', 'start_db', 'close_db']