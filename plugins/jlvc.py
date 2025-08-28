#!/usr/bin/env python3
"""
Voice Chat Plugin dengan Premium Emoji Support - FIXED VERSION
File: plugins/jlvc.py  
Author: Vzoel Fox's (Enhanced by Morgan)
Compatible dengan plugin system VZOEL ASSISTANT v0.1.0.75
"""

import re
import os
import sys
import json
import asyncio
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat
from telethon.tl.functions.phone import JoinGroupCallRequest, LeaveGroupCallRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import (
    ChatAdminRequiredError, 
    UserAlreadyParticipantError,
    ChatWriteForbiddenError,
    FloodWaitError
)

# Premium emoji configuration (akan di-inject dari main.py)
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

# Global variables (akan di-inject oleh plugin system)
premium_status = None
client = None  # Will be injected by plugin loader

# Plugin-specific variables
vc_sessions = {}  
topic_keywords = defaultdict(list)
monitoring_active = {}
voice_call_active = False

# Data files
VC_HISTORY_FILE = "data/vc_history.json"
TOPIC_KEYWORDS_FILE = "data/topic_keywords.json"

# Fallback functions (jika tidak di-inject dari main.py)
def safe_convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts dengan fallback"""
    try:
        if 'convert_font' in globals():
            return convert_font(text, font_type)
    except:
        pass
    
    if font_type not in FONTS:
        return text
    
    font_map = FONTS[font_type]
    result = ""
    for char in text:
        result += font_map.get(char, char)
    return result

def safe_get_emoji(emoji_type):
    """Get premium emoji character dengan fallback"""
    try:
        if 'get_emoji' in globals():
            return get_emoji(emoji_type)
    except:
        pass
    
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def safe_create_premium_entities(text):
    """Create premium emoji entities dengan fallback"""
    try:
        if 'create_premium_entities' in globals():
            return create_premium_entities(text)
    except:
        pass
    
    return []

async def safe_check_premium_status():
    """Check premium status dengan fallback"""
    global premium_status
    try:
        if 'check_premium_status' in globals():
            return await check_premium_status()
    except:
        pass
    
    try:
        if not client:
            premium_status = False
            return False
            
        me = await client.get_me()
        premium_status = getattr(me, 'premium', False)
        return premium_status
    except Exception:
        premium_status = False
        return False

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available"""
    try:
        if 'safe_send_with_entities' in globals():
            return await safe_send_with_entities(event, text)
    except:
        pass
    
    try:
        await safe_check_premium_status()
        
        if premium_status:
            entities = safe_create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

async def safe_is_owner_check(user_id):
    """Check if user is owner dengan fallback"""
    try:
        if 'is_owner' in globals():
            return await is_owner(user_id)
    except:
        pass
    
    try:
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        if client:
            me = await client.get_me()
            return user_id == me.id
        return False
    except Exception:
        return False

def safe_get_prefix():
    """Get command prefix dengan fallback"""
    return os.getenv("COMMAND_PREFIX", ".")

def ensure_data_directory():
    """Ensure data directory exists"""
    os.makedirs("data", exist_ok=True)

def save_vc_history(chat_id, action, duration=None, topics=None):
    """Save VC history to file"""
    ensure_data_directory()
    
    try:
        if os.path.exists(VC_HISTORY_FILE):
            with open(VC_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'chat_id': chat_id,
            'action': action,
            'duration': duration,
            'topics': topics or []
        }
        
        history.append(entry)
        history = history[-100:]  # Keep last 100
        
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
        if not client:
            return str(chat_id)
        entity = await client.get_entity(chat_id)
        return getattr(entity, 'title', str(chat_id))
    except Exception:
        return str(chat_id)

