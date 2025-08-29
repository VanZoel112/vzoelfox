#!/usr/bin/env python3
"""
🔍 VOICE CLONE VALIDATOR PLUGIN - Advanced Validation & Monitoring System
Fitur: Real-time validation, monitoring, dan troubleshooting voice cloning
Author: Vzoel Fox's (Enhanced by Morgan)  
Version: 1.0.0 - Validation Edition
"""

import asyncio
import json
import os
import time
import requests
import sqlite3
from datetime import datetime, timedelta
from telethon import events
import threading

# ===== PLUGIN INFO =====
PLUGIN_INFO = {
    "name": "voice_clone_validator", 
    "version": "1.0.0",
    "description": "🔍 Advanced validation & monitoring untuk voice cloning system",
    "author": "Vzoel Fox's (Enhanced by Morgan)",
    "commands": [
        ".vvalid check", ".vvalid monitor", ".vvalid quota", ".vvalid health",
        ".vvalid fix", ".vvalid report", ".vvalid optimize"
    ],
    "features": [
        "Real-time API validation", "Quota monitoring", "Error diagnosis",
        "Performance optimization", "Health checks", "Auto-fix issues"
    ]
}

# ===== CONFIGURATION =====
CONFIG_FILE = "voice_clone_config.json"
VALIDATOR_DB = "voice_clone_validator.db"
MONITOR_INTERVAL = 300  # 5 minutes

# Premium emoji configuration
PREMIUM_EMOJIS = {
    'valid': {'id': '5794407002566300853', 'char': '✅'},
    'invalid': {'id': '5357404860566235955', 'char': '❌'},
    'warning': {'id': '5794353925360457382', 'char': '⚠️'},
    'monitor': {'id': '5793913811471700779', 'char': '📊'},
    'fix': {'id': '5321412209992033736', 'char': '🔧'},
    'health': {'id': '5793973133559993740', 'char': '💚'}
}

def create_premium_message(emoji_key, text):
    emoji = PREMIUM_EMOJIS.get(emoji_key, {'char': '🔍'})
    return f"<emoji id='{emoji['id']}'>{emoji['char']}</emoji> {text}"

