#!/bin/bash
# VzoelFox Ubuntu LTS 24 Setup Script
# Usage: chmod +x setup_ubuntu.sh && ./setup_ubuntu.sh

set -e

echo "🚀 VzoelFox Ubuntu LTS 24 Setup Starting..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y python3 python3-pip python3-venv git curl wget ffmpeg

# Install yt-dlp for music features
echo "🎵 Installing yt-dlp..."
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Your exact setup commands
echo "🐍 Setting up Python virtual environment..."
cd /home/ubuntu/vzoelfox || {
    echo "❌ Please run from /home/ubuntu/vzoelfox directory"
    exit 1
}

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install all requirements
echo "📋 Installing Python dependencies..."
pip install telethon
pip install yt-dlp mutagen  # For music features
pip install aiohttp         # For AI features
pip install requests        # For web requests

# Install additional dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📋 Installing from requirements.txt..."
    pip install -r requirements.txt
fi

echo "✅ Setup completed successfully!"
echo ""
echo "🔧 To run VzoelFox:"
echo "cd /home/ubuntu/vzoelfox"
echo "source venv/bin/activate"
echo "python3 main.py"
echo ""
echo "🎯 Or use the quick start script:"
echo "./start_ubuntu.sh"