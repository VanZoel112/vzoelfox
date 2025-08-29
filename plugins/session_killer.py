"""
Session Killer Plugin for Vzoel Assistant - SECURITY MODULE
Fitur: Terminate unauthorized sessions menggunakan akun kita, defensive security
Author: Vzoel Fox's (Enhanced by Morgan)  
Version: 1.0.0 - Session Management & Security
"""

import os
import logging
import asyncio
from datetime import datetime
from telethon import events
from telethon.tl.functions.auth import LogOutRequest
from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest
from telethon.errors import SessionPasswordNeededError, FloodWaitError

# Plugin Info
PLUGIN_INFO = {
    "name": "session_killer",
    "version": "1.0.0", 
    "description": "Defensive session management - terminate unauthorized access to your Telegram account",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".sessions", ".killsession", ".killall", ".checksec"],
    "features": ["session listing", "selective termination", "mass termination", "security audit"]
}

# Global variables
client = None
logger = None

# Premium Emoji Mapping (Independent)
PREMIUM_EMOJIS = {
    'main':     {'id': '6156784006194009426', 'char': '🤩'},
    'check':    {'id': '5794353925360457382', 'char': '⚙️'},
    'warning':  {'id': '5794407002566300853', 'char': '⛈'},
    'success':  {'id': '5793913811471700779', 'char': '✅'},
    'security': {'id': '5321412209992033736', 'char': '👽'},
    'kill':     {'id': '5793973133559993740', 'char': '✈️'},
    'danger':   {'id': '5357404860566235955', 'char': '😈'},
    'monitor':  {'id': '5794323465452394551', 'char': '🎚️'}
}

def setup_logger():
    """Setup dedicated logger"""
    global logger
    logger = logging.getLogger("session_killer_plugin")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

def get_emoji(emoji_type):
    """Get premium emoji dari mapping independent"""
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def convert_font(text, font_type='bold'):
    """Convert text to Unicode fonts"""
    if font_type == 'bold':
        bold_map = {
            'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
            'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
            's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
            'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
            'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
            '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
        }
        return ''.join([bold_map.get(c, c) for c in text])
    elif font_type == 'mono':
        mono_map = {
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
            'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
            's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
            'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
            'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉'
        }
        return ''.join([mono_map.get(c, c) for c in text])
    return text

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        OWNER_ID = os.getenv('OWNER_ID')
        if OWNER_ID:
            return user_id == int(OWNER_ID)
        if client:
            me = await client.get_me()
            return user_id == me.id
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Owner check error: {e}")
    return False

async def get_active_sessions():
    """Get list of active sessions"""
    try:
        if not client:
            return None
        
        authorizations = await client(GetAuthorizationsRequest())
        return authorizations.authorizations
    except FloodWaitError as e:
        if logger:
            logger.warning(f"[SessionKiller] Rate limited, wait {e.seconds}s")
        return None
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Error getting sessions: {e}")
        return None

async def format_session_info(auth):
    """Format session information"""
    try:
        device = getattr(auth, 'device_model', 'Unknown Device')
        platform = getattr(auth, 'platform', 'Unknown Platform')
        app_name = getattr(auth, 'app_name', 'Unknown App')
        app_version = getattr(auth, 'app_version', '?')
        location = getattr(auth, 'country', 'Unknown Location')
        date_created = getattr(auth, 'date_created', None)
        date_active = getattr(auth, 'date_active', None)
        current = getattr(auth, 'current', False)
        hash_val = getattr(auth, 'hash', 0)
        
        status_emoji = get_emoji('success') if current else get_emoji('warning')
        status_text = "Current Session" if current else "Remote Session"
        
        date_str = ""
        if date_created:
            date_str = f"\n{get_emoji('monitor')} Created: {date_created.strftime('%Y-%m-%d %H:%M')}"
        if date_active:
            date_str += f"\n{get_emoji('check')} Last Active: {date_active.strftime('%Y-%m-%d %H:%M')}"
        
        return f"""
{status_emoji} {convert_font(status_text, 'bold')}
{get_emoji('security')} Hash: `{hash_val}`
{get_emoji('check')} Device: `{device}`
{get_emoji('check')} Platform: `{platform}`  
{get_emoji('check')} App: `{app_name} v{app_version}`
{get_emoji('check')} Location: `{location}`{date_str}
        """.strip()
        
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Error formatting session: {e}")
        return f"{get_emoji('warning')} Error formatting session info"

