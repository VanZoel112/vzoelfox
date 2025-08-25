# ============= ENHANCED FEATURES FOR VZOEL ASSISTANT =============
"""
TAMBAHAN FITUR BARU:
1. .addbl - Menambahkan grup/channel ke blacklist
2. .rmbl - Menghapus dari blacklist  
3. .listbl - Melihat daftar blacklist
4. .gcast - Sekarang bisa reply pesan
5. Help command yang diperbaiki
"""

# Tambahkan di bagian global variables (setelah spam_users = {})
blacklisted_chats = set()  # Set untuk menyimpan chat yang diblacklist
BLACKLIST_FILE = "vzoel_blacklist.txt"  # File untuk menyimpan blacklist

# ============= BLACKLIST MANAGEMENT FUNCTIONS =============

def load_blacklist():
    """Load blacklist dari file"""
    global blacklisted_chats
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                blacklisted_chats = set(int(line.strip()) for line in f if line.strip())
            logger.info(f"✅ Loaded {len(blacklisted_chats)} blacklisted chats")
        else:
            blacklisted_chats = set()
            logger.info("📝 Created new blacklist file")
    except Exception as e:
        logger.error(f"Error loading blacklist: {e}")
        blacklisted_chats = set()

def save_blacklist():
    """Save blacklist ke file"""
    try:
        with open(BLACKLIST_FILE, 'w') as f:
            for chat_id in blacklisted_chats:
                f.write(f"{chat_id}\n")
        logger.info(f"💾 Saved {len(blacklisted_chats)} blacklisted chats")
    except Exception as e:
        logger.error(f"Error saving blacklist: {e}")

# ============= ENHANCED GCAST COMMAND (DENGAN REPLY SUPPORT) =============

@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}gcast(\s+(.+))?', re.DOTALL)))
async def enhanced_gcast_handler(event):
    """Enhanced Global Broadcast dengan reply support dan blacklist"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "gcast")
    
    # Cek apakah ada pesan yang direply atau ada text
    message_to_send = None
    
    if event.is_reply:
        # Jika reply, gunakan pesan yang direply
        reply_msg = await event.get_reply_message()
        message_to_send = reply_msg.text or reply_msg.caption or None
        
        # Jika reply pesan kosong tapi ada text setelah .gcast
        if not message_to_send:
            text_match = event.pattern_match.group(2)
            message_to_send = text_match.strip() if text_match else None
    else:
        # Jika tidak reply, gunakan text setelah .gcast
        text_match = event.pattern_match.group(2)
        message_to_send = text_match.strip() if text_match else None
    
    if not message_to_send:
        await event.reply(f"""
❌ **GCAST USAGE ERROR!**

📋 **Cara Penggunaan:**
• `{COMMAND_PREFIX}gcast <pesan>` - Ketik pesan langsung
• `{COMMAND_PREFIX}gcast` - Reply ke pesan yang mau di-gcast

💡 **Contoh:**
• `{COMMAND_PREFIX}gcast Halo semua!`
• Reply pesan lalu ketik `{COMMAND_PREFIX}gcast`
        """.strip())
        return
    
    try:
        # Load blacklist
        load_blacklist()
        
        # 8-phase animation dengan info blacklist
        gcast_animations = [
            "🔥 **lagi otw ngegikes.......**",
            "⚡ **cuma gikes aja diblacklist.. kek mui ngeblacklist sound horeg wkwkwkwkwkwk...**",
            "🛡️ **Loading blacklist filter...**",
            f"📊 **Blacklisted chats: {len(blacklisted_chats)}**",
            "🚀 **dikitÂ² blacklist...**",
            "⚠️ **dikitÂ² maen mute...**",
            "🔨 **dikitÂ² gban...**",
            "😂 **wkwkwkwk...**"
        ]
        
        msg = await event.reply(gcast_animations[0])
        
        # Animate first phases
        for i in range(1, 5):
            await asyncio.sleep(1.5)
            await msg.edit(gcast_animations[i])
        
        # Get channels (exclude blacklisted)
        all_channels = await get_broadcast_channels()
        channels = [ch for ch in all_channels if ch['id'] not in blacklisted_chats]
        
        total_channels = len(channels)
        blacklisted_count = len(all_channels) - total_channels
        
        if total_channels == 0:
            await msg.edit(f"""
❌ **No available channels for broadcasting!**

📊 **Stats:**
• Total chats found: `{len(all_channels)}`
• Blacklisted chats: `{blacklisted_count}`
• Available for broadcast: `0`

