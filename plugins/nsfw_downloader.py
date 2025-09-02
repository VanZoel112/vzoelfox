import asyncio
import os
import re
from datetime import datetime
from typing import List, Dict, Tuple
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError, PeerIdInvalid, ChannelPrivate

class IndonesianFilter:
    """Quick Indonesian content detection for integration"""
    
    @staticmethod
    def is_indonesian_quick(text: str, caption: str = "") -> bool:
        """Quick Indonesian detection"""
        try:
            content = f"{text} {caption}".lower()
            
            indo_indicators = [
                'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'ini', 'itu',
                'gak', 'ga', 'ngga', 'udah', 'banget', 'dong', 'sih', 'kok', 'gimana',
                'jakarta', 'bandung', 'surabaya', 'jogja', 'medan', 'semarang',
                'pap', 'tt', 'vcs', 'ml', 'exe', 'colmek', 'coli', 'bacol',
                'tante', 'om', 'kak', 'mas', 'mba', 'gan', 'suhu',
                'jomblo', 'pdkt', 'gebetan', 'pacar', 'cowo', 'cewe',
                'wib', 'jabodetabek', 'jabar', 'jateng', 'jatim'
            ]
            
            score = sum(1 for word in indo_indicators if word in content)
            return score >= 3
        except Exception as e:
            print(f"Indonesian filter error: {e}")
            return False

