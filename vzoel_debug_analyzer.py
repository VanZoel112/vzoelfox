#!/usr/bin/env python3
"""
VZOEL DEBUG ANALYZER
Analyze which plugins are failing and why
"""

import re
import os
import logging
from datetime import datetime

# Setup enhanced logging untuk debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('vzoel_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class VzoelPluginDebugger:
    """Debug tool untuk analyze plugin failures"""
    
    def __init__(self):
        self.handlers = []
        self.failed_handlers = []
        self.success_handlers = []
        
    def analyze_client_handlers(self):
        """Analyze semua handlers di client.py"""
        
        # List semua command patterns dari client.py
        expected_commands = [
            'alive',
            'gcast',
            'joinvc', 
            'leavevc',
            'vzl',
            'info',
            'help',
            'sg',
            'infofounder',
            'ping',
            'loadplugin',
            'listplugins',
            'addplugindir',
            'scanplugins'
        ]
        
        logger.info("="*60)
        logger.info("🔍 VZOEL PLUGIN ANALYZER")
        logger.info("="*60)
        
        print("📊 EXPECTED COMMANDS:")
        for i, cmd in enumerate(expected_commands, 1):
            status = "❓ UNKNOWN"
            print(f"{i:2d}. {cmd:15s} - {status}")
        
        print(f"\n📈 Expected Success Rate: {len(expected_commands)} commands")
        print(f"🔥 Current Issue: Only 80% working = ~{int(len(expected_commands) * 0.8)} commands")
        print(f"❌ Failed Commands: ~{len(expected_commands) - int(len(expected_commands) * 0.8)} commands")
        
        return expected_commands
    
    def test_regex_patterns(self, prefix="."):
        """Test regex patterns untuk semua commands"""
        
        print(f"\n🧪 TESTING REGEX PATTERNS (prefix: '{prefix}'):")
        print("-"*50)
        
        test_messages = [
            f"{prefix}alive",
            f"{prefix}gcast hello",
            f"{prefix}joinvc",
            f"{prefix}leavevc", 
            f"{prefix}vzl",
            f"{prefix}info",
            f"{prefix}help",
            f"{prefix}sg",
            f"{prefix}infofounder",
            f"{prefix}ping",
            f"{prefix}loadplugin /path/to/plugin.py",
            f"{prefix}listplugins",
            f"{prefix}addplugindir /path/to/dir",
            f"{prefix}scanplugins"
        ]
        
        patterns = {
            'alive': rf'{re.escape(prefix)}alive',
            'gcast': rf'{re.escape(prefix)}gcast\s+(.+)',
            'joinvc': rf'{re.escape(prefix)}joinvc',
            'leavevc': rf'{re.escape(prefix)}leavevc',
            'vzl': rf'{re.escape(prefix)}vzl',
            'info': rf'{re.escape(prefix)}info',
            'help': rf'{re.escape(prefix)}help',
            'sg': rf'{re.escape(prefix)}sg',
            'infofounder': rf'{re.escape(prefix)}infofounder',
            'ping': rf'{re.escape(prefix)}ping',
            'loadplugin': rf'{re.escape(prefix)}loadplugin\s+(.+)',
            'listplugins': rf'{re.escape(prefix)}listplugins',
            'addplugindir': rf'{re.escape(prefix)}addplugindir\s+(.+)',
            'scanplugins': rf'{re.escape(prefix)}scanplugins'
        }
        
        for msg in test_messages:
            print(f"\n🧪 Testing: '{msg}'")
            
            for cmd, pattern in patterns.items():
                try:
                    if re.match(pattern, msg):
                        print(f"  ✅ {cmd:15s} - MATCH")
                        break
                except Exception as e:
                    print(f"  ❌ {cmd:15s} - REGEX ERROR: {e}")
            else:
                print(f"  ❌ NO PATTERN MATCHED")
    
    def check_common_issues(self):
        """Check common issues yang menyebabkan plugin failure"""
        
        print(f"\n🔍 COMMON ISSUES ANALYSIS:")
        print("-"*50)
        
        issues = [
            {
                'issue': 'Import Errors',
                'description': 'Missing dependencies atau import failures',
                'solution': 'Check all imports at top of client.py'
            },
            {
                'issue': 'Async/Await Issues', 
                'description': 'Handler functions tidak properly async',
                'solution': 'Ensure all handlers are async def'
            },
            {
                'issue': 'Exception Handling',
                'description': 'Unhandled exceptions crash handlers',
                'solution': 'Add try-catch blocks in all handlers'
            },
            {
                'issue': 'Regex Pattern Errors',
                'description': 'Invalid regex patterns dalam event handlers',
                'solution': 'Test regex patterns separately'
            },
            {
                'issue': 'Owner Permission Check',
                'description': 'is_owner() function failures',
                'solution': 'Check OWNER_ID configuration'
            },
            {
                'issue': 'Client Connection',
                'description': 'Telethon client connection issues',
                'solution': 'Verify API_ID, API_HASH, session file'
            },
            {
                'issue': 'Event Registration',
                'description': 'Handlers tidak properly registered',
                'solution': 'Check @client.on() decorators'
            }
        ]
        
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue['issue']}")
            print(f"   📝 {issue['description']}")
            print(f"   💡 Solution: {issue['solution']}")
            print()
    
    def generate_test_client(self):
        """Generate test client untuk debug individual plugins"""
        
        test_code = '''
#!/usr/bin/env python3
"""
VZOEL TEST CLIENT - Debug Individual Plugins
"""

import asyncio
import logging
import re
from telethon import TelegramClient, events
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "vzoel_test")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", ".")

# Enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Test individual handlers one by one
@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}testping'))
async def test_ping(event):
    """Test basic functionality"""
    try:
        logger.info("✅ Test ping handler called")
        await event.reply("🏓 Test ping successful!")
    except Exception as e:
        logger.error(f"❌ Test ping failed: {e}")
        await event.reply(f"❌ Error: {e}")

# Add more test handlers here...

async def main():
    """Test main function"""
    try:
        await client.start()
        logger.info("✅ Test client started")
        
        me = await client.get_me()
        logger.info(f"👤 Logged in as: {me.first_name}")
        
        await client.send_message('me', 
            "🧪 **TEST CLIENT STARTED**\\n"
            "Use `.testping` to test basic functionality"
        )
        
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Test client error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        return test_code
    
    def run_analysis(self):
        """Run complete analysis"""
        
        print("🚀 STARTING VZOEL PLUGIN ANALYSIS...\n")
        
        # 1. Analyze expected handlers
        expected_commands = self.analyze_client_handlers()
        
        # 2. Test regex patterns
        self.test_regex_patterns()
        
        # 3. Check common issues
        self.check_common_issues()
        
        # 4. Generate recommendations
        print("💡 RECOMMENDATIONS:")
        print("-"*50)
        print("1. ✅ Add detailed logging to each handler")
        print("2. ✅ Test each command individually") 
        print("3. ✅ Check error logs for failed commands")
        print("4. ✅ Verify OWNER_ID and permissions")
        print("5. ✅ Test with debug client first")
        
        print(f"\n📊 SUMMARY:")
        print(f"Expected commands: {len(expected_commands)}")
        print(f"Working (80%): ~{int(len(expected_commands) * 0.8)}")
        print(f"Failed (20%): ~{len(expected_commands) - int(len(expected_commands) * 0.8)}")
        
        print(f"\n🔥 NEXT STEPS:")
        print("1. Run client.py with DEBUG logging")
        print("2. Test each command manually")
        print("3. Check vzoel_debug.log for errors")
        print("4. Fix failed handlers one by one")
        
        return self.generate_test_client()

# Run analysis
if __name__ == "__main__":
    debugger = VzoelPluginDebugger()
    test_client_code = debugger.run_analysis()
    
    # Save test client
    with open('vzoel_test_client.py', 'w') as f:
        f.write(test_client_code)
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 Test client saved as: vzoel_test_client.py")
    print(f"📁 Debug log: vzoel_debug.log")
