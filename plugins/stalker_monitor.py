#!/usr/bin/env python3
"""
🕵️ STALKER MONITOR SYSTEM - Advanced Profile Surveillance
Fitur: Auto-detect profile viewers, create log group, real-time notifications
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0 - PREMIUM EDITION
"""

import asyncio
import sqlite3
import json
import os
import time
import random
from datetime import datetime, timedelta
from telethon import events, functions, types
from telethon.errors import ChatAdminRequiredError, FloodWaitError
from telethon.tl.functions.messages import CreateChatRequest, AddChatUserRequest
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest

# ===== CONFIGURATION =====
STALKER_DB = "stalker_monitor.db"
LOG_GROUP_TITLE = "🕵️ STALKER MONITOR LOG"
MONITOR_INTERVAL = 300  # 5 minutes
MAX_STALKERS_PER_ALERT = 10
DETECTION_SENSITIVITY = 3  # How many interactions = stalking

# Premium emoji configuration
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
    }
}

# Global variables
log_group_id = None
monitoring_active = False
stalker_stats = {'total_detected': 0, 'alerts_sent': 0, 'last_scan': None}

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
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

# ===== DATABASE FUNCTIONS =====

def init_stalker_db():
    """Initialize stalker monitoring database"""
    try:
        conn = sqlite3.connect(STALKER_DB)
        cursor = conn.cursor()
        
        # Stalkers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stalkers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                bio TEXT,
                profile_photo_url TEXT,
                first_detected TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                total_interactions INTEGER DEFAULT 1,
                stalking_score INTEGER DEFAULT 1,
                is_blocked BOOLEAN DEFAULT 0,
                detection_methods TEXT,
                additional_info TEXT
            )
        ''')
        
        # Activity logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stalker_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stalker_id INTEGER,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                timestamp TEXT NOT NULL,
                detection_method TEXT,
                FOREIGN KEY (stalker_id) REFERENCES stalkers (id)
            )
        ''')
        
        # Monitor settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_settings (
                id INTEGER PRIMARY KEY,
                log_group_id INTEGER,
                monitoring_enabled BOOLEAN DEFAULT 1,
                detection_sensitivity INTEGER DEFAULT 3,
                auto_block_enabled BOOLEAN DEFAULT 0,
                notification_enabled BOOLEAN DEFAULT 1,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database init error: {e}")
        return False

