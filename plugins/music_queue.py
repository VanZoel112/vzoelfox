"""
Music Queue Management Plugin for VzoelFox
Advanced queue system dengan premium emoji support
"""

import asyncio
import logging
from typing import List, Dict, Any
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji

# Import voice manager dan utilities
try:
    from voice_manager import get_voice_manager
    from config import EMOJI_MAPPING
    from utils import get_emoji, is_owner_check
except ImportError:
    def get_emoji(key: str) -> str:
        mappings = {
            'queue': '📝',
            'play': '▶️',
            'skip': '⏭️',
            'clear': '🗑️',
            'shuffle': '🔀',
            'loop': '🔁',
            'success': '✅',
            'error': '❌',
            'info': 'ℹ️',
            'music': '🎵'
        }
        return mappings.get(key, '🎵')
    
    async def is_owner_check(user_id):
        return True

logger = logging.getLogger(__name__)

# Queue management system
music_queues: Dict[int, List[Dict[str, Any]]] = {}
queue_settings: Dict[int, Dict[str, Any]] = {}

@events.register(events.NewMessage(pattern=r'\.vcqueue(?:\s+(.+))?$'))
async def manage_queue(event):
    """Queue management command"""
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
            await show_queue(event, chat_id, vm)
            return
        
        # Add to queue
        status_msg = await event.reply(f"{get_emoji('info')} Adding to queue: `{query}`...")
        
        from plugins.voice_chat import extract_audio_info
        audio_url, title = await extract_audio_info(query)
        
        if not audio_url:
            await status_msg.edit(f"{get_emoji('error')} Could not extract audio: {query}")
            return
        
        # Initialize queue if needed
        if chat_id not in music_queues:
            music_queues[chat_id] = []
        
        # Add to queue
        track_info = {
            'source': audio_url,
            'title': title,
            'query': query
        }
        
        music_queues[chat_id].append(track_info)
        vm.add_to_queue(chat_id, audio_url, title)
        
        queue_pos = len(music_queues[chat_id])
        
        await status_msg.edit(
            f"{get_emoji('queue')} **Added to Queue:**\n"
            f"{get_emoji('music')} `{title}`\n" 
            f"{get_emoji('info')} **Position:** {queue_pos}"
        )
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")
        logger.error(f"Queue management error: {e}")

@events.register(events.NewMessage(pattern=r'\.vcskip$'))
async def skip_track(event):
    """Skip current track"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        vm = get_voice_manager()
        if not vm or not vm.is_connected(event.chat_id):
            await event.reply(f"{get_emoji('info')} Not connected to voice chat")
            return
        
        chat_id = event.chat_id
        
        # Stop current track
        await vm.stop_audio(chat_id)
        
        # Play next in queue
        if await vm.play_next(chat_id):
            # Get current playing info
            info = vm.get_voice_chat_info(chat_id)
            current_track = info.get('current_track', 'Unknown') if info else 'Unknown'
            
            await event.reply(
                f"{get_emoji('skip')} **Skipped to next track:**\n"
                f"{get_emoji('play')} `{current_track}`"
            )
        else:
            await event.reply(f"{get_emoji('info')} Queue is empty - stopped playback")
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcclear$'))
async def clear_queue(event):
    """Clear music queue"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat_id = event.chat_id
        
        if chat_id in music_queues:
            queue_length = len(music_queues[chat_id])
            music_queues[chat_id].clear()
        else:
            queue_length = 0
        
        # Clear voice manager queue too
        vm = get_voice_manager()
        if vm:
            vm.music_queue[chat_id] = []
        
        await event.reply(
            f"{get_emoji('clear')} **Queue cleared**\n"
            f"{get_emoji('info')} Removed {queue_length} tracks"
        )
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcshuffle$'))
async def shuffle_queue(event):
    """Shuffle music queue"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat_id = event.chat_id
        
        if chat_id not in music_queues or not music_queues[chat_id]:
            await event.reply(f"{get_emoji('info')} Queue is empty")
            return
        
        import random
        random.shuffle(music_queues[chat_id])
        
        # Update voice manager queue
        vm = get_voice_manager()
        if vm and chat_id in vm.music_queue:
            random.shuffle(vm.music_queue[chat_id])
        
        await event.reply(
            f"{get_emoji('shuffle')} **Queue shuffled**\n"
            f"{get_emoji('queue')} {len(music_queues[chat_id])} tracks randomized"
        )
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcloop$'))
async def toggle_loop(event):
    """Toggle loop mode"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat_id = event.chat_id
        
        if chat_id not in queue_settings:
            queue_settings[chat_id] = {'loop': False}
        
        queue_settings[chat_id]['loop'] = not queue_settings[chat_id].get('loop', False)
        loop_status = queue_settings[chat_id]['loop']
        
        status_text = "enabled" if loop_status else "disabled"
        
        await event.reply(
            f"{get_emoji('loop')} **Loop mode {status_text}**\n"
            f"{get_emoji('info')} Queue will {'repeat' if loop_status else 'stop when empty'}"
        )
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

@events.register(events.NewMessage(pattern=r'\.vcremove(?:\s+(\d+))?$'))
async def remove_from_queue(event):
    """Remove track from queue by position"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        chat_id = event.chat_id
        position_str = event.pattern_match.group(1)
        
        if not position_str:
            await event.reply(
                f"{get_emoji('info')} **Usage:** `.vcremove <position>`\n"
                f"{get_emoji('info')} Use `.vcqueue` to see track positions"
            )
            return
        
        position = int(position_str) - 1  # Convert to 0-based index
        
        if chat_id not in music_queues or not music_queues[chat_id]:
            await event.reply(f"{get_emoji('info')} Queue is empty")
            return
        
        if position < 0 or position >= len(music_queues[chat_id]):
            await event.reply(f"{get_emoji('error')} Invalid position: {position + 1}")
            return
        
        removed_track = music_queues[chat_id].pop(position)
        
        # Update voice manager queue
        vm = get_voice_manager()
        if vm and chat_id in vm.music_queue and position < len(vm.music_queue[chat_id]):
            vm.music_queue[chat_id].pop(position)
        
        await event.reply(
            f"{get_emoji('clear')} **Removed from queue:**\n"
            f"{get_emoji('music')} `{removed_track['title']}`"
        )
        
    except ValueError:
        await event.reply(f"{get_emoji('error')} Invalid position number")
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error: {str(e)}")

async def show_queue(event, chat_id: int, vm):
    """Show current queue"""
    try:
        if chat_id not in music_queues or not music_queues[chat_id]:
            await event.reply(
                f"{get_emoji('info')} **Queue is empty**\n"
                f"{get_emoji('info')} Use `.vcqueue <search>` to add tracks"
            )
            return
        
        queue = music_queues[chat_id]
        
        # Get current playing track
        info = vm.get_voice_chat_info(chat_id) if vm else None
        current_track = info.get('current_track') if info else None
        
        # Build queue display
        queue_text = f"{get_emoji('queue')} **Music Queue ({len(queue)} tracks)**\n\n"
        
        if current_track:
            queue_text += f"{get_emoji('play')} **Now Playing:** `{current_track}`\n\n"
        
        queue_text += f"{get_emoji('info')} **Up Next:**\n"
        
        for i, track in enumerate(queue[:10], 1):  # Show first 10 tracks
            queue_text += f"`{i}.` {track['title']}\n"
        
        if len(queue) > 10:
            queue_text += f"\n{get_emoji('info')} ...and {len(queue) - 10} more tracks"
        
        # Add queue settings
        settings = queue_settings.get(chat_id, {})
        if settings.get('loop'):
            queue_text += f"\n\n{get_emoji('loop')} Loop mode enabled"
        
        await event.reply(queue_text)
        
    except Exception as e:
        await event.reply(f"{get_emoji('error')} Error showing queue: {str(e)}")

async def auto_play_next(chat_id: int):
    """Automatically play next track when current ends"""
    try:
        vm = get_voice_manager()
        if not vm or not vm.is_connected(chat_id):
            return
        
        # Check loop setting
        settings = queue_settings.get(chat_id, {})
        if settings.get('loop') and chat_id in music_queues:
            # If loop enabled and queue exists, add current track back to end
            info = vm.get_voice_chat_info(chat_id)
            if info and info.get('current_track'):
                # Re-add current track to queue for loop
                pass  # Implementation would depend on specific loop behavior needed
        
        # Play next track
        await vm.play_next(chat_id)
        
    except Exception as e:
        logger.error(f"Auto play next error: {e}")

# Command list for help system
COMMAND_LIST = [
    ("vcqueue [search]", "Show queue or add track to queue"),
    ("vcskip", "Skip to next track in queue"),
    ("vcclear", "Clear entire music queue"),
    ("vcshuffle", "Shuffle current queue"),
    ("vcloop", "Toggle queue loop mode"),
    ("vcremove <position>", "Remove track from queue by position")
]