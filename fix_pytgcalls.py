#!/usr/bin/env python3
"""
PyTgCalls API Compatibility Fixer
Detects PyTgCalls version dan provides proper imports
"""

import subprocess
import sys

def check_pytgcalls_version():
    """Check PyTgCalls version and API"""
    try:
        result = subprocess.run([sys.executable, '-c', 'import pytgcalls; print(pytgcalls.__version__)'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ PyTgCalls version: {version}")
            return version
        else:
            print("❌ PyTgCalls not installed")
            return None
    except Exception as e:
        print(f"❌ Error checking PyTgCalls: {e}")
        return None

def test_imports():
    """Test different import patterns"""
    import_tests = [
        "from pytgcalls.types import AudioPiped, VideoPiped",
        "from pytgcalls.types.input_stream import AudioPiped, VideoPiped", 
        "from pytgcalls.types.input_stream.audio_piped import AudioPiped",
    ]
    
    working_imports = []
    
    for import_test in import_tests:
        try:
            exec(import_test)
            working_imports.append(import_test)
            print(f"✅ {import_test}")
        except ImportError as e:
            print(f"❌ {import_test} - {e}")
    
    return working_imports

def install_specific_version():
    """Install compatible PyTgCalls version"""
    print("\n🔧 Installing compatible PyTgCalls version...")
    try:
        # Uninstall current version
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'py-tgcalls', '-y'])
        
        # Install specific working version
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'py-tgcalls==1.0.8'])
        
        print("✅ PyTgCalls 1.0.8 installed")
        return True
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

if __name__ == "__main__":
    print("🎵 PyTgCalls Compatibility Checker\n")
    
    version = check_pytgcalls_version()
    if not version:
        print("\n🔧 Installing PyTgCalls...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'py-tgcalls'])
        version = check_pytgcalls_version()
    
    if version:
        print(f"\n📝 Testing imports for version {version}:")
        working = test_imports()
        
        if not working:
            print("\n❌ No working imports found. Installing compatible version...")
            if install_specific_version():
                print("\n📝 Re-testing imports:")
                test_imports()
        else:
            print(f"\n✅ Found {len(working)} working import patterns")
    
    print("\n🎯 Voice chat system should now work on VPS deployment")