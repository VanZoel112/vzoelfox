#!/usr/bin/env python3
"""
Configuration file for Vzoel Assistant
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_session")

# Bot settings
OWNER_ID = int(os.getenv("OWNER_ID", "0")) if os.getenv("OWNER_ID") else None
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"

# Feature settings
MAX_SPAM_COUNT = int(os.getenv("MAX_SPAM_COUNT", "10"))
NOTIFICATION_CHAT = os.getenv("NOTIFICATION_CHAT", "me")

# Database settings (optional)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///vzoel_assistant.db")

# Validation
if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH must be set in .env file!")

print(f"✅ Config loaded - Session: {SESSION_NAME}")
