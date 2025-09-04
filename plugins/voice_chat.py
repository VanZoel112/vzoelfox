"""
Voice Chat Plugin for VzoelFox
Supports premium emoji mapping and markdown formatting
"""

import asyncio
import logging
import yt_dlp
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Import voice manager
try:
    from voice_manager import get_voice_manager, initialize_voice_manager
    from config import EMOJI_MAPPING
    from utils import get_emoji, is_owner_check
except ImportError:
    def get_emoji(key: str) -> str:
        mappings = {
            'join': '🎤',
            'leave': '🚪', 
            'play': '▶️',
            'pause': '⏸️',
            'stop': '⏹️',
            'queue': '📝',
            'volume': '🔊',
            'success': '✅',
            'error': '❌',
            'info': 'ℹ️'
        }
        return mappings.get(key, '🎵')
    
    async def is_owner_check(user_id):
        return True

logger = logging.getLogger(__name__)

async def setup(bot):
    """Setup voice chat plugin"""
    try:
        success = await initialize_voice_manager(bot)
        if success:
            logger.info(f"{get_emoji('success')} Voice chat plugin initialized")
        else:
            logger.error(f"{get_emoji('error')} Failed to initialize voice chat")
    except Exception as e:
        logger.error(f"Voice chat setup error: {e}")

