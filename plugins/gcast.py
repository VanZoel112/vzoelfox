#!/usr/bin/env python3
"""
Advanced Gcast Plugin with Real-time Word Replacement
Features: Smart targeting, custom word replacement, progress tracking
"""

import asyncio
import time
import random
from telethon import events
from telethon.errors import FloodWaitError, ChatWriteForbiddenError, UserBannedInChannelError
from telethon.tl.types import Channel, Chat, User

from plugins import (
    COMMAND_PREFIX, owner_only, log_command_usage, 
    error_handler, word_replacer, get_word_replacer
)

# ============= GCAST CONFIGURATION =============

class GcastConfig:
    def __init__(self):
        self.delay_min = 2  # Minimum delay antar message (detik)
        self.delay_max = 5  # Maximum delay antar message
        self.batch_size = 10  # Berapa grup per batch
        self.batch_delay = 30  # Delay antar batch (detik)
        self.replacement_intensity = 0.8  # Seberapa sering replace words (80%)
        self.max_retries = 3
        
        # Blacklist chat IDs (grup yang ga mau di-gcast)
        self.blacklisted_chats = set()
        
        # Allowed chat types
        self.allowed_types = {Channel, Chat}

gcast_config = GcastConfig()

# ============= GCAST FUNCTIONS =============

async def get_dialogs_for_gcast(client):
    """Get all dialogs suitable for gcast"""
    try:
        dialogs = []
        async for dialog in client.iter_dialogs():
            # Skip private chats (User type)
            if isinstance(dialog.entity, User):
                continue
                
            # Skip blacklisted chats
            if dialog.id in gcast_config.blacklisted_chats:
                continue
                
            # Only include groups and channels
            if type(dialog.entity) in gcast_config.allowed_types:
                # Additional filtering
                entity = dialog.entity
                
                # Skip if we're not admin and it's a channel
                if isinstance(entity, Channel):
                    if entity.broadcast and not entity.creator and not entity.admin_rights:
                        continue
                
                dialogs.append({
                    'id': dialog.id,
                    'title': dialog.title,
                    'entity': dialog.entity,
                    'type': 'channel' if isinstance(entity, Channel) else 'group'
                })
        
        return dialogs
    except Exception as e:
        raise Exception(f"Error getting dialogs: {str(e)}")

async def send_gcast_message(client, chat_id, message, chat_title="Unknown"):
    """Send message to specific chat with error handling"""
    try:
        # Process message with word replacement setiap kali kirim
        replacer = get_word_replacer()
        processed_message = replacer.process_text(
            message, 
            context="gcast", 
            intensity=gcast_config.replacement_intensity
        )
        
        # Add random delay untuk avoid detection
        delay = random.uniform(gcast_config.delay_min, gcast_config.delay_max)
        await asyncio.sleep(delay)
        
        # Send message
        await client.send_message(chat_id, processed_message)
        return True, None
        
    except FloodWaitError as e:
        return False, f"Flood wait: {e.seconds}s"
    except ChatWriteForbiddenError:
        return False, "Write forbidden"
    except UserBannedInChannelError:
        return False, "Banned in chat"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============= GCAST COMMANDS =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gcast (.+)'))
