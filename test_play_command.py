#!/usr/bin/env python3
"""
Test script for .play command functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')
sys.path.append('plugins')
sys.path.append('utils')

async def test_play_functionality():
    """Test the music play functionality"""
    print("🤩 Testing VzoelFox Music Player Plugin...")
    
    try:
        # Import the plugin
        from music_player import search_and_download_music, ensure_directories, get_audio_info
        
        # Ensure directories exist
        ensure_directories()
        print("✅ Directories created/verified")
        
        # Test search and download
        print("🔍 Testing music search and download...")
        test_query = "perfect ed sheeran"
        
        result = await search_and_download_music(test_query)
        
        if result['success']:
            print(f"✅ Download successful!")
            print(f"   Title: {result['title']}")
            print(f"   File: {result['file_path']}")
            print(f"   Size: {result['size']} bytes ({result['size'] // 1024 // 1024:.1f} MB)")
            
            # Test audio info extraction
            audio_info = get_audio_info(result['file_path'])
            if audio_info:
                print(f"✅ Audio info extracted:")
                print(f"   Title: {audio_info['title']}")
                print(f"   Duration: {audio_info['duration']} seconds")
                print(f"   Performer: {audio_info['performer']}")
            else:
                print("⚠️ Could not extract audio metadata")
            
            # Check if file actually exists and is readable
            if os.path.exists(result['file_path']):
                file_size = os.path.getsize(result['file_path'])
                print(f"✅ File exists and is {file_size} bytes")
            else:
                print("❌ File does not exist on filesystem")
            
        else:
            print(f"❌ Download failed: {result['error']}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def test_plugin_registration():
    """Test if plugin can be properly loaded"""
    print("\n🔧 Testing plugin registration...")
    
    try:
        import music_player
        
        # Check required functions exist
        required_functions = ['setup', 'get_plugin_info', 'play_music_handler']
        for func in required_functions:
            if hasattr(music_player, func):
                print(f"✅ Function {func} exists")
            else:
                print(f"❌ Function {func} missing")
        
        # Test plugin info
        plugin_info = music_player.get_plugin_info()
        print(f"✅ Plugin info: {plugin_info['name']} v{plugin_info['version']}")
        print(f"   Commands: {plugin_info['commands']}")
        
    except Exception as e:
        print(f"❌ Plugin registration test failed: {e}")

def test_dependencies():
    """Test if required dependencies are available"""
    print("\n📦 Testing dependencies...")
    
    # Test yt-dlp
    try:
        import subprocess
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ yt-dlp version: {result.stdout.strip()}")
        else:
            print("❌ yt-dlp not working properly")
    except:
        print("❌ yt-dlp not available")
    
    # Test ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            ffmpeg_version = result.stdout.split('\n')[0]
            print(f"✅ {ffmpeg_version}")
        else:
            print("⚠️ ffmpeg not available (will use webm/ogg format)")
    except:
        print("⚠️ ffmpeg not available (will use webm/ogg format)")
    
    # Test directories
    dirs_to_check = ['downloads/music', 'downloads/temp']
    for dir_path in dirs_to_check:
        if os.path.exists(dir_path):
            print(f"✅ Directory {dir_path} exists")
        else:
            print(f"⚠️ Directory {dir_path} will be created")

async def main():
    """Main test function"""
    print("🎵 VzoelFox Music Player Test Suite")
    print("=" * 50)
    
    # Test dependencies first
    test_dependencies()
    
    # Test plugin registration
    test_plugin_registration() 
    
    # Test actual functionality
    print("\n🎶 Testing music download functionality...")
    await test_play_functionality()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    
    # Show available music files
    music_dir = "downloads/music"
    if os.path.exists(music_dir):
        files = os.listdir(music_dir)
        if files:
            print(f"\n🎵 Downloaded music files ({len(files)}):")
            for file in files:
                file_path = os.path.join(music_dir, file)
                size = os.path.getsize(file_path) // 1024 // 1024
                print(f"   • {file} ({size:.1f} MB)")
        else:
            print("\n📁 No music files downloaded yet")

if __name__ == "__main__":
    asyncio.run(main())