#!/usr/bin/env python3
"""
Setup Script untuk Enhanced Vzoel Assistant Plugin System
Script ini akan membuat struktur folder yang diperlukan dan contoh plugin
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create the plugins directory structure"""
    print("🔄 Creating plugins directory structure...")
    
    # Create main plugins directory
    plugins_dir = Path("plugins")
    plugins_dir.mkdir(exist_ok=True)
    print(f"✅ Created: {plugins_dir}")
    
    # Create __init__.py in plugins directory
    init_file = plugins_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('"""Vzoel Assistant Plugins Directory"""\n')
        print(f"✅ Created: {init_file}")
    
    # Create example subdirectories
    subdirs = ['utils', 'fun', 'admin', 'tools']
    for subdir in subdirs:
        subdir_path = plugins_dir / subdir
        subdir_path.mkdir(exist_ok=True)
        
        # Create __init__.py in subdirectory
        sub_init = subdir_path / "__init__.py"
        if not sub_init.exists():
            with open(sub_init, 'w', encoding='utf-8') as f:
                f.write(f'"""{subdir.title()} Plugins for Vzoel Assistant"""\n')
        
        print(f"✅ Created: {subdir_path}")
    
    return plugins_dir

def create_sample_plugins():
    """Create sample plugins to demonstrate the system"""
    print("\n🔄 Creating sample plugins...")
    
    plugins_dir = Path("plugins")
    
    # Sample plugin 1: Basic test
    test_plugin = plugins_dir / "test.py"
    if not test_plugin.exists():
        with open(test_plugin, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
"""
Test Plugin untuk Enhanced Vzoel Assistant
Plugin ini mendemonstrasikan cara kerja sistem plugin yang telah diupdate
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
import asyncio
import random

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}test'))
@owner_only
@log_command_usage
async def test_handler(event):
    """Test plugin command"""
    await event.edit("✅ **Test Plugin Working!**\\n📂 Loaded from plugins directory")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}echo (.+)'))
@owner_only
@log_command_usage
async def echo_handler(event):
    """Echo command - repeats your message"""
    message = event.pattern_match.group(1)
    await event.edit(f"🔊 **Echo:** {message}")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}quote'))
@owner_only
@log_command_usage
async def quote_handler(event):
    """Random motivational quote"""
    quotes = [
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "The only way to do great work is to love what you do.",
        "Innovation distinguishes between a leader and a follower.",
    ]
    
    quote = random.choice(quotes)
    await event.edit(f"💡 **Quote:**\\n\\n_{quote}_")
''')
        print(f"✅ Created: {test_plugin}")
    
    # Sample plugin 2: Utils
    utils_plugin = plugins_dir / "utils" / "system_info.py"
    if not utils_plugin.exists():
        with open(utils_plugin, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
"""
System Info Plugin - Utilities category
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
import psutil
import platform
from datetime import datetime

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}sysinfo'))
@owner_only
@log_command_usage
async def sysinfo_handler(event):
    """Show system information"""
    try:
        # Get system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        info_text = f"""
🖥️ **System Information:**

**💻 Platform:** `{platform.system()} {platform.release()}`
**🏗️ Architecture:** `{platform.architecture()[0]}`
**🔧 Processor:** `{platform.processor()[:50]}`

**📊 Resources:**
• **CPU:** `{cpu_percent}%`
• **Memory:** `{memory.percent}%` (`{memory.used//1024//1024}MB/{memory.total//1024//1024}MB`)
• **Disk:** `{disk.percent}%` (`{disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB`)

**⏰ Boot time:** `{datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}`
        """.strip()
        
        await event.edit(info_text)
    except ImportError:
        await event.edit("❌ psutil module not installed. Run: pip install psutil")
    except Exception as e:
        await event.edit(f"❌ Error getting system info: {str(e)}")
''')
        print(f"✅ Created: {utils_plugin}")
    
    # Sample plugin 3: Fun category
    fun_plugin = plugins_dir / "fun" / "dice.py"
    if not fun_plugin.exists():
        with open(fun_plugin, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
"""
Dice Plugin - Fun category
"""

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage
import random

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}dice'))
@owner_only
@log_command_usage
async def dice_handler(event):
    """Roll a dice"""
    result = random.randint(1, 6)
    dice_faces = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    await event.edit(f"🎲 **Dice Roll:** {dice_faces[result-1]} ({result})")

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}coinflip'))
@owner_only
@log_command_usage
async def coinflip_handler(event):
    """Flip a coin"""
    result = random.choice(['Heads', 'Tails'])
    emoji = '👨' if result == 'Heads' else '🔢'
    await event.edit(f"🪙 **Coin Flip:** {emoji} {result}")
''')
        print(f"✅ Created: {fun_plugin}")

def create_readme():
    """Create README for plugins directory"""
    print("\n🔄 Creating plugin documentation...")
    
    readme_content = """# Vzoel Assistant Plugins Directory

