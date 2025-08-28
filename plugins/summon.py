#!/usr/bin/env python3
"""
All-in-One Summon Plugin dengan Premium Emoji Support
File: plugins/summon.py
Author: Vzoel Fox's (Enhanced by Morgan)
NO EXTERNAL FILES NEEDED - Everything in memory!
"""

import re
import os
import sys
import json
import asyncio
import random
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji
from telethon.errors import FloodWaitError

# Premium emoji configuration (copy dari main.py)
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

# ============================================================================
# IN-MEMORY DATA STORAGE - NO EXTERNAL FILES NEEDED!
# ============================================================================

# Virtual accounts database (stored in memory)
VIRTUAL_ACCOUNTS = {
    "account_1": {
        "name": "SummonBot1",
        "status": "active",
        "last_used": None,
        "total_summons": 0,
        "created": datetime.now().isoformat()
    },
    "account_2": {
        "name": "SummonBot2", 
        "status": "active",
        "last_used": None,
        "total_summons": 0,
        "created": datetime.now().isoformat()
    },
    "account_3": {
        "name": "SummonBot3",
        "status": "active", 
        "last_used": None,
        "total_summons": 0,
        "created": datetime.now().isoformat()
    },
    "account_4": {
        "name": "SummonBot4",
        "status": "dead",  # Simulate some dead accounts
        "last_used": None,
        "total_summons": 0,
        "created": datetime.now().isoformat()
    },
    "account_5": {
        "name": "SummonBot5",
        "status": "active",
        "last_used": None,
        "total_summons": 0,
        "created": datetime.now().isoformat()
    }
}

# Summon statistics (in memory)
SUMMON_STATS = {
    "total_summons": 0,
    "successful_summons": 0,
    "failed_summons": 0,
    "last_summon": None,
    "most_used_account": None
}

# Active summon sessions
ACTIVE_SUMMONS = {}

# Account status constants
STATUS_ACTIVE = "active"
STATUS_DEAD = "dead"
STATUS_BANNED = "banned"
STATUS_UNKNOWN = "unknown"

# Global premium status
premium_status = None

async def check_premium_status():
    """Check premium status in plugin"""
    global premium_status
    try:
        me = await client.get_me()
        premium_status = getattr(me, 'premium', False)
        return premium_status
    except Exception:
        premium_status = False
        return False

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
    if emoji_type in PREMIUM_EMOJIS:
        return PREMIUM_EMOJIS[emoji_type]['char']
    return '🤩'

def create_premium_entities(text):
    """Create premium emoji entities for text"""
    if not premium_status:
        return []
    
    entities = []
    current_offset = 0
    i = 0
    
    try:
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

async def safe_send_with_entities(event, text):
    """Send message with premium entities if available"""
    try:
        await check_premium_status()
        
        if premium_status:
            entities = create_premium_entities(text)
            if entities:
                await event.reply(text, formatting_entities=entities)
                return
        
        await event.reply(text)
    except Exception:
        await event.reply(text)

async def is_owner_check(user_id):
    """Check if user is owner"""
    try:
        import os
        owner_id = os.getenv("OWNER_ID")
        if owner_id:
            return user_id == int(user_id)
        
        me = await client.get_me()
        return user_id == me.id
    except Exception:
        return True

def get_prefix():
    """Get command prefix"""
    try:
        import os
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

# ============================================================================
# VIRTUAL ACCOUNT MANAGEMENT
# ============================================================================

def add_virtual_account(count=1):
    """Add virtual accounts to the pool"""
    added = 0
    for i in range(count):
        account_id = f"account_{len(VIRTUAL_ACCOUNTS) + 1}"
        if account_id not in VIRTUAL_ACCOUNTS:
            VIRTUAL_ACCOUNTS[account_id] = {
                "name": f"SummonBot{len(VIRTUAL_ACCOUNTS) + 1}",
                "status": STATUS_ACTIVE,
                "last_used": None,
                "total_summons": 0,
                "created": datetime.now().isoformat()
            }
            added += 1
    return added

def simulate_account_health_check():
    """Simulate checking account health (some might go dead randomly)"""
    for account_id, data in VIRTUAL_ACCOUNTS.items():
        # Small chance an account goes dead
        if data["status"] == STATUS_ACTIVE and random.random() < 0.05:  # 5% chance
            data["status"] = STATUS_DEAD
        # Small chance a dead account comes back
        elif data["status"] == STATUS_DEAD and random.random() < 0.1:  # 10% chance
            data["status"] = STATUS_ACTIVE

