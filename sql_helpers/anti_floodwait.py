"""
Anti FloodWait SQL Helper - Enhanced untuk VzoelFox Userbot
Manage flood control dengan SQLAlchemy persistent storage
"""

try:
    from sql_helpers import BASE, SESSION, DB_LOCK
except ImportError:
    raise AttributeError("SQL helpers not available - check database configuration")

import threading
from sqlalchemy import BigInteger, Column, Integer, String, DateTime, Text
from datetime import datetime

# Default values
DEF_COUNT = 0
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)

class FloodControl(BASE):
    """FloodControl table untuk anti-flood management"""
    __tablename__ = "antiflood"
    
    chat_id = Column(String(20), primary_key=True)
    user_id = Column(BigInteger)
    count = Column(Integer, default=DEF_COUNT)
    limit = Column(Integer, default=DEF_LIMIT)
    last_update = Column(DateTime, default=datetime.utcnow)
    chat_title = Column(Text, default="Unknown")
    
    def __init__(self, chat_id, chat_title=None):
        self.chat_id = str(chat_id)  # ensure string
        self.chat_title = chat_title or "Unknown"
        self.last_update = datetime.utcnow()

    def __repr__(self):
        return f"<FloodControl chat_id={self.chat_id} limit={self.limit} count={self.count}>"

# Create table will be handled by start_db() in __init__.py
# FloodControl.__table__.create(bind=engine, checkfirst=True) # Moved to main init
print("✅ [AntiFlood] Table definition ready")

# Thread-safe insertion lock
INSERTION_LOCK = threading.RLock()

# In-memory flood tracking cache
CHAT_FLOOD = {}

def set_flood(chat_id, amount, chat_title=None):
    """Set flood limit untuk chat tertentu"""
    with INSERTION_LOCK:
        try:
            flood = SESSION.query(FloodControl).get(str(chat_id))
            if not flood:
                flood = FloodControl(str(chat_id), chat_title)
            
            flood.user_id = None
            flood.limit = amount
            flood.last_update = datetime.utcnow()
            if chat_title:
                flood.chat_title = chat_title
            
            # Update cache
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)
            
            SESSION.add(flood)
            SESSION.commit()
            
            print(f"[AntiFlood] Set flood limit {amount} for chat {chat_id}")
            return True
            
        except Exception as e:
            print(f"[AntiFlood] Error setting flood: {e}")
            SESSION.rollback()
            return False

def update_flood(chat_id: str, user_id, user_name=None) -> bool:
    """Update flood count untuk user di chat - return True jika limit exceeded"""
    chat_id = str(chat_id)
    
    if chat_id not in CHAT_FLOOD:
        # Load from database if not in cache
        __load_chat_flood(chat_id)
    
    curr_user_id, count, limit = CHAT_FLOOD.get(chat_id, DEF_OBJ)
    
    if limit == 0:  # no antiflood enabled
        return False
    
    if user_id != curr_user_id or user_id is None:  # different user
        CHAT_FLOOD[chat_id] = (user_id, 1, limit)
        return False
    
    # Same user - increment count
    count += 1
    if count > limit:  # flood detected!
        CHAT_FLOOD[chat_id] = (None, DEF_COUNT, limit)  # reset
        print(f"[AntiFlood] Flood detected: user {user_id} in chat {chat_id} ({count}/{limit})")
        return True
    
    # Update count
    CHAT_FLOOD[chat_id] = (user_id, count, limit)
    return False

def get_flood_limit(chat_id):
    """Get flood limit untuk chat"""
    chat_id = str(chat_id)
    if chat_id not in CHAT_FLOOD:
        __load_chat_flood(chat_id)
    return CHAT_FLOOD.get(chat_id, DEF_OBJ)[2]

def get_flood_info(chat_id):
    """Get complete flood info untuk chat"""
    chat_id = str(chat_id)
    if chat_id not in CHAT_FLOOD:
        __load_chat_flood(chat_id)
    
    curr_user_id, count, limit = CHAT_FLOOD.get(chat_id, DEF_OBJ)
    return {
        'chat_id': chat_id,
        'current_user': curr_user_id,
        'current_count': count,
        'flood_limit': limit,
        'antiflood_enabled': limit > 0
    }