This directory contains all the plugins for the Enhanced Vzoel Assistant.

## Directory Structure

```
plugins/
├── __init__.py              # Main plugins directory
├── *.py                     # Plugin files
├── utils/                   # Utility plugins
│   ├── __init__.py
│   └── *.py
├── fun/                     # Fun/entertainment plugins
│   ├── __init__.py
│   └── *.py
├── admin/                   # Administration plugins
│   ├── __init__.py
│   └── *.py
└── tools/                   # Tool plugins
    ├── __init__.py
    └── *.py
```

## Creating Plugins

### Basic Plugin Template

```python
#!/usr/bin/env python3
\"\"\"
Your Plugin Description
\"\"\"

from telethon import events
from config import COMMAND_PREFIX
from __init__ import owner_only, log_command_usage

@events.register(events.NewMessage(pattern=rf'{COMMAND_PREFIX}yourcommand'))
@owner_only
@log_command_usage
async def your_handler(event):
    \"\"\"Your command description\"\"\"
    await event.reply("Your plugin response")
```

### Plugin Guidelines

1. **Always use the decorators:**
   - `@events.register()` for event handling
   - `@owner_only` for owner-only commands
   - `@log_command_usage` for command logging

2. **Import requirements:**
   - Import from `telethon` for events
   - Import from `config` for COMMAND_PREFIX
   - Import decorators from `__init__`

3. **File placement:**
   - Place in `plugins/` directory
   - Or in subdirectories for organization
   - Use descriptive filenames

4. **Command patterns:**
   - Use `COMMAND_PREFIX` from config
   - Use regex patterns for parameters
   - Handle errors gracefully

## Loading Plugins

Plugins are automatically loaded when the assistant starts. Use these commands:

- `.plugins` - List loaded plugins
- `.plugininfo` - Detailed plugin information
- `.structure` - Show directory structure
- `.reload` - Reload all plugins

## Sample Plugins

The setup creates these sample plugins:

- `test.py` - Basic test commands
- `utils/system_info.py` - System information
- `fun/dice.py` - Dice roll and coin flip

You can modify or delete these as needed.

## Troubleshooting

1. **Plugin not loading:**
   - Check file syntax
   - Ensure proper imports
   - Check log files for errors

2. **Commands not working:**
   - Verify decorators are used
   - Check command patterns
   - Ensure owner_only is working

3. **Import errors:**
   - Check if required modules are installed
   - Verify import paths

For more help, check the main documentation or logs.
"""
    
    readme_file = Path("plugins") / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ Created: {readme_file}")

def show_completion_info():
    """Show completion information"""
    print("\n" + "="*60)
    print("🎉 Plugin System Setup Complete!")
    print("="*60)
    print()
    print("📁 Directory structure created:")
    print("   plugins/")
    print("   ├── __init__.py")
    print("   ├── README.md")
    print("   ├── test.py (sample)")
    print("   ├── utils/system_info.py (sample)")
    print("   ├── fun/dice.py (sample)")
    print("   └── subdirectories for organization")
    print()
    print("🚀 Next steps:")
    print("   1. Start your Vzoel Assistant: python main.py")
    print("   2. Test sample plugins: .test, .echo Hello, .sysinfo")
    print("   3. Create your own plugins in the plugins/ directory")
    print("   4. Use .plugins to see loaded plugins")
    print("   5. Use .plugininfo for detailed information")
    print()
    print("📖 For plugin development, check plugins/README.md")
    print("🔧 All plugins are automatically loaded on startup")
    print()

def main():
    """Main setup function"""
    print("🔌 Enhanced Vzoel Assistant Plugin System Setup")
    print("=" * 50)
    
    try:
        # Create directory structure
        create_directory_structure()
        
        # Create sample plugins
        create_sample_plugins()
        
        # Create documentation
        create_readme()
        
        # Show completion info
        show_completion_info()
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Setup failed!")
        sys.exit(1)