💡 Use `{COMMAND_PREFIX}listbl` to see blacklisted chats
            """.strip())
            return
        
        # Continue animation dengan stats
        await asyncio.sleep(1.5)
        await msg.edit(f"""
{gcast_animations[5]}

📊 **Broadcast Stats:**
• Total chats: `{len(all_channels)}`
• Blacklisted: `{blacklisted_count}`
• Target chats: `{total_channels}`
        """.strip())
        
        await asyncio.sleep(1.5)
        await msg.edit(f"{gcast_animations[6]}\n🚀 **Starting broadcast...**")
        
        # Start broadcasting
        success_count = 0
        failed_count = 0
        failed_chats = []
        skipped_count = blacklisted_count
        
        for i, channel_info in enumerate(channels, 1):
            try:
                entity = channel_info['entity']
                
                # Send message
                if event.is_reply and reply_msg.media:
                    # Jika reply pesan dengan media, forward media + caption
                    await client.send_message(entity, message_to_send, file=reply_msg.media)
                else:
                    # Kirim text biasa
                    await client.send_message(entity, message_to_send)
                
                success_count += 1
                
                # Update progress every 3 messages
                if i % 3 == 0 or i == total_channels:
                    progress = (i / total_channels) * 100
                    current_title = channel_info['title'][:20]
                    
                    await msg.edit(f"""
🔥 **lagi otw ngegikesss...**

**Total Kandang:** `{i}/{total_channels}` ({progress:.1f}%)
**Kandang yang berhasil:** `{success_count}`
**Kandang pelit.. alay.. dikitÂ² maen mute:** `{failed_count}`
**Kandang di-blacklist:** `{skipped_count}`
⚡ **Current:** {current_title}...
                    """.strip())
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except FloodWaitError as e:
                wait_time = e.seconds
                if wait_time > 300:  # Skip if wait too long
                    failed_count += 1
                    failed_chats.append(f"{channel_info['title']} (Flood: {wait_time}s)")
                    continue
                    
                await asyncio.sleep(wait_time)
                try:
                    if event.is_reply and reply_msg.media:
                        await client.send_message(entity, message_to_send, file=reply_msg.media)
                    else:
                        await client.send_message(entity, message_to_send)
                    success_count += 1
                except Exception:
                    failed_count += 1
                    failed_chats.append(f"{channel_info['title']} (Flood retry failed)")
                    
            except Exception as e:
                failed_count += 1
                error_msg = str(e)[:50]
                failed_chats.append(f"{channel_info['title']} ({error_msg})")
                logger.error(f"Gcast error for {channel_info['title']}: {e}")
                continue
        
        # Final animation
        await asyncio.sleep(2)
        await msg.edit(gcast_animations[7])
        await asyncio.sleep(2)
        
        # Calculate success rate
        success_rate = (success_count / total_channels * 100) if total_channels > 0 else 0
        
        final_message = f"""
🔥 **Gcast kelar....**

╔═══════════════════════════════════════╗
     **𝐕𝐙𝐎𝐄𝐋 𝐆𝐂𝐀𝐒𝐓 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄** 
╚═══════════════════════════════════════╝

📊 **Final Stats:**
• **Total Kandang:** `{len(all_channels)}`
• **Kandang yang berhasil:** `{success_count}`
• **Kandang pelit.. alay.. dikitÂ² mute:** `{failed_count}`
• **Kandang di-blacklist:** `{skipped_count}`
• **Success Rate:** `{success_rate:.1f}%`

