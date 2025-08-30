#!/usr/bin/env python3
"""
Blacklist GCast Plugin dengan Premium Emoji Support
File: plugins/blacklistgcast_premium.py
Founder : Vzoel Fox's Ltpn ( mapping by Kiya )
Description:
    Plugin ini menjaga blacklist GCast dan menambahkan dukungan 
    untuk emoji premium. Komentar diperjelas agar alur bot terlihat.
"""

import re
import os
import sys
import json
from datetime import datetime
from telethon import events
from telethon.tl.types import MessageEntityCustomEmoji, Channel, Chat, User
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError

# ===== Plugin Info =====
PLUGIN_INFO = {
    "name": "blacklistgcast_premium",
    "version": "1.1.1",
    "description": "Blacklist management with Premium Emoji support (manual mapping)",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".addbl", ".rmbl", ".listbl", ".clearbl"],
    "features": ["blacklist management", "gcast protection", "premium emojis"]
}

# ===== Auto Premium Emoji Mapping (UTF-16 auto-detection) =====
PREMIUM_EMOJIS = {
    "main":    {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "check":   {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"}, 
    "adder1":  {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "adder2":  {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "adder3":  {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "adder4":  {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "adder5":  {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "adder6":  {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}

# ===== Global Client Variable =====
client = None

# ===== Blacklist File Path =====
BLACKLIST_FILE = "gcast_blacklist.json"

# ===== Helper Functions =====
async def safe_send_message(event, text):
    """Send message with premium emoji entities"""
    try:
        entities = create_premium_emoji_entities(text)
        if entities:
            await event.reply(text, formatting_entities=entities)
        else:
            await event.reply(text)
    except Exception as e:
        # Fallback to regular message if premium emojis fail
        await event.reply(text)

def get_emoji(emoji_type):
    """Ambil emoji premium dari mapping manual"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

def get_utf16_length(emoji_char):
    """Get UTF-16 length of emoji character"""
    try:
        # Convert to UTF-16 and get byte length, then divide by 2 for character count
        utf16_bytes = emoji_char.encode('utf-16le')
        return len(utf16_bytes) // 2
    except:
        return 1

def create_premium_emoji_entities(text):
    """Automatically create MessageEntityCustomEmoji entities for premium emojis"""
    entities = []
    utf16_offset = 0
    
    # Process text character by character to get accurate UTF-16 offsets
    for i, char in enumerate(text):
        # Check if this character matches any premium emoji
        for emoji_name, emoji_data in PREMIUM_EMOJIS.items():
            if char == emoji_data["emoji"]:
                # Get actual UTF-16 length of this emoji
                emoji_length = get_utf16_length(char)
                
                # Create custom emoji entity with automatic offset/length
                entity = MessageEntityCustomEmoji(
                    offset=utf16_offset,
                    length=emoji_length,
                    document_id=int(emoji_data["custom_emoji_id"])
                )
                entities.append(entity)
                break
        
        # Update UTF-16 offset for next character
        utf16_offset += get_utf16_length(char)
    
    return entities

def analyze_emoji_positions(text):
    """Debug function to analyze emoji positions in text"""
    result = []
    utf16_offset = 0
    
    for i, char in enumerate(text):
        char_length = get_utf16_length(char)
        if char in [emoji_data["emoji"] for emoji_data in PREMIUM_EMOJIS.values()]:
            result.append({
                "char": char,
                "position": i,
                "utf16_offset": utf16_offset,
                "utf16_length": char_length,
                "is_emoji": True
            })
        utf16_offset += char_length
    
    return result

def safe_convert_font(text, font_type='bold'):
    """Convert teks ke format sederhana (bold / mono)"""
    if font_type == 'bold':
        return f"**{text}**"
    elif font_type == 'mono':
        return f"`{text}`"
    return text

async def is_owner_check(user_id):
    """Cek apakah user adalah owner"""
    OWNER_ID = 7847025168  # Ganti sesuai ID Master
    return user_id == OWNER_ID

def get_prefix():
    """Ambil prefix command dari environment atau default '.'"""
    try:
        return os.getenv("COMMAND_PREFIX", ".")
    except:
        return "."

def load_blacklist():
    """Load blacklist dari file JSON"""
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'blacklisted_chats' in data:
                    # Convert old format ke dict modern
                    blacklist_data = {}
                    for chat_id in data['blacklisted_chats']:
                        blacklist_data[int(chat_id)] = {
                            'title': f'Chat {chat_id}',
                            'type': 'Unknown',
                            'added_date': datetime.now().isoformat(),
                            'added_by': 'legacy'
                        }
                    return blacklist_data
                elif isinstance(data, dict):
                    # New format, pastikan key adalah angka
                    return {int(k): v for k, v in data.items() if k.lstrip('-').isdigit()}
        return {}
    except Exception as e:
        print(f"Error loading blacklist: {e}")
        return {}

def save_blacklist(blacklist):
    """Simpan blacklist ke file JSON"""
    try:
        data = {str(k): v for k, v in blacklist.items()}
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving blacklist: {e}")
        return False

async def get_chat_info(chat_id):
    """Ambil info chat: title & type"""
    try:
        entity = await client.get_entity(chat_id)
        if isinstance(entity, Channel):
            chat_type = "Channel" if entity.broadcast else "Supergroup"
            title = entity.title
        elif isinstance(entity, Chat):
            chat_type = "Group"
            title = entity.title
        else:
            chat_type = "Unknown"
            title = str(chat_id)
        return {'title': title, 'type': chat_type, 'id': chat_id}
    except Exception:
        return {'title': f"Chat {chat_id}", 'type': "Unknown", 'id': chat_id}

def is_valid_chat_id(chat_id_str):
    """Validasi format chat ID"""
    try:
        int(chat_id_str)
        return True
    except ValueError:
        return False

# ===== Event Handlers =====
# Tambah / hapus / list / clear blacklist dengan komentar rapi
# (seluruh logic asli tidak diubah, cuma komentar & mapping premium emoji diperbarui)
# ===== ADD BLACKLIST COMMAND =====
async def add_blacklist_handler(event):
    """Tambahkan chat ke blacklist GCast"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        blacklist = load_blacklist()
        
        # Jika tidak ada argumen, gunakan chat saat ini
        if not command_arg or not command_arg.strip():
            chat_id = event.chat_id
            source = "current chat"
        else:
            # Validasi chat ID manual
            chat_id_str = command_arg.strip()
            if not is_valid_chat_id(chat_id_str):
                error_text = f"""
{get_emoji('adder3')} {safe_convert_font('INVALID CHAT ID', 'mono')}
{get_emoji('check')} Gunakan format chat ID valid:
• Negatif untuk group/channel
• Contoh: -1001234567890
{get_emoji('main')} Atau pakai `{prefix}addbl` di chat target
                """.strip()
                await safe_send_message(event, error_text)
                return
            
            chat_id = int(chat_id_str)
            source = "manual ID"
        
        # Cek apakah sudah blacklisted
        if chat_id in blacklist:
            already_text = f"""
{get_emoji('adder1')} {safe_convert_font('ALREADY BLACKLISTED', 'mono')}
{get_emoji('check')} Chat sudah ada di blacklist
{get_emoji('main')} Gunakan `{prefix}listbl` untuk melihat semua
            """.strip()
            await safe_send_message(event, already_text)
            return
        
        # Ambil info chat
        chat_info = await get_chat_info(chat_id)
        
        # Tambahkan ke blacklist
        blacklist[chat_id] = {
            'title': chat_info['title'],
            'type': chat_info['type'],
            'added_date': datetime.now().isoformat(),
            'added_by': source
        }
        
        # Simpan ke file
        if save_blacklist(blacklist):
            success_text = f"""
{get_emoji('adder2')} {safe_convert_font('BLACKLIST ADDED', 'mono')}
╔══════════════════════════════════╗
   {get_emoji('main')} {safe_convert_font('GCAST PROTECTION ACTIVE', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝
{get_emoji('check')} {safe_convert_font('Chat:', 'bold')} {safe_convert_font(chat_info['title'], 'mono')}
{get_emoji('adder1')} {safe_convert_font('Type:', 'bold')} {chat_info['type']}
{get_emoji('adder4')} {safe_convert_font('ID:', 'bold')} {chat_id}
{get_emoji('adder5')} {safe_convert_font('Added:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{get_emoji('adder6')} {safe_convert_font('Protection Status:', 'bold')}
{get_emoji('check')} GCast messages will be blocked
{get_emoji('check')} Automatic filtering enabled
{get_emoji('check')} Persistent across bot restarts
{get_emoji('main')} Total blacklisted chats: {safe_convert_font(str(len(blacklist)), 'bold')}
            """.strip()
            await safe_send_message(event, success_text)
        else:
            error_text = f"""
{get_emoji('adder3')} {safe_convert_font('SAVE ERROR', 'mono')}
{get_emoji('check')} Gagal menyimpan blacklist
{get_emoji('main')} Periksa permission bot
            """.strip()
            await safe_send_message(event, error_text)
        
    except Exception as e:
        await safe_send_message(event, f"{get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# ===== REMOVE BLACKLIST COMMAND =====
async def remove_blacklist_handler(event):
    """Hapus chat dari blacklist GCast"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        blacklist = load_blacklist()
        
        # Jika tidak ada argumen, gunakan chat saat ini
        if not command_arg or not command_arg.strip():
            chat_id = event.chat_id
        else:
            chat_id_str = command_arg.strip()
            if not is_valid_chat_id(chat_id_str):
                error_text = f"""
{get_emoji('adder3')} {safe_convert_font('INVALID CHAT ID', 'mono')}
{get_emoji('check')} Gunakan chat ID valid
{get_emoji('main')} Contoh: `{prefix}rmbl -1001234567890`
                """.strip()
                await safe_send_message(event, error_text)
                return
            chat_id = int(chat_id_str)
        
        # Cek apakah ada di blacklist
        if chat_id not in blacklist:
            not_found_text = f"""
{get_emoji('adder1')} {safe_convert_font('NOT IN BLACKLIST', 'mono')}
{get_emoji('check')} Chat belum ada di blacklist
{get_emoji('main')} Gunakan `{prefix}listbl` untuk melihat semua
            """.strip()
            await safe_send_message(event, not_found_text)
            return
        
        # Ambil info chat sebelum dihapus
        chat_data = blacklist[chat_id]
        
        # Hapus dari blacklist
        del blacklist[chat_id]
        
        # Simpan perubahan
        if save_blacklist(blacklist):
            removed_text = f"""
{get_emoji('adder4')} {safe_convert_font('BLACKLIST REMOVED', 'mono')}
╔══════════════════════════════════╗
   {get_emoji('main')} {safe_convert_font('GCAST ACCESS RESTORED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝
{get_emoji('check')} {safe_convert_font('Chat:', 'bold')} {safe_convert_font(chat_data['title'], 'mono')}
{get_emoji('adder2')} {safe_convert_font('Type:', 'bold')} {chat_data['type']}
{get_emoji('adder3')} {safe_convert_font('ID:', 'bold')} {chat_id}
{get_emoji('adder5')} {safe_convert_font('Removed:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{get_emoji('adder6')} {safe_convert_font('Access Status:', 'bold')}
{get_emoji('check')} GCast messages will be delivered
{get_emoji('check')} Chat unprotected
{get_emoji('check')} Changes saved permanently
{get_emoji('main')} Remaining blacklisted chats: {safe_convert_font(str(len(blacklist)), 'bold')}
            """.strip()
            await safe_send_message(event, removed_text)
        else:
            error_text = f"""
{get_emoji('adder3')} {safe_convert_font('SAVE ERROR', 'mono')}
{get_emoji('check')} Gagal menyimpan perubahan
{get_emoji('main')} Periksa permission bot
            """.strip()
            await safe_send_message(event, error_text)
        
    except Exception as e:
        await safe_send_message(event, f"{get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# ===== LIST BLACKLIST COMMAND =====
async def list_blacklist_handler(event):
    """Tampilkan semua chat yang di-blacklist"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        blacklist = load_blacklist()
        prefix = get_prefix()
        
        if not blacklist:
            empty_text = f"""
{get_emoji('check')} {safe_convert_font('GCAST BLACKLIST', 'mono')}
{get_emoji('main')} Tidak ada chat yang di-blacklist
{get_emoji('adder1')} Semua chat akan menerima gcast
{get_emoji('adder2')} {safe_convert_font('Commands:', 'bold')}
• `{prefix}addbl` - Tambah chat saat ini
• `{prefix}addbl <chat_id>` - Tambah chat spesifik
            """.strip()
            await safe_send_message(event, empty_text)
            return
        
        # Buat list dengan maksimal 15 chat untuk menghindari batas pesan
        list_text = f"""
{get_emoji('adder6')} {safe_convert_font('GCAST BLACKLIST', 'mono')}
╔══════════════════════════════════╗
   {get_emoji('main')} {safe_convert_font('PROTECTED CHATS LIST', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝
{get_emoji('check')} {safe_convert_font('Total Blacklisted:', 'bold')} {len(blacklist)} chats
"""
        count = 0
        for chat_id, data in list(blacklist.items())[:15]:
            count += 1
            title = data.get('title', f'Chat {chat_id}')[:25]
            chat_type = data.get('type', 'Unknown')
            added_date = datetime.fromisoformat(data.get('added_date', datetime.now().isoformat()))
            list_text += f"""
{get_emoji('adder1')} {safe_convert_font(f'#{count}', 'bold')} {safe_convert_font(title, 'mono')}
{get_emoji('adder2')} {safe_convert_font('Type:', 'mono')} {chat_type} | {safe_convert_font('ID:', 'mono')} {chat_id}
{get_emoji('adder4')} {safe_convert_font('Added:', 'mono')} {added_date.strftime('%m/%d %H:%M')}
"""
        if len(blacklist) > 15:
            list_text += f"{get_emoji('adder5')} ... and {len(blacklist) - 15} more chats\n\n"
        list_text += f"""
{get_emoji('adder3')} {safe_convert_font('Management:', 'bold')}
• `{prefix}rmbl <chat_id>` - Hapus dari blacklist
• `{prefix}clearbl confirm` - Hapus semua blacklist
• `{prefix}addbl` - Tambah chat saat ini
        """.strip()
        await safe_send_message(event, list_text)
        
    except Exception as e:
        await safe_send_message(event, f"{get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")
   # ===== CLEAR BLACKLIST COMMAND =====
async def clear_blacklist_handler(event):
    """Hapus semua chat dari blacklist (dengan konfirmasi)"""
    if not await is_owner_check(event.sender_id):
        return
    
    try:
        blacklist = load_blacklist()
        prefix = get_prefix()
        command_arg = event.pattern_match.group(2)
        
        if not blacklist:
            empty_text = f"""
{get_emoji('check')} {safe_convert_font('BLACKLIST STATUS', 'mono')}
{get_emoji('main')} Blacklist sudah kosong
{get_emoji('adder1')} Tidak ada chat untuk dihapus
            """.strip()
            await safe_send_message(event, empty_text)
            return
        
        # Cek konfirmasi
        if command_arg and 'confirm' in command_arg.lower():
            empty_blacklist = {}
            if save_blacklist(empty_blacklist):
                cleared_text = f"""
{get_emoji('adder4')} {safe_convert_font('BLACKLIST CLEARED', 'mono')}
╔══════════════════════════════════╗
   {get_emoji('main')} {safe_convert_font('ALL RESTRICTIONS REMOVED', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝
{get_emoji('check')} {safe_convert_font('Cleared:', 'bold')} {len(blacklist)} chats
{get_emoji('adder2')} {safe_convert_font('Status:', 'bold')} Semua chat bisa menerima gcast
{get_emoji('adder6')} {safe_convert_font('Time:', 'bold')} {datetime.now().strftime('%H:%M:%S')}
{get_emoji('main')} {safe_convert_font('Blacklist sekarang kosong', 'bold')}
{get_emoji('adder1')} Gunakan `{prefix}addbl` untuk proteksi lagi
                """.strip()
                await safe_send_message(event, cleared_text)
            else:
                error_text = f"""
{get_emoji('adder3')} {safe_convert_font('CLEAR ERROR', 'mono')}
{get_emoji('check')} Gagal menyimpan perubahan
{get_emoji('main')} Periksa permission bot
                """.strip()
                await safe_send_message(event, error_text)
        else:
            # Minta konfirmasi
            confirmation_text = f"""
{get_emoji('adder3')} {safe_convert_font('CLEAR CONFIRMATION REQUIRED', 'mono')}
╔══════════════════════════════════╗
   {get_emoji('main')} {safe_convert_font('DANGER ZONE', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝
{get_emoji('adder1')} {safe_convert_font('Ini akan menghapus SEMUA', 'bold')} {len(blacklist)} {safe_convert_font('blacklisted chats', 'bold')}
{get_emoji('adder2')} Semua chat akan menerima gcast lagi
{get_emoji('adder5')} {safe_convert_font('Aksi ini tidak bisa dibatalkan', 'bold')}
{get_emoji('check')} Kirim `{prefix}clearbl confirm` untuk melanjutkan
{get_emoji('main')} Atau pakai `{prefix}listbl` dulu
            """.strip()
            await safe_send_message(event, confirmation_text)
        
    except Exception as e:
        await safe_send_message(event, f"{get_emoji('adder3')} {safe_convert_font('Error:', 'bold')} {str(e)}")

# ===== Test Command for UTF-16 Emoji Detection =====
async def test_emoji_handler(event):
    """Test automatic UTF-16 emoji detection"""
    if not await is_owner_check(event.sender_id):
        return
    
    test_text = "⚙️⛈✅👽✈️😈🎚"
    analysis = analyze_emoji_positions(test_text)
    
    debug_text = f"""
{get_emoji('main')} **EMOJI UTF-16 ANALYSIS**

{get_emoji('check')} **Test Text:** `{test_text}`

{get_emoji('adder2')} **Automatic Detection Results:**
"""
    
    for item in analysis:
        debug_text += f"• {item['char']} → offset={item['utf16_offset']}, length={item['utf16_length']}\n"
    
    debug_text += f"""
{get_emoji('adder4')} **Total entities detected:** {len(analysis)}
{get_emoji('adder6')} Now using automatic UTF-16 calculation instead of manual mapping!
"""
    
    await safe_send_message(event, debug_text.strip())

# ===== PLUGIN INFO =====
def get_plugin_info():
    return PLUGIN_INFO

# ===== SETUP PLUGIN =====
def setup(client_instance):
    """Setup plugin: register event handlers"""
    global client
    client = client_instance
    
    # Registrasi semua handler
    client.add_event_handler(add_blacklist_handler, events.NewMessage(pattern=r"\.addbl(\s+(.+))?"))
    client.add_event_handler(remove_blacklist_handler, events.NewMessage(pattern=r"\.rmbl(\s+(.+))?"))
    client.add_event_handler(list_blacklist_handler, events.NewMessage(pattern=r"\.listbl"))
    client.add_event_handler(clear_blacklist_handler, events.NewMessage(pattern=r"\.clearbl(\s+(.+))?"))
    client.add_event_handler(test_emoji_handler, events.NewMessage(pattern=r"\.testemoji"))
    
    print(f"✅ [GCast Blacklist] Plugin loaded with auto UTF-16 emoji detection v{PLUGIN_INFO['version']}")
     
