#!/usr/bin/env python3
"""
VzoelFox Music System - Complete Rebuild v3.0.0
Fitur: .play untuk streaming preview, .download untuk full download
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 3.0.0 - Total Rework
"""

import os
import asyncio
import subprocess
import glob
import shutil
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, DocumentAttributeAudio

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "music_system",
    "version": "3.0.0",
    "description": "Complete music system: .play for preview, .download for full download",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩", 
    "commands": [".play <song>", ".download <song>", ".musicstatus"],
    "features": ["music preview", "full download", "multiple formats", "premium emoji"]
}

# ===== PREMIUM EMOJI CONFIGURATION =====
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

def get_emoji(emoji_type):
    """Get premium emoji character"""
    return PREMIUM_EMOJIS.get(emoji_type, {}).get('char', '🤩')

def create_premium_entities(text):
    """Create premium emoji entities for text with UTF-16 support"""
    try:
        entities = []
        current_offset = 0
        i = 0
        
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

async def safe_send_premium(event, text, file=None):
    """Send message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities and file:
            return await event.reply(text, formatting_entities=entities, file=file)
        elif entities:
            return await event.reply(text, formatting_entities=entities)
        elif file:
            return await event.reply(text, file=file)
        else:
            return await event.reply(text)
    except Exception:
        if file:
            return await event.reply(text, file=file)
        else:
            return await event.reply(text)

async def safe_edit_premium(message, text):
    """Edit message with premium entities"""
    try:
        entities = create_premium_entities(text)
        if entities:
            return await message.edit(text, formatting_entities=entities)
        else:
            return await message.edit(text)
    except Exception:
        return await message.edit(text)

# Configuration
TEMP_DIR = os.path.expanduser("~/vzoelfox/temp/music")
DOWNLOAD_DIR = os.path.expanduser("~/vzoelfox/downloads/music")

def ensure_directories():
    """Ensure all directories exist"""
    for directory in [TEMP_DIR, DOWNLOAD_DIR]:
        os.makedirs(directory, exist_ok=True)

async def check_ytdlp():
    """Check if yt-dlp is available"""
    try:
        result = await asyncio.create_subprocess_exec(
            'yt-dlp', '--version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode == 0:
            version = stdout.decode().strip()
            return {'available': True, 'version': version}
        else:
            return {'available': False, 'error': 'Command failed'}
    except Exception as e:
        return {'available': False, 'error': str(e)}

async def search_youtube(query):
    """Search YouTube and get basic info"""
    try:
        cmd = [
            'yt-dlp',
            '--get-title',
            '--get-duration', 
            '--get-id',
            '--no-playlist',
            f'ytsearch1:{query}'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            lines = stdout.decode().strip().split('\n')
            if len(lines) >= 3:
                return {
                    'success': True,
                    'title': lines[0],
                    'duration': lines[1],
                    'video_id': lines[2],
                    'url': f'https://youtube.com/watch?v={lines[2]}'
                }
        
        return {
            'success': False,
            'error': 'Search failed or no results found'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Search error: {str(e)}'
        }

async def download_music_preview(query):
    """Download short preview (30 seconds) for .play command"""
    try:
        ensure_directories()
        
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '128K',
            '--postprocessor-args', 'ffmpeg:-t 30',  # 30 seconds only
            '--output', f'{TEMP_DIR}/preview_%(title)s.%(ext)s',
            '--no-playlist',
            f'ytsearch1:{query}'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Find the preview file
            preview_files = glob.glob(f"{TEMP_DIR}/preview_*.mp3")
            if preview_files:
                newest_file = max(preview_files, key=os.path.getmtime)
                title = os.path.basename(newest_file).replace('preview_', '').replace('.mp3', '')
                size = os.path.getsize(newest_file)
                
                return {
                    'success': True,
                    'file_path': newest_file,
                    'title': title,
                    'size': size,
                    'type': 'preview'
                }
        
        return {
            'success': False,
            'error': f'Preview download failed: {stderr.decode() if stderr else "Unknown error"}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Preview error: {str(e)}'
        }

async def download_music_full(query):
    """Download full song for .download command"""
    try:
        ensure_directories()
        
        # Method 1: High quality MP3
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '320K',
            '--output', f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            '--no-playlist',
            f'ytsearch1:{query}'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Find downloaded file
            audio_files = glob.glob(f"{DOWNLOAD_DIR}/*.mp3")
            if audio_files:
                newest_file = max(audio_files, key=os.path.getmtime)
                title = os.path.basename(newest_file).replace('.mp3', '')
                size = os.path.getsize(newest_file)
                
                return {
                    'success': True,
                    'file_path': newest_file,
                    'title': title,
                    'size': size,
                    'type': 'full',
                    'format': 'MP3 320K'
                }
        
        # Method 2: Best audio available
        cmd_fallback = [
            'yt-dlp',
            '--format', 'bestaudio/best',
            '--output', f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            '--no-playlist',
            f'ytsearch1:{query}'
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd_fallback,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Find any audio file
            audio_exts = ['.mp3', '.webm', '.m4a', '.ogg', '.opus']
            audio_files = []
            for ext in audio_exts:
                audio_files.extend(glob.glob(f"{DOWNLOAD_DIR}/*{ext}"))
            
            if audio_files:
                newest_file = max(audio_files, key=os.path.getmtime)
                title = os.path.basename(newest_file).split('.')[0]
                size = os.path.getsize(newest_file)
                ext = os.path.splitext(newest_file)[1].upper()
                
                return {
                    'success': True,
                    'file_path': newest_file,
                    'title': title,
                    'size': size,
                    'type': 'full',
                    'format': f'{ext} Best Quality'
                }
        
        return {
            'success': False,
            'error': f'Full download failed: {stderr.decode() if stderr else "All methods failed"}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Download error: {str(e)}'
        }

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        if client:
            me = await client.get_me()
            return user_id == me.id
            
        OWNER_ID = 7847025168  # Replace with actual owner ID
        return user_id == OWNER_ID
    except Exception:
        return True

def cleanup_old_files():
    """Clean up old temporary files"""
    try:
        # Clean temp files older than 1 hour
        temp_files = glob.glob(f"{TEMP_DIR}/*")
        for file in temp_files:
            if os.path.getmtime(file) < (datetime.now().timestamp() - 3600):
                os.remove(file)
        
        # Keep only 20 newest downloads
        download_files = glob.glob(f"{DOWNLOAD_DIR}/*")
        if len(download_files) > 20:
            download_files.sort(key=os.path.getmtime)
            for old_file in download_files[:-20]:
                os.remove(old_file)
    except Exception as e:
        print(f"[Music] Cleanup error: {e}")

# Global client reference
client = None

async def play_handler(event):
    """Handle .play command - preview streaming"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split(maxsplit=1)
        if len(args) < 2:
            help_text = f"""{get_emoji('main')} **VZOELFOX MUSIC PREVIEW**

{get_emoji('check')} **Usage:**
{get_emoji('adder4')} `.play <song>` - Stream 30s preview
{get_emoji('adder4')} `.download <song>` - Download full song

{get_emoji('adder2')} **Examples:**
{get_emoji('adder6')} `.play Shape of You`
{get_emoji('adder6')} `.download Ed Sheeran Perfect`

{get_emoji('main')} **VzoelFox Music System v3.0**
{get_emoji('adder5')} Vzoel Fox's Premium Technology"""
            await safe_send_premium(event, help_text)
            return
        
        query = args[1].strip()
        
        # Send search message
        search_msg = await safe_send_premium(event, f"""{get_emoji('adder1')} **MUSIC PREVIEW MODE**

{get_emoji('check')} **Song:** `{query}`
{get_emoji('adder4')} **Type:** 30-second preview
{get_emoji('adder6')} **Status:** Searching YouTube...

{get_emoji('main')} **VzoelFox Music Engine**""")
        
        # Search first
        search_result = await search_youtube(query)
        
        if not search_result['success']:
            await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **SEARCH FAILED**