def remove_flood(chat_id):
    """Remove flood protection untuk chat"""
    with INSERTION_LOCK:
        try:
            chat_id = str(chat_id)
            flood = SESSION.query(FloodControl).get(chat_id)
            if flood:
                SESSION.delete(flood)
                SESSION.commit()
            
            # Remove from cache
            CHAT_FLOOD.pop(chat_id, None)
            
            print(f"[AntiFlood] Removed flood protection for chat {chat_id}")
            return True
            
        except Exception as e:
            print(f"[AntiFlood] Error removing flood: {e}")
            SESSION.rollback()
            return False

def migrate_chat(old_chat_id, new_chat_id):
    """Migrate flood settings ke chat ID baru"""
    with INSERTION_LOCK:
        try:
            old_chat_id, new_chat_id = str(old_chat_id), str(new_chat_id)
            
            flood = SESSION.query(FloodControl).get(old_chat_id)
            if flood:
                # Update cache
                CHAT_FLOOD[new_chat_id] = CHAT_FLOOD.get(old_chat_id, DEF_OBJ)
                CHAT_FLOOD.pop(old_chat_id, None)
                
                # Update database
                flood.chat_id = new_chat_id
                flood.last_update = datetime.utcnow()
                SESSION.commit()
                
                print(f"[AntiFlood] Migrated chat {old_chat_id} → {new_chat_id}")
            
        except Exception as e:
            print(f"[AntiFlood] Migration error: {e}")
            SESSION.rollback()
        finally:
            SESSION.close()

def get_all_floods():
    """Get all flood-controlled chats"""
    try:
        all_floods = SESSION.query(FloodControl).all()
        result = []
        for flood in all_floods:
            result.append({
                'chat_id': flood.chat_id,
                'chat_title': flood.chat_title,
                'limit': flood.limit,
                'last_update': flood.last_update
            })
        return result
    except Exception as e:
        print(f"[AntiFlood] Error getting all floods: {e}")
        return []

def reset_flood_count(chat_id):
    """Reset flood count untuk chat"""
    chat_id = str(chat_id)
    if chat_id in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD[chat_id]
        CHAT_FLOOD[chat_id] = (None, DEF_COUNT, limit)
        print(f"[AntiFlood] Reset flood count for chat {chat_id}")
        return True
    return False

def __load_chat_flood(chat_id):
    """Load single chat flood setting dari database ke cache"""
    try:
        chat_id = str(chat_id)
        flood = SESSION.query(FloodControl).get(chat_id)
        if flood:
            CHAT_FLOOD[chat_id] = (None, DEF_COUNT, flood.limit)
        else:
            CHAT_FLOOD[chat_id] = DEF_OBJ
    except Exception as e:
        print(f"[AntiFlood] Error loading chat flood: {e}")
        CHAT_FLOOD[chat_id] = DEF_OBJ

def __load_flood_settings():
    """Load all flood settings dari database ke memory cache"""
    global CHAT_FLOOD
    try:
        with INSERTION_LOCK:
            all_chats = SESSION.query(FloodControl).all()
            CHAT_FLOOD = {
                chat.chat_id: (None, DEF_COUNT, chat.limit) 
                for chat in all_chats
            }
            print(f"[AntiFlood] Loaded {len(CHAT_FLOOD)} flood controls")
            
    except Exception as e:
        print(f"[AntiFlood] Error loading flood settings: {e}")
        CHAT_FLOOD = {}
    finally:
        SESSION.close()
    
    return CHAT_FLOOD

# Auto-load flood settings akan dipanggil setelah table creation
# __load_flood_settings() # Will be called after tables are created

# Export functions
__all__ = [
    'set_flood', 'update_flood', 'get_flood_limit', 'get_flood_info',
    'remove_flood', 'migrate_chat', 'get_all_floods', 'reset_flood_count',
    'FloodControl', 'CHAT_FLOOD'
]