def get_available_accounts(limit=None):
    """Get list of active virtual accounts"""
    simulate_account_health_check()  # Update statuses
    
    available = []
    for account_id, data in VIRTUAL_ACCOUNTS.items():
        if data["status"] == STATUS_ACTIVE:
            # Calculate priority based on last used time
            last_used = data.get("last_used")
            if last_used:
                last_used_time = datetime.fromisoformat(last_used)
                hours_since_used = (datetime.now() - last_used_time).total_seconds() / 3600
            else:
                hours_since_used = 999  # Never used, highest priority
            
            available.append({
                "id": account_id,
                "data": data,
                "priority": hours_since_used
            })
    
    # Sort by priority (longest time since last used first)
    available.sort(key=lambda x: x["priority"], reverse=True)
    
    if limit:
        available = available[:limit]
    
    return available

async def simulate_summon(account_id, message, chat_id, delay=0):
    """Simulate summoning an account (send message from main bot with different styling)"""
    try:
        if delay > 0:
            await asyncio.sleep(delay)
        
        account_data = VIRTUAL_ACCOUNTS.get(account_id)
        if not account_data:
            return False, "Account not found"
        
        if account_data["status"] != STATUS_ACTIVE:
            return False, f"Account {account_data['status']}"
        
        # Simulate random failures (5% chance)
        if random.random() < 0.05:
            failure_reasons = ["Connection timeout", "Rate limited", "Temporary ban"]
            return False, random.choice(failure_reasons)
        
        # Create stylized message with account identifier
        account_name = account_data["name"]
        
        # Different message styling for each account
        styles = [
            message,  # Original
            f"• {message}",  # Bullet
            f"⚡ {message}",  # With emoji
            f">> {message}",  # Arrow
            f"★ {message}",  # Star
            f"◆ {message}",  # Diamond
        ]
        
        styled_message = random.choice(styles)
        
        # Add subtle account signature (optional)
        if random.random() < 0.3:  # 30% chance to add signature
            styled_message += f" ᵇʸ {account_name[-1]}"  # Just last character as signature
        
        # Send the message (from main client but styled as different account)
        await client.send_message(chat_id, styled_message)
        
        # Update account stats
        account_data["last_used"] = datetime.now().isoformat()
        account_data["total_summons"] = account_data.get("total_summons", 0) + 1
        
        # Update global stats
        SUMMON_STATS["successful_summons"] += 1
        
        return True, "Message sent"
        
    except FloodWaitError as e:
        return False, f"Flood wait: {e.seconds}s"
    except Exception as e:
        return False, str(e)

# ============================================================================
# PLUGIN COMMANDS
# ============================================================================

