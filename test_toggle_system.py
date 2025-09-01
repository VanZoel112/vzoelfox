#!/usr/bin/env python3
"""
Test Script for VzoelFox Toggle Bot System
Author: Vzoel Fox's (Enhanced by Morgan)
Version: 1.0.0 - System Integration Test
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime

# Test Results
test_results = []

def log_test(test_name, status, details=""):
    """Log test result"""
    result = {
        'test': test_name,
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_icon} {test_name}: {status}")
    if details:
        print(f"   {details}")

def check_file_exists(filepath, test_name):
    """Check if file exists"""
    exists = os.path.exists(filepath)
    log_test(test_name, "PASS" if exists else "FAIL", 
             f"File {'found' if exists else 'missing'}: {filepath}")
    return exists

def check_executable(filepath, test_name):
    """Check if file is executable"""
    if not os.path.exists(filepath):
        log_test(test_name, "FAIL", f"File not found: {filepath}")
        return False
    
    executable = os.access(filepath, os.X_OK)
    log_test(test_name, "PASS" if executable else "FAIL",
             f"File {'is' if executable else 'is not'} executable: {filepath}")
    return executable

def check_command_available(command, test_name):
    """Check if command is available"""
    try:
        result = subprocess.run(['which', command], capture_output=True, text=True)
        available = result.returncode == 0
        log_test(test_name, "PASS" if available else "FAIL",
                 f"Command {'found' if available else 'not found'}: {command}")
        return available
    except Exception as e:
        log_test(test_name, "FAIL", f"Error checking command: {e}")
        return False

def check_node_version():
    """Check Node.js version"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            log_test("Node.js Version", "PASS", f"Version: {version}")
            return True
        else:
            log_test("Node.js Version", "FAIL", "Node.js not found")
            return False
    except Exception as e:
        log_test("Node.js Version", "FAIL", f"Error: {e}")
        return False

def check_npm_dependencies():
    """Check npm dependencies"""
    if os.path.exists('node_modules'):
        log_test("NPM Dependencies", "PASS", "node_modules directory found")
        return True
    else:
        log_test("NPM Dependencies", "WARN", "node_modules not found - run npm install")
        return False

def check_plugin_imports():
    """Check if plugin can be imported"""
    try:
        sys.path.append('plugins')
        sys.path.append('utils')
        
        # Test premium emoji helper import
        try:
            from premium_emoji_helper import get_emoji, safe_send_premium
            log_test("Premium Emoji Import", "PASS", "premium_emoji_helper imported successfully")
        except ImportError as e:
            log_test("Premium Emoji Import", "FAIL", f"Import error: {e}")
        
        # Test toggle bot integration import
        try:
            import toggle_bot_integration
            log_test("Toggle Bot Integration Import", "PASS", "toggle_bot_integration imported successfully")
        except ImportError as e:
            log_test("Toggle Bot Integration Import", "FAIL", f"Import error: {e}")
        
        return True
    except Exception as e:
        log_test("Plugin Imports", "FAIL", f"General import error: {e}")
        return False

def test_bot_token():
    """Test bot token format"""
    bot_token = "8380293227:AAHYbOVl5Mou_yJmqKO890lwNqvDyLMM_lE"
    
    # Basic token format check
    if ':' in bot_token and len(bot_token) > 40:
        log_test("Bot Token Format", "PASS", f"Token format looks valid: {bot_token[:20]}...")
        return True
    else:
        log_test("Bot Token Format", "FAIL", "Invalid token format")
        return False

def check_userbot_main():
    """Check if userbot main.py exists"""
    main_files = ['main.py', 'client.py', 'userbot.py']
    
    for main_file in main_files:
        if os.path.exists(main_file):
            log_test("Userbot Main Script", "PASS", f"Found: {main_file}")
            return True
    
    log_test("Userbot Main Script", "WARN", "No main userbot script found")
    return False

async def test_toggle_bot_syntax():
    """Test toggle bot JavaScript syntax"""
    try:
        # Use Node.js to check syntax
        process = await asyncio.create_subprocess_exec(
            'node', '-c', 'vzoel_toggle_bot.js',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            log_test("Toggle Bot Syntax", "PASS", "JavaScript syntax is valid")
            return True
        else:
            log_test("Toggle Bot Syntax", "FAIL", f"Syntax error: {stderr.decode()}")
            return False
    except Exception as e:
        log_test("Toggle Bot Syntax", "FAIL", f"Error checking syntax: {e}")
        return False

async def test_startup_script():
    """Test startup script functionality"""
    try:
        # Test script help
        process = await asyncio.create_subprocess_exec(
            'bash', 'start_toggle_bot.sh', 'help',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if 'Usage:' in stdout.decode():
            log_test("Startup Script Help", "PASS", "Help text available")
            return True
        else:
            log_test("Startup Script Help", "FAIL", "Help text not found")
            return False
    except Exception as e:
        log_test("Startup Script Help", "FAIL", f"Error: {e}")
        return False

def generate_report():
    """Generate test report"""
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if r['status'] == 'PASS'])
    failed_tests = len([r for r in test_results if r['status'] == 'FAIL'])
    warned_tests = len([r for r in test_results if r['status'] == 'WARN'])
    
    print("\n" + "="*60)
    print("🤩 VZOELFOX TOGGLE BOT SYSTEM TEST REPORT")
    print("="*60)
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⚠️ Warnings: {warned_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in test_results:
            if result['status'] == 'FAIL':
                print(f"  • {result['test']}: {result['details']}")
    
    if warned_tests > 0:
        print(f"\n⚠️ WARNINGS:")
        for result in test_results:
            if result['status'] == 'WARN':
                print(f"  • {result['test']}: {result['details']}")
    
    print(f"\n🚀 NEXT STEPS:")
    if failed_tests == 0:
        print("  ✅ All critical tests passed!")
        print("  🔧 Run: ./start_toggle_bot.sh install")
        print("  🚀 Run: ./start_toggle_bot.sh start")
        print("  📱 Test with: .togglebot status")
    else:
        print("  🔧 Fix the failed tests above")
        print("  📖 Check TOGGLE_BOT_README.md for help")
        print("  🆘 Run: ./start_toggle_bot.sh install")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'warned': warned_tests,
            'success_rate': passed_tests/total_tests*100
        },
        'results': test_results
    }
    
    with open('toggle_system_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved: toggle_system_test_report.json")
    print("="*60)

async def main():
    """Main test function"""
    print("🤩 Starting VzoelFox Toggle Bot System Test...")
    print("=" * 60)
    
    # File existence tests
    check_file_exists('vzoel_toggle_bot.js', 'Toggle Bot Script')
    check_file_exists('start_toggle_bot.sh', 'Startup Script')
    check_file_exists('package.json', 'Package.json')
    check_file_exists('plugins/toggle_bot_integration.py', 'Integration Plugin')
    check_file_exists('utils/premium_emoji_helper.py', 'Premium Emoji Helper')
    
    # Executable tests
    check_executable('start_toggle_bot.sh', 'Startup Script Executable')
    
    # Command availability tests
    check_command_available('node', 'Node.js Command')
    check_command_available('npm', 'NPM Command')
    check_command_available('bash', 'Bash Command')
    
    # Version and dependency tests
    check_node_version()
    check_npm_dependencies()
    
    # Code tests
    await test_toggle_bot_syntax()
    await test_startup_script()
    
    # Import tests
    check_plugin_imports()
    
    # Configuration tests
    test_bot_token()
    check_userbot_main()
    
    # Generate final report
    generate_report()

if __name__ == "__main__":
    asyncio.run(main())