@owner_only
@log_command_usage
@error_handler
async def gcast_handler(event):
    """Advanced gcast with real-time word replacement"""
    
    message = event.pattern_match.group(1).strip()
    if not message:
        await event.edit("❌ Please provide a message to broadcast!")
        return
    
    # Import client
    from main import client
    
    # Initial status message
    status_msg = await event.edit("🔄 **Preparing gcast...**\n📡 Getting chat list...")
    
    # Get dialogs
    try:
        dialogs = await get_dialogs_for_gcast(client)
        if not dialogs:
            await status_msg.edit("❌ No suitable chats found for gcast!")
            return
    except Exception as e:
        await status_msg.edit(f"❌ Error getting chats: {str(e)}")
        return
    
    # Update status with chat count
    await status_msg.edit(
        f"🔄 **Starting gcast...**\n"
        f"📊 Target chats: `{len(dialogs)}`\n"
        f"⚡ Word replacement: `{int(gcast_config.replacement_intensity*100)}%`\n"
        f"⏱️ Delay: `{gcast_config.delay_min}-{gcast_config.delay_max}s`"
    )
    
    # Gcast statistics
    stats = {
        'total': len(dialogs),
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    start_time = time.time()
    
    # Process in batches
    for i in range(0, len(dialogs), gcast_config.batch_size):
        batch = dialogs[i:i+gcast_config.batch_size]
        batch_num = (i // gcast_config.batch_size) + 1
        total_batches = (len(dialogs) + gcast_config.batch_size - 1) // gcast_config.batch_size
        
        # Update status for current batch
        await status_msg.edit(
            f"🚀 **Gcast in progress...**\n"
            f"📊 Batch: `{batch_num}/{total_batches}`\n"
            f"✅ Sent: `{stats['sent']}`\n"
            f"❌ Failed: `{stats['failed']}`\n"
            f"⏱️ Processing..."
        )
        
        # Process each chat in batch
        batch_tasks = []
        for dialog in batch:
            task = send_gcast_message(
                client, 
                dialog['id'], 
                message, 
                dialog['title']
            )
            batch_tasks.append(task)
        
        # Execute batch concurrently
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process results
        for j, (dialog, result) in enumerate(zip(batch, batch_results)):
            if isinstance(result, Exception):
                stats['failed'] += 1
                stats['errors'].append(f"{dialog['title']}: {str(result)}")
            else:
                success, error = result
                if success:
                    stats['sent'] += 1
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"{dialog['title']}: {error}")
        
        # Inter-batch delay (except for last batch)
        if i + gcast_config.batch_size < len(dialogs):
            await asyncio.sleep(gcast_config.batch_delay)
    
    # Final statistics
    end_time = time.time()
    duration = int(end_time - start_time)
    
    # Create final report
    success_rate = (stats['sent'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    final_report = f"""
🎯 **Gcast Completed!**

📊 **Statistics:**
• Total chats: `{stats['total']}`
• Successfully sent: `{stats['sent']}`
• Failed: `{stats['failed']}`
• Success rate: `{success_rate:.1f}%`
• Duration: `{duration}s`

⚡ **Features used:**
• Word replacement: `{int(gcast_config.replacement_intensity*100)}%` intensity
• Smart delays: `{gcast_config.delay_min}-{gcast_config.delay_max}s`
• Batch processing: `{gcast_config.batch_size}` chats/batch
    """.strip()
    
    # Add error summary if any
    if stats['errors'] and len(stats['errors']) <= 5:
        final_report += f"\n\n❌ **Recent errors:**\n"
        for error in stats['errors'][-5:]:
            final_report += f"• {error}\n"
    elif len(stats['errors']) > 5:
        final_report += f"\n\n❌ **Errors:** {len(stats['errors'])} total (check logs)"
    
    await status_msg.edit(final_report)

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gcastinfo'))
@owner_only
@log_command_usage 
@error_handler
async def gcastinfo_handler(event):
    """Show gcast configuration and stats"""
    
    # Import client
    from main import client
    
    msg = await event.edit("🔄 Gathering gcast information...")
    
    try:
        # Get dialog count
        dialogs = await get_dialogs_for_gcast(client)
        
        # Word replacer stats
        replacer_stats = word_replacer.get_stats()
        
        info_text = f"""
🔧 **Gcast Configuration:**

📊 **Targeting:**
• Available chats: `{len(dialogs)}`
• Blacklisted chats: `{len(gcast_config.blacklisted_chats)}`
• Allowed types: Groups, Channels

⚡ **Performance:**
• Delay range: `{gcast_config.delay_min}-{gcast_config.delay_max}s`
• Batch size: `{gcast_config.batch_size}` chats
• Batch delay: `{gcast_config.batch_delay}s`
• Max retries: `{gcast_config.max_retries}`

🔤 **Word Replacement:**
• Intensity: `{int(gcast_config.replacement_intensity*100)}%`
• Total words: `{replacer_stats['total_words']}`
• Total replacements: `{replacer_stats['total_replacements']}`

💡 **Usage:**
• `{COMMAND_PREFIX}gcast <message>` - Broadcast message
• `{COMMAND_PREFIX}gcastconfig` - Edit configuration
• `{COMMAND_PREFIX}blacklist <chat_id>` - Blacklist chat
        """.strip()
        
        await msg.edit(info_text)
        
    except Exception as e:
        await msg.edit(f"❌ Error getting gcast info: {str(e)}")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gcastconfig'))
@owner_only
@log_command_usage
@error_handler
async def gcastconfig_handler(event):
    """Configure gcast settings"""
    
    config_text = f"""
🔧 **Gcast Configuration Menu:**

**Current Settings:**
• Delay: `{gcast_config.delay_min}-{gcast_config.delay_max}s`
• Batch size: `{gcast_config.batch_size}`
• Word intensity: `{int(gcast_config.replacement_intensity*100)}%`

**Quick Commands:**
• `{COMMAND_PREFIX}gdelay <min> <max>` - Set delay range
• `{COMMAND_PREFIX}gbatch <size>` - Set batch size  
• `{COMMAND_PREFIX}gintensity <percent>` - Set word replacement intensity
• `{COMMAND_PREFIX}blacklist <chat_id>` - Blacklist chat
• `{COMMAND_PREFIX}unblacklist <chat_id>` - Remove from blacklist

**Examples:**
• `{COMMAND_PREFIX}gdelay 3 8` - Set 3-8 second delays
• `{COMMAND_PREFIX}gintensity 90` - 90% word replacement
    """.strip()
    
    await event.edit(config_text)

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gdelay (\d+) (\d+)'))
@owner_only
@log_command_usage
@error_handler
async def gdelay_handler(event):
    """Set gcast delay range"""
    
    min_delay = int(event.pattern_match.group(1))
    max_delay = int(event.pattern_match.group(2))
    
    if min_delay >= max_delay:
        await event.edit("❌ Minimum delay must be less than maximum delay!")
        return
    
    if min_delay < 1 or max_delay > 60:
        await event.edit("❌ Delay must be between 1-60 seconds!")
        return
    
    gcast_config.delay_min = min_delay
    gcast_config.delay_max = max_delay
    
    await event.edit(f"✅ Gcast delay set to `{min_delay}-{max_delay}s`")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gintensity (\d+)'))
@owner_only
@log_command_usage
@error_handler  
async def gintensity_handler(event):
    """Set word replacement intensity"""
    
    intensity_percent = int(event.pattern_match.group(1))
    
    if intensity_percent < 0 or intensity_percent > 100:
        await event.edit("❌ Intensity must be between 0-100%!")
        return
    
    gcast_config.replacement_intensity = intensity_percent / 100.0
    
    await event.edit(f"✅ Word replacement intensity set to `{intensity_percent}%`")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}blacklist (-?\d+)'))
@owner_only
@log_command_usage
@error_handler
async def blacklist_handler(event):
    """Add chat to gcast blacklist"""
    
    chat_id = int(event.pattern_match.group(1))
    gcast_config.blacklisted_chats.add(chat_id)
    
    await event.edit(f"✅ Chat `{chat_id}` added to blacklist")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}unblacklist (-?\d+)'))
@owner_only
@log_command_usage
@error_handler
async def unblacklist_handler(event):
    """Remove chat from gcast blacklist"""
    
    chat_id = int(event.pattern_match.group(1))
    if chat_id in gcast_config.blacklisted_chats:
        gcast_config.blacklisted_chats.remove(chat_id)
        await event.edit(f"✅ Chat `{chat_id}` removed from blacklist")
    else:
        await event.edit(f"❌ Chat `{chat_id}` not in blacklist")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gtest (.+)'))
@owner_only
@log_command_usage
@error_handler
async def gtest_handler(event):
    """Test word replacement without sending gcast"""
    
    message = event.pattern_match.group(1).strip()
    
    # Test dengan beberapa intensity level
    test_results = []
    for intensity in [0.3, 0.5, 0.8, 1.0]:
        processed = word_replacer.process_text(
            message, 
            context="gcast", 
            intensity=intensity
        )
        test_results.append(f"**{int(intensity*100)}%:** {processed}")
    
    test_output = f"""
🧪 **Word Replacement Test:**

**Original:** {message}

**Results:**
{chr(10).join(test_results)}

**Current intensity:** `{int(gcast_config.replacement_intensity*100)}%`
    """.strip()
    
    await event.edit(test_output)

# ============= CHAT MANAGEMENT =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}chatlist'))
@owner_only
@log_command_usage
@error_handler
async def chatlist_handler(event):
    """List all available chats for gcast"""
    
    # Import client
    from main import client
    
    msg = await event.edit("🔄 Getting chat list...")
    
    try:
        dialogs = await get_dialogs_for_gcast(client)
        
        if not dialogs:
            await msg.edit("❌ No chats available for gcast!")
            return
        
        # Group by type
        groups = [d for d in dialogs if d['type'] == 'group']
        channels = [d for d in dialogs if d['type'] == 'channel']
        
        # Create list (show first 20 to avoid message limit)
        chat_text = f"📋 **Available Chats ({len(dialogs)} total):**\n\n"
        
        if groups:
            chat_text += f"**👥 Groups ({len(groups)}):**\n"
            for i, group in enumerate(groups[:10], 1):
                status = "🚫" if group['id'] in gcast_config.blacklisted_chats else "✅"
                chat_text += f"{i}. {status} `{group['id']}` - {group['title'][:30]}...\n"
            
            if len(groups) > 10:
                chat_text += f"... and {len(groups)-10} more groups\n"
        
        if channels:
            chat_text += f"\n**📢 Channels ({len(channels)}):**\n"
            for i, channel in enumerate(channels[:10], 1):
                status = "🚫" if channel['id'] in gcast_config.blacklisted_chats else "✅"
                chat_text += f"{i}. {status} `{channel['id']}` - {channel['title'][:30]}...\n"
            
            if len(channels) > 10:
                chat_text += f"... and {len(channels)-10} more channels\n"
        
        chat_text += f"\n**Legend:**\n✅ = Available for gcast\n🚫 = Blacklisted"
        
        if len(dialogs) > 20:
            chat_text += f"\n\n💡 Showing first 20 chats only. Total: {len(dialogs)}"
        
        await msg.edit(chat_text)
        
    except Exception as e:
        await msg.edit(f"❌ Error getting chat list: {str(e)}")

# ============= WORD MANAGEMENT COMMANDS =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}addword (.+?)\\|(.+)'))
@owner_only
@log_command_usage
@error_handler
async def addword_handler(event):
    """Add custom word replacement"""
    
    original = event.pattern_match.group(1).strip()
    replacement = event.pattern_match.group(2).strip()
    
    if not original or not replacement:
        await event.edit(f"❌ Format: `{COMMAND_PREFIX}addword original|replacement`")
        return
    
    if word_replacer.add_word(original, replacement):
        await event.edit(f"✅ **Word added:**\n`{original}` → `{replacement}`")
    else:
        await event.edit("❌ Failed to add word!")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}removeword (.+)'))