def extract_keywords(text, limit=10):
    """Extract important keywords from text"""
    stopwords = {
        'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'ini', 'itu', 'tidak', 'ya', 'sudah',
        'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'this', 'that', 'not', 'yes', 'already',
        'aku', 'kamu', 'dia', 'kita', 'mereka', 'saya', 'anda', 'gue', 'lo', 'gw', 'lu',
        'i', 'you', 'he', 'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered_words = [word for word in words if word not in stopwords and len(word) >= 3]
    word_count = Counter(filtered_words)
    
    return [word for word, count in word_count.most_common(limit)]

# Enhanced voice chat functionality
async def join_voice_chat_enhanced(chat):
    """Enhanced voice chat joining with proper error handling"""
    global voice_call_active
    try:
        # Get chat info
        if isinstance(chat, Channel):
            try:
                full_chat = await client(GetFullChannelRequest(chat))
                call = getattr(full_chat.full_chat, 'call', None)
            except Exception:
                call = None
        else:
            call = getattr(chat, 'call', None)
        
        if not call:
            return False, "No active voice chat found in this chat"
        
        # Try to join
        try:
            await client(JoinGroupCallRequest(
                call=call,
                muted=False,
                video_stopped=True
            ))
            voice_call_active = True
            return True, "Successfully joined voice chat"
        except ChatAdminRequiredError:
            return False, "Admin rights required to join voice chat"
        except Exception as join_error:
            return False, f"Failed to join voice chat: {str(join_error)}"
        
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

async def leave_voice_chat_enhanced():
    """Enhanced voice chat leaving"""
    global voice_call_active
    try:
        if not voice_call_active:
            return False, "Not currently in a voice chat"
        
        await client(LeaveGroupCallRequest())
        voice_call_active = False
        return True, "Successfully left voice chat"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

# JOIN VC COMMAND
@client.on(events.NewMessage(pattern=rf'\.joinvc'))
async def join_vc_handler(event):
    """Join voice chat with monitoring setup"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        chat_title = getattr(chat, 'title', str(chat_id))
        
        # Check if already in VC
        if chat_id in vc_sessions:
            status_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('VC STATUS', 'mono')}

{safe_get_emoji('check')} Already connected to voice chat in:
{safe_convert_font(chat_title, 'bold')}

{safe_get_emoji('main')} Use `{safe_get_prefix()}leavevc` to disconnect first
            """.strip()
            await safe_send_with_entities(event, status_text)
            return
        
        # Try to join VC using enhanced function
        success, message = await join_voice_chat_enhanced(chat)
        
        if success:
            # Record VC session start
            vc_sessions[chat_id] = {
                'start_time': datetime.now(),
                'chat_title': chat_title,
                'messages_monitored': 0,
                'keywords_collected': []
            }
            
            monitoring_active[chat_id] = True
            
            join_text = f"""
{safe_get_emoji('adder2')} {safe_convert_font('VC CONNECTED', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('VOICE CHAT MONITORING ACTIVE', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Connected to:', 'bold')} {safe_convert_font(chat_title, 'mono')}
{safe_get_emoji('adder1')} {safe_convert_font('Start Time:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{safe_get_emoji('adder4')} {safe_convert_font('Monitoring:', 'bold')} Active
{safe_get_emoji('adder5')} {safe_convert_font('Topic Tracking:', 'bold')} Enabled

{safe_get_emoji('adder6')} {safe_convert_font('Features Active:', 'bold')}
{safe_get_emoji('check')} Duration tracking
{safe_get_emoji('check')} Topic keyword extraction  
{safe_get_emoji('check')} Message monitoring
{safe_get_emoji('check')} Auto-summary generation

{safe_get_emoji('main')} Use `{safe_get_prefix()}vcstatus` for live monitoring
            """.strip()
            
            await safe_send_with_entities(event, join_text)
            
            # Start monitoring task
            asyncio.create_task(monitor_vc_activity(chat_id))
            
        else:
            error_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('VC JOIN ERROR', 'mono')}

{safe_get_emoji('adder1')} {safe_convert_font('Error:', 'bold')} {message}
{safe_get_emoji('check')} Make sure voice chat is active
{safe_get_emoji('check')} Check bot permissions in group
{safe_get_emoji('check')} Verify admin rights if required
            """.strip()
            await safe_send_with_entities(event, error_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# LEAVE VC COMMAND
@client.on(events.NewMessage(pattern=rf'\.leavevc'))
async def leave_vc_handler(event):
    """Leave voice chat with activity summary"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        chat_title = getattr(chat, 'title', str(chat_id))
        
        # Check if in VC
        if chat_id not in vc_sessions:
            status_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('VC STATUS', 'mono')}