async def sessions_handler(event):
    """Handle .sessions command"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        if logger:
            logger.info(f"[SessionKiller] Sessions check requested by user {event.sender_id}")
        
        # Show loading message
        loading_msg = await event.reply(f"{get_emoji('monitor')} {convert_font('Fetching active sessions...', 'mono')}")
        
        sessions = await get_active_sessions()
        
        if sessions is None:
            await loading_msg.edit(f"{get_emoji('warning')} {convert_font('Failed to fetch sessions!', 'bold')}")
            return
        
        if not sessions:
            await loading_msg.edit(f"{get_emoji('check')} {convert_font('No active sessions found.', 'bold')}")
            return
        
        # Format session list
        session_list = []
        current_session = None
        remote_sessions = []
        
        for i, auth in enumerate(sessions):
            session_info = await format_session_info(auth)
            if getattr(auth, 'current', False):
                current_session = f"{get_emoji('main')} {convert_font('SESSION 0 (CURRENT)', 'bold')}\n{session_info}"
            else:
                remote_sessions.append(f"{get_emoji('danger')} {convert_font(f'SESSION {i+1}', 'bold')}\n{session_info}")
        
        # Build response
        response_parts = [
            f"{get_emoji('security')} {convert_font('ACTIVE TELEGRAM SESSIONS', 'bold')}\n"
        ]
        
        if current_session:
            response_parts.append(current_session)
        
        if remote_sessions:
            response_parts.append(f"\n{get_emoji('warning')} {convert_font('REMOTE SESSIONS:', 'bold')}")
            response_parts.extend(remote_sessions)
            response_parts.append(f"\n{get_emoji('kill')} Use `.killsession <hash>` to terminate specific session")
            response_parts.append(f"{get_emoji('danger')} Use `.killall` to terminate ALL remote sessions")
        else:
            response_parts.append(f"\n{get_emoji('success')} {convert_font('No remote sessions detected', 'bold')}")
        
        response_parts.append(f"\n{get_emoji('check')} Use `.checksec` for security audit")
        
        full_response = "\n".join(response_parts)
        
        # Split if too long
        if len(full_response) > 4000:
            await loading_msg.edit(response_parts[0] + response_parts[1] if current_session else response_parts[0])
            if remote_sessions:
                remote_text = "\n".join([response_parts[2]] + remote_sessions[:3] + [f"... and {len(remote_sessions)-3} more sessions"])
                await event.reply(remote_text)
        else:
            await loading_msg.edit(full_response)
        
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Sessions handler error: {e}")
        await event.reply(f"{get_emoji('warning')} {convert_font('Error fetching sessions!', 'bold')}")

async def kill_session_handler(event):
    """Handle .killsession command"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        args = event.text.split()
        if len(args) < 2:
            await event.reply(f"{get_emoji('warning')} {convert_font('Usage: .killsession <hash>', 'mono')}")
            return
        
        try:
            session_hash = int(args[1])
        except ValueError:
            await event.reply(f"{get_emoji('warning')} {convert_font('Invalid hash format!', 'bold')}")
            return
        
        if logger:
            logger.info(f"[SessionKiller] Kill session {session_hash} requested by user {event.sender_id}")
        
        loading_msg = await event.reply(f"{get_emoji('kill')} {convert_font('Terminating session...', 'mono')}")
        
        try:
            await client(ResetAuthorizationRequest(hash=session_hash))
            await loading_msg.edit(f"{get_emoji('success')} {convert_font('Session terminated successfully!', 'bold')}\n{get_emoji('security')} Hash: `{session_hash}`")
            
            if logger:
                logger.info(f"[SessionKiller] Session {session_hash} terminated successfully")
                
        except FloodWaitError as e:
            await loading_msg.edit(f"{get_emoji('warning')} {convert_font('Rate limited!', 'bold')} Wait {e.seconds}s")
        except Exception as e:
            await loading_msg.edit(f"{get_emoji('warning')} {convert_font('Failed to terminate session!', 'bold')}\n{convert_font(str(e), 'mono')}")
            if logger:
                logger.error(f"[SessionKiller] Kill session error: {e}")
    
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Kill session handler error: {e}")
        await event.reply(f"{get_emoji('warning')} {convert_font('Command error!', 'bold')}")

