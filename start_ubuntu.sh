#!/bin/bash
# VzoelFox Ubuntu LTS 24 Quick Start Script
# Usage: ./start_ubuntu.sh

echo "🚀 Starting VzoelFox on Ubuntu LTS 24..."

# Navigate to correct directory
cd /home/ubuntu/vzoelfox || {
    echo "❌ VzoelFox directory not found at /home/ubuntu/vzoelfox"
    echo "Please clone the repository first:"
    echo "cd /home/ubuntu && git clone https://github.com/VanZoel112/vzoelfox.git"
    exit 1
}

# Activate virtual environment
echo "🐍 Activating Python virtual environment..."
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Running setup first..."
    ./setup_ubuntu.sh
    exit 1
fi

source venv/bin/activate

# Check if session exists
if [ ! -f "userbot_session.session" ]; then
    echo "⚠️ Session file not found!"
    echo "Please copy your session file to /home/ubuntu/vzoelfox/"
    echo "Or generate a new session by running: python3 main.py"
    echo ""
fi

# Your exact commands
echo "⚙️ Upgrading pip..."
pip install --upgrade pip

echo "📦 Ensuring telethon is installed..."
pip install telethon

echo "🎵 Ensuring music dependencies..."
pip install yt-dlp mutagen

echo "🤖 Starting VzoelFox userbot..."
python3 main.py