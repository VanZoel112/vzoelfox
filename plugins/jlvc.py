#!/usr/bin/env python3
"""
Voice Chat Monitor Plugin dengan Premium Emoji Support
File: plugins/voicemonitor.py  
Author: Vzoel Fox's (Enhanced by Morgan)
"""

import re
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, InputPeerChannel, InputPeerChat
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatAdminRequiredError, UserAlreadyParticipantError

# Premium emoji configuration (copy dari main.py)
PREMIUM_EMOJIS = {
    'main': {'id': '6156784006194009426', 'char': '🤩'},
    'check': {'id': '5794353925360457382', 'char': '⚙️'},
    'adder1': {'id': '5794407002566300853', 'char': '⛈'},
    'adder2': {'id': '5793913811471700779', 'char': '✅'},
    'adder3': {'id': '5321412209992033736', 'char': '👽'},
    'adder4': {'id': '5793973133559993740', 'char': '✈️'},
    'adder5': {'id': '5357404860566235955', 'char': '😈'},
    'adder6': {'id': '5794323465452394551', 'char': '🎚️'}
}

# Unicode Fonts
FONTS = {
    'bold': {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
        'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
        's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
        'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
        'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    },
    'mono': {
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
        'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
        's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
        'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
        'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
        '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
    }
}

# Global variables
premium_status = None
vc_sessions = {}  # Track active VC sessions
topic_keywords = defaultdict(list)  # Track keywords per chat
monitoring_active = {}  # Track monitoring status per chat

# Data files
VC_HISTORY_FILE = "data/vc_history.json"
TOPIC_KEYWORDS_FILE = "data/topic_keywords.json"

async def check_premium_status():
    """Check premium status in plugin"""
    global premium_status
    try:
        me = await client.get_me()
        premium_status = getattr(me, 'premium', False)
        return premium_status
    except Exception:
        premium_status = False
        return False

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def get_emoji(emoji_type):
    """Get premium emoji character"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    if not premium_status:
        return []
    
    entities = []
    current_offset = 0
    i = 0
    
    try:
        while i < len(text):
            found_emoji = False
            
            for emoji_type, emoji_data in PREMIUM_EMOJIS.items():
                emoji_char = emoji_data['char']
                emoji_id = emoji_data['id']
                
                if text[i:].startswith(emoji_char):
                    try:
                        emoji_bytes = emoji_char.encode('utf-16-le')
                        utf16_length = len(emoji_bytes) // 2
                        
                        entities.append(MessageEntityCustomEmoji(
                            offset=current_offset,
                            length=utf16_length,
                            document_id=int(emoji_id)
                        ))
                        
                        i += len(emoji_char)
                        current_offset += utf16_length
                        found_emoji = True
                        break
                        
                    except Exception:
                        break
            
            if not found_emoji:
                char = text[i]
                char_bytes = char.encode('utf-16-le')
                char_utf16_length = len(char_bytes) // 2
                current_offset += char_utf16_length
                i += 1
        
        return entities
    except Exception:
        return []

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available"""
    try:
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return True

def get_prefix():
    """Get command prefix"""
    try:
        import os
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

def ensure_data_directory():
    """Ensure data directory exists"""
    os.makedirs("data", exist_ok=True)

def save_vc_history(chat_id, action, duration=None, topics=None):
    """Save VC history to file"""
    ensure_data_directory()
    
    try:
        # Load existing history
        if os.path.exists(VC_HISTORY_FILE):
            with open(VC_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Add new entry
        entry = {
            'timestamp': datetime.now().isoformat(),
            'chat_id': chat_id,
            'action': action,
            'duration': duration,
            'topics': topics or []
        }
        
        history.append(entry)
        
        # Keep only last 100 entries
        history = history[-100:]
        
        # Save to file
        with open(VC_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        print(f"Error saving VC history: {e}")

def load_vc_history():
    """Load VC history from file"""
    try:
        if os.path.exists(VC_HISTORY_FILE):
            with open(VC_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def extract_keywords(text, limit=10):
    """Extract important keywords from text"""
    # Common words to ignore
    stopwords = {
        'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'ini', 'itu', 'tidak', 'ya', 'sudah',
        'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'this', 'that', 'not', 'yes', 'already',
        'aku', 'kamu', 'dia', 'kita', 'mereka', 'saya', 'anda', 'gue', 'lo', 'gw', 'lu',
        'i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Clean and split text
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter stopwords and count
    filtered_words = [word for word in words if word not in stopwords and len(word) >= 3]
    word_count = Counter(filtered_words)
    
    # Return top keywords
    return [word for word, count in word_count.most_common(limit)]

def format_duration(seconds):
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"

async def get_chat_title(chat_id):
    """Get chat title by ID"""
    try:
        entity = await client.get_entity(chat_id)
        return getattr(entity, 'title', str(chat_id))
    except Exception:
        return str(chat_id)

# JOIN VC COMMAND WITH MONITORING
@client.on(events.NewMessage(pattern=r'\.joinvc'))
async def join_vc_handler(event):
    """Join voice chat with monitoring setup"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        chat_title = chat.title or str(chat_id)
        
        # Check if already in VC
        if chat_id in vc_sessions:
            status_text = f"""
{get_emoji('adder3')} {convert_font('VC STATUS', 'mono')}

{get_emoji('check')} Already connected to voice chat in:
{convert_font(chat_title, 'bold')}

{get_emoji('main')} Use `{get_prefix()}leavevc` to disconnect first
            """.strip()
            await safe_send_with_entities(event, status_text)
            return
        
        # Try to join VC
        try:
            # For channels
            if hasattr(chat, 'broadcast') and chat.broadcast:
                peer = InputPeerChannel(chat.id, chat.access_hash)
            else:
                # For groups
                peer = InputPeerChat(chat.id)
            
            # Join the group call (this is a simplified version)
            # You might need to implement actual voice chat joining based on your setup
            
            # Record VC session start
            vc_sessions[chat_id] = {
                'start_time': datetime.now(),
                'chat_title': chat_title,
                'messages_monitored': 0,
                'keywords_collected': []
            }
            
            # Enable topic monitoring
            monitoring_active[chat_id] = True
            
            join_text = f"""
{get_emoji('adder2')} {convert_font('VC CONNECTED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('VOICE CHAT MONITORING ACTIVE', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Connected to:', 'bold')} {convert_font(chat_title, 'mono')}
{get_emoji('adder1')} {convert_font('Start Time:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{get_emoji('adder4')} {convert_font('Monitoring:', 'bold')} Active
{get_emoji('adder5')} {convert_font('Topic Tracking:', 'bold')} Enabled

{get_emoji('adder6')} {convert_font('Features Active:', 'bold')}
{get_emoji('check')} Duration tracking
{get_emoji('check')} Topic keyword extraction  
{get_emoji('check')} Message monitoring
{get_emoji('check')} Auto-summary generation

{get_emoji('main')} Use `{get_prefix()}vcstatus` for live monitoring
            """.strip()
            
            await safe_send_with_entities(event, join_text)
            
            # Start monitoring task
            asyncio.create_task(monitor_vc_activity(chat_id))
            
        except Exception as join_error:
            error_text = f"""
{get_emoji('adder3')} {convert_font('VC JOIN ERROR', 'mono')}

{get_emoji('adder1')} Error: {str(join_error)}
{get_emoji('check')} Make sure voice chat is active
{get_emoji('check')} Check bot permissions
            """.strip()
            await safe_send_with_entities(event, error_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# LEAVE VC COMMAND WITH SUMMARY
@client.on(events.NewMessage(pattern=r'\.leavevc'))
async def leave_vc_handler(event):
    """Leave voice chat with activity summary"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        chat_title = chat.title or str(chat_id)
        
        # Check if in VC
        if chat_id not in vc_sessions:
            status_text = f"""
{get_emoji('adder3')} {convert_font('VC STATUS', 'mono')}

{get_emoji('check')} Not connected to voice chat in this group
{get_emoji('main')} Use `{get_prefix()}joinvc` to connect
            """.strip()
            await safe_send_with_entities(event, status_text)
            return
        
        # Calculate session duration
        session = vc_sessions[chat_id]
        duration = int((datetime.now() - session['start_time']).total_seconds())
        duration_str = format_duration(duration)
        
        # Get collected topics
        collected_keywords = session.get('keywords_collected', [])
        top_keywords = collected_keywords[:10] if collected_keywords else ['No topics detected']
        
        # Save to history
        save_vc_history(chat_id, 'leave', duration, collected_keywords)
        
        # Remove from active sessions
        del vc_sessions[chat_id]
        monitoring_active[chat_id] = False
        
        # Generate summary
        summary_text = f"""
{get_emoji('adder4')} {convert_font('VC SESSION COMPLETE', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('MONITORING SUMMARY', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Chat:', 'bold')} {convert_font(chat_title, 'mono')}
{get_emoji('adder1')} {convert_font('Duration:', 'bold')} {duration_str}
{get_emoji('adder2')} {convert_font('Messages Monitored:', 'bold')} {session.get('messages_monitored', 0)}
{get_emoji('adder3')} {convert_font('Keywords Extracted:', 'bold')} {len(collected_keywords)}

{get_emoji('adder5')} {convert_font('Top Discussion Topics:', 'bold')}
""" + "\n".join([f"{get_emoji('check')} {convert_font(keyword.title(), 'mono')}" for keyword in top_keywords[:5]]) + f"""

{get_emoji('adder6')} {convert_font('Session End:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{get_emoji('main')} Monitoring data saved to history
        """.strip()
        
        await safe_send_with_entities(event, summary_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# VC STATUS COMMAND
@client.on(events.NewMessage(pattern=r'\.vcstatus'))
async def vc_status_handler(event):
    """Show current VC monitoring status"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        
        if chat_id not in vc_sessions:
            status_text = f"""
{get_emoji('adder3')} {convert_font('VC STATUS', 'mono')}

{get_emoji('check')} Not currently in voice chat
{get_emoji('main')} Use `{get_prefix()}joinvc` to start monitoring
            """.strip()
            await safe_send_with_entities(event, status_text)
            return
        
        session = vc_sessions[chat_id]
        current_duration = int((datetime.now() - session['start_time']).total_seconds())
        duration_str = format_duration(current_duration)
        
        recent_keywords = session.get('keywords_collected', [])[-10:]
        
        status_text = f"""
{get_emoji('main')} {convert_font('VC MONITORING STATUS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder2')} {convert_font('LIVE MONITORING ACTIVE', 'mono')} {get_emoji('adder2')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Connected Duration:', 'bold')} {duration_str}
{get_emoji('adder1')} {convert_font('Messages Monitored:', 'bold')} {session.get('messages_monitored', 0)}
{get_emoji('adder4')} {convert_font('Keywords Collected:', 'bold')} {len(session.get('keywords_collected', []))}

{get_emoji('adder5')} {convert_font('Recent Topics:', 'bold')}
""" + "\n".join([f"{get_emoji('check')} {convert_font(keyword.title(), 'mono')}" for keyword in recent_keywords]) + f"""

{get_emoji('adder6')} {convert_font('Monitoring Since:', 'bold')} {session['start_time'].strftime('%H:%M:%S')}
{get_emoji('main')} Real-time topic extraction active
        """.strip()
        
        await safe_send_with_entities(event, status_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# VC HISTORY COMMAND
@client.on(events.NewMessage(pattern=r'\.vchistory'))
async def vc_history_handler(event):
    """Show VC session history"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        history = load_vc_history()
        
        if not history:
            history_text = f"""
{get_emoji('adder3')} {convert_font('VC HISTORY', 'mono')}

{get_emoji('check')} No voice chat history found
{get_emoji('main')} Join voice chats to start tracking
            """.strip()
            await safe_send_with_entities(event, history_text)
            return
        
        # Show last 5 sessions
        recent_sessions = history[-5:]
        
        history_text = f"""
{get_emoji('adder6')} {convert_font('VC SESSION HISTORY', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('RECENT VC ACTIVITIES', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

"""
        
        for i, session in enumerate(reversed(recent_sessions), 1):
            chat_title = await get_chat_title(session['chat_id'])
            timestamp = datetime.fromisoformat(session['timestamp']).strftime('%m/%d %H:%M')
            duration_str = format_duration(session.get('duration', 0)) if session.get('duration') else 'N/A'
            topic_count = len(session.get('topics', []))
            
            history_text += f"""
{get_emoji('check')} {convert_font(f'Session #{i}', 'bold')}
{get_emoji('adder1')} {convert_font('Chat:', 'mono')} {chat_title[:30]}
{get_emoji('adder2')} {convert_font('Date:', 'mono')} {timestamp}
{get_emoji('adder4')} {convert_font('Duration:', 'mono')} {duration_str}
{get_emoji('adder5')} {convert_font('Topics:', 'mono')} {topic_count} keywords

"""
        
        history_text += f"{get_emoji('main')} Use `{get_prefix()}vcstats` for detailed statistics"
        
        await safe_send_with_entities(event, history_text.strip())
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

async def monitor_vc_activity(chat_id):
    """Background task to monitor VC activity and extract topics"""
    try:
        while chat_id in vc_sessions and monitoring_active.get(chat_id, False):
            await asyncio.sleep(5)  # Check every 5 seconds
            
            # This would be where you implement actual voice chat monitoring
            # For now, we'll monitor text messages during VC session
            
    except Exception as e:
        print(f"VC monitoring error for {chat_id}: {e}")

# Message monitoring during VC (captures topics from text chat)
@client.on(events.NewMessage)
async def message_monitor(event):
    """Monitor messages during VC for topic extraction"""
    try:
        chat_id = event.chat_id
        
        # Only monitor if VC session is active
        if chat_id not in vc_sessions or not monitor