# ADD VIRTUAL ACCOUNTS COMMAND
@client.on(events.NewMessage(pattern=r'\.addaccounts?(\s+(\d+))?'))
async def add_accounts_handler(event):
    """Add virtual accounts to the summon pool"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        count = int(command_arg) if command_arg else 1
        
        if count <= 0 or count > 20:
            await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Count must be between 1-20', 'bold')}")
            return
        
        # Add virtual accounts
        added = add_virtual_account(count)
        
        success_text = f"""
{get_emoji('adder2')} {convert_font('VIRTUAL ACCOUNTS ADDED', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('SUMMON POOL EXPANDED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Added:', 'bold')} {added} virtual accounts
{get_emoji('adder1')} {convert_font('Total Pool:', 'bold')} {len(VIRTUAL_ACCOUNTS)} accounts
{get_emoji('adder4')} {convert_font('Active:', 'bold')} {len([a for a in VIRTUAL_ACCOUNTS.values() if a['status'] == STATUS_ACTIVE])}

{get_emoji('main')} {convert_font('Ready for summoning!', 'bold')}
Use `{prefix}summon <text> <count>` to test
        """.strip()
        
        await safe_send_with_entities(event, success_text)
        
    except ValueError:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Invalid number format!', 'bold')}")
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Error:', 'bold')} {str(e)}")

# CHECK ACCOUNTS STATUS
@client.on(events.NewMessage(pattern=r'\.checkaccounts?'))
async def check_accounts_handler(event):
    """Check status of all virtual accounts"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        # Update account statuses
        simulate_account_health_check()
        
        if not VIRTUAL_ACCOUNTS:
            empty_text = f"""
{get_emoji('check')} {convert_font('NO ACCOUNTS', 'mono')}

{get_emoji('main')} No virtual accounts in pool
{get_emoji('adder1')} Use `{get_prefix()}addaccounts 5` to add accounts
            """.strip()
            await safe_send_with_entities(event, empty_text)
            return
        
        active_count = len([a for a in VIRTUAL_ACCOUNTS.values() if a['status'] == STATUS_ACTIVE])
        dead_count = len([a for a in VIRTUAL_ACCOUNTS.values() if a['status'] == STATUS_DEAD])
        banned_count = len([a for a in VIRTUAL_ACCOUNTS.values() if a['status'] == STATUS_BANNED])
        
        check_text = f"""
{get_emoji('main')} {convert_font('ACCOUNT POOL STATUS', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder1')} {convert_font('VIRTUAL ACCOUNTS OVERVIEW', 'mono')} {get_emoji('adder1')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Total Accounts:', 'bold')} {len(VIRTUAL_ACCOUNTS)}
{get_emoji('adder2')} {convert_font('Active:', 'bold')} {active_count} ({round(active_count/len(VIRTUAL_ACCOUNTS)*100)}%)
{get_emoji('adder3')} {convert_font('Dead:', 'bold')} {dead_count}
{get_emoji('adder5')} {convert_font('Banned:', 'bold')} {banned_count}

╔══════════════════════════════════╗
   {get_emoji('adder4')} {convert_font('RECENT ACCOUNTS', 'mono')} {get_emoji('adder4')}
╚══════════════════════════════════╝

"""
        
        # Show first 8 accounts
        count = 0
        for account_id, data in list(VIRTUAL_ACCOUNTS.items())[:8]:
            count += 1
            status = data['status']
            total_summons = data.get('total_summons', 0)
            name = data.get('name', account_id)
            
            status_emoji = {
                STATUS_ACTIVE: get_emoji('adder2'),
                STATUS_DEAD: get_emoji('adder3'),
                STATUS_BANNED: get_emoji('adder5'),
                STATUS_UNKNOWN: get_emoji('adder6')
            }.get(status, get_emoji('adder6'))
            
            check_text += f"""
{status_emoji} {convert_font(f'#{count}', 'bold')} {convert_font(name, 'mono')}
{get_emoji('check')} Status: {status} | Summons: {total_summons}

"""
        
        if len(VIRTUAL_ACCOUNTS) > 8:
            check_text += f"{get_emoji('adder6')} ... and {len(VIRTUAL_ACCOUNTS) - 8} more accounts\n\n"
        
        check_text += f"""
{get_emoji('main')} {convert_font('Pool Health:', 'bold')} {'✅ Good' if active_count >= 3 else '⚠️ Low'}
{get_emoji('adder1')} Available for summon: {active_count} accounts
        """.strip()
        
        await safe_send_with_entities(event, check_text)
        
    except Exception as e:
        await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Check error:', 'bold')} {str(e)}")

# MAIN SUMMON COMMAND
@client.on(events.NewMessage(pattern=r'\.summon(\s+(.+)\s+(\d+))?'))
async def summon_handler(event):
    """Main summon command - simulate multiple accounts sending messages"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_parts = event.pattern_match.groups()
        
        if not command_parts[1]:
            # Show usage
            available_count = len([a for a in VIRTUAL_ACCOUNTS.values() if a['status'] == STATUS_ACTIVE])
            
            usage_text = f"""
{get_emoji('main')} {convert_font('SUMMON COMMAND', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('adder1')} {convert_font('MASS VIRTUAL SUMMONING', 'mono')} {get_emoji('adder1')}
╚══════════════════════════════════╝

{get_emoji('check')} {convert_font('Format:', 'bold')} `{prefix}summon <text> <count>`

{get_emoji('adder2')} {convert_font('Examples:', 'bold')}
• `{prefix}summon gacor 10` - 10 virtual accounts say "gacor"
• `{prefix}summon hello world 5` - 5 accounts say "hello world" 
• `{prefix}summon 🚀 15` - 15 accounts send rocket emoji

{get_emoji('adder4')} {convert_font('Features:', 'bold')}
{get_emoji('check')} Smart account selection (least recently used)
{get_emoji('check')} Natural random delays (1-4 seconds)
{get_emoji('check')} Different message styling per account
{get_emoji('check')} Automatic dead account skipping
{get_emoji('check')} Real-time progress updates

{get_emoji('main')} {convert_font('Available accounts:', 'bold')} {available_count}
{get_emoji('adder6')} {convert_font('Max per summon:', 'bold')} 25 accounts

{get_emoji('adder3')} Note: This uses virtual accounts (no external sessions needed!)
            """.strip()
            await safe_send_with_entities(event, usage_text)
            return
        
        message_text = command_parts[1].strip()
        count = int(command_parts[2]) if command_parts[2] else 1
        
        if count <= 0 or count > 25:
            await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Count must be between 1-25', 'bold')}")
            return
        
        if not message_text:
            await safe_send_with_entities(event, f"{get_emoji('adder3')} {convert_font('Message text cannot be empty', 'bold')}")
            return
        
        # Get available accounts
        available_accounts = get_available_accounts(count)
        
        if not available_accounts:
            no_accounts_text = f"""
{get_emoji('adder3')} {convert_font('NO ACTIVE ACCOUNTS', 'mono')}

{get_emoji('check')} No virtual accounts available for summoning
{get_emoji('main')} Use `{get_prefix()}addaccounts 10` to add accounts
{get_emoji('adder1')} Use `{get_prefix()}checkaccounts` to see status
            """.strip()
            await safe_send_with_entities(event, no_accounts_text)
            return
        
        actual_count = min(count, len(available_accounts))
        if actual_count < count:
            await safe_send_with_entities(event, f"{get_emoji('adder1')} {convert_font(f'Only {actual_count} accounts available (requested {count})', 'mono')}")
        
        # Show starting message
        s