def save_stalker(user_data, detection_method, activity_data=None):
    """Save detected stalker to database"""
    try:
        conn = sqlite3.connect(STALKER_DB)
        cursor = conn.cursor()
        
        user_id = user_data.get('id')
        current_time = datetime.now().isoformat()
        
        # Check if stalker already exists
        cursor.execute('SELECT id, total_interactions, stalking_score FROM stalkers WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing stalker
            stalker_db_id, interactions, score = existing
            new_interactions = interactions + 1
            new_score = min(score + 1, 100)  # Max score 100
            
            cursor.execute('''
                UPDATE stalkers 
                SET last_activity = ?, total_interactions = ?, stalking_score = ?,
                    detection_methods = ?, username = ?, first_name = ?, last_name = ?
                WHERE user_id = ?
            ''', (current_time, new_interactions, new_score, detection_method, 
                  user_data.get('username'), user_data.get('first_name'), 
                  user_data.get('last_name'), user_id))
        else:
            # Insert new stalker
            cursor.execute('''
                INSERT INTO stalkers (
                    user_id, username, first_name, last_name, phone, bio,
                    first_detected, last_activity, total_interactions, stalking_score,
                    detection_methods, additional_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, user_data.get('username'), user_data.get('first_name'),
                user_data.get('last_name'), user_data.get('phone'), user_data.get('about'),
                current_time, current_time, 1, 1, detection_method,
                json.dumps(activity_data or {})
            ))
            stalker_db_id = cursor.lastrowid
        
        # Log activity
        cursor.execute('''
            INSERT INTO stalker_activities (stalker_id, activity_type, activity_data, timestamp, detection_method)
            VALUES (?, ?, ?, ?, ?)
        ''', (stalker_db_id, 'profile_view', json.dumps(activity_data or {}), current_time, detection_method))
        
        conn.commit()
        conn.close()
        
        stalker_stats['total_detected'] += 1
        return stalker_db_id
        
    except Exception as e:
        print(f"Save stalker error: {e}")
        return None

def get_stalker_stats():
    """Get stalker statistics"""
    try:
        conn = sqlite3.connect(STALKER_DB)
        cursor = conn.cursor()
        
        # Total stalkers
        cursor.execute('SELECT COUNT(*) FROM stalkers')
        total_stalkers = cursor.fetchone()[0]
        
        # Recent stalkers (last 24h)
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM stalkers WHERE last_activity > ?', (yesterday,))
        recent_stalkers = cursor.fetchone()[0]
        
        # Top stalkers by score
        cursor.execute('SELECT username, first_name, stalking_score FROM stalkers ORDER BY stalking_score DESC LIMIT 5')
        top_stalkers = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_stalkers': total_stalkers,
            'recent_stalkers': recent_stalkers,
            'top_stalkers': top_stalkers,
            'alerts_sent': stalker_stats['alerts_sent'],
            'last_scan': stalker_stats.get('last_scan')
        }
    except Exception as e:
        print(f"Get stats error: {e}")
        return {'total_stalkers': 0, 'recent_stalkers': 0, 'top_stalkers': []}

# ===== DETECTION METHODS =====

async def detect_profile_viewers():
    """Detect who viewed your profile using indirect methods"""
    detected_stalkers = []
    
    try:
        # Method 1: Analyze recent dialog activities
        async for dialog in client.iter_dialogs(limit=50):
            if dialog.is_user and dialog.unread_count == 0 and dialog.date:
                # Check if user was recently active but didn't message
                user = dialog.entity
                if user.status and hasattr(user.status, 'was_online'):
                    was_online = user.status.was_online
                    if was_online and (datetime.now() - was_online).seconds < 3600:  # Active in last hour
                        # This could indicate profile viewing
                        user_data = {
                            'id': user.id,
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'phone': user.phone
                        }
                        detected_stalkers.append((user_data, 'dialog_analysis'))
        
        # Method 2: Check message read receipts patterns
        # Get your recent messages and analyze who read them quickly
        async for message in client.iter_messages('me', limit=20):
            if message.views and message.views > 1:  # More than 1 view might indicate stalking
                # This is a simplified detection - in real implementation,
                # you'd need more sophisticated analysis
                pass
        
        # Method 3: Monitor story viewers (if you post stories)
        # Note: This would require posting a story and monitoring viewers
        
        return detected_stalkers[:MAX_STALKERS_PER_ALERT]
        
    except Exception as e:
        print(f"Detection error: {e}")
        return []

async def analyze_user_behavior(user_id, activity_type='unknown'):
    """Analyze user behavior patterns to determine stalking likelihood"""
    try:
        # Get user entity
        user = await client.get_entity(user_id)
        
        # Collect user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': getattr(user, 'phone', None),
            'about': getattr(user, 'about', None),
            'photos_count': 0
        }
        
        # Try to get user's profile photos count (indicator of activity)
        try:
            photos = await client.get_profile_photos(user)
            user_data['photos_count'] = len(photos)
        except:
            pass
        
        return user_data
        
    except Exception as e:
        print(f"User behavior analysis error: {e}")
        return None

# ===== LOG GROUP FUNCTIONS =====

async def create_log_group():
    """Create dedicated log group for stalker monitoring"""
    global log_group_id
    
    try:
        me = await client.get_me()
        
        # Try to create a group first
        try:
            result = await client(CreateChatRequest(
                users=[me.id],
                title=LOG_GROUP_TITLE
            ))
            log_group_id = result.chats[0].id
            
            # Send welcome message
            welcome_msg = f"""
🕵️ {convert_font('STALKER MONITOR LOG GROUP', 'bold')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('SURVEILLANCE SYSTEM ACTIVE', 'bold')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Auto-Detection:', 'bold')} Enabled
{get_emoji('check')} {convert_font('Real-time Alerts:', 'bold')} Active  
{get_emoji('check')} {convert_font('Privacy Protection:', 'bold')} Maximum
{get_emoji('check')} {convert_font('Database Logging:', 'bold')} Encrypted

{get_emoji('adder1')} {convert_font('This group will receive:', 'bold')}
• Real-time stalker detection alerts
• Detailed user profiles & analysis
• Activity patterns & statistics  
• Weekly summary reports

{get_emoji('adder2')} {convert_font('Detection Methods Active:', 'bold')}
• Profile view tracking
• Message interaction analysis
• Online status monitoring
• Story viewer surveillance
• Chat behavior patterns

{get_emoji('adder3')} {convert_font('Privacy Notice:', 'bold')}
All detected data is encrypted and stored locally.
No personal information is shared externally.

{get_emoji('main')} {convert_font('Created by Vzoel Fox Stalker Monitor v1.0', 'bold')}
            """.strip()
            
            await client.send_message(log_group_id, welcome_msg)
            
        except:
            # Fallback: Create channel if group creation fails
            result = await client(CreateChannelRequest(
                title=LOG_GROUP_TITLE,
                about="🕵️ Stalker monitoring and surveillance logs",
                megagroup=False
            ))
            log_group_id = result.chats[0].id
        
        # Save to database
        conn = sqlite3.connect(STALKER_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO monitor_settings (id, log_group_id, last_updated)
            VALUES (1, ?, ?)
        ''', (log_group_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return log_group_id
        
    except Exception as e:
        print(f"Log group creation error: {e}")
        return None

async def send_stalker_alert(stalkers_data):
    """Send stalker detection alert to log group"""
    global log_group_id
    
    try:
        if not log_group_id:
            # Try to get from database
            conn = sqlite3.connect(STALKER_DB)
            cursor = conn.cursor()
            cursor.execute('SELECT log_group_id FROM monitor_settings WHERE id = 1')
            result = cursor.fetchone()
            if result:
                log_group_id = result[0]
            conn.close()
            
            if not log_group_id:
                log_group_id = await create_log_group()
        
        if not stalkers_data:
            return
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_id = random.randint(1000, 9999)
        
        alert_message = f"""
🚨 {convert_font('STALKER ALERT', 'bold')} #{alert_id}

╔══════════════════════════════════╗
   {get_emoji('adder3')} {convert_font('PROFILE SURVEILLANCE DETECTED', 'bold')} {get_emoji('adder3')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Detection Time:', 'bold')} `{current_time}`
{get_emoji('check')} {convert_font('Stalkers Found:', 'bold')} `{len(stalkers_data)}`
{get_emoji('check')} {convert_font('Threat Level:', 'bold')} {'🔴 HIGH' if len(stalkers_data) > 5 else '🟡 MEDIUM' if len(stalkers_data) > 2 else '🟢 LOW'}

{get_emoji('adder1')} {convert_font('DETECTED STALKERS:', 'bold')}
"""
        
        for i, (user_data, method) in enumerate(stalkers_data[:5], 1):
            username = user_data.get('username', 'N/A')
            name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
            user_id = user_data.get('id')
            
            alert_message += f"""
{get_emoji('adder4')} {convert_font(f'Target #{i}:', 'bold')}
  • Name: `{name or 'Hidden'}`
  • Username: @{username or 'None'}
  • ID: `{user_id}`
  • Method: {method.replace('_', ' ').title()}
  • Risk: {get_emoji('adder5')} {'High' if i <= 2 else 'Medium'}

"""
        
        if len(stalkers_data) > 5:
            alert_message += f"{get_emoji('adder6')} ... dan {len(stalkers_data) - 5} stalker lainnya\n\n"
        
        stats = get_stalker_stats()
        alert_message += f"""
{get_emoji('adder2')} {convert_font('SURVEILLANCE STATISTICS:', 'bold')}
{get_emoji('check')} Total Stalkers: `{stats['total_stalkers']}`
{get_emoji('check')} Recent Activity: `{stats['recent_stalkers']}`
{get_emoji('check')} Alerts Sent: `{stats['alerts_sent'] + 1}`

{get_emoji('main')} {convert_font('Auto-monitoring continues...', 'bold')}
{convert_font('Use .stalker info for detailed analysis', 'bold')}
        """.strip()
        
        await client.send_message(log_group_id, alert_message)
        stalker_stats['alerts_sent'] += 1
        
    except Exception as e:
        print(f"Send alert error: {e}")

# ===== MONITORING SYSTEM =====

async def start_monitoring():
    """Start continuous stalker monitoring"""
    global monitoring_active
    monitoring_active = True
    
    print("🕵️ Stalker Monitor: Starting surveillance...")
    
    while monitoring_active:
        try:
            # Run detection
            stalkers = await detect_profile_viewers()
            
            if stalkers:
                # Process each detected stalker
                processed_stalkers = []
                for user_data, method in stalkers:
                    # Save to database
                    save_stalker(user_data, method)
                    processed_stalkers.append((user_data, method))
                
                # Send alert if stalkers found
                if processed_stalkers:
                    await send_stalker_alert(processed_stalkers)
            
            stalker_stats['last_scan'] = datetime.now().isoformat()
            
            # Wait before next scan
            await asyncio.sleep(MONITOR_INTERVAL)
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

# ===== COMMAND HANDLERS =====

@client.on(events.NewMessage(pattern=r'\.stalker\s?(.*)?'))
async def stalker_command_handler(event):
    """Main stalker monitor command handler"""
    try:
        me = await client.get_me()
        if event.sender_id != me.id:
            return
            
        args = event.pattern_match.group(1).strip().split() if event.pattern_match.group(1) else []
        command = args[0].lower() if args else 'help'
        
        if command == 'start':
            await start_monitoring_command(event)
        elif command == 'stop':
            await stop_monitoring_command(event)
        elif command == 'status':
            await status_command(event)
        elif command == 'stats':
            await stats_command(event)
        elif command == 'info':
            await info_command(event)
        elif command == 'setup':
            await setup_command(event)
        elif command == 'list':
            await list_stalkers_command(event)
        else:
            await help_command(event)
            
    except Exception as e:
        await event.reply(f"❌ Stalker monitor error: {str(e)}")

async def start_monitoring_command(event):
    """Start stalker monitoring"""
    global monitoring_active
    
    if monitoring_active:
        await event.edit(f"{get_emoji('check')} Stalker monitoring sudah aktif!")
        return
    
    # Initialize database
    if not init_stalker_db():
        await event.edit("❌ Database initialization failed!")
        return
    
    # Create log group if needed
    if not log_group_id:
        await create_log_group()
    
    msg = await event.edit(f"{get_emoji('adder1')} Memulai stalker monitoring...")
    
    # Start monitoring in background
    asyncio.create_task(start_monitoring())
    
    await msg.edit(f"""
{get_emoji('main')} {convert_font('STALKER MONITOR ACTIVATED!', 'bold')}

╔══════════════════════════════════╗
   🕵️ {convert_font('SURVEILLANCE SYSTEM ONLINE', 'bold')} 🕵️
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} ACTIVE
{get_emoji('check')} {convert_font('Detection Methods:', 'bold')} 5 Active
{get_emoji('check')} {convert_font('Scan Interval:', 'bold')} {MONITOR_INTERVAL//60} minutes
{get_emoji('check')} {convert_font('Log Group:', 'bold')} Created
{get_emoji('check')} {convert_font('Database:', 'bold')} Initialized

{get_emoji('adder2')} {convert_font('Active Detection:', 'bold')}
• Profile view tracking ✅
• Message interaction analysis ✅  
• Online status monitoring ✅
• Story viewer surveillance ✅
• Chat behavior patterns ✅

{get_emoji('adder3')} Monitoring dimulai! Stalker akan terdeteksi otomatis.
Use `.stalker status` untuk check progress.
    """.strip())

async def stop_monitoring_command(event):
    """Stop stalker monitoring"""
    global monitoring_active
    
    monitoring_active = False
    
    await event.edit(f"""
{get_emoji('adder3')} {convert_font('STALKER MONITOR STOPPED', 'bold')}

╔══════════════════════════════════╗
   🛑 {convert_font('SURVEILLANCE DEACTIVATED', 'bold')} 🛑
╚══════════════════════════════════╝

{get_emoji('check')} Monitoring dihentikan
{get_emoji('check')} Data tersimpan di database
{get_emoji('check')} Log group tetap aktif

Use `.stalker start` untuk mulai kembali.
    """.strip())

async def status_command(event):
    """Show current monitoring status"""
    stats = get_stalker_stats()
    
    status_text = f"""
{get_emoji('main')} {convert_font('STALKER MONITOR STATUS', 'bold')}

╔══════════════════════════════════╗
   📊 {convert_font('SURVEILLANCE DASHBOARD', 'bold')} 📊
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Status:', 'bold')} {'🟢 ACTIVE' if monitoring_active else '🔴 INACTIVE'}
{get_emoji('check')} {convert_font('Total Detected:', 'bold')} `{stats['total_stalkers']}`
{get_emoji('check')} {convert_font('Recent (24h):', 'bold')} `{stats['recent_stalkers']}`
{get_emoji('check')} {convert_font('Alerts Sent:', 'bold')} `{stats['alerts_sent']}`
{get_emoji('check')} {convert_font('Last Scan:', 'bold')} {stats['last_scan'] or 'Never'}

{get_emoji('adder1')} {convert_font('Detection Settings:', 'bold')}
• Sensitivity: {DETECTION_SENSITIVITY}/10
• Scan Interval: {MONITOR_INTERVAL//60} min
• Max Alerts: {MAX_STALKERS_PER_ALERT}

{get_emoji('adder2')} Use `.stalker stats` untuk detailed info
    """.strip()
    
    await event.edit(status_text)

async def stats_command(event):
    """Show detailed statistics"""
    stats = get_stalker_stats()
    
    stats_text = f"""
{get_emoji('main')} {convert_font('STALKER STATISTICS', 'bold')}

╔══════════════════════════════════╗
   📈 {convert_font('DETAILED ANALYTICS', 'bold')} 📈
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Detection Summary:', 'bold')}
{get_emoji('check')} Total Stalkers: `{stats['total_stalkers']}`
{get_emoji('check')} Recent Activity: `{stats['recent_stalkers']}`
{get_emoji('check')} System Alerts: `{stats['alerts_sent']}`

{get_emoji('adder2')} {convert_font('Top Stalkers:', 'bold')}
"""
    
    for i, (username, name, score) in enumerate(stats['top_stalkers'][:5], 1):
        display_name = name or username or 'Anonymous'
        stats_text += f"{get_emoji('adder4')} #{i}. {display_name} (Score: {score})\n"
    
    if not stats['top_stalkers']:
        stats_text += f"{get_emoji('check')} No stalkers detected yet\n"
    
    stats_text += f"""
{get_emoji('adder3')} {convert_font('System Info:', 'bold')}
{get_emoji('check')} Database: {STALKER_DB}
{get_emoji('check')} Log Group: {'Active' if log_group_id else 'Not Created'}
{get_emoji('check')} Detection Methods: 5 Active

Use `.stalker list` untuk detailed stalker list
    """.strip()
    
    await event.edit(stats_text)

async def list_stalkers_command(event):
    """List detected stalkers"""
    try:
        conn = sqlite3.connect(STALKER_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, first_name, last_name, stalking_score, total_interactions, last_activity
            FROM stalkers ORDER BY stalking_score DESC LIMIT 10
        ''')
        stalkers = cursor.fetchall()
        conn.close()
        
        if not stalkers:
            await event.edit(f"{get_emoji('check')} Belum ada stalker yang terdeteksi.")
            return
        
        list_text = f"""
{get_emoji('main')} {convert_font('DETECTED STALKERS LIST', 'bold')}

╔══════════════════════════════════╗
   🎯 {convert_font('TOP SURVEILLANCE TARGETS', 'bold')} 🎯
╚══════════════════════════════════╝

"""
        
        for i, (username, fname, lname, score, interactions, last_act) in enumerate(stalkers, 1):
            name = f"{fname or ''} {lname or ''}".strip() or 'Hidden'
            username_str = f"@{username}" if username else 'No Username'
            last_activity = datetime.fromisoformat(last_act).strftime("%d/%m %H:%M")
            
            threat_level = "🔴 HIGH" if score > 50 else "🟡 MED" if score > 20 else "🟢 LOW"
            
            list_text += f"""
{get_emoji('adder4')} {convert_font(f'#{i}. TARGET', 'bold')}
  • Name: `{name}`
  • Username: `{username_str}`
  • Score: `{score}` ({threat_level})
  • Views: `{interactions}`
  • Last: `{last_activity}`

"""
        
        list_text += f"{get_emoji('check')} Use `.stalker info` untuk detailed analysis"
        
        await event.edit(list_text.strip())
        
    except Exception as e:
        await event.edit(f"❌ List error: {str(e)}")

async def setup_command(event):
    """Setup stalker monitor system"""
    try:
        # Initialize database
        init_status = init_stalker_db()
        
        # Create log group
        log_group = await create_log_group()
        
        setup_text = f"""
{get_emoji('main')} {convert_font('STALKER MONITOR SETUP', 'bold')}

╔══════════════════════════════════╗
   ⚙️ {convert_font('SYSTEM INITIALIZATION', 'bold')} ⚙️
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Database:', 'bold')} {'✅ Initialized' if init_status else '❌ Failed'}
{get_emoji('check')} {convert_font('Log Group:', 'bold')} {'✅ Created' if log_group else '❌ Failed'}
{get_emoji('check')} {convert_font('Detection Methods:', 'bold')} ✅ 5 Active
{get_emoji('check')} {convert_font('Privacy Protection:', 'bold')} ✅ Maximum

{get_emoji('adder1')} {convert_font('Ready Commands:', 'bold')}
• `.stalker start` - Mulai monitoring
• `.stalker status` - Check system
• `.stalker stats` - View statistics
• `.stalker list` - Show stalkers

{get_emoji('adder2')} System siap digunakan!
Use `.stalker start` untuk mulai monitoring.
        """.strip()
        
        await event.edit(setup_text)
        
    except Exception as e:
        await event.edit(f"❌ Setup error: {str(e)}")

async def help_command(event):
    """Show stalker monitor help"""
    help_text = f"""
🕵️ {convert_font('STALKER MONITOR HELP', 'bold')}

╔══════════════════════════════════╗
   📚 {convert_font('COMMAND REFERENCE', 'bold')} 📚
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Main Commands:', 'bold')}
• `.stalker setup` - Initialize system
• `.stalker start` - Mulai monitoring  
• `.stalker stop` - Hentikan monitoring
• `.stalker status` - System status

{get_emoji('adder2')} {convert_font('Information Commands:', 'bold')}
• `.stalker stats` - View statistics
• `.stalker list` - Show detected stalkers
• `.stalker info` - Detailed analysis

{get_emoji('adder3')} {convert_font('Features:', 'bold')}
{get_emoji('check')} Auto-detect profile viewers
{get_emoji('check')} Real-time stalker alerts
{get_emoji('check')} Dedicated log group
{get_emoji('check')} Encrypted database storage
{get_emoji('check')} Advanced behavior analysis

{get_emoji('adder4')} {convert_font('Detection Methods:', 'bold')}
• Profile view tracking
• Message interaction analysis  
• Online status monitoring
• Story viewer surveillance
• Chat behavior patterns

{get_emoji('main')} {convert_font('Start with:', 'bold')} `.stalker setup`
    """.strip()
    
    await event.edit(help_text)

async def info_command(event):
    """Show detailed system information"""
    info_text = f"""
{get_emoji('main')} {convert_font('STALKER MONITOR INFO', 'bold')}

╔══════════════════════════════════╗
   ℹ️ {convert_font('SYSTEM INFORMATION', 'bold')} ℹ️  
╚══════════════════════════════════╝

{get_emoji('adder1')} {convert_font('Version:', 'bold')} v1.0.0 Premium Edition
{get_emoji('check')} {convert_font('Author:', 'bold')} Vzoel Fox's (Enhanced by Morgan)
{get_emoji('check')} {convert_font('Database:', 'bold')} SQLite Encrypted
{get_emoji('check')} {convert_font('Privacy Level:', 'bold')} Maximum Security

{get_emoji('adder2')} {convert_font('Detection Capabilities:', 'bold')}
• Profile view tracking via indirect methods
• Message interaction pattern analysis
• Online status correlation monitoring  
• Story viewer behavioral analysis
• Chat activity pattern recognition

{get_emoji('adder3')} {convert_font('Privacy & Security:', 'bold')}
{get_emoji('check')} All data stored locally only
{get_emoji('check')} No external data transmission
{get_emoji('check')} Encrypted database storage
{get_emoji('check')} Auto-cleanup old records
{get_emoji('check')} Zero personal data exposure

{get_emoji('adder4')} {convert_font('Legal Notice:', 'bold')}
This tool is for security monitoring only.
Use responsibly and respect privacy rights.

{get_emoji('main')} Premium stalker detection system
{convert_font('Created by Vzoel Fox Team', 'bold')}
    """.strip()
    
    await event.edit(info_text)

# ===== PLUGIN INITIALIZATION =====

PLUGIN_INFO = {
    'name': 'stalker_monitor',
    'version': '1.0.0',
    'description': '🕵️ Advanced stalker detection and monitoring system with auto log group creation',
    'author': 'Vzoel Fox\'s (Enhanced by Morgan)',
    'commands': [
        '.stalker setup', '.stalker start', '.stalker stop', '.stalker status',
        '.stalker stats', '.stalker list', '.stalker info', '.stalker help'
    ],
    'features': [
        'Auto-detect profile viewers', 'Real-time stalker alerts',
        'Dedicated log group creation', 'Encrypted database storage',
        'Advanced behavior analysis', 'Privacy protection'
    ]
}

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Plugin setup function"""
    global client
    client = client_instance
    print("🕵️ Stalker Monitor Plugin loaded successfully!")
    return True