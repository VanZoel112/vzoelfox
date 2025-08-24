# Vzoel Assistant Plugin System

Advanced plugin system for the Enhanced Vzoel Assistant with support for organized plugin directories and automatic loading.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Quick Start](#quick-start)
- [Plugin Development](#plugin-development)
- [Available Commands](#available-commands)
- [Sample Plugins](#sample-plugins)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Overview

The Enhanced Vzoel Assistant plugin system supports:

- **Automatic plugin discovery** from multiple locations
- **Organized directory structure** with subdirectories
- **Hot reloading** of plugins without restart
- **Detailed plugin information** and management
- **Command logging** and owner-only restrictions
- **Error handling** and debugging support

## Directory Structure

```
vzoel_assistant/
├── main.py                  # Main application
├── __init__.py              # Plugin system core
├── config.py                # Configuration
├── setup_plugins.py         # Setup script
├── *.py                     # Root level plugins
└── plugins/                 # Main plugins directory
    ├── __init__.py          # Plugins module
    ├── README.md            # This file
    ├── *.py                 # Plugin files
    ├── utils/               # Utility plugins
    │   ├── __init__.py
    │   └── *.py
    ├── fun/                 # Entertainment plugins
    │   ├── __init__.py
    │   └── *.py
    ├── admin/               # Administrative plugins
    │   ├── __init__.py
    │   └── *.py
    └── tools/               # Tool plugins
        ├── __init__.py
        └── *.py
```

## Quick Start

### 1. Setup Plugin Environment

Run the setup script to create the directory structure:

```bash
python setup_plugins.py
```

### 2. Start the Assistant

```bash
python main.py
```

### 3. Test Plugin Commands

```
.plugins        # List all loaded plugins
.test           # Test sample plugin
.echo Hello     # Echo command
.sysinfo        # System information
.dice           # Roll a dice
```

## Plugin Development

### Basic Plugin Template

```python
#!/usr/bin/env python3
"""
Plugin Name - Brief Description
Category: utils/fun/admin/tools
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}command'))
@owner_only
@log_command_usage
async def command_handler(event):
    """Command description"""
    await event.reply("Plugin response")
```

### Required Components

#### 1. Imports
```python
from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
```

#### 2. Event Registration
```python
@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}command'))
```

#### 3. Decorators
- `@owner_only` - Restricts command to owner only
- `@log_command_usage` - Logs command usage

#### 4. Handler Function
```python
async def handler_name(event):
    """Docstring describing the command"""
    # Command logic here
    await event.reply("Response")
```

### Command Patterns

#### Simple Command
```python
pattern=rf'{COMMAND_PREFIX}hello'
```

#### Command with Parameter
```python
pattern=rf'{COMMAND_PREFIX}echo (.+)'
# Access with: event.pattern_match.group(1)
```

#### Command with Optional Parameters
```python
pattern=rf'{COMMAND_PREFIX}count (\d+)'
# Access with: int(event.pattern_match.group(1))
```

#### Multiple Parameters
```python
pattern=rf'{COMMAND_PREFIX}send (\d+) (.+)'
# Access with: group(1) and group(2)
```

### Error Handling

Always include proper error handling:

```python
@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}risky'))
@owner_only
@log_command_usage
async def risky_handler(event):
    """Command with error handling"""
    try:
        # Risky operation
        result = some_operation()
        await event.edit(f"Success: {result}")
    except Exception as e:
        await event.edit(f"Error: {str(e)}")
```

## Available Commands

### Plugin Management
- `.plugins` - List loaded plugins by location
- `.plugininfo` - Detailed plugin information
- `.structure` - Show directory structure
- `.reload` - Reload all plugins

### Built-in Commands
- `.ping` - Test response time
- `.info` - Assistant information
- `.alive` - Status check
- `.help` - Command help
- `.logs` - Recent logs
- `.env` - Environment info

### Sample Plugin Commands
- `.test` - Test plugin functionality
- `.echo [message]` - Echo a message
- `.quote` - Random motivational quote
- `.countdown [seconds]` - Countdown timer
- `.sysinfo` - System information
- `.dice` - Roll a dice
- `.coinflip` - Flip a coin

## Sample Plugins

### 1. Basic Test Plugin (`plugins/test.py`)

```python
from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}test'))
@owner_only
@log_command_usage
async def test_handler(event):
    """Test plugin command"""
    await event.edit("Plugin system working!")
```

### 2. Utility Plugin (`plugins/utils/system_info.py`)

```python
import psutil
import platform
from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}sysinfo'))
@owner_only
@log_command_usage
async def sysinfo_handler(event):
    """Show system information"""
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    info = f"""
System: {platform.system()}
CPU: {cpu}%
Memory: {memory.percent}%
    """.strip()
    
    await event.edit(f"**System Info:**\n```\n{info}\n```")
```

### 3. Fun Plugin (`plugins/fun/dice.py`)

```python
import random
from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}dice'))
@owner_only
@log_command_usage
async def dice_handler(event):
    """Roll a dice"""
    result = random.randint(1, 6)
    await event.edit(f"Dice: {result}")
```

## Advanced Features

### Plugin with Configuration

```python
# Plugin configuration
PLUGIN_CONFIG = {
    'enabled': True,
    'max_requests': 10,
    'timeout': 30
}

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}configure'))
@owner_only
@log_command_usage
async def configure_handler(event):
    """Configure plugin settings"""
    # Configuration logic
    pass
```

### Plugin with Database

```python
import sqlite3

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('plugin_data.db')
    return conn

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}save (.+)'))
@owner_only
@log_command_usage
async def save_handler(event):
    """Save data to database"""
    data = event.pattern_match.group(1)
    
    with get_db_connection() as conn:
        conn.execute('INSERT INTO data (content) VALUES (?)', (data,))
        conn.commit()
    
    await event.edit("Data saved!")
```

### Plugin with External API

```python
import aiohttp

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}weather (.+)'))
@owner_only
@log_command_usage
async def weather_handler(event):
    """Get weather information"""
    city = event.pattern_match.group(1)
    
    async with aiohttp.ClientSession() as session:
        url = f"http://api.weather.com/{city}"
        async with session.get(url) as response:
            data = await response.json()
    
    await event.edit(f"Weather in {city}: {data['weather']}")
```

### Plugin with File Operations

```python
import os
import aiofiles

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}savefile (.+)'))
@owner_only
@log_command_usage
async def savefile_handler(event):
    """Save content to file"""
    content = event.pattern_match.group(1)
    filename = f"saved_{event.date.timestamp()}.txt"
    
    async with aiofiles.open(filename, 'w') as f:
        await f.write(content)
    
    await event.edit(f"Saved to {filename}")
```

## Troubleshooting

### Common Issues

#### Plugin Not Loading

**Problem:** Plugin file exists but doesn't load

**Solutions:**
1. Check file syntax: `python -m py_compile plugins/yourplugin.py`
2. Verify imports are correct
3. Ensure decorators are properly used
4. Check logs for error messages

#### Commands Not Responding

**Problem:** Commands don't trigger handlers

**Solutions:**
1. Verify `@owner_only` decorator is working
2. Check command pattern syntax
3. Ensure COMMAND_PREFIX is correct
4. Test with `.ping` to verify bot is working

#### Import Errors

**Problem:** Module import failures

**Solutions:**
1. Install missing dependencies: `pip install module_name`
2. Check Python path configuration
3. Verify relative imports
4. Use absolute imports when necessary

#### Permission Issues

**Problem:** Plugin can't access files/resources

**Solutions:**
1. Check file permissions
2. Verify directory structure
3. Ensure proper error handling
4. Test with simple operations first

### Debug Mode

Enable debug mode for detailed logging:

```python
# In config.py
LOG_LEVEL = "DEBUG"
ENABLE_LOGGING = True
```

### Log Analysis

Check logs for plugin issues:

```bash
tail -f vzoel_assistant.log | grep -i plugin
```

## API Reference

### Core Functions

#### `@owner_only`
Decorator to restrict commands to owner only.

```python
@owner_only
async def handler(event):
    pass
```

#### `@log_command_usage`
Decorator to log command usage.

```python
@log_command_usage
async def handler(event):
    pass
```

#### `get_plugin_manager()`
Get the global plugin manager instance.

```python
from __init__ import get_plugin_manager
pm = get_plugin_manager()
```

### Event Patterns

#### Basic Pattern
```python
pattern=rf'{COMMAND_PREFIX}command'
```

#### With Parameters
```python
pattern=rf'{COMMAND_PREFIX}command (.+)'
pattern=rf'{COMMAND_PREFIX}command (\d+)'
pattern=rf'{COMMAND_PREFIX}command (\w+) (.+)'
```

#### Optional Parameters
```python
pattern=rf'{COMMAND_PREFIX}command(?: (.+))?'
```

### Response Methods

#### Edit Message
```python
await event.edit("New content")
```

#### Reply to Message
```python
await event.reply("Reply content")
```

#### Send New Message
```python
await client.send_message(event.chat_id, "Content")
```

#### Delete Message
```python
await event.delete()
```

### Plugin Manager Methods

#### Load Plugin
```python
pm.load_plugin(plugin_info)
```

#### Get Plugin Info
```python
info = pm.get_plugin_info()
```

#### Reload Plugin
```python
pm.reload_plugin("plugin_name")
```

---

## Contributing

When contributing plugins:

1. Follow the established directory structure
2. Include proper documentation
3. Add error handling
4. Test thoroughly
5. Use descriptive names and comments

## License

This plugin system is part of the Enhanced Vzoel Assistant project.

---

**Last Updated:** 2025
**Version:** 2.1.0