{safe_get_emoji('check')} Not connected to voice chat in this group
{safe_get_emoji('main')} Use `{safe_get_prefix()}joinvc` to connect
            """.strip()
            await safe_send_with_entities(event, status_text)
            return
        
        # Try to leave VC
        success, message = await leave_voice_chat_enhanced()
        
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
        status_emoji = safe_get_emoji('adder2') if success else safe_get_emoji('adder3')
        summary_text = f"""
{status_emoji} {safe_convert_font('VC SESSION COMPLETE', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('MONITORING SUMMARY', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Chat:', 'bold')} {safe_convert_font(chat_title, 'mono')}
{safe_get_emoji('adder1')} {safe_convert_font('Duration:', 'bold')} {duration_str}
{safe_get_emoji('adder2')} {safe_convert_font('Messages Monitored:', 'bold')} {session.get('messages_monitored', 0)}
{safe_get_emoji('adder3')} {safe_convert_font('Keywords Extracted:', 'bold')} {len(collected_keywords)}

{safe_get_emoji('adder5')} {safe_convert_font('Top Discussion Topics:', 'bold')}
""" + "\n".join([f"{safe_get_emoji('check')} {safe_convert_font(keyword.title(), 'mono')}" for keyword in top_keywords[:5]]) + f"""

{safe_get_emoji('adder6')} {safe_convert_font('Session End:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{safe_get_emoji('main')} Monitoring data saved to history

{safe_get_emoji('adder1')} {safe_convert_font('Leave Status:', 'bold')} {message}
        """.strip()
        
        await safe_send_with_entities(event, summary_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# VC STATUS COMMAND
@client.on(events.NewMessage(pattern=rf'\.vcstatus'))
async def vc_status_handler(event):
    """Show current VC monitoring status"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        chat = await event.get_chat()
        chat_id = chat.id
        
        if chat_id not in vc_sessions:
            status_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('VC STATUS', 'mono')}

{safe_get_emoji('check')} Not currently in voice chat
{safe_get_emoji('main')} Use `{safe_get_prefix()}joinvc` to start monitoring
            """.strip()
            await safe_send_with_entities(event, status_text)
            return
        
        session = vc_sessions[chat_id]
        current_duration = int((datetime.now() - session['start_time']).total_seconds())
        duration_str = format_duration(current_duration)
        
        recent_keywords = session.get('keywords_collected', [])[-10:]
        
        status_text = f"""
{safe_get_emoji('main')} {safe_convert_font('VC MONITORING STATUS', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('adder2')} {safe_convert_font('LIVE MONITORING ACTIVE', 'mono')} {safe_get_emoji('adder2')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Connected Duration:', 'bold')} {duration_str}
{safe_get_emoji('adder1')} {safe_convert_font('Messages Monitored:', 'bold')} {session.get('messages_monitored', 0)}
{safe_get_emoji('adder4')} {safe_convert_font('Keywords Collected:', 'bold')} {len(session.get('keywords_collected', []))}
{safe_get_emoji('adder5')} {safe_convert_font('Voice Call Status:', 'bold')} {'Active' if voice_call_active else 'Inactive'}

{safe_get_emoji('adder5')} {safe_convert_font('Recent Topics:', 'bold')}
""" + "\n".join([f"{safe_get_emoji('check')} {safe_convert_font(keyword.title(), 'mono')}" for keyword in recent_keywords[:5]]) + f"""

{safe_get_emoji('adder6')} {safe_convert_font('Monitoring Since:', 'bold')} {session['start_time'].strftime('%H:%M:%S')}
{safe_get_emoji('main')} Real-time topic extraction active
        """.strip()
        
        await safe_send_with_entities(event, status_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# VC HISTORY COMMAND
@client.on(events.NewMessage(pattern=rf'\.vchistory'))
async def vc_history_handler(event):
    """Show VC session history"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        history = load_vc_history()
        
        if not history:
            history_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('VC HISTORY', 'mono')}

{safe_get_emoji('check')} No voice chat history found
{safe_get_emoji('main')} Join voice chats to start tracking
            """.strip()
            await safe_send_with_entities(event, history_text)
            return
        
        # Show last 5 sessions
        recent_sessions = history[-5:]
        
        history_text = f"""
{safe_get_emoji('adder6')} {safe_convert_font('VC SESSION HISTORY', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('main')} {safe_convert_font('RECENT VC ACTIVITIES', 'mono')} {safe_get_emoji('main')}
╚══════════════════════════════════╝

"""
        
        for i, session in enumerate(reversed(recent_sessions), 1):
            chat_title = await get_chat_title(session['chat_id'])
            timestamp = datetime.fromisoformat(session['timestamp']).strftime('%m/%d %H:%M')
            duration_str = format_duration(session.get('duration', 0)) if session.get('duration') else 'N/A'
            topic_count = len(session.get('topics', []))
            
            history_text += f"""
{safe_get_emoji('check')} {safe_convert_font(f'Session #{i}', 'bold')}
{safe_get_emoji('adder1')} {safe_convert_font('Chat:', 'mono')} {chat_title[:30]}
{safe_get_emoji('adder2')} {safe_convert_font('Date:', 'mono')} {timestamp}
{safe_get_emoji('adder4')} {safe_convert_font('Duration:', 'mono')} {duration_str}
{safe_get_emoji('adder5')} {safe_convert_font('Topics:', 'mono')} {topic_count} keywords

"""
        
        history_text += f"{safe_get_emoji('main')} Total sessions tracked: {len(history)}"
        
        await safe_send_with_entities(event, history_text.strip())
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# VC STATISTICS COMMAND
@client.on(events.NewMessage(pattern=rf'\.vcstats'))
async def vc_stats_handler(event):
    """Show detailed VC statistics"""
    if not await safe_is_owner_check(event.sender_id):
        return
    
    try:
        history = load_vc_history()
        
        if not history:
            stats_text = f"""
{safe_get_emoji('adder3')} {safe_convert_font('VC STATISTICS', 'mono')}

{safe_get_emoji('check')} No statistics available yet
{safe_get_emoji('main')} Start using voice chat features to collect data
            """.strip()
            await safe_send_with_entities(event, stats_text)
            return
        
        # Calculate statistics
        total_sessions = len(history)
        total_duration = sum(session.get('duration', 0) for session in history)
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
        
        # Get chat statistics
        chat_stats = Counter(session['chat_id'] for session in history)
        top_chats = chat_stats.most_common(3)
        
        # Get topic statistics
        all_topics = []
        for session in history:
            all_topics.extend(session.get('topics', []))
        topic_stats = Counter(all_topics)
        top_topics = topic_stats.most_common(5)
        
        stats_text = f"""
{safe_get_emoji('main')} {safe_convert_font('VC STATISTICS REPORT', 'mono')}

╔══════════════════════════════════╗
   {safe_get_emoji('adder6')} {safe_convert_font('COMPREHENSIVE VC ANALYTICS', 'mono')} {safe_get_emoji('adder6')}
╚══════════════════════════════════╝

{safe_get_emoji('check')} {safe_convert_font('Session Statistics:', 'bold')}
{safe_get_emoji('adder1')} Total Sessions: {total_sessions}
{safe_get_emoji('adder2')} Total Duration: {format_duration(total_duration)}
{safe_get_emoji('adder3')} Average Duration: {format_duration(int(avg_duration))}
{safe_get_emoji('adder4')} Currently Active: {len(vc_sessions)}

{safe_get_emoji('adder5')} {safe_convert_font('Top Active Chats:', 'bold')}
"""
        
        for i, (chat_id, count) in enumerate(top_chats, 1):
            chat_title = await get_chat_title(chat_id)
            stats_text += f"{safe_get_emoji('check')} {i}. {chat_title[:25]} ({count} sessions)\n"
        
        stats_text += f"""
{safe_get_emoji('adder6')} {safe_convert_font('Top Discussion Topics:', 'bold')}
"""
        
        for i, (topic, count) in enumerate(top_topics, 1):
            stats_text += f"{safe_get_emoji('check')} {i}. {topic.title()} ({count} mentions)\n"
        
        stats_text += f"""
{safe_get_emoji('main')} Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await safe_send_with_entities(event, stats_text.strip())
        
    except Exception as e:
        await safe_send_with_entities(event, f"{safe_get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# Background monitoring task
async def monitor_vc_activity(chat_id):
    """Background task to monitor VC activity and extract topics"""
    try:
        while chat_id in vc_sessions and monitoring_active.get(chat_id, False):
            await asyncio.sleep(10)  # Check every 10 seconds
            
            # Update session status
            if chat_id in vc_sessions:
                session = vc_sessions[chat_id]
                current_time = datetime.now()
                duration = int((current_time - session['start_time']).total_seconds())
                
                # Auto-save every 5 minutes
                if duration % 300 == 0 and duration > 0:  # Every 5 minutes
                    save_vc_history(chat_id, 'checkpoint', duration, session.get('keywords_collected', []))
            
    except Exception as e:
        print(f"VC monitoring error for {chat_id}: {e}")

# Message monitoring during VC
@client.on(events.NewMessage)
async def message_monitor(event):
    """Monitor messages during VC for topic extraction"""
    try:
        chat_id = event.chat_id
        
        # Only monitor if VC session is active
        if chat_id not in vc_sessions or not monitoring_active.get(chat_id, False):
            return
        
        # Skip if no text
        if not event.text:
            return
        
        # Extract keywords from message
        keywords = extract_keywords(event.text, limit=5)
        if keywords:
            session = vc_sessions[chat_id]
            
            # Add to collected keywords
            session['keywords_collected'].extend(keywords)
            session['messages_monitored'] += 1
            
            # Keep only unique keywords (last 50)
            all_keywords = session['keywords_collected']
            unique_keywords = list(dict.fromkeys(all_keywords))  # Preserve order, remove duplicates
            session['keywords_collected'] = unique_keywords[-50:]  # Keep last 50
    
    except Exception as e:
        print(f"Message monitoring error: {e}")

# Plugin info untuk plugin system
PLUGIN_INFO = {
    'name': 'jlvc',
    'version': '1.0.1',
    'description': 'Voice Chat Management with Monitoring Features',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': ['joinvc', 'leavevc', 'vcstatus', 'vchistory', 'vcstats'],
    'features': ['Voice chat joining/leaving', 'Topic monitoring', 'Session tracking', 'History logging'],
    'dependencies': ['client', 'convert_font', 'get_emoji', 'safe_send_with_entities']
}

def get_plugin_info():
    """Required function for plugin system"""
    return PLUGIN_INFO

def initialize_plugin():
    """Initialize plugin data structures"""
    try:
        ensure_data_directory()
        
        # Load existing data
        try:
            if os.path.exists(TOPIC_KEYWORDS_FILE):
                with open(TOPIC_KEYWORDS_FILE, 'r') as f:
                    data = json.load(f)
                    topic_keywords.update(data)
        except Exception as e:
            print(f"Error loading topic keywords: {e}")
        
        print(f"✅ {PLUGIN_INFO['name']} plugin initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing {PLUGIN_INFO['name']} plugin: {e}")
        return False

def cleanup_plugin():
    """Clean up plugin resources"""
    try:
        # Save any active session data
        for chat_id, session in vc_sessions.items():
            duration = int((datetime.now() - session['start_time']).total_seconds())
            save_vc_history(chat_id, 'forced_cleanup', duration, session.get('keywords_collected', []))
        
        # Clear active sessions
        vc_sessions.clear()
        monitoring_active.clear()
        
        print(f"✅ {PLUGIN_INFO['name']} plugin cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Error cleaning up {PLUGIN_INFO['name']} plugin: {e}")

# Export functions for compatibility
__all__ = [
    'join_voice_chat_enhanced',
    'leave_voice_chat_enhanced', 
    'vc_sessions',
    'monitoring_active',
    'get_plugin_info',
    'initialize_plugin',
    'cleanup_plugin'
]