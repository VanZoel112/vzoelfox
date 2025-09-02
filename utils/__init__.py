#!/usr/bin/env python3
"""
Utils package for VzoelFox Userbot
Contains font helper, premium emoji helper, and auto logger utilities
"""

# Make utils a proper Python package
from .font_helper import convert_font, process_markdown_bold, process_markdown_mono, process_all_markdown
from .premium_emoji_helper import get_emoji, create_premium_entities, safe_send_premium

__all__ = [
    'convert_font',
    'process_markdown_bold', 
    'process_markdown_mono',
    'process_all_markdown',
    'get_emoji',
    'create_premium_entities',
    'safe_send_premium'
]