#!/usr/bin/env python3
"""
VzoelFox Music Player - Simple & Reliable Music Download System
Fitur: YouTube music download, premium emoji, simple commands
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 2.0.0 - Complete Rebuild
"""

import os
import asyncio
import subprocess
import glob
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, DocumentAttributeAudio

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "music_player",
    "version": "2.0.0",
    "description": "Simple music download dari YouTube dengan premium emoji support",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩", 
    "commands": [".play <song>", ".musicinfo"],
    "features": ["youtube download", "premium emoji", "simple interface", "audio metadata"]
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

# Download configuration - simplified path
DOWNLOAD_DIR = os.path.expanduser("~/vzoelfox/downloads/music")

def ensure_download_dir():
    """Ensure download directory exists"""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    return DOWNLOAD_DIR

async def download_youtube_audio(query):
    """Download audio from YouTube using yt-dlp - SIMPLIFIED & ROBUST"""
    try:
        ensure_download_dir()
        
        # Method 1: Try basic yt-dlp download
        try:
            cmd = [
                'yt-dlp', 
                '--extract-audio',
                '--audio-format', 'mp3',
                '--output', f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
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
                        'size': size
                    }
        except Exception as e1:
            print(f"[Music] Method 1 failed: {e1}")
        
        # Method 2: Simple download without conversion 
        try:
            cmd_simple = [
                'yt-dlp',
                '--format', 'bestaudio/best',
                '--output', f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                f'ytsearch1:{query}'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd_simple,
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
                    
                    return {
                        'success': True,
                        'file_path': newest_file,
                        'title': title,
                        'size': size
                    }
        except Exception as e2:
            print(f"[Music] Method 2 failed: {e2}")
        
        # Method 3: Basic fallback
        try:
            cmd_fallback = ['yt-dlp', '--output', f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', f'ytsearch1:{query}']
            
            process = await asyncio.create_subprocess_exec(
                *cmd_fallback,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Find any file
                all_files = glob.glob(f"{DOWNLOAD_DIR}/*")
                if all_files:
                    newest_file = max(all_files, key=os.path.getmtime)
                    title = os.path.basename(newest_file).split('.')[0]
                    size = os.path.getsize(newest_file)
                    
                    return {
                        'success': True,
                        'file_path': newest_file,
                        'title': title,
                        'size': size
                    }
        except Exception as e3:
            print(f"[Music] Method 3 failed: {e3}")
            
        return {
            'success': False,
            'error': f'All download methods failed. Check yt-dlp installation and internet connection.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Download error: {str(e)}'
        }

async def is_owner_check(client, user_id):
    """Check if user is bot owner"""
    try:
        # Try environment variable first
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(owner_id)
        
        # Fallback to self check
        if client:
            me = await client.get_me()
            return user_id == me.id
            
        # Hardcoded fallback (replace with your ID)
        OWNER_ID = 7847025168  # Replace with actual owner ID
        return user_id == OWNER_ID
    except Exception:
        return True  # Allow if check fails

# Global client reference
client = None

async def play_handler(event):
    """Handle .play command"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        args = event.text.split(maxsplit=1)
        if len(args) < 2:
            help_text = f"""{get_emoji('main')} **VZOELFOX MUSIC PLAYER**

{get_emoji('check')} **Usage:**
{get_emoji('adder4')} `.play <song title>` - Download music

{get_emoji('adder2')} **Examples:**
{get_emoji('adder6')} `.play Shape of You`
{get_emoji('adder6')} `.play Ed Sheeran Perfect`

{get_emoji('main')} **VzoelFox Premium System**
{get_emoji('adder5')} Powered by Vzoel Fox's Technology
{get_emoji('adder6')} © 2025 Vzoel Fox's (LTPN)"""
            await safe_send_premium(event, help_text)
            return
        
        query = args[1].strip()
        
        # Send searching message
        search_msg = await safe_send_premium(event, f"""{get_emoji('adder1')} **SEARCHING MUSIC...**

{get_emoji('check')} **Query:** `{query}`
{get_emoji('adder4')} **Source:** YouTube
{get_emoji('adder6')} **Status:** Downloading...

{get_emoji('main')} **VzoelFox Music Engine**""")
        
        # Download music with debugging
        print(f"[Music] Starting download for: {query}")
        result = await download_youtube_audio(query)
        print(f"[Music] Download result: {result}")
        
        if result['success']:
            # Send success message
            await safe_edit_premium(search_msg, f"""{get_emoji('adder2')} **DOWNLOAD COMPLETE!**

{get_emoji('check')} **Title:** {result['title'][:50]}
{get_emoji('adder4')} **Size:** {result['size'] // 1024} KB
{get_emoji('adder6')} **Status:** Ready to send

{get_emoji('main')} **VzoelFox Music Player**""")
            
            # Send audio file
            try:
                with open(result['file_path'], 'rb') as audio:
                    # Try to send as audio with metadata
                    try:
                        audio_attrs = [DocumentAttributeAudio(
                            duration=180,  # Default 3 minutes
                            title=result['title'][:50],
                            performer="VzoelFox Music"
                        )]
                        await event.reply(
                            file=audio,
                            attributes=audio_attrs,
                            supports_streaming=True
                        )
                    except:
                        # Fallback: send as document
                        await event.reply(file=audio)
                
                # Clean up old files (keep only 5 newest)
                try:
                    all_files = glob.glob(f"{DOWNLOAD_DIR}/*")
                    if len(all_files) > 5:
                        # Sort by modification time and remove oldest
                        all_files.sort(key=os.path.getmtime)
                        for old_file in all_files[:-5]:
                            os.remove(old_file)
                except:
                    pass
                
            except Exception as e:
                await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **SEND FAILED**

{get_emoji('check')} **Download:** Success
{get_emoji('adder3')} **Error:** {str(e)[:100]}
{get_emoji('adder4')} **File:** Saved to device

{get_emoji('main')} **VzoelFox Premium System**""")
        
        else:
            # Send error message
            await safe_edit_premium(search_msg, f"""{get_emoji('adder5')} **DOWNLOAD FAILED**

{get_emoji('check')} **Query:** `{query}`
{get_emoji('adder3')} **Error:** {result['error'][:100]}
{get_emoji('adder4')} **Suggestion:** Try different keywords

{get_emoji('main')} **VzoelFox Premium System**""")
    
    except Exception as e:
        error_text = f"""{get_emoji('adder5')} **MUSIC PLAYER ERROR**

{get_emoji('check')} **Error:** {str(e)[:100]}
{get_emoji('adder3')} **Contact:** @VzoelFox for support

{get_emoji('main')} **VzoelFox Premium System**"""
        await safe_send_premium(event, error_text)

async def musicinfo_handler(event):
    """Handle music info command"""
    global client
    if not await is_owner_check(client, event.sender_id):
        return
    
    try:
        # Test yt-dlp availability
        try:
            result = subprocess.run(['yt-dlp', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                yt_dlp_status = f"{get_emoji('adder2')} v{result.stdout.strip()}"
            else:
                yt_dlp_status = f"{get_emoji('adder5')} Error"
        except:
            yt_dlp_status = f"{get_emoji('adder5')} Not installed"
        
        # Check download directory
        download_count = len(glob.glob(f"{DOWNLOAD_DIR}/*")) if os.path.exists(DOWNLOAD_DIR) else 0
        
        info_text = f"""{get_emoji('main')} **VZOELFOX MUSIC SYSTEM**

{get_emoji('check')} **System Status:**
{get_emoji('adder4')} Version: v{PLUGIN_INFO['version']}
{get_emoji('adder4')} yt-dlp: {yt_dlp_status}
{get_emoji('adder4')} Download Dir: {get_emoji('adder2')} Ready
{get_emoji('adder4')} Cached Files: {download_count}

{get_emoji('adder6')} **Commands:**
{get_emoji('adder4')} `.play <song>` - Download music
{get_emoji('adder4')} `.musicinfo` - Show this info

{get_emoji('adder3')} **Features:**
{get_emoji('adder6')} YouTube music download
{get_emoji('adder6')} Premium emoji integration
{get_emoji('adder6')} Auto file cleanup
{get_emoji('adder6')} Audio metadata support

{get_emoji('main')} **VzoelFox Premium System**
{get_emoji('adder5')} Powered by Vzoel Fox's Technology
{get_emoji('adder6')} © 2025 Vzoel Fox's (LTPN)"""
        
        await safe_send_premium(event, info_text)
    
    except Exception as e:
        error_text = f"""{get_emoji('adder5')} **INFO ERROR**

{get_emoji('check')} **Error:** {str(e)}
{get_emoji('main')} **VzoelFox Premium System**"""
        await safe_send_premium(event, error_text)

def get_plugin_info():
    return PLUGIN_INFO

def setup(client_instance):
    """Setup function untuk register event handlers"""
    global client
    client = client_instance
    
    # Ensure download directory exists
    ensure_download_dir()
    
    # Register handlers
    client.add_event_handler(play_handler, events.NewMessage(pattern=r'\.play(?:\s+(.+))?$'))
    client.add_event_handler(musicinfo_handler, events.NewMessage(pattern=r'\.musicinfo$'))
    
    print(f"✅ [Music Player] VzoelFox Music System v{PLUGIN_INFO['version']} loaded")
    print(f"✅ [Music Player] Download directory: {DOWNLOAD_DIR}")

def cleanup_plugin():
    """Cleanup plugin resources"""
    global client
    try:
        print("[Music Player] Plugin cleanup initiated")
        client = None
        print("[Music Player] Plugin cleanup completed")
    except Exception as e:
        print(f"[Music Player] Cleanup error: {e}")

# Export functions
__all__ = ['setup', 'cleanup_plugin', 'get_plugin_info', 'play_handler', 'musicinfo_handler']