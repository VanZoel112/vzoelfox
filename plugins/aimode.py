"""
AIMode & AI Responder Plugin for Vzoel Assistant
Fitur: Mode AI otomatis dengan premium emoji support, env assetjson, config & status persist di SQLite, model failover otomatis.
Founder Userbot: Vzoel Fox's Ltpn 🤩
"""

import sqlite3
import os
import json
from datetime import datetime
from telethon import events
import asyncio
import aiohttp

PLUGIN_INFO = {
    "name": "aimode",
    "version": "2.0.0",
    "description": "AI Mode & Responder dengan OpenAI GPT, config persist SQLite, premium emoji assetjson, failover otomatis.",
    "author": "Founder Userbot: Vzoel Fox's Ltpn 🤩",
    "commands": [".aimode on", ".aimode off", ".aimode status", ".aiconfig", ".ai"],
    "features": ["ai mode", "auto reply ai", "status/config in sqlite", "model failover"]
}

# Manual Premium Emoji Mapping berdasarkan data yang diberikan
PREMIUM_EMOJIS = {
    "main": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"},
    "check": {"emoji": "⚙️", "custom_emoji_id": "5794353925360457382"}, 
    "cross": {"emoji": "👽", "custom_emoji_id": "5321412209992033736"},
    "storm": {"emoji": "⛈", "custom_emoji_id": "5794407002566300853"},
    "success": {"emoji": "✅", "custom_emoji_id": "5793913811471700779"},
    "plane": {"emoji": "✈️", "custom_emoji_id": "5793973133559993740"},
    "devil": {"emoji": "😈", "custom_emoji_id": "5357404860566235955"},
    "slider": {"emoji": "🎚", "custom_emoji_id": "5794323465452394551"}
}
DB_FILE = "plugins/aimode.db"

async def safe_send_message(event, text):
    """Send message with basic reply"""
    await event.reply(text)

def safe_get_emoji(emoji_type):
    """Get premium emoji with manual mapping"""
    emoji_data = PREMIUM_EMOJIS.get(emoji_type, PREMIUM_EMOJIS["main"])
    return emoji_data["emoji"]

DEFAULT_CONFIG = {
    "primary": {
        "type": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "key": "proj_KTN67DL8wG2g1jMVCwW1vUQ2",
        "model": "gpt-3.5-turbo"
    },
    "backup": {
        "type": "openai",
        "endpoint": "https://api.openai.com/v1/chat/completions", 
        "key": "proj_KTN67DL8wG2g1jMVCwW1vUQ2",
        "model": "gpt-4o-mini"
    },
    "system_prompt": "You are Vzoel AI Assistant. MANDATORY: Start EVERY response with this EXACT format: '🤩 Saya AI yang Diciptakan oleh Vzoel Fox.. Izinkan saya menanggapi ini, [konteks]' where [konteks] matches the user's question context. Examples: \n- User asks 'Apa itu Python?' → Start with '🤩 Saya AI yang Diciptakan oleh Vzoel Fox.. Izinkan saya menanggapi ini, tentang bahasa pemrograman Python'\n- User says 'Hello' → Start with '🤩 Saya AI yang Diciptakan oleh Vzoel Fox.. Izinkan saya menanggapi ini, sapaan yang ramah'\n- User asks 'How to code?' → Start with '🤩 Saya AI yang Diciptakan oleh Vzoel Fox.. Izinkan saya menanggapi ini, tentang cara belajar coding'\n\nAlways follow this format, then give helpful response in user's language.",
    "max_tokens": 250,
    "temperature": 0.7,
    "cooldown": 5
}