💌 **Message Type:** {'Media + Text' if (event.is_reply and reply_msg.media) else 'Text Only'}
✅ **Message delivered successfully!**
⚡ **Enhanced Gcast by Vzoel Assistant**
        """.strip()
        
        await msg.edit(final_message)
        
        # Show error log if needed
        if failed_chats and len(failed_chats) <= 10:
            error_log = "**Failed Chats:**\n"
            for chat in failed_chats[:10]:
                error_log += f"• {chat}\n"
            if len(failed_chats) > 10:
                error_log += f"• And {len(failed_chats) - 10} more..."
            await event.reply(error_log)
        
    except Exception as e:
        await event.reply(f"❌ **Enhanced Gcast Error:** {str(e)}")
        logger.error(f"Enhanced gcast error: {e}")

# ============= BLACKLIST COMMANDS =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}addbl(\s+(.+))?'))
async def addbl_handler(event):
    """Add chat to blacklist - bisa dengan ID atau reply di grup"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "addbl")
    
    try:
        chat_to_blacklist = None
        chat_title = "Unknown"
        
        # Cek parameter ID
        param = event.pattern_match.group(2)
        if param:
            try:
                # Coba parse sebagai ID
                if param.strip().lstrip('-').isdigit():
                    chat_id = int(param.strip())
                    chat_entity = await client.get_entity(chat_id)
                    chat_to_blacklist = chat_id
                    chat_title = getattr(chat_entity, 'title', f'Chat {chat_id}')
                else:
                    await event.reply("❌ **Invalid chat ID! Use numeric ID only.**")
                    return
            except Exception as e:
                await event.reply(f"❌ **Error getting chat info:** `{str(e)}`")
                return
        else:
            # Jika tidak ada parameter, gunakan chat saat ini
            chat = await event.get_chat()
            if hasattr(chat, 'id'):
                chat_to_blacklist = chat.id
                chat_title = getattr(chat, 'title', 'Private Chat')
            else:
                await event.reply(f"""
❌ **ADDBL USAGE ERROR!**

📋 **Cara Penggunaan:**
• `{COMMAND_PREFIX}addbl` - Blacklist grup/channel ini
• `{COMMAND_PREFIX}addbl -1001234567890` - Blacklist dengan ID

💡 **Cara dapat ID grup:**
1. Forward pesan dari grup ke @userinfobot
2. Atau gunakan `{COMMAND_PREFIX}id` di grup tersebut
                """.strip())
                return
        
        # Load current blacklist
        load_blacklist()
        
        if chat_to_blacklist in blacklisted_chats:
            await event.reply(f"""
⚠️ **CHAT SUDAH DI-BLACKLIST!**

📊 **Info:**
• **Chat:** {chat_title}
• **ID:** `{chat_to_blacklist}`
• **Status:** Already blacklisted

Use `{COMMAND_PREFIX}listbl` to see all blacklisted chats
            """.strip())
            return
        
        # Add to blacklist
        blacklisted_chats.add(chat_to_blacklist)
        save_blacklist()
        
        await event.reply(f"""
✅ **CHAT BERHASIL DI-BLACKLIST!**

╔═══════════════════════════════════════╗
    **𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓 𝐀𝐃𝐃𝐄𝐃** 
╚═══════════════════════════════════════╝

📝 **Chat:** {chat_title}
🆔 **ID:** `{chat_to_blacklist}`
📊 **Total Blacklisted:** `{len(blacklisted_chats)}`
🚫 **Effect:** Won't receive gcast messages

⚡ **Vzoel Blacklist System Active**
        """.strip())
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"AddBL error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}rmbl(\s+(.+))?'))
async def rmbl_handler(event):
    """Remove chat from blacklist"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "rmbl")
    
    try:
        chat_to_remove = None
        chat_title = "Unknown"
        
        # Cek parameter ID
        param = event.pattern_match.group(2)
        if param:
            try:
                if param.strip().lstrip('-').isdigit():
                    chat_id = int(param.strip())
                    chat_entity = await client.get_entity(chat_id)
                    chat_to_remove = chat_id
                    chat_title = getattr(chat_entity, 'title', f'Chat {chat_id}')
                else:
                    await event.reply("❌ **Invalid chat ID! Use numeric ID only.**")
                    return
            except Exception as e:
                await event.reply(f"❌ **Error getting chat info:** `{str(e)}`")
                return
        else:
            # Gunakan chat saat ini
            chat = await event.get_chat()
            if hasattr(chat, 'id'):
                chat_to_remove = chat.id
                chat_title = getattr(chat, 'title', 'Private Chat')
            else:
                await event.reply(f"""
❌ **RMBL USAGE ERROR!**

📋 **Cara Penggunaan:**
• `{COMMAND_PREFIX}rmbl` - Remove blacklist grup/channel ini
• `{COMMAND_PREFIX}rmbl -1001234567890` - Remove blacklist dengan ID

Use `{COMMAND_PREFIX}listbl` to see blacklisted chats
                """.strip())
                return
        
        # Load blacklist
        load_blacklist()
        
        if chat_to_remove not in blacklisted_chats:
            await event.reply(f"""
⚠️ **CHAT TIDAK ADA DI BLACKLIST!**

📊 **Info:**
• **Chat:** {chat_title}
• **ID:** `{chat_to_remove}`
• **Status:** Not blacklisted