@events.register(events.NewMessage(pattern=r'\.vcjoin$'))
async def join_voice_chat(event):
    """Join voice chat command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm:
            await event.reply(f"{get_emoji('error')} Voice manager not initialized")
            return
        
        chat_id = event.chat_id
        
        status_msg = await event.reply(f"{get_emoji('info')} Joining voice chat...")
        
        success = await vm.join_voice_chat(chat_id)
        
        if success:
            await status_msg.edit(
                f"{get_emoji('join')} **Successfully joined voice chat!**\n"
                f"{get_emoji('info')} Ready to play music"
            )
        else:
            await status_msg.edit(f"{get_emoji('error')} Failed to join voice chat")
            
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")
        logger.error(f"Join voice chat error: {e}")

@events.register(events.NewMessage(pattern=r'\.vcleave$'))
async def leave_voice_chat(event):
    """Leave voice chat command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm:
            await event.reply(f"{get_emoji('error')} Voice manager not initialized")
            return
        
        chat_id = event.chat_id
        
        if not vm.is_connected(chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        status_msg = await event.reply(f"{get_emoji('info')} Leaving voice chat...")
        
        success = await vm.leave_voice_chat(chat_id)
        
        if success:
            await status_msg.edit(f"{get_emoji('leave')} Left voice chat successfully")
        else:
            await status_msg.edit(f"{get_emoji('error')} Failed to leave voice chat")
            
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")
        logger.error(f"Leave voice chat error: {e}")

@events.register(events.NewMessage(pattern=r'\.vcplay(?:\s+(.+))?$'))
async def play_music(event):
    """Play music command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm:
            await event.reply(f"{get_emoji('error')} Voice manager not initialized")
            return
        
        chat_id = event.chat_id
        query = event.pattern_match.group(1)
        
        if not query:
            await event.reply(
                f"{get_emoji('info')} **Usage:** `.vcplay <YouTube URL or search>`\n"
                f"{get_emoji('info')} **Example:** `.vcplay Rick Astley Never Gonna Give You Up`"
            )
            return
        
        if not vm.is_connected(chat_id):
            await event.reply(f"{get_emoji('info')} Joining voice chat first...")
            if not await vm.join_voice_chat(chat_id):
                await event.reply(f"{get_emoji('error')} Failed to join voice chat")
                return
        
        status_msg = await event.reply(f"{get_emoji('info')} Processing: `{query}`...")
        
        # Extract audio URL using yt-dlp
        audio_url, title = await extract_audio_info(query)
        
        if not audio_url:
            await status_msg.edit(f"{get_emoji('error')} Could not extract audio from: {query}")
            return
        
        await status_msg.edit(f"{get_emoji('info')} Playing: **{title}**...")
        
        success = await vm.play_audio(chat_id, audio_url, title)
        
        if success:
            await status_msg.edit(
                f"{get_emoji('play')} **Now Playing:**\n"
                f"{get_emoji('info')} `{title}`\n"
                f"{get_emoji('info')} Use `.vcstop` to stop, `.vcpause` to pause"
            )
        else:
            await status_msg.edit(f"{get_emoji('error')} Failed to play: {title}")
            
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")
        logger.error(f"Play music error: {e}")

@events.register(events.NewMessage(pattern=r'\.vcpause$'))
async def pause_music(event):
    """Pause music command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm or not vm.is_connected(event.chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        success = await vm.pause_audio(event.chat_id)
        
        if success:
            await event.reply(f"{get_emoji('pause')} Music paused")
        else:
            await event.reply(f"{get_emoji('error')} Failed to pause music")
            
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcresume$'))
async def resume_music(event):
    """Resume music command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm or not vm.is_connected(event.chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        success = await vm.resume_audio(event.chat_id)
        
        if success:
            await event.reply(f"{get_emoji('play')} Music resumed")
        else:
            await event.reply(f"{get_emoji('error')} Failed to resume music")
            
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcstop$'))
async def stop_music(event):
    """Stop music command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm or not vm.is_connected(event.chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        success = await vm.stop_audio(event.chat_id)
        
        if success:
            await event.reply(f"{get_emoji('stop')} Music stopped")
        else:
            await event.reply(f"{get_emoji('error')} Failed to stop music")
            
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcvolume(?:\s+(\d+))?$'))
async def set_volume(event):
    """Set volume command"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm or not vm.is_connected(event.chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        volume_str = event.pattern_match.group(1)
        if not volume_str:
            info = vm.get_voice_chat_info(event.chat_id)
            current_volume = info.get('volume', 100) if info else 100
            await event.reply(
                f"{get_emoji('volume')} **Current Volume:** {current_volume}%\n"
                f"{get_emoji('info')} **Usage:** `.vcvolume <0-200>`"
            )
            return
        
        volume = int(volume_str)
        success = await vm.set_volume(event.chat_id, volume)
        
        if success:
            await event.reply(f"{get_emoji('volume')} Volume set to {volume}%")
        else:
            await event.reply(f"{get_emoji('error')} Failed to set volume")
            
    except ValueError:
        await event.reply(f"{get_emoji('error')} Invalid volume value")
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcstatus$'))
async def voice_chat_status(event):
    """Show voice chat status"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm:
            await event.reply(f"{get_emoji('error')} Voice manager not initialized")
            return
        
        chat_id = event.chat_id
        
        if not vm.is_connected(chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        info = vm.get_voice_chat_info(chat_id)
        queue = vm.get_queue(chat_id)
        
        status_text = (
            f"{get_emoji('info')} **Voice Chat Status**\n"
            f"{get_emoji('play')} **Status:** {info.get('status', 'unknown').title()}\n"
            f"{get_emoji('info')} **Current Track:** {info.get('current_track', 'None')}\n"
            f"{get_emoji('volume')} **Volume:** {info.get('volume', 100)}%\n"
            f"{get_emoji('queue')} **Queue:** {len(queue)} tracks"
        )
        
        await event.reply(status_text)
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

async def extract_audio_info(query: str):
    """Extract audio URL and title from YouTube"""
    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]',
            'noplaylist': True,
            'quiet': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if query.startswith(('http://', 'https://')):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                info = info['entries'][0] if info['entries'] else None
            
            if info:
                return info.get('url'), info.get('title', 'Unknown')
            return None, None
            
    except Exception as e:
        logger.error(f"YouTube extraction error: {e}")
        return None, None

# Command list for help system
COMMAND_LIST = [
    ("vcjoin", "Join voice chat"),
    ("vcleave", "Leave voice chat"), 
    ("vcplay <query>", "Play music from YouTube"),
    ("vcpause", "Pause current track"),
    ("vcresume", "Resume current track"),
    ("vcstop", "Stop current track"),
    ("vcvolume [0-200]", "Set or check volume"),
    ("vcstatus", "Show voice chat status")
]