def get_db_conn():
    try:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS aimode_status (
                chat_id INTEGER PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                updated_at TEXT
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS aimode_config (
                id INTEGER PRIMARY KEY,
                config TEXT,
                updated_at TEXT
            );
        """)
        return conn
    except Exception as e:
        print(f"[AIMode] Local SQLite error: {e}")
    return None

def set_aimode(chat_id, enabled):
    try:
        conn = get_db_conn()
        if not conn: return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT OR REPLACE INTO aimode_status (chat_id, enabled, updated_at) VALUES (?, ?, ?)",
            (chat_id, enabled, now)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[AIMode] Set status error: {e}")
        return False

def get_aimode(chat_id):
    try:
        conn = get_db_conn()
        if not conn: return False
        cur = conn.execute("SELECT enabled FROM aimode_status WHERE chat_id = ?", (chat_id,))
        row = cur.fetchone()
        conn.close()
        return row and row['enabled'] == 1
    except Exception as e:
        print(f"[AIMode] Get status error: {e}")
        return False

def get_config():
    try:
        conn = get_db_conn()
        if not conn: return DEFAULT_CONFIG
        cur = conn.execute("SELECT config FROM aimode_config WHERE id = 1")
        row = cur.fetchone()
        conn.close()
        if row and row['config']:
            cfg = json.loads(row['config'])
            # merge missing with default
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception as e:
        print(f"[AIMode] Load config error: {e}")
    return DEFAULT_CONFIG.copy()

def set_config(new_cfg):
    try:
        conn = get_db_conn()
        if not conn: return False
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT OR REPLACE INTO aimode_config (id, config, updated_at) VALUES (1, ?, ?)",
            (json.dumps(new_cfg), now)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[AIMode] Set config error: {e}")
        return False

async def aimode_handler(event):
    # Simple owner check
    OWNER_ID = 7847025168
    if event.sender_id != OWNER_ID:
        return
    chat = await event.get_chat()
    chat_id = chat.id
    args = event.text.split()
    if len(args) < 2:
        status = get_aimode(chat_id)
        txt = f"{safe_get_emoji('main')} AIMode status: {'ON' if status else 'OFF'}"
        await safe_send_message(event, txt)
        return
    cmd = args[1].lower()
    if cmd == "on":
        set_aimode(chat_id, 1)
        await safe_send_message(event, f"{safe_get_emoji('check')} AIMode *ON* di chat ini!")
    elif cmd == "off":
        set_aimode(chat_id, 0)
        await safe_send_message(event, f"{safe_get_emoji('cross')} AIMode *OFF* di chat ini!")
    elif cmd == "status":
        status = get_aimode(chat_id)
        await safe_send_message(event, f"{safe_get_emoji('main')} AIMode status: {'ON' if status else 'OFF'}")
    else:
        await safe_send_message(event, "Format: `.aimode on` / `.aimode off` / `.aimode status`")

async def aiconfig_handler(event):
    # Simple owner check
    OWNER_ID = 7847025168
    if event.sender_id != OWNER_ID:
        return
    args = event.text.split(maxsplit=2)
    cfg = get_config()
    if len(args) == 1 or (len(args) == 2 and args[1] == "show"):
        txt = f"{safe_get_emoji('main')} AIMode Config:\n\n<pre>{json.dumps(cfg, indent=2, ensure_ascii=False)}</pre>"
        await safe_send_message(event, txt)
    elif len(args) >= 3:
        try:
            field, value = args[1], args[2]
            # Only allow top-level fields
            if field in cfg:
                if value.startswith("{") or value.startswith("["):
                    cfg[field] = json.loads(value)
                else:
                    cfg[field] = value
                set_config(cfg)
                await safe_send_message(event, f"{safe_get_emoji('check')} Config `{field}` updated.")
            else:
                await safe_send_message(event, f"{safe_get_emoji('cross')} Field `{field}` not found.")
        except Exception as e:
            await safe_send_message(event, f"❌ Config update error: {e}")

async def ai_autoreply_handler(event):
    chat = await event.get_chat()
    chat_id = chat.id
    if get_aimode(chat_id) and not event.text.startswith('.'):
        msg = event.message.message
        cfg = get_config()
        reply = await ai_generate(msg, cfg)
        await safe_send_message(event, reply)

# ---- AI API Call & Failover ---- #
async def ai_generate(prompt, cfg):
    # Try primary, then backup if error
    reply = await call_ai(cfg['primary'], prompt, cfg)
    if not reply or "error" in reply.lower() or reply.startswith("❌"):
        reply = await call_ai(cfg['backup'], prompt, cfg)
        if not reply:
            reply = f"{safe_get_emoji('cross')} AI Error: All models failed."
    return reply

async def call_ai(api_cfg, prompt, cfg):
    try:
        headers = {}
        payload = {}
        model_type = api_cfg['type']
        endpoint = api_cfg['endpoint']
        key = api_cfg['key']
        model = api_cfg['model']
        temp = float(cfg.get('temperature', 0.6))
        max_tokens = int(cfg.get('max_tokens', 128))
        sys_prompt = cfg.get('system_prompt', '')

        if model_type == "huggingface":
            headers = {"Authorization": f"Bearer {key}"}
            payload = {"inputs": prompt}
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, dict) and "generated_text" in data:
                            return data["generated_text"]
                        elif isinstance(data, list) and len(data) and "generated_text" in data[0]:
                            return data[0]["generated_text"]
                        elif isinstance(data, dict) and "error" in data:
                            return f"❌ Error: {data['error']}"
                        return json.dumps(data)
                    return f"❌ Error: {resp.status}"
        elif model_type == "openai":
            headers = {
                "Authorization": f"Bearer {key}", 
                "Content-Type": "application/json"
            }
            messages = []
            if sys_prompt:
                messages.append({"role": "system", "content": sys_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temp
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "choices" in data and len(data["choices"]):
                            return data["choices"][0]["message"]["content"].strip()
                        return json.dumps(data)
                    else:
                        error_text = await resp.text()
                        return f"❌ OpenAI Error ({resp.status}): {error_text[:100]}"
                        
        elif model_type == "openrouter":
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}]
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temp
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "choices" in data and len(data["choices"]):
                            return data["choices"][0]["message"]["content"].strip()
                        return json.dumps(data)
                    return f"❌ Error: {resp.status}"
        
        return f"❌ Model type `{model_type}` not implemented."
    except Exception as e:
        return f"❌ AI API error: {e}"

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    client.add_event_handler(aimode_handler, events.NewMessage(pattern=r"\.aimode"))
    client.add_event_handler(aiconfig_handler, events.NewMessage(pattern=r"\.aiconfig"))
    client.add_event_handler(ai_autoreply_handler, events.NewMessage(incoming=True, func=lambda e: not e.is_private and not e.text.startswith('.')))
    print("[AIMode] Plugin loaded with manual emoji mapping.")