Use `{COMMAND_PREFIX}listbl` to see all blacklisted chats
            """.strip())
            return
        
        # Remove from blacklist
        blacklisted_chats.remove(chat_to_remove)
        save_blacklist()
        
        await event.reply(f"""
✅ **CHAT BERHASIL DIHAPUS DARI BLACKLIST!**

╔═══════════════════════════════════════╗
   **𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓 𝐑𝐄𝐌𝐎𝐕𝐄𝐃** 
╚═══════════════════════════════════════╝

📝 **Chat:** {chat_title}
🆔 **ID:** `{chat_to_remove}`
📊 **Total Blacklisted:** `{len(blacklisted_chats)}`
✅ **Effect:** Will receive gcast messages again

⚡ **Vzoel Blacklist System Updated**
        """.strip())
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"RmBL error: {e}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}listbl'))
async def listbl_handler(event):
    """Show blacklisted chats"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "listbl")
    
    try:
        load_blacklist()
        
        if not blacklisted_chats:
            await event.reply(f"""
📋 **BLACKLIST KOSONG!**

╔═══════════════════════════════════════╗
    **𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓 𝐄𝐌𝐏𝐓𝐘** 
╚═══════════════════════════════════════╝

📊 **Total Blacklisted:** `0`
✅ **All chats will receive gcast**

💡 **Add to blacklist:**
• `{COMMAND_PREFIX}addbl` - Blacklist current chat
• `{COMMAND_PREFIX}addbl -1001234567890` - Blacklist by ID
            """.strip())
            return
        
        # Get chat info for each blacklisted chat
        blacklist_info = []
        for chat_id in list(blacklisted_chats)[:20]:  # Limit to 20 for readability
            try:
                entity = await client.get_entity(chat_id)
                title = getattr(entity, 'title', 'Unknown')
                chat_type = 'Channel' if isinstance(entity, Channel) and entity.broadcast else 'Group'
                blacklist_info.append(f"• **{title[:30]}** ({chat_type})\n  `{chat_id}`")
            except Exception:
                blacklist_info.append(f"• **Unknown Chat**\n  `{chat_id}` (Error getting info)")
        
        blacklist_text = f"""
📋 **DAFTAR BLACKLIST**

╔═══════════════════════════════════════╗
    **𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓𝐄𝐃 𝐂𝐇𝐀𝐓𝐒** 
╚═══════════════════════════════════════╝

📊 **Total:** `{len(blacklisted_chats)}` chats

{chr(10).join(blacklist_info[:15])}

{'...' if len(blacklisted_chats) > 15 else ''}

💡 **Commands:**
• `{COMMAND_PREFIX}rmbl <id>` - Remove from blacklist
• `{COMMAND_PREFIX}addbl <id>` - Add to blacklist

⚡ **Vzoel Blacklist System**
        """.strip()
        
        await event.reply(blacklist_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"ListBL error: {e}")

