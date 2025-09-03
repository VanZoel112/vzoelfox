"""
User Info SQL Helper untuk VzoelFox Userbot  
Manage user information dan statistics
"""

try:
    from sql_helpers import BASE, SESSION, DB_LOCK
except ImportError:
    raise AttributeError("SQL helpers not available")

import threading
from sqlalchemy import BigInteger, Column, String, DateTime, Integer, Boolean, Text
from datetime import datetime

class UserInfo(BASE):
    """Table untuk menyimpan user information"""
    __tablename__ = "user_info"
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    is_bot = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    language_code = Column(String(10), nullable=True)
    
    # Tracking info
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    
    # Additional info
    bio = Column(Text, nullable=True)
    profile_photo_count = Column(Integer, default=0)
    common_chats_count = Column(Integer, default=0)
    
    def __init__(self, user_id):
        self.user_id = int(user_id)
        self.first_seen = datetime.utcnow()
        self.last_seen = datetime.utcnow()
    
    def __repr__(self):
        return f"<UserInfo {self.user_id} @{self.username or 'no_username'}>"

class UserStats(BASE):
    """Table untuk user statistics dan activity"""
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    chat_id = Column(BigInteger)
    date = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=1)
    
    def __init__(self, user_id, chat_id):
        self.user_id = int(user_id)
        self.chat_id = int(chat_id) 
        self.date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)  # Daily stats
    
    def __repr__(self):
        return f"<UserStats user={self.user_id} chat={self.chat_id} messages={self.message_count}>"

# Create tables will be handled by start_db() in __init__.py
print("✅ [UserInfoSQL] Table definitions ready")

INSERTION_LOCK = threading.RLock()

def update_user_info(user_id, username=None, first_name=None, last_name=None, 
                    phone=None, is_bot=False, is_premium=False, language_code=None, bio=None):
    """Update atau create user info"""
    with INSERTION_LOCK:
        try:
            user_id = int(user_id)
            
            user = SESSION.query(UserInfo).get(user_id)
            if not user:
                user = UserInfo(user_id)
                SESSION.add(user)
            
            # Update fields jika provided
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if phone is not None:
                user.phone = phone
            if bio is not None:
                user.bio = bio
            
            user.is_bot = is_bot
            user.is_premium = is_premium
            user.language_code = language_code
            user.last_seen = datetime.utcnow()
            
            SESSION.commit()
            return True
            
        except Exception as e:
            print(f"[UserInfoSQL] Error updating user info: {e}")
            SESSION.rollback()
            return False

def get_user_info(user_id):
    """Get user information"""
    try:
        user_id = int(user_id)
        user = SESSION.query(UserInfo).get(user_id)
        if user:
            return {
                'user_id': user.user_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'is_bot': user.is_bot,
                'is_premium': user.is_premium,
                'language_code': user.language_code,
                'first_seen': user.first_seen,
                'last_seen': user.last_seen,
                'message_count': user.message_count,
                'bio': user.bio,
                'profile_photo_count': user.profile_photo_count,
                'common_chats_count': user.common_chats_count
            }
        return None
    except Exception as e:
        print(f"[UserInfoSQL] Error getting user info: {e}")
        return None

def increment_user_messages(user_id, chat_id=None):
    """Increment message count untuk user"""
    with INSERTION_LOCK:
        try:
            user_id = int(user_id)
            
            # Update user info message count
            user = SESSION.query(UserInfo).get(user_id)
            if user:
                user.message_count += 1
                user.last_seen = datetime.utcnow()
            
            # Update daily stats jika chat_id provided
            if chat_id:
                chat_id = int(chat_id)
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                
                stat = SESSION.query(UserStats).filter(
                    UserStats.user_id == user_id,
                    UserStats.chat_id == chat_id,
                    UserStats.date == today
                ).first()
                
                if stat:
                    stat.message_count += 1
                else:
                    stat = UserStats(user_id, chat_id)
                    SESSION.add(stat)
            
            SESSION.commit()
            return True
            
        except Exception as e:
            print(f"[UserInfoSQL] Error incrementing messages: {e}")
            SESSION.rollback()
            return False

def get_user_stats(user_id, days=7):
    """Get user statistics untuk beberapa hari terakhir"""
    try:
        user_id = int(user_id)
        from datetime import timedelta
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        stats = SESSION.query(UserStats).filter(
            UserStats.user_id == user_id,
            UserStats.date >= since_date
        ).all()
        
        result = []
        for stat in stats:
            result.append({
                'user_id': stat.user_id,
                'chat_id': stat.chat_id,
                'date': stat.date,
                'message_count': stat.message_count
            })
        
        return result
        
    except Exception as e:
        print(f"[UserInfoSQL] Error getting user stats: {e}")
        return []

def get_top_users(limit=10):
    """Get top users berdasarkan message count"""
    try:
        top_users = SESSION.query(UserInfo).order_by(UserInfo.message_count.desc()).limit(limit).all()
        
        result = []
        for user in top_users:
            result.append({
                'user_id': user.user_id,
                'username': user.username,
                'first_name': user.first_name,
                'message_count': user.message_count,
                'last_seen': user.last_seen
            })
        
        return result
        
    except Exception as e:
        print(f"[UserInfoSQL] Error getting top users: {e}")
        return []

def search_users(query, limit=10):
    """Search users berdasarkan username atau name"""
    try:
        search_pattern = f"%{query.lower()}%"
        
        users = SESSION.query(UserInfo).filter(
            (UserInfo.username.ilike(search_pattern)) |
            (UserInfo.first_name.ilike(search_pattern)) |
            (UserInfo.last_name.ilike(search_pattern))
        ).limit(limit).all()
        
        result = []
        for user in users:
            result.append({
                'user_id': user.user_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'message_count': user.message_count,
                'last_seen': user.last_seen
            })
        
        return result
        
    except Exception as e:
        print(f"[UserInfoSQL] Error searching users: {e}")
        return []

def get_user_count():
    """Get total registered users"""
    try:
        count = SESSION.query(UserInfo).count()
        return count
    except Exception as e:
        print(f"[UserInfoSQL] Error getting user count: {e}")
        return 0

def cleanup_old_stats(days=30):
    """Cleanup statistics older than specified days"""
    with INSERTION_LOCK:
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted = SESSION.query(UserStats).filter(UserStats.date < cutoff_date).delete()
            SESSION.commit()
            
            print(f"[UserInfoSQL] Cleaned up {deleted} old stat entries")
            return deleted
            
        except Exception as e:
            print(f"[UserInfoSQL] Error cleaning up stats: {e}")
            SESSION.rollback()
            return 0

# Export functions
__all__ = [
    'update_user_info', 'get_user_info', 'increment_user_messages',
    'get_user_stats', 'get_top_users', 'search_users', 'get_user_count',
    'cleanup_old_stats', 'UserInfo', 'UserStats'
]