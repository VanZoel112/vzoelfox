#!/usr/bin/env python3
"""
Font Helper Utility for VzoelFox Userbot - Universal Font Conversion System
Fitur: Bold, mono, italic Unicode font conversion, markdown processing
Founder Userbot: Vzoel Fox's Ltpn 🤩
Version: 1.0.0 - Universal Font System
"""

import re

# Unicode Font Maps
FONT_MAPS = {
    'bold': {
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢',
        'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
        's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈',
        'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑',
        'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    },
    'mono': {
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
        'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
        's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
        'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
        'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
        '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
    },
    'italic': {
        'a': '𝑎', 'b': '𝑏', 'c': '𝑐', 'd': '𝑑', 'e': '𝑒', 'f': '𝑓', 'g': '𝑔', 'h': 'ℎ', 'i': '𝑖',
        'j': '𝑗', 'k': '𝑘', 'l': '𝑙', 'm': '𝑚', 'n': '𝑛', 'o': '𝑜', 'p': '𝑝', 'q': '𝑞', 'r': '𝑟',
        's': '𝑞', 't': '𝑡', 'u': '𝑢', 'v': '𝑣', 'w': '𝑤', 'x': '𝑥', 'y': '𝑦', 'z': '𝑧',
        'A': '𝐴', 'B': '𝐵', 'C': '𝐶', 'D': '𝐷', 'E': '𝐸', 'F': '𝐹', 'G': '𝐺', 'H': '𝐻', 'I': '𝐼',
        'J': '𝐽', 'K': '𝐾', 'L': '𝐿', 'M': '𝑀', 'N': '𝑁', 'O': '𝑂', 'P': '𝑃', 'Q': '𝑄', 'R': '𝑅',
        'S': '𝑆', 'T': '𝑇', 'U': '𝑈', 'V': '𝑉', 'W': '𝑊', 'X': '𝑋', 'Y': '𝑌', 'Z': '𝑍'
    },
    'bold_italic': {
        'a': '𝒂', 'b': '𝒃', 'c': '𝒄', 'd': '𝒅', 'e': '𝒆', 'f': '𝒇', 'g': '𝒈', 'h': '𝒉', 'i': '𝒊',
        'j': '𝒋', 'k': '𝒌', 'l': '𝒍', 'm': '𝒎', 'n': '𝒏', 'o': '𝒐', 'p': '𝒑', 'q': '𝒒', 'r': '𝒓',
        's': '𝒔', 't': '𝒕', 'u': '𝒖', 'v': '𝒗', 'w': '𝒘', 'x': '𝒙', 'y': '𝒚', 'z': '𝒛',
        'A': '𝑨', 'B': '𝑩', 'C': '𝑪', 'D': '𝑫', 'E': '𝑬', 'F': '𝑭', 'G': '𝑮', 'H': '𝑯', 'I': '𝑰',
        'J': '𝑱', 'K': '𝑲', 'L': '𝑳', 'M': '𝑴', 'N': '𝑵', 'O': '𝑶', 'P': '𝑷', 'Q': '𝑸', 'R': '𝑹',
        'S': '𝑺', 'T': '𝑻', 'U': '𝑼', 'V': '𝑽', 'W': '𝑾', 'X': '𝑿', 'Y': '𝒀', 'Z': '𝒁'
    }
}

def convert_font(text, font_type='bold'):
    """
    Convert text to Unicode fonts (bold, mono, italic, bold_italic)
    
    Args:
        text (str): Text to convert
        font_type (str): Font type ('bold', 'mono', 'italic', 'bold_italic')
    
    Returns:
        str: Converted text with Unicode fonts
    """
    if font_type not in FONT_MAPS:
        return text
    
    font_map = FONT_MAPS[font_type]
    return ''.join([font_map.get(c, c) for c in text])

def process_markdown_bold(text):
    """
    Process **bold** markdown syntax and convert to Unicode bold
    
    Args:
        text (str): Text with **bold** markdown
    
    Returns:
        str: Text with Unicode bold conversion
    """
    def bold_replace(match):
        content = match.group(1)
        return convert_font(content, 'bold')
    
    # Replace **text** with Unicode bold
    result = re.sub(r'\*\*(.*?)\*\*', bold_replace, text)
    return result

def process_markdown_mono(text):
    """
    Process `mono` markdown syntax and convert to Unicode mono
    
    Args:
        text (str): Text with `mono` markdown
    
    Returns:
        str: Text with Unicode mono conversion
    """
    def mono_replace(match):
        content = match.group(1)
        return convert_font(content, 'mono')
    
    # Replace `text` with Unicode mono
    result = re.sub(r'`([^`]+)`', mono_replace, text)
    return result

def process_markdown_italic(text):
    """
    Process *italic* markdown syntax and convert to Unicode italic
    
    Args:
        text (str): Text with *italic* markdown
    
    Returns:
        str: Text with Unicode italic conversion
    """
    def italic_replace(match):
        content = match.group(1)
        return convert_font(content, 'italic')
    
    # Replace *text* with Unicode italic (avoid ** bold)
    result = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', italic_replace, text)
    return result

def process_all_markdown(text):
    """
    Process all markdown syntax (**, *, `) and convert to Unicode fonts
    
    Args:
        text (str): Text with markdown syntax
    
    Returns:
        str: Text with all markdown converted to Unicode fonts
    """
    # Process in order: bold, italic, mono
    text = process_markdown_bold(text)
    text = process_markdown_italic(text) 
    text = process_markdown_mono(text)
    return text

def bold(text):
    """Quick bold conversion"""
    return convert_font(text, 'bold')

def mono(text):
    """Quick mono conversion"""
    return convert_font(text, 'mono')

def italic(text):
    """Quick italic conversion"""
    return convert_font(text, 'italic')

def bold_italic(text):
    """Quick bold italic conversion"""
    return convert_font(text, 'bold_italic')

def clean_markdown(text):
    """Remove markdown syntax without conversion"""
    # Remove **bold**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove *italic*
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
    # Remove `mono`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text

# Export functions
__all__ = [
    'convert_font', 'process_markdown_bold', 'process_markdown_mono', 
    'process_markdown_italic', 'process_all_markdown', 'bold', 'mono', 
    'italic', 'bold_italic', 'clean_markdown', 'FONT_MAPS'
]