@owner_only
@log_command_usage
@error_handler
async def removeword_handler(event):
    """Remove custom word completely"""
    
    word = event.pattern_match.group(1).strip()
    
    if word_replacer.remove_word(word):
        await event.edit(f"✅ **Word removed:** `{word}`")
    else:
        await event.edit(f"❌ Word `{word}` not found!")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}listwords'))
@owner_only
@log_command_usage
@error_handler
async def listwords_handler(event):
    """List all custom words"""
    
    words = word_replacer.custom_words
    
    if not words:
        await event.edit("❌ No custom words found!")
        return
    
    # Get stats
    stats = word_replacer.get_stats()
    
    # Create word list (first 20 to avoid message limit)
    word_items = list(words.items())
    word_text = f"📝 **Custom Words ({stats['total_words']} total):**\n\n"
    
    for i, (original, replacements) in enumerate(word_items[:20], 1):
        if isinstance(replacements, list):
            replacement_text = ", ".join([f"`{r}`" for r in replacements[:3]])
            if len(replacements) > 3:
                replacement_text += f" +{len(replacements)-3} more"
        else:
            replacement_text = f"`{replacements}`"
        
        word_text += f"{i}. **{original}** → {replacement_text}\n"
    
    if len(word_items) > 20:
        word_text += f"\n... and {len(word_items)-20} more words"
    
    word_text += f"""
    
📊 **Statistics:**
• Total words: `{stats['total_words']}`
• Total replacements: `{stats['total_replacements']}`
• Categories: {stats['categories']}

💡 **Commands:**
• `{COMMAND_PREFIX}addword word|replacement` - Add word
• `{COMMAND_PREFIX}removeword word` - Remove word
• `{COMMAND_PREFIX}gtest message` - Test replacement
    """.strip()
    
    await event.edit(word_text)

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}wordstats'))
@owner_only
@log_command_usage
@error_handler
async def wordstats_handler(event):
    """Show detailed word replacement statistics"""
    
    stats = word_replacer.get_stats()
    
    # Calculate additional stats
    words = word_replacer.custom_words
    multi_replacement_words = sum(1 for v in words.values() if isinstance(v, list) and len(v) > 1)
    avg_replacements = stats['total_replacements'] / stats['total_words'] if stats['total_words'] > 0 else 0
    
    stats_text = f"""
📊 **Word Replacement Statistics:**

**📈 Overview:**
• Total words: `{stats['total_words']}`
• Total replacements: `{stats['total_replacements']}`
• Words with multiple options: `{multi_replacement_words}`
• Average replacements per word: `{avg_replacements:.1f}`

**🎯 Categories:**
• Greetings: `{stats['categories']['greetings']}`
• Responses: `{stats['categories']['responses']}`  
• Actions: `{stats['categories']['actions']}`
• Others: `{stats['total_words'] - sum(stats['categories'].values())}`

**⚡ Current Settings:**
• Gcast intensity: `{int(gcast_config.replacement_intensity*100)}%`
• Storage: `{len(str(words))} bytes`

**💡 Performance:**
• Words loaded: `{stats['total_words'] > 0 and "✅" or "❌"}`
• Ready for gcast: `{"✅" if stats['total_words'] > 0 else "❌"}`
    """.strip()
    
    await event.edit(stats_text)

# ============= ADVANCED GCAST FEATURES =============

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}gcastto (.+?) (.+)'))
@owner_only
@log_command_usage
@error_handler
async def gcastto_handler(event):
    """Send gcast to specific chat types"""
    
    target_type = event.pattern_match.group(1).strip().lower()
    message = event.pattern_match.group(2).strip()
    
    if target_type not in ['groups', 'channels', 'all']:
        await event.edit(f"❌ Invalid type! Use: `groups`, `channels`, or `all`")
        return
    
    # Import client
    from main import client
    
    msg = a
