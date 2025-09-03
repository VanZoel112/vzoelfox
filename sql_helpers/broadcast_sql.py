"""
Broadcast SQL Helper untuk VzoelFox Userbot
Manage broadcast channels dengan keyword-based system
"""

try:
    from sql_helpers import BASE, SESSION, DB_LOCK
except ImportError:
    raise AttributeError("SQL helpers not available")

import threading
from sqlalchemy import Column, String, UnicodeText, distinct, func

class VzoelBroadcast(BASE):
    """Table untuk menyimpan broadcast channels dengan keyword"""
    __tablename__ = "vzoel_broadcast"
    
    keywoard = Column(UnicodeText, primary_key=True)
    group_id = Column(String(20), primary_key=True, nullable=False)

    def __init__(self, keywoard, group_id):
        self.keywoard = keywoard
        self.group_id = str(group_id)

    def __repr__(self):
        return f"<VzoelBroadcast channels '{self.group_id}' for '{self.keywoard}'>"

    def __eq__(self, other):
        return bool(
            isinstance(other, VzoelBroadcast)
            and self.keywoard == other.keywoard
            and self.group_id == other.group_id
        )

# Table creation will be handled by start_db()
print("✅ [BroadcastSQL] Table definition ready")

BROADCAST_INSERTION_LOCK = threading.RLock()

class BROADCAST_SQL:
    """Broadcast SQL management class"""
    def __init__(self):
        self.BROADCAST_CHANNELS = {}

BROADCAST_SQL_ = BROADCAST_SQL()

def add_to_broadcastlist(keywoard, group_id):
    """Add group ke broadcast list untuk keyword tertentu"""
    with BROADCAST_INSERTION_LOCK:
        try:
            broadcast_group = VzoelBroadcast(keywoard, str(group_id))
            
            SESSION.merge(broadcast_group)
            SESSION.commit()
            
            # Update memory cache
            BROADCAST_SQL_.BROADCAST_CHANNELS.setdefault(keywoard, set()).add(str(group_id))
            
            print(f"[BroadcastSQL] Added group {group_id} to broadcast list '{keywoard}'")
            return True
            
        except Exception as e:
            print(f"[BroadcastSQL] Error adding to broadcast list: {e}")
            SESSION.rollback()
            return False

def rm_from_broadcastlist(keywoard, group_id):
    """Remove group dari broadcast list"""
    with BROADCAST_INSERTION_LOCK:
        try:
            broadcast_group = SESSION.query(VzoelBroadcast).get((keywoard, str(group_id)))
            if broadcast_group:
                # Remove from memory cache
                if str(group_id) in BROADCAST_SQL_.BROADCAST_CHANNELS.get(keywoard, set()):
                    BROADCAST_SQL_.BROADCAST_CHANNELS.get(keywoard, set()).remove(str(group_id))
                
                SESSION.delete(broadcast_group)
                SESSION.commit()
                
                print(f"[BroadcastSQL] Removed group {group_id} from broadcast list '{keywoard}'")
                return True
            
            return False
            
        except Exception as e:
            print(f"[BroadcastSQL] Error removing from broadcast list: {e}")
            SESSION.rollback()
            return False
        finally:
            SESSION.close()

def is_in_broadcastlist(keywoard, group_id):
    """Check if group ada di broadcast list untuk keyword"""
    try:
        broadcast_group = SESSION.query(VzoelBroadcast).get((keywoard, str(group_id)))
        return bool(broadcast_group)
    except Exception as e:
        print(f"[BroadcastSQL] Error checking broadcast list: {e}")
        return False
    finally:
        SESSION.close()

def del_keyword_broadcastlist(keywoard):
    """Delete seluruh broadcast list untuk keyword"""
    with BROADCAST_INSERTION_LOCK:
        try:
            deleted_count = (
                SESSION.query(VzoelBroadcast)
                .filter(VzoelBroadcast.keywoard == keywoard)
                .delete()
            )
            
            # Remove from memory cache
            BROADCAST_SQL_.BROADCAST_CHANNELS.pop(keywoard, None)
            SESSION.commit()
            
            print(f"[BroadcastSQL] Deleted {deleted_count} groups from broadcast list '{keywoard}'")
            return deleted_count
            
        except Exception as e:
            print(f"[BroadcastSQL] Error deleting keyword broadcast list: {e}")
            SESSION.rollback()
            return 0

def get_chat_broadcastlist(keywoard):
    """Get semua groups untuk keyword tertentu"""
    return BROADCAST_SQL_.BROADCAST_CHANNELS.get(keywoard, set())

def get_broadcastlist_chats():
    """Get semua unique keywords yang ada broadcast lists"""
    try:
        chats = SESSION.query(VzoelBroadcast.keywoard).distinct().all()
        return [i[0] for i in chats]
    except Exception as e:
        print(f"[BroadcastSQL] Error getting broadcast list chats: {e}")
        return []
    finally:
        SESSION.close()

def num_broadcastlist():
    """Count total broadcast entries"""
    try:
        return SESSION.query(VzoelBroadcast).count()
    except Exception as e:
        print(f"[BroadcastSQL] Error counting broadcast list: {e}")
        return 0
    finally:
        SESSION.close()