async def kill_all_handler(event):
    """Handle .killall command"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        if logger:
            logger.info(f"[SessionKiller] Kill all sessions requested by user {event.sender_id}")
        
        loading_msg = await event.reply(f"{get_emoji('danger')} {convert_font('Fetching sessions for mass termination...', 'mono')}")
        
        sessions = await get_active_sessions()
        
        if sessions is None:
            await loading_msg.edit(f"{get_emoji('warning')} {convert_font('Failed to fetch sessions!', 'bold')}")
            return
        
        # Filter remote sessions only
        remote_sessions = [auth for auth in sessions if not getattr(auth, 'current', False)]
        
        if not remote_sessions:
            await loading_msg.edit(f"{get_emoji('check')} {convert_font('No remote sessions to terminate.', 'bold')}")
            return
        
        await loading_msg.edit(f"{get_emoji('kill')} {convert_font(f'Terminating {len(remote_sessions)} remote sessions...', 'mono')}")
        
        success_count = 0
        failed_count = 0
        
        for auth in remote_sessions:
            try:
                session_hash = getattr(auth, 'hash', 0)
                await client(ResetAuthorizationRequest(hash=session_hash))
                success_count += 1
                await asyncio.sleep(1)  # Prevent rate limiting
                
            except FloodWaitError as e:
                if logger:
                    logger.warning(f"[SessionKiller] Rate limited during mass kill: {e.seconds}s")
                await asyncio.sleep(e.seconds)
                failed_count += 1
            except Exception as e:
                if logger:
                    logger.error(f"[SessionKiller] Error killing session {getattr(auth, 'hash', 0)}: {e}")
                failed_count += 1
        
        result_text = f"""
{get_emoji('success')} {convert_font('MASS TERMINATION COMPLETE!', 'bold')}

{get_emoji('kill')} Terminated: {convert_font(str(success_count), 'mono')} sessions
{get_emoji('warning')} Failed: {convert_font(str(failed_count), 'mono')} sessions

{get_emoji('security')} {convert_font('Your account security has been enhanced!', 'bold')}
{get_emoji('check')} Use `.sessions` to verify results
        """.strip()
        
        await loading_msg.edit(result_text)
        
        if logger:
            logger.info(f"[SessionKiller] Mass termination completed: {success_count} success, {failed_count} failed")
    
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Kill all handler error: {e}")
        await event.reply(f"{get_emoji('warning')} {convert_font('Mass termination error!', 'bold')}")

async def checksec_handler(event):
    """Handle .checksec command - security audit"""
    try:
        if not await is_owner_check(event.sender_id):
            return
        
        loading_msg = await event.reply(f"{get_emoji('monitor')} {convert_font('Running security audit...', 'mono')}")
        
        sessions = await get_active_sessions()
        
        if sessions is None:
            await loading_msg.edit(f"{get_emoji('warning')} {convert_font('Security audit failed!', 'bold')}")
            return
        
        # Analyze sessions
        total_sessions = len(sessions)
        current_sessions = len([s for s in sessions if getattr(s, 'current', False)])
        remote_sessions = total_sessions - current_sessions
        
        # Check for suspicious patterns
        suspicious_apps = []
        unknown_devices = []
        old_sessions = []
        
        for auth in sessions:
            app_name = getattr(auth, 'app_name', '').lower()
            device = getattr(auth, 'device_model', '').lower()
            date_active = getattr(auth, 'date_active', None)
            
            # Check for suspicious apps
            if any(sus in app_name for sus in ['userbot', 'telegram-userbot', 'pyrogram', 'telethon']):
                suspicious_apps.append(auth)
            
            # Check for unknown devices
            if 'unknown' in device or device == '':
                unknown_devices.append(auth)
            
            # Check for old sessions (no recent activity)
            if date_active:
                days_inactive = (datetime.now() - date_active).days
                if days_inactive > 30:
                    old_sessions.append((auth, days_inactive))
        
        # Generate security report
        risk_level = "LOW"
        if remote_sessions > 5 or suspicious_apps or len(unknown_devices) > 2:
            risk_level = "HIGH"
        elif remote_sessions > 2 or unknown_devices or old_sessions:
            risk_level = "MEDIUM"
        
        risk_emoji = get_emoji('success') if risk_level == 'LOW' else get_emoji('warning') if risk_level == 'MEDIUM' else get_emoji('danger')
        
        report = f"""
{get_emoji('security')} {convert_font('SECURITY AUDIT REPORT', 'bold')}

