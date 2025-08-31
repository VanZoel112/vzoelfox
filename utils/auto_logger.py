#!/usr/bin/env python3
"""
Auto Logger Utility for VzoelFox Userbot - Automatic Log Sending via Bot
Fitur: Automatic log forwarding, bot integration, activity monitoring
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Automatic Logging System
"""

import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient

class AutoLogger:
    def __init__(self):
        self.bot_config = None
        self.bot_client = None
        self.log_queue = []
        self.is_running = False
        
    def load_config(self):
        """Load bot configuration"""
        try:
            bot_config_path = os.path.expanduser("~/.vzoelfox_bots/bot_config.json")
            if os.path.exists(bot_config_path):
                with open(bot_config_path, 'r') as f:
                    self.bot_config = json.load(f)
                return True
        except:
            pass
        return False
    
    async def initialize_bot(self):
        """Initialize bot client for logging"""
        if not self.bot_config or not self.bot_config.get('bot_token'):
            return False
        
        try:
            self.bot_client = TelegramClient(
                'auto_logger_bot', 
                api_id=os.getenv('API_ID'), 
                api_hash=os.getenv('API_HASH')
            )
            await self.bot_client.start(bot_token=self.bot_config['bot_token'])
            return True
        except Exception as e:
            print(f"AutoLogger initialization error: {e}")
            return False
    
    async def send_log(self, message, log_type="INFO"):
        """Send log message via bot"""
        if not self.bot_client or not self.bot_config:
            return False
        
        try:
            # Premium emojis mapping
            emoji_map = {
                "INFO": "⚙️",
                "SUCCESS": "✅", 
                "WARNING": "⛈",
                "ERROR": "😈",
                "ACTIVITY": "🎚️",
                "SYSTEM": "👽"
            }
            
            emoji = emoji_map.get(log_type, "🤩")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            log_message = f"""
{emoji} **VZOEL LOG - {log_type}**

🕐 **Time**: {timestamp}
📋 **Message**: {message}
🤖 **Source**: VzoelFox Userbot
📍 **Type**: {log_type}

👽 Auto-logged by Vzoel Assistant
            """.strip()
            
            log_group_id = self.bot_config.get('log_group_id')
            if log_group_id:
                await self.bot_client.send_message(log_group_id, log_message)
                return True
        except Exception as e:
            print(f"AutoLogger send error: {e}")
        
        return False
    
    def queue_log(self, message, log_type="INFO"):
        """Queue log for batch sending"""
        self.log_queue.append({
            'message': message,
            'log_type': log_type,
            'timestamp': datetime.now().isoformat()
        })
    
    async def process_queue(self):
        """Process queued logs"""
        if not self.log_queue:
            return
        
        for log_item in self.log_queue[:5]:  # Process max 5 at a time
            await self.send_log(log_item['message'], log_item['log_type'])
        
        # Remove processed items
        self.log_queue = self.log_queue[5:]
    
    async def start_auto_logging(self):
        """Start automatic logging service"""
        if self.is_running:
            return
        
        if not self.load_config():
            print("AutoLogger: No bot config found")
            return
        
        if not await self.initialize_bot():
            print("AutoLogger: Bot initialization failed") 
            return
        
        self.is_running = True
        print("AutoLogger: Service started")
        
        # Send startup log
        await self.send_log("VzoelFox Userbot started - AutoLogger active", "SYSTEM")
        
        # Background queue processing
        while self.is_running:
            try:
                await self.process_queue()
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"AutoLogger queue processing error: {e}")
                await asyncio.sleep(30)
    
    async def stop_auto_logging(self):
        """Stop automatic logging service"""
        self.is_running = False
        
        if self.bot_client:
            await self.send_log("VzoelFox Userbot stopped - AutoLogger service ended", "SYSTEM")
            await self.bot_client.disconnect()
        
        print("AutoLogger: Service stopped")
    
    def log_activity(self, activity, details=""):
        """Log userbot activity"""
        message = f"Activity: {activity}"
        if details:
            message += f" | Details: {details}"
        self.queue_log(message, "ACTIVITY")
    
    def log_command(self, command, user_id):
        """Log command usage"""
        message = f"Command '{command}' executed by user {user_id}"
        self.queue_log(message, "INFO")
    
    def log_error(self, error_msg, plugin="Unknown"):
        """Log error"""
        message = f"Plugin '{plugin}' error: {error_msg}"
        self.queue_log(message, "ERROR")
    
    def log_success(self, action):
        """Log success action"""
        message = f"Success: {action}"
        self.queue_log(message, "SUCCESS")
    
    def log_warning(self, warning_msg):
        """Log warning"""
        self.queue_log(warning_msg, "WARNING")

# Global auto logger instance
auto_logger = AutoLogger()

# Helper functions for easy usage
async def log_activity(activity, details=""):
    """Quick log activity"""
    auto_logger.log_activity(activity, details)

async def log_command(command, user_id):
    """Quick log command"""
    auto_logger.log_command(command, user_id)

async def log_error(error_msg, plugin="Unknown"):
    """Quick log error"""
    auto_logger.log_error(error_msg, plugin)

async def log_success(action):
    """Quick log success"""
    auto_logger.log_success(action)

async def log_warning(warning_msg):
    """Quick log warning"""
    auto_logger.log_warning(warning_msg)

async def start_logging_service():
    """Start the auto logging service"""
    await auto_logger.start_auto_logging()

async def stop_logging_service():
    """Stop the auto logging service"""
    await auto_logger.stop_auto_logging()

# Export for easy import
__all__ = [
    'AutoLogger', 'auto_logger', 
    'log_activity', 'log_command', 'log_error', 'log_success', 'log_warning',
    'start_logging_service', 'stop_logging_service'
]