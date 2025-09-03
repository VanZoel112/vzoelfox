"""
Blacklist SQL Helper untuk VzoelFox Userbot
Manage persistent blacklist dengan SQLAlchemy
"""

try:
    from sql_helpers import BASE, SESSION, DB_LOCK
except ImportError:
    raise AttributeError("SQL helpers not available")

import threading
from sqlalchemy import BigInteger, Column, String, DateTime, Text, Boolean
from datetime import datetime

class BlacklistChat(BASE):
    """Table untuk menyimpan blacklisted chats"""
    __tablename__ = "blacklist_chats"
    
    chat_id = Column(BigInteger, primary_key=True)
    chat_title = Column(Text, default="Unknown")
    chat_type = Column(String(20), default="Unknown")  # Group, Channel, Supergroup
    added_date = Column(DateTime, default=datetime.utcnow)
    added_by = Column(String(50), default="system")
    permanent = Column(Boolean, default=False)
    reason = Column(Text, default="")
    
    def __init__(self, chat_id, chat_title=None, chat_type=None, added_by="system", permanent=False, reason=""):
        self.chat_id = int(chat_id)
        self.chat_title = chat_title or "Unknown"
        self.chat_type = chat_type or "Unknown"
        self.added_by = added_by
        self.permanent = permanent
        self.reason = reason
        self.added_date = datetime.utcnow()
    
    def __repr__(self):
        return f"<BlacklistChat {self.chat_id} '{self.chat_title}' permanent={self.permanent}>"

# Create table will be handled by start_db() in __init__.py
print("✅ [BlacklistSQL] Table definition ready")

INSERTION_LOCK = threading.RLock()

def add_blacklist_chat(chat_id, chat_title=None, chat_type=None, added_by="system", permanent=False, reason=""):
    """Add chat ke blacklist dengan detail info"""
    with INSERTION_LOCK:
        try:
            chat_id = int(chat_id)
            
            # Check if already exists
            existing = SESSION.query(BlacklistChat).get(chat_id)
            if existing:
                # Update existing entry
                if chat_title:
                    existing.chat_title = chat_title
                if chat_type:
                    existing.chat_type = chat_type
                if reason:
                    existing.reason = reason
                existing.permanent = permanent
                existing.added_date = datetime.utcnow()
                existing.added_by = added_by
            else:
                # Create new entry
                blacklist_entry = BlacklistChat(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    chat_type=chat_type,
                    added_by=added_by,
                    permanent=permanent,
                    reason=reason
                )
                SESSION.add(blacklist_entry)
            
            SESSION.commit()
            print(f"[BlacklistSQL] Added {chat_id} to blacklist (permanent={permanent})")
            return True
            
        except Exception as e:
            print(f"[BlacklistSQL] Error adding to blacklist: {e}")
            SESSION.rollback()
            return False

def remove_blacklist_chat(chat_id):
    """Remove chat dari blacklist (jika tidak permanent)"""
    with INSERTION_LOCK:
        try:
            chat_id = int(chat_id)
            
            blacklist_entry = SESSION.query(BlacklistChat).get(chat_id)
            if blacklist_entry:
                if blacklist_entry.permanent:
                    print(f"[BlacklistSQL] Cannot remove {chat_id} - marked as permanent")
                    return False
                
                SESSION.delete(blacklist_entry)
                SESSION.commit()
                print(f"[BlacklistSQL] Removed {chat_id} from blacklist")
                return True
            else:
                print(f"[BlacklistSQL] Chat {chat_id} not in blacklist")
                return False
                
        except Exception as e:
            print(f"[BlacklistSQL] Error removing from blacklist: {e}")
            SESSION.rollback()
            return False

def is_chat_blacklisted(chat_id):
    """Check if chat ada di blacklist"""
    try:
        chat_id = int(chat_id)
        blacklist_entry = SESSION.query(BlacklistChat).get(chat_id)
        return blacklist_entry is not None
    except (ValueError, TypeError):
        return True  # Invalid ID dianggap blacklisted untuk safety
    except Exception as e:
        print(f"[BlacklistSQL] Error checking blacklist: {e}")
        return True

def get_blacklist_info(chat_id):
    """Get detail info tentang blacklisted chat"""
    try:
        chat_id = int(chat_id)
        blacklist_entry = SESSION.query(BlacklistChat).get(chat_id)
        if blacklist_entry:
            return {
                'chat_id': blacklist_entry.chat_id,
                'chat_title': blacklist_entry.chat_title,
                'chat_type': blacklist_entry.chat_type,
                'added_date': blacklist_entry.added_date,
                'added_by': blacklist_entry.added_by,
                'permanent': blacklist_entry.permanent,
                'reason': blacklist_entry.reason
            }
        return None
    except Exception as e:
        print(f"[BlacklistSQL] Error getting blacklist info: {e}")
        return None

def get_all_blacklisted_chats():
    """Get semua blacklisted chats dengan detail"""
    try:
        all_blacklisted = SESSION.query(BlacklistChat).all()
        result = []
        for entry in all_blacklisted:
            result.append({
                'chat_id': entry.chat_id,
                'chat_title': entry.chat_title,
                'chat_type': entry.chat_type,
                'added_date': entry.added_date,
                'added_by': entry.added_by,
                'permanent': entry.permanent,
                'reason': entry.reason
            })
        return result
    except Exception as e:
        print(f"[BlacklistSQL] Error getting all blacklisted chats: {e}")
        return []

def get_blacklisted_ids():
    """Get list of blacklisted chat IDs only (untuk fast checking)"""
    try:
        result = SESSION.query(BlacklistChat.chat_id).all()
        return [row[0] for row in result]
    except Exception as e:
        print(f"[BlacklistSQL] Error getting blacklisted IDs: {e}")
        return []

def count_blacklisted_chats():
    """Count total blacklisted chats"""
    try:
        count = SESSION.query(BlacklistChat).count()
        return count
    except Exception as e:
        print(f"[BlacklistSQL] Error counting blacklisted chats: {e}")
        return 0

def migrate_blacklist_chat(old_chat_id, new_chat_id):
    """Migrate blacklist entry ke chat ID baru"""
    with INSERTION_LOCK:
        try:
            old_chat_id, new_chat_id = int(old_chat_id), int(new_chat_id)
            
            entry = SESSION.query(BlacklistChat).get(old_chat_id)
            if entry:
                # Create new entry dengan new ID
                new_entry = BlacklistChat(
                    chat_id=new_chat_id,
                    chat_title=entry.chat_title,
                    chat_type=entry.chat_type,
                    added_by=entry.added_by,
                    permanent=entry.permanent,
                    reason=f"Migrated from {old_chat_id}. {entry.reason}"
                )
                
                SESSION.add(new_entry)
                SESSION.delete(entry)  # Remove old entry
                SESSION.commit()
                
                print(f"[BlacklistSQL] Migrated blacklist {old_chat_id} → {new_chat_id}")
                return True
            
        except Exception as e:
            print(f"[BlacklistSQL] Migration error: {e}")
            SESSION.rollback()
            return False

# Export functions
__all__ = [
    'add_blacklist_chat', 'remove_blacklist_chat', 'is_chat_blacklisted',
    'get_blacklist_info', 'get_all_blacklisted_chats', 'get_blacklisted_ids',
    'count_blacklisted_chats', 'migrate_blacklist_chat', 'BlacklistChat'
]