{get_emoji('check')} {convert_font('Session Summary:', 'bold')}
• Total Sessions: {convert_font(str(total_sessions), 'mono')}
• Current Sessions: {convert_font(str(current_sessions), 'mono')}  
• Remote Sessions: {convert_font(str(remote_sessions), 'mono')}

{risk_emoji} {convert_font('Risk Level:', 'bold')} {convert_font(risk_level, 'bold')}

{get_emoji('warning')} {convert_font('Security Findings:', 'bold')}
• Suspicious Apps: {convert_font(str(len(suspicious_apps)), 'mono')}
• Unknown Devices: {convert_font(str(len(unknown_devices)), 'mono')}
• Inactive Sessions (30+ days): {convert_font(str(len(old_sessions)), 'mono')}
        """.strip()
        
        # Add recommendations
        if risk_level != 'LOW':
            report += f"\n\n{get_emoji('kill')} {convert_font('Recommendations:', 'bold')}"
            
            if suspicious_apps:
                report += f"\n• Terminate suspicious userbot sessions immediately"
            if remote_sessions > 3:
                report += f"\n• Consider terminating unused remote sessions"
            if old_sessions:
                report += f"\n• Clean up inactive sessions"
                
            report += f"\n\n{get_emoji('danger')} Use `.killall` to terminate all remote sessions"
        else:
            report += f"\n\n{get_emoji('success')} {convert_font('Account security looks good!', 'bold')}"
        
        await loading_msg.edit(report)
        
        if logger:
            logger.info(f"[SessionKiller] Security audit completed - Risk: {risk_level}")
    
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Security audit error: {e}")
        await event.reply(f"{get_emoji('warning')} {convert_font('Security audit failed!', 'bold')}")

def get_plugin_info():
    return PLUGIN_INFO

def setup(telegram_client):
    global client, logger
    setup_logger()
    
    try:
        client = telegram_client
        if client:
            # Register event handlers
            client.add_event_handler(sessions_handler, events.NewMessage(pattern=r'\.sessions$'))
            client.add_event_handler(kill_session_handler, events.NewMessage(pattern=r'\.killsession'))  
            client.add_event_handler(kill_all_handler, events.NewMessage(pattern=r'\.killall$'))
            client.add_event_handler(checksec_handler, events.NewMessage(pattern=r'\.checksec$'))
            
            if logger:
                logger.info("[SessionKiller] Plugin setup completed - Defensive security module active")
        return True
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Setup error: {e}")
        return False

def cleanup_plugin():
    global client, logger
    try:
        if logger:
            logger.info("[SessionKiller] Plugin cleanup initiated")
        client = None
        if logger:
            logger.info("[SessionKiller] Plugin cleanup completed")
    except Exception as e:
        if logger:
            logger.error(f"[SessionKiller] Cleanup error: {e}")

__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'is_owner_check', 'get_emoji', 'convert_font', 'PREMIUM_EMOJIS']