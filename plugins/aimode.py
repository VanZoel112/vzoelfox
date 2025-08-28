"""
AIMode & AI Responder Plugin for Vzoel Assistant
Fitur: Mode AI otomatis dengan premium emoji support, env assetjson, config & status persist di SQLite, model failover otomatis.
Author: Vzoel Fox's (Enhanced by Morgan)
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
    "description": "AI Mode & Responder, config persist di SQLite, emoji premium dari assetjson, failover model otomatis.",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [".aimode on", ".aimode off", ".aimode status", ".aiconfig", ".ai"],
    "features": ["ai mode", "auto reply ai", "status/config in sqlite", "model failover"]
}

try:
    from assetjson import create_plugin_environment
except ImportError:
    def create_plugin_environment(client=None): return {}

env = None
DB_FILE = "plugins/aimode.db"

DEFAULT_CONFIG = {
    "primary": {
        "type": "huggingface",
        "endpoint": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        "key": "hf_your_primary_token",
        "model": "microsoft/DialoGPT-medium"
    },
    "backup": {
        "type": "openrouter",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "key": "sk-or-your_backup_key",
        "model": "mistralai/mistral-7b-instruct:free"
    },
    "system_prompt": "You are a helpful AI assistant for Telegram.",
    "max_tokens": 128,
    "temperature": 0.6,
    "cooldown": 10
}

def get_db_conn():
    try:
        if env and 'get_db_connection' in env:
            return env['get_db_connection']('main')
    except Exception as e:
        if env and 'logger' in env:
            env['logger'].warning(f"[AIMode] DB from assetjson failed: {e}")
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
        if env and 'logger' in env:
            env['logger'].error(f"[AIMode] Local SQLite error: {e}")
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
        if env and 'logger' in env:
            env['logger'].error(f"[AIMode] Set status error: {e}")
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
        if env and 'logger' in env:
            env['logger'].error(f"[AIMode] Get status error: {e}")
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
        if env and 'logger' in env:
            env['logger'].error(f"[AIMode] Load config error: {e}")
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
        if env and 'logger' in env:
            env['logger'].error(f"[AIMode] Set config error: {e}")
        return False

async def aimode_handler(event):
    if not await env['is_owner'](event.sender_id): return
    chat = await event.get_chat()
    chat_id = chat.id
    args = event.text.split()
    if len(args) < 2:
        status = get_aimode(chat_id)
        txt = f"{env['get_emoji']('main')} AIMode status: {'ON' if status else 'OFF'}"
        await env['safe_send_with_entities'](event, txt)
        return
    cmd = args[1].lower()
    if cmd == "on":
        set_aimode(chat_id, 1)
        await env['safe_send_with_entities'](event, f"{env['get_emoji']('check')} AIMode *ON* di chat ini!")
    elif cmd == "off":
        set_aimode(chat_id, 0)
        await env['safe_send_with_entities'](event, f"{env['get_emoji']('cross')} AIMode *OFF* di chat ini!")
    elif cmd == "status":
        status = get_aimode(chat_id)
        await env['safe_send_with_entities'](event, f"{env['get_emoji']('main')} AIMode status: {'ON' if status else 'OFF'}")
    else:
        await env['safe_send_with_entities'](event, "Format: `.aimode on` / `.aimode off` / `.aimode status`")

async def aiconfig_handler(event):
    if not await env['is_owner'](event.sender_id): return
    args = event.text.split(maxsplit=2)
    cfg = get_config()
    if len(args) == 1 or (len(args) == 2 and args[1] == "show"):
        txt = f"{env['get_emoji']('main')} AIMode Config:\n\n<pre>{json.dumps(cfg, indent=2, ensure_ascii=False)}</pre>"
        await env['safe_send_with_entities'](event, txt)
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
                await env['safe_send_with_entities'](event, f"{env['get_emoji']('check')} Config `{field}` updated.")
            else:
                await env['safe_send_with_entities'](event, f"{env['get_emoji']('cross')} Field `{field}` not found.")
        except Exception as e:
            await env['safe_send_with_entities'](event, f"❌ Config update error: {e}")

async def ai_autoreply_handler(event):
    chat = await event.get_chat()
    chat_id = chat.id
    if get_aimode(chat_id) and not event.text.startswith('.'):
        msg = event.message.message
        cfg = get_config()
        reply = await ai_generate(msg, cfg)
        await env['safe_send_with_entities'](event, reply)

# ---- AI API Call & Failover ---- #
async def ai_generate(prompt, cfg):
    # Try primary, then backup if error
    reply = await call_ai(cfg['primary'], prompt, cfg)
    if not reply or "error" in reply.lower() or reply.startswith("❌"):
        reply = await call_ai(cfg['backup'], prompt, cfg)
        if not reply:
            reply = f"{env['get_emoji']('cross')} AI Error: All models failed."
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
        # Add more APIs here if needed (OpenAI, Gemini, etc)
        # else...
        return f"❌ Model type `{model_type}` not implemented."
    except Exception as e:
        return f"❌ AI API error: {e}"

def get_plugin_info():
    return PLUGIN_INFO

def setup(client):
    global env
    env = create_plugin_environment(client)
    client.add_event_handler(aimode_handler, events.NewMessage(pattern=r"\.aimode"))
    client.add_event_handler(aiconfig_handler, events.NewMessage(pattern=r"\.aiconfig"))
    client.add_event_handler(ai_autoreply_handler, events.NewMessage(incoming=True, func=lambda e: not e.is_private and not e.text.startswith('.')))
    if env and 'logger' in env:
        env['logger'].info("[AIMode] Plugin loaded and commands registered.")