def num_broadcastlist_chat(keywoard):
    """Count groups untuk keyword tertentu"""
    try:
        return (
            SESSION.query(VzoelBroadcast.keywoard)
            .filter(VzoelBroadcast.keywoard == keywoard)
            .count()
        )
    except Exception as e:
        print(f"[BroadcastSQL] Error counting broadcast chat: {e}")
        return 0
    finally:
        SESSION.close()

def num_broadcastlist_chats():
    """Count unique keywords"""
    try:
        return SESSION.query(func.count(distinct(VzoelBroadcast.keywoard))).scalar()
    except Exception as e:
        print(f"[BroadcastSQL] Error counting broadcast chats: {e}")
        return 0
    finally:
        SESSION.close()

def get_all_broadcast_info():
    """Get complete broadcast information"""
    try:
        all_broadcasts = SESSION.query(VzoelBroadcast).all()
        result = {}
        
        for broadcast in all_broadcasts:
            keyword = broadcast.keywoard
            if keyword not in result:
                result[keyword] = []
            result[keyword].append(broadcast.group_id)
        
        return result
        
    except Exception as e:
        print(f"[BroadcastSQL] Error getting all broadcast info: {e}")
        return {}
    finally:
        SESSION.close()

def search_broadcast_keywords(query):
    """Search keywords yang mengandung query"""
    try:
        search_pattern = f"%{query}%"
        keywords = (
            SESSION.query(VzoelBroadcast.keywoard)
            .filter(VzoelBroadcast.keywoard.like(search_pattern))
            .distinct()
            .all()
        )
        return [k[0] for k in keywords]
    except Exception as e:
        print(f"[BroadcastSQL] Error searching broadcast keywords: {e}")
        return []
    finally:
        SESSION.close()

def migrate_broadcast_group(old_group_id, new_group_id):
    """Migrate broadcast group ke ID baru"""
    with BROADCAST_INSERTION_LOCK:
        try:
            old_group_id, new_group_id = str(old_group_id), str(new_group_id)
            
            # Get all broadcasts for old group
            broadcasts = SESSION.query(VzoelBroadcast).filter(
                VzoelBroadcast.group_id == old_group_id
            ).all()
            
            migrated_count = 0
            for broadcast in broadcasts:
                # Create new broadcast entry
                new_broadcast = VzoelBroadcast(broadcast.keywoard, new_group_id)
                SESSION.add(new_broadcast)
                
                # Delete old entry
                SESSION.delete(broadcast)
                
                # Update memory cache
                keyword = broadcast.keywoard
                if keyword in BROADCAST_SQL_.BROADCAST_CHANNELS:
                    if old_group_id in BROADCAST_SQL_.BROADCAST_CHANNELS[keyword]:
                        BROADCAST_SQL_.BROADCAST_CHANNELS[keyword].remove(old_group_id)
                    BROADCAST_SQL_.BROADCAST_CHANNELS[keyword].add(new_group_id)
                
                migrated_count += 1
            
            SESSION.commit()
            print(f"[BroadcastSQL] Migrated {migrated_count} broadcast entries: {old_group_id} → {new_group_id}")
            return migrated_count
            
        except Exception as e:
            print(f"[BroadcastSQL] Migration error: {e}")
            SESSION.rollback()
            return 0

def __load_chat_broadcastlists():
    """Load broadcast lists dari database ke memory cache"""
    try:
        # Get all unique keywords
        chats = SESSION.query(VzoelBroadcast.keywoard).distinct().all()
        for (keywoard,) in chats:
            BROADCAST_SQL_.BROADCAST_CHANNELS[keywoard] = []

        # Load all broadcast entries
        all_groups = SESSION.query(VzoelBroadcast).all()
        for x in all_groups:
            BROADCAST_SQL_.BROADCAST_CHANNELS[x.keywoard].append(x.group_id)

        # Convert lists to sets untuk better performance
        BROADCAST_SQL_.BROADCAST_CHANNELS = {
            x: set(y) for x, y in BROADCAST_SQL_.BROADCAST_CHANNELS.items()
        }
        
        print(f"[BroadcastSQL] Loaded {len(BROADCAST_SQL_.BROADCAST_CHANNELS)} broadcast keywords")

    except Exception as e:
        print(f"[BroadcastSQL] Error loading broadcast lists: {e}")
        BROADCAST_SQL_.BROADCAST_CHANNELS = {}
    finally:
        SESSION.close()

# Auto-load broadcast lists akan dipanggil setelah table creation
# __load_chat_broadcastlists() # Will be called after tables are created

# Export functions
__all__ = [
    'add_to_broadcastlist', 'rm_from_broadcastlist', 'is_in_broadcastlist',
    'del_keyword_broadcastlist', 'get_chat_broadcastlist', 'get_broadcastlist_chats',
    'num_broadcastlist', 'num_broadcastlist_chat', 'num_broadcastlist_chats',
    'get_all_broadcast_info', 'search_broadcast_keywords', 'migrate_broadcast_group',
    'VzoelBroadcast', 'BROADCAST_SQL_'
]