class NSFWDownloader:
    def __init__(self, client):
        self.client = client
        self.download_path = "downloads/nsfw"
        self.indo_filter = IndonesianFilter()
        self.ensure_download_dir()
    
    def ensure_download_dir(self):
        try:
            if not os.path.exists(self.download_path):
                os.makedirs(self.download_path, exist_ok=True)
        except Exception as e:
            print(f"Directory creation error: {e}")
    
    def parse_telegram_link(self, link: str):
        """Parse Telegram link and extract chat info and message ID"""
        try:
            patterns = [
                r't\.me/([^/\s]+)/(\d+)',  # t.me/channel/123
                r'telegram\.me/([^/\s]+)/(\d+)',  # telegram.me/channel/123
                r't\.me/c/(\d+)/(\d+)',  # t.me/c/123456/789 (private channel)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, link)
                if match:
                    if 't.me/c/' in link:
                        chat_id = f"-100{match.group(1)}"  # Convert to supergroup format
                        message_id = int(match.group(2))
                    else:
                        chat_id = match.group(1)
                        message_id = int(match.group(2))
                    return chat_id, message_id
            
            return None, None
        except Exception as e:
            print(f"Link parsing error: {e}")
            return None, None
    
    async def download_from_link(self, link: str):
        """Download media from Telegram link"""
        try:
            chat_id, message_id = self.parse_telegram_link(link)
            if not chat_id or not message_id:
                return False, "❌ Invalid Telegram link format!"
            
            # Get the message
            message = await self.client.get_messages(chat_id, message_id)
            if not message:
                return False, "❌ Message not found or not accessible!"
            
            # Get chat info for source
            try:
                chat = await self.client.get_chat(chat_id)
                if chat.type.name == "CHANNEL":
                    source_info = f"Channel: @{chat.username}" if chat.username else f"Channel: {chat.title}"
                elif chat.type.name in ["GROUP", "SUPERGROUP"]:
                    source_info = f"Group: {chat.title}"
                else:
                    source_info = f"@{chat.username}" if hasattr(chat, 'username') and chat.username else "Private"
            except:
                source_info = "Unknown Source"
            
            # Download and forward
            success = await self.download_and_forward(message, f"{source_info}\n🔗 **Link:** {link}")
            
            if success:
                return True, "✅ Media downloaded and saved successfully!"
            else:
                return False, "❌ No media found in the message!"
                
        except ChannelPrivate:
            return False, "❌ Channel is private! You need to join first."
        except PeerIdInvalid:
            return False, "❌ Invalid chat ID or you don't have access!"
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await self.download_from_link(link)
        except Exception as e:
            print(f"Download from link error: {e}")
            return False, f"❌ Error: {str(e)}"

    async def download_and_forward(self, message: Message, source_info: str = ""):
        try:
            media_types = [
                message.photo, message.video, message.animation, 
                message.document, message.sticker, message.video_note
            ]
            
            media = next((m for m in media_types if m), None)
            if not media:
                return False
            
            # Download media
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{timestamp}_{message.id}"
            
            if message.photo:
                file_name += ".jpg"
            elif message.video:
                file_name += ".mp4" 
            elif message.animation:
                file_name += ".gif"
            elif message.document:
                file_name += f".{message.document.file_name.split('.')[-1] if message.document.file_name else 'file'}"
            
            file_path = os.path.join(self.download_path, file_name)
            
            # Download file
            await message.download(file_path)
            
            # Prepare caption with Indonesian detection
            original_caption = message.caption or ""
            message_text = message.text or ""
            
            # Check if content is Indonesian
            is_indonesian = self.indo_filter.is_indonesian_quick(message_text, original_caption)
            indo_flag = "🇮🇩" if is_indonesian else "🌍"
            
            new_caption = f"📥 **Saved from:** {source_info}\n"
            new_caption += f"🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            new_caption += f"🆔 **Message ID:** {message.id}\n"
            new_caption += f"{indo_flag} **Origin:** {'Indonesian Content' if is_indonesian else 'International Content'}\n"
            if original_caption:
                new_caption += f"📝 **Caption:** {original_caption}"
            
            # Forward to Saved Messages
            if message.photo:
                await self.client.send_photo("me", file_path, caption=new_caption)
            elif message.video:
                await self.client.send_video("me", file_path, caption=new_caption)
            elif message.animation:
                await self.client.send_animation("me", file_path, caption=new_caption)
            elif message.document:
                await self.client.send_document("me", file_path, caption=new_caption)
            elif message.sticker:
                await self.client.send_sticker("me", file_path)
            elif message.video_note:
                await self.client.send_video_note("me", file_path)
            
            return True
            
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await self.download_and_forward(message, source_info)
        except Exception as e:
            print(f"Error downloading media: {e}")
            return False

# Plugin handlers
nsfw_downloader = None

@Client.on_message(filters.command(["save", "dl"], prefixes=".") & filters.me)
async def save_media_handler(client: Client, message: Message):
    global nsfw_downloader
    if not nsfw_downloader:
        nsfw_downloader = NSFWDownloader(client)
    
    reply = message.reply_to_message
    if not reply:
        await message.edit("❌ Reply to a media message to save it!")
        return
    
    # Get source info
    chat = await client.get_chat(reply.chat.id)
    if chat.type.name == "PRIVATE":
        source_info = f"@{chat.username}" if chat.username else f"Private ({chat.first_name})"
    elif chat.type.name in ["GROUP", "SUPERGROUP"]:
        source_info = f"Group: {chat.title}"
    elif chat.type.name == "CHANNEL":
        source_info = f"Channel: @{chat.username}" if chat.username else f"Channel: {chat.title}"
    else:
        source_info = "Unknown"
    
    await message.edit("📥 Downloading and saving...")
    
    success = await nsfw_downloader.download_and_forward(reply, source_info)
    
    if success:
        await message.edit("✅ Media saved to your Saved Messages!")
    else:
        await message.edit("❌ Failed to save media!")
    
    # Auto delete command message after 3 seconds
    await asyncio.sleep(3)
    await message.delete()

@Client.on_message(filters.command(["linkdl", "link"], prefixes=".") & filters.me)
async def link_download_handler(client: Client, message: Message):
    global nsfw_downloader
    if not nsfw_downloader:
        nsfw_downloader = NSFWDownloader(client)
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.edit("❌ Usage: `.linkdl <telegram_link>`\n\n**Examples:**\n• `.linkdl https://t.me/channel/123`\n• `.linkdl https://t.me/c/1234567890/456`")
        await asyncio.sleep(5)
        await message.delete()
        return
    
    link = args[1]
    await message.edit("🔍 Processing link...")
    
    success, result_message = await nsfw_downloader.download_from_link(link)
    await message.edit(result_message)
    
    # Auto delete after 5 seconds
    await asyncio.sleep(5)
    await message.delete()

@Client.on_message(filters.command(["indosave"], prefixes=".") & filters.me)
async def indo_save_handler(client: Client, message: Message):
    """Save only Indonesian content"""
    global nsfw_downloader
    if not nsfw_downloader:
        nsfw_downloader = NSFWDownloader(client)
    
    reply = message.reply_to_message
    if not reply:
        await message.edit("❌ Reply to a media message to check and save if Indonesian!")
        return
    
    # Check if Indonesian first
    text = reply.text or ""
    caption = reply.caption or ""
    is_indonesian = nsfw_downloader.indo_filter.is_indonesian_quick(text, caption)
    
    if not is_indonesian:
        await message.edit("❌ Content is not Indonesian! Use `.save` for non-Indonesian content.")
        await asyncio.sleep(3)
        await message.delete()
        return
    
    # Get source info
    chat = await client.get_chat(reply.chat.id)
    if chat.type.name == "PRIVATE":
        source_info = f"@{chat.username}" if chat.username else f"Private ({chat.first_name})"
    elif chat.type.name in ["GROUP", "SUPERGROUP"]:
        source_info = f"Group: {chat.title}"
    elif chat.type.name == "CHANNEL":
        source_info = f"Channel: @{chat.username}" if chat.username else f"Channel: {chat.title}"
    else:
        source_info = "Unknown"
    
    await message.edit("🇮🇩 Downloading Indonesian content...")
    
    success = await nsfw_downloader.download_and_forward(reply, f"🇮🇩 {source_info}")
    
    if success:
        await message.edit("✅ Indonesian content saved!")
    else:
        await message.edit("❌ Failed to save content!")
    
    # Auto delete after 3 seconds
    await asyncio.sleep(3)
    await message.delete()