# ===== DATABASE FUNCTIONS =====
def init_validator_db():
    """Initialize validator database"""
    try:
        conn = sqlite3.connect(VALIDATOR_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                api_key_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                error_message TEXT,
                quota_remaining INTEGER,
                quota_reset_time TEXT,
                last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validation_type TEXT NOT NULL,
                provider TEXT,
                status TEXT NOT NULL,
                details TEXT,
                response_time REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                provider TEXT,
                value REAL,
                unit TEXT,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Validator DB init error: {e}")
        return False

def log_validation(validation_type, provider, status, details=None, response_time=None):
    """Log validation result"""
    try:
        conn = sqlite3.connect(VALIDATOR_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO validation_logs (validation_type, provider, status, details, response_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (validation_type, provider, status, details, response_time))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Log validation error: {e}")
        return False

def get_validation_history(hours=24):
    """Get validation history"""
    try:
        conn = sqlite3.connect(VALIDATOR_DB)
        cursor = conn.cursor()
        
        since_time = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT provider, status, COUNT(*) as count, AVG(response_time) as avg_response
            FROM validation_logs 
            WHERE timestamp > ?
            GROUP BY provider, status
        ''', (since_time.isoformat(),))
        
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Get validation history error: {e}")
        return []

# ===== VALIDATION FUNCTIONS =====
async def validate_api_comprehensive(provider, api_key):
    """Comprehensive API validation"""
    start_time = time.time()
    result = {
        'provider': provider,
        'status': 'unknown',
        'response_time': 0,
        'quota_info': {},
        'error': None,
        'features': [],
        'recommendations': []
    }
    
    try:
        if provider == "elevenlabs":
            headers = {"xi-api-key": api_key}
            
            # Test voices endpoint
            response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=15)
            result['response_time'] = time.time() - start_time
            
            if response.status_code == 200:
                result['status'] = 'valid'
                voices_data = response.json()
                result['features'] = [f"{len(voices_data.get('voices', []))} voices available"]
                
                # Get user info for quota
                try:
                    user_response = requests.get("https://api.elevenlabs.io/v1/user", headers=headers, timeout=10)
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        subscription = user_data.get('subscription', {})
                        result['quota_info'] = {
                            'tier': subscription.get('tier', 'free'),
                            'character_count': subscription.get('character_count', 0),
                            'character_limit': subscription.get('character_limit', 10000),
                            'reset_date': subscription.get('next_character_count_reset_unix', 0)
                        }
                        
                        # Calculate quota percentage
                        used = result['quota_info']['character_count']
                        limit = result['quota_info']['character_limit']
                        quota_pct = (used / limit * 100) if limit > 0 else 0
                        
                        if quota_pct > 90:
                            result['recommendations'].append('⚠️ Quota hampir habis! Consider upgrade.')
                        elif quota_pct > 75:
                            result['recommendations'].append('📊 Quota usage tinggi, monitor closely.')
                except:
                    pass
            
            elif response.status_code == 401:
                result['status'] = 'invalid'
                result['error'] = 'Invalid API key'
                result['recommendations'].append('🔑 Check API key di ElevenLabs dashboard')
            
            elif response.status_code == 429:
                result['status'] = 'rate_limited'
                result['error'] = 'Rate limit exceeded'
                result['recommendations'].append('⏳ Wait atau upgrade plan untuk rate limit lebih tinggi')
            
            else:
                result['status'] = 'error'
                result['error'] = f'HTTP {response.status_code}: {response.text[:100]}'
        
        elif provider == "openai":
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # Test models endpoint
            response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=15)
            result['response_time'] = time.time() - start_time
            
            if response.status_code == 200:
                result['status'] = 'valid'
                models_data = response.json()
                tts_models = [m for m in models_data.get('data', []) if 'tts' in m.get('id', '')]
                result['features'] = [f"{len(tts_models)} TTS models available"]
                
                # OpenAI doesn't provide quota info via API
                result['quota_info'] = {
                    'tier': 'pay-per-use',
                    'note': 'Check usage at platform.openai.com'
                }
                result['recommendations'].append('💰 Monitor usage di OpenAI dashboard')
            
            elif response.status_code == 401:
                result['status'] = 'invalid'
                result['error'] = 'Invalid API key'
                result['recommendations'].append('🔑 Check API key di OpenAI platform')
            
            else:
                result['status'] = 'error'
                result['error'] = f'HTTP {response.status_code}: {response.text[:100]}'
        
        elif provider == "murf":
            headers = {"Authorization": f"Bearer {api_key}"}
            
            # Test voices endpoint (if available)
            response = requests.get("https://api.murf.ai/v1/voices", headers=headers, timeout=15)
            result['response_time'] = time.time() - start_time
            
            if response.status_code == 200:
                result['status'] = 'valid'
                result['features'] = ['Murf.ai API accessible']
                result['recommendations'].append('📊 Check quota di Murf.ai dashboard')
            
            elif response.status_code == 401:
                result['status'] = 'invalid'
                result['error'] = 'Invalid API key'
                result['recommendations'].append('🔑 Check API key di Murf.ai dashboard')
            
            else:
                result['status'] = 'error'
                result['error'] = f'HTTP {response.status_code}: {response.text[:100]}'
        
    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['error'] = 'Request timeout'
        result['recommendations'].append('🌐 Check internet connection')
    
    except requests.exceptions.ConnectionError:
        result['status'] = 'connection_error'
        result['error'] = 'Connection failed'
        result['recommendations'].append('🔌 Check network connectivity')
    
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        result['recommendations'].append('🔧 Contact support jika masalah berlanjut')
    
    # Log validation
    log_validation('comprehensive', provider, result['status'], 
                  result.get('error'), result['response_time'])
    
    return result

async def health_check_system():
    """Perform system health check"""
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy',
        'components': {},
        'issues': [],
        'recommendations': []
    }
    
    try:
        # Check config file
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                health_report['components']['config'] = 'healthy'
            except json.JSONDecodeError:
                health_report['components']['config'] = 'corrupted'
                health_report['issues'].append('Config file corrupted')
                health_report['recommendations'].append('Run .vsetup auto to recreate config')
        else:
            health_report['components']['config'] = 'missing'
            health_report['issues'].append('Config file missing')
            health_report['recommendations'].append('Run .vsetup auto to create config')
        
        # Check directories
        required_dirs = ['temp_audio', 'voice_models', 'voice_clone_backups']
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                health_report['components'][f'dir_{dir_name}'] = 'healthy'
            else:
                health_report['components'][f'dir_{dir_name}'] = 'missing'
                health_report['recommendations'].append(f'Create directory: {dir_name}')
        
        # Check database
        if os.path.exists(VALIDATOR_DB):
            try:
                conn = sqlite3.connect(VALIDATOR_DB)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM validation_logs')
                log_count = cursor.fetchone()[0]
                conn.close()
                health_report['components']['database'] = 'healthy'
                health_report['components']['log_entries'] = log_count
            except:
                health_report['components']['database'] = 'corrupted'
                health_report['issues'].append('Validator database corrupted')
        else:
            health_report['components']['database'] = 'missing'
            health_report['recommendations'].append('Database will be created automatically')
        
        # Check API keys if config exists
        if health_report['components'].get('config') == 'healthy':
            api_status = {}
            for provider, key_info in config.get('api_keys', {}).items():
                key = key_info.get('key', '')
                if key.startswith('YOUR_'):
                    api_status[provider] = 'not_configured'
                else:
                    # Quick validation
                    result = await validate_api_comprehensive(provider, key)
                    api_status[provider] = result['status']
            
            health_report['components']['api_keys'] = api_status
        
        # Determine overall status
        if health_report['issues']:
            health_report['overall_status'] = 'needs_attention'
        
        # Add general recommendations
        if not health_report['recommendations']:
            health_report['recommendations'].append('✅ System berjalan dengan baik!')
        
    except Exception as e:
        health_report['overall_status'] = 'error'
        health_report['issues'].append(f'Health check error: {str(e)}')
    
    return health_report

# ===== EVENT HANDLERS =====
@client.on(events.NewMessage(pattern=r'^\.vvalid check$'))
async def validate_system(event):
    """Comprehensive system validation"""
    try:
        msg = await event.respond(create_premium_message('monitor', '**🔍 Starting comprehensive validation...**'))
        
        if not os.path.exists(CONFIG_FILE):
            await msg.edit(create_premium_message('invalid', '**No config found!** Run `.vsetup auto` first.'))
            return
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate each API
        api_results = []
        total_time = 0
        
        for provider, key_info in config.get('api_keys', {}).items():
            key = key_info.get('key', '')
            if not key.startswith('YOUR_'):
                await msg.edit(create_premium_message('monitor', f'**Validating {provider.title()}...**'))
                result = await validate_api_comprehensive(provider, key)
                api_results.append(result)
                total_time += result['response_time']
        
        # Format results
        if api_results:
            results_text = []
            for result in api_results:
                status_emoji = {
                    'valid': '✅',
                    'invalid': '❌', 
                    'error': '🔴',
                    'timeout': '⏰',
                    'rate_limited': '🚫'
                }.get(result['status'], '❓')
                
                provider_text = f"{status_emoji} **{result['provider'].title()}**"
                if result['status'] == 'valid':
                    provider_text += f" ({result['response_time']:.2f}s)"
                    if result.get('quota_info'):
                        quota = result['quota_info']
                        if 'character_count' in quota and 'character_limit' in quota:
                            used_pct = (quota['character_count'] / quota['character_limit'] * 100)
                            provider_text += f"\n   📊 Quota: {used_pct:.1f}% used"
                else:
                    provider_text += f"\n   ⚠️ {result.get('error', 'Unknown error')}"
                
                if result.get('recommendations'):
                    provider_text += f"\n   💡 {result['recommendations'][0]}"
                
                results_text.append(provider_text)
            
            final_result = f"""**🔍 Validation Complete!**

{chr(10).join(results_text)}

**Summary:**
• Total APIs: {len(api_results)}
• Valid: {len([r for r in api_results if r['status'] == 'valid'])}
• Average Response: {(total_time/len(api_results)):.2f}s

**Next:** `.vvalid monitor` for continuous monitoring"""
            
            await msg.edit(create_premium_message('valid', final_result))
        else:
            await msg.edit(create_premium_message('warning', '**No API keys configured!** Use `.vsetup keys` to add keys.'))
            
    except Exception as e:
        await event.respond(create_premium_message('invalid', f'**Validation error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.vvalid health$'))
async def system_health(event):
    """System health check"""
    try:
        msg = await event.respond(create_premium_message('health', '**💚 Running system health check...**'))
        
        health = await health_check_system()
        
        # Format health report
        status_emoji = '💚' if health['overall_status'] == 'healthy' else '⚠️'
        
        components_text = []
        for component, status in health['components'].items():
            if isinstance(status, str):
                emoji = {'healthy': '✅', 'missing': '❌', 'corrupted': '🔴'}.get(status, '❓')
                components_text.append(f"{emoji} {component.replace('_', ' ').title()}")
            elif isinstance(status, dict):
                for sub_comp, sub_status in status.items():
                    emoji = {'valid': '✅', 'invalid': '❌', 'not_configured': '⚪'}.get(sub_status, '❓')
                    components_text.append(f"  {emoji} {sub_comp.title()}")
        
        result = f"""**{status_emoji} System Health Report**

**Overall Status:** {health['overall_status'].replace('_', ' ').title()}

**Components:**
{chr(10).join(components_text)}

**Issues Found:** {len(health['issues'])}"""

        if health['issues']:
            result += f"\n{chr(10).join(f'• {issue}' for issue in health['issues'])}"
        
        if health['recommendations']:
            result += f"\n\n**Recommendations:**\n{chr(10).join(f'• {rec}' for rec in health['recommendations'])}"
        
        await msg.edit(create_premium_message('health', result))
        
    except Exception as e:
        await event.respond(create_premium_message('invalid', f'**Health check error:** {str(e)}'))

@client.on(events.NewMessage(pattern=r'^\.vvalid quota$'))
async def check_quota(event):
    """Check API quotas"""
    try:
        msg = await event.respond(create_premium_message('monitor', '**📊 Checking API quotas...**'))
        
        if not os.path.exists(CONFIG_FILE):
            await msg.edit(create_premium_message('invalid', '**No config found!** Run `.vsetup auto` first.'))
            return
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        quota_info = []
        for provider, key_info in config.get('api_keys', {}).items():
            key = key_info.get('key', '')
            if not key.startswith('YOUR_'):
                result = await validate_api_comprehensive(provider, key)
                if result['status'] == 'valid' and result.get('quota_info'):
                    quota = result['quota_info']
                    
                    if provider == 'elevenlabs':
                        used = quota.get('character_count', 0)
                        limit = quota.get('character_limit', 10000)
                        tier = quota.get('tier', 'free')
                        used_pct = (used / limit * 100) if limit > 0 else 0
                        
                        status_emoji = '🟢' if used_pct < 75 else '🟡' if used_pct < 90 else '🔴'
                        quota_info.append(f"""{status_emoji} **ElevenLabs ({tier.title()})**
• Used: {used:,} / {limit:,} chars ({used_pct:.1f}%)
• Remaining: {limit - used:,} chars""")
                    
                    elif provider == 'openai':
                        quota_info.append(f"""💰 **OpenAI (Pay-per-use)**
• Model: TTS-1 ($0.015/1k chars)
• Check usage: platform.openai.com""")
                    
                    else:
                        quota_info.append(f"""📊 **{provider.title()}**
• Check dashboard for quota info""")
        
        if quota_info:
            result = f"""**📊 API Quota Status**

{chr(10).join(quota_info)}

**Tips:**
• Monitor usage secara regular
• Set alerts untuk quota tinggi
• Consider upgrade jika diperlukan"""
            
            await msg.edit(create_premium_message('monitor', result))
        else:
            await msg.edit(create_premium_message('warning', '**No quota information available.** Configure API keys first.'))
            
    except Exception as e:
        await event.respond(create_premium_message('invalid', f'**Quota check error:** {str(e)}'))

# ===== INITIALIZATION =====
def setup():
    """Plugin setup function"""
    print("🔍 Voice Clone Validator Plugin loaded!")
    init_validator_db()
    return True

if __name__ == "__main__":
    setup()