# ============= ENHANCED HELP COMMAND =============

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}help'))
async def enhanced_help_handler(event):
    """Enhanced help command with better organization and all new features"""
    if not await is_owner(event.sender_id):
        return
    
    await log_command(event, "help")
    
    try:
        help_text = f"""
[🆘](https://imgur.com/gallery/k-qzrssZX) **VZOEL ASSISTANT HELP MENU**

╔═══════════════════════════════════════╗
   📚 **𝐄𝐍𝐇𝐀𝐍𝐂𝐄𝐃 𝐂𝐎𝐌𝐌𝐀𝐍𝐃 𝐋𝐈𝐒𝐓** 📚
╚═══════════════════════════════════════╝

🔥 **SYSTEM COMMANDS:**
• `{COMMAND_PREFIX}alive` - Bot status dengan logo & animasi
• `{COMMAND_PREFIX}info` - System info lengkap
• `{COMMAND_PREFIX}ping` - Test response time
• `{COMMAND_PREFIX}help` - Show menu ini

🌐 **BROADCAST SYSTEM (ENHANCED):**
• `{COMMAND_PREFIX}gcast <pesan>` - Global broadcast text
• `{COMMAND_PREFIX}gcast` (reply) - Broadcast pesan yang direply
• `{COMMAND_PREFIX}gcast` (reply media) - Broadcast media + caption

🛡️ **BLACKLIST MANAGEMENT (NEW):**
• `{COMMAND_PREFIX}addbl` - Blacklist grup/channel ini
• `{COMMAND_PREFIX}addbl <id>` - Blacklist by chat ID
• `{COMMAND_PREFIX}rmbl` - Remove blacklist grup ini
• `{COMMAND_PREFIX}rmbl <id>` - Remove blacklist by ID
• `{COMMAND_PREFIX}listbl` - Lihat daftar blacklist

🎵 **VOICE CHAT CONTROL:**
• `{COMMAND_PREFIX}joinvc` - Join voice chat dengan animasi
• `{COMMAND_PREFIX}leavevc` - Leave voice chat dengan animasi

🔍 **USER UTILITIES:**
• `{COMMAND_PREFIX}id` (reply) - Get user ID dari reply
• `{COMMAND_PREFIX}id <username>` - Get user ID dari username
• `{COMMAND_PREFIX}id <user_id>` - Get info dari user ID

🛡️ **SECURITY FEATURES:**
• `{COMMAND_PREFIX}sg` - Toggle spam guard protection

✨ **SPECIAL ANIMATIONS:**
• `{COMMAND_PREFIX}vzl` - Spektakuler 12-phase animation
• `{COMMAND_PREFIX}infofounder` - Info founder dengan logo

📝 **USAGE EXAMPLES:**

**Broadcast Examples:**
```
{COMMAND_PREFIX}gcast Halo semua! 👋
{COMMAND_PREFIX}gcast (reply ke pesan)
{COMMAND_PREFIX}gcast (reply ke foto/video)
```

**Blacklist Examples:**
```
{COMMAND_PREFIX}addbl (di grup yang mau diblacklist)
{COMMAND_PREFIX}addbl -1001234567890
{COMMAND_PREFIX}rmbl -1001234567890
{COMMAND_PREFIX}listbl
```

**ID Lookup Examples:**
```
{COMMAND_PREFIX}id (reply ke user)
{COMMAND_PREFIX}id @username
{COMMAND_PREFIX}id 123456789
```

🆕 **NEW FEATURES v2.1:**
• Enhanced gcast dengan reply support
• Media broadcast support (foto/video + caption)
• Smart blacklist system dengan file storage
• Improved error handling & flood protection
• Better progress tracking & statistics

⚠️ **SECURITY NOTE:**
Semua commands hanya bisa digunakan oleh owner untuk keamanan maksimal

📞 **SUPPORT & INFO:**
• **Telegram:** @VZLfx | @VZLfxs
• **Channel:** t.me/damnitvzoel
• **Instagram:** @vzoel.fox_s

⚡ **Created by Vzoel Fox's (LTPN) ©2025**
🔥 **Enhanced Edition v2.1 - Python Powered**
        """.strip()
        
        await event.edit(help_text)
        
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e)}")
        logger.error(f"Enhanced help error: {e}")

# ============= TAMBAHAN DI STARTUP FUNCTION =============
# Tambahkan load_blacklist() di startup function, setelah start_time = datetime.now():

async def enhanced_startup():
    """Enhanced startup dengan blacklist loading"""
    global start_time
    start_time = datetime.now()
    
    # Load blacklist at startup
    load_blacklist()
    
    logger.info("🚀 Starting Vzoel Assistant (Enhanced Edition v2.1)...")
    logger.info(f"🛡️ Loaded {len(blacklisted_chats)} blacklisted chats")
    
    # ... rest of startup function

# ============= INSTALLATION INSTRUCTIONS =============
"""
📥 CARA INSTALASI FITUR BARU:

1. Backup file main.py yang lama
2. Tambahkan code di atas ke file main.py Anda:
   - Tambahkan global variables (blacklisted_chats, BLACKLIST_FILE)
   - Replace gcast_handler dengan enhanced_gcast_handler
   - Tambahkan semua function baru (addbl, rmbl, listbl)
   - Replace help_handler dengan enhanced_help_handler
   - Tambahkan load_blacklist() di startup

3. Install dependencies (sudah ada):
   pip install telethon python-dotenv

4. Run bot:
   python main.py

✅ FITUR BARU YANG DITAMBAHKAN:
• .gcast sekarang bisa reply pesan (text/media)
• .addbl untuk blacklist grup/channel
• .rmbl untuk remove blacklist
• .listbl untuk lihat daftar blacklist
• Help menu yang lebih lengkap dan terorganisir
• Blacklist otomatis tersimpan di file
• Statistics yang lebih detail di gcast
• Media broadcast support (foto/video + caption)

🔥 Semua fitur terintegrasi dengan sistem existing tanpa merusak fungsi lama!
⚡ Created by Vzoel Fox's (LTPN) ©2025
"""