{get_emoji('adder3')} **Error:** {search_result['error']}
{get_emoji('adder1')} **Try:** Different keywords
{get_emoji('adder4')} **Or:** Use `.download` for full search

{get_emoji('main')} **VzoelFox Music System**""")
            return
        
        # Update with found info
        await safe_edit_premium(search_msg, f"""{get_emoji('adder2')} **SONG FOUND!**

{get_emoji('check')} **Title:** {search_result['title'][:40]}...
{get_emoji('adder4')} **Duration:** {search_result['duration']}
{get_emoji('adder6')} **Status:** Downloading preview...

{get_emoji('main')} **VzoelFox Music Engine**""")
        
        # Download preview
        result = await download_music_preview(query)
        
        if result['success']:
            await safe_edit_premium(search_msg, f"""{get_emoji('adder2')} **PREVIEW READY!**

{get_emoji('check')} **Title:** {result['title'][:40]}...
{get_emoji('adder4')} **Size:** {result['size'] // 1024} KB
{get_emoji('adder6')} **Type:** 30-second preview

{get_emoji('main')} **VzoelFox Music Player**""")
            
            # Send preview file
            try:
                with open(result['file_path'], 'rb') as audio:
                    await event.reply(
                        file=audio,
                        attributes=[DocumentAttributeAudio(
                            duration=30,
                            title=f"🎵 {result['title'][:30]} (Preview)",
                            performer="VzoelFox Music"
                        )]
                    )
                
                # Clean up preview file
                os.remove(result['file_path'])
                
            except Exception as e:
                await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **SEND FAILED**

{get_emoji('adder3')} **Error:** {str(e)[:50]}...
{get_emoji('adder1')} **File saved locally**

{get_emoji('main')} **VzoelFox Music System**""")
        
        else:
            await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **PREVIEW FAILED**

{get_emoji('adder3')} **Error:** {result['error'][:80]}...
{get_emoji('adder1')} **Try:** `.download {query}` for full version
{get_emoji('adder4')} **Or:** Different search terms

{get_emoji('main')} **VzoelFox Music System**""")
        
    except Exception as e:
        error_text = f"""{get_emoji('adder5')} **PLAY COMMAND ERROR**

{get_emoji('adder3')} **Error:** {str(e)[:60]}...
{get_emoji('adder1')} **Try:** `.download` command instead

{get_emoji('main')} **VzoelFox Music System**"""
        await safe_send_premium(event, error_text)

async def download_handler(event):
    """Handle .download command - full download"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split(maxsplit=1)
        if len(args) < 2:
            help_text = f"""{get_emoji('main')} **VZOELFOX MUSIC DOWNLOAD**

{get_emoji('check')} **Usage:**
{get_emoji('adder4')} `.download <song>` - Full quality download
{get_emoji('adder4')} `.play <song>` - 30s preview only

{get_emoji('adder2')} **Download Features:**
{get_emoji('adder6')} High quality MP3 (320K)
{get_emoji('adder6')} Full song duration
{get_emoji('adder6')} Audio metadata included

{get_emoji('main')} **VzoelFox Music System v3.0**
{get_emoji('adder5')} Vzoel Fox's Premium Technology"""
            await safe_send_premium(event, help_text)
            return
        
        query = args[1].strip()
        
        # Send search message
        search_msg = await safe_send_premium(event, f"""{get_emoji('adder1')} **FULL DOWNLOAD MODE**

{get_emoji('check')} **Song:** `{query}`
{get_emoji('adder4')} **Quality:** High (MP3 320K)
{get_emoji('adder6')} **Status:** Searching YouTube...

{get_emoji('main')} **VzoelFox Download Engine**""")
        
        # Search first
        search_result = await search_youtube(query)
        
        if search_result['success']:
            await safe_edit_premium(search_msg, f"""{get_emoji('adder2')} **SONG FOUND!**

{get_emoji('check')} **Title:** {search_result['title'][:40]}...
{get_emoji('adder4')} **Duration:** {search_result['duration']}
{get_emoji('adder6')} **Status:** Downloading full song...

{get_emoji('main')} **VzoelFox Download Engine**""")
        
        # Download full song
        result = await download_music_full(query)
        
        if result['success']:
            await safe_edit_premium(search_msg, f"""{get_emoji('adder2')} **DOWNLOAD COMPLETE!**

{get_emoji('check')} **Title:** {result['title'][:40]}...
{get_emoji('adder4')} **Size:** {result['size'] // 1024} KB
{get_emoji('adder6')} **Format:** {result['format']}

{get_emoji('main')} **VzoelFox Music Player**""")
            
            # Send full file
            try:
                with open(result['file_path'], 'rb') as audio:
                    await event.reply(
                        file=audio,
                        attributes=[DocumentAttributeAudio(
                            duration=180,  # Default duration
                            title=result['title'][:50],
                            performer="VzoelFox Music"
                        )],
                        supports_streaming=True
                    )
                
                # Cleanup old files
                cleanup_old_files()
                
            except Exception as e:
                await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **SEND FAILED**

{get_emoji('adder3')} **Error:** {str(e)[:50]}...
{get_emoji('adder1')} **File saved to:** Downloads folder

{get_emoji('main')} **VzoelFox Music System**""")
        
        else:
            await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **DOWNLOAD FAILED**

{get_emoji('adder3')} **Error:** {result['error'][:80]}...
{get_emoji('adder1')} **Try:** Different search terms
{get_emoji('adder4')} **Or:** Check internet connection

{get_emoji('main')} **VzoelFox Music System**""")
        
    except Exception as e:
        error_text = f"""{get_emoji('adder5')} **DOWNLOAD COMMAND ERROR**

{get_emoji('adder3')} **Error:** {str(e)[:60]}...
{get_emoji('adder1')} **Contact:** Support if issue persists

{get_emoji('main')} **VzoelFox Music System**"""
        await safe_send_premium(event, error_text)

async def musicstatus_handler(event):
    """Handle music status command"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        # Check yt-dlp status
        ytdlp_status = await check_ytdlp()
        
        # Check directories
        temp_files = len(glob.glob(f"{TEMP_DIR}/*")) if os.path.exists(TEMP_DIR) else 0
        download_files = len(glob.glob(f"{DOWNLOAD_DIR}/*")) if os.path.exists(DOWNLOAD_DIR) else 0
        
        status_text = f"""{get_emoji('main')} **VZOELFOX MUSIC STATUS**

{get_emoji('check')} **System Info:**
{get_emoji('adder4')} Version: v{PLUGIN_INFO['version']}
{get_emoji('adder4')} yt-dlp: {'✅ ' + ytdlp_status.get('version', 'Unknown') if ytdlp_status['available'] else '❌ Not available'}
{get_emoji('adder4')} Directories: ✅ Ready

{get_emoji('adder2')} **File Statistics:**
{get_emoji('adder6')} Temp Files: {temp_files}
{get_emoji('adder6')} Downloads: {download_files}

{get_emoji('adder3')} **Commands:**
{get_emoji('adder4')} `.play <song>` - 30s preview
{get_emoji('adder4')} `.download <song>` - Full download
{get_emoji('adder4')} `.musicstatus` - Show this status

{get_emoji('adder5')} **Features:**
{get_emoji('adder6')} High quality MP3 downloads
{get_emoji('adder6')} YouTube search integration
{get_emoji('adder6')} Audio metadata support
{get_emoji('adder6')} Automatic file cleanup

{get_emoji('main')} **VzoelFox Music System v3.0**
{get_emoji('adder5')} Vzoel Fox's Premium Technology
{get_emoji('adder6')} - 2025 Vzoel Fox's (LTPN)"""
        
        await safe_send_premium(event, status_text)
    
    except Exception as e:
        error_text = f"""{get_emoji('adder5')} **STATUS ERROR**

{get_emoji('adder3')} **Error:** {str(e)[:60]}...

{get_emoji('main')} **VzoelFox Music System**"""
        await safe_send_premium(event, error_text)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Ensure directories exist
    ensure_directories()
    
    # Register handlers
    client.add_event_handler(play_handler, events.NewMessage(pattern=r'\.play(?:\s+(.+))?$'))
    client.add_event_handler(download_handler, events.NewMessage(pattern=r'\.download(?:\s+(.+))?$'))
    client.add_event_handler(musicstatus_handler, events.NewMessage(pattern=r'\.musicstatus$'))
    
    print(f"✅ [Music System] VzoelFox Music System v{PLUGIN_INFO['version']} loaded")
    print(f"✅ [Music System] Commands: .play (preview), .download (full)")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Music System] Plugin cleanup initiated")
        cleanup_old_files()
        client = None
        print("[Music System] Plugin cleanup completed")
    except Exception as e:
        print(f"[Music System] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'play_handler', 'download_handler', 'musicstatus_handler']