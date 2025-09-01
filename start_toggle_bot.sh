#!/bin/bash
#
# VzoelFox Toggle Bot Startup Script
# Author: Vzoel Fox's (Enhanced by Morgan)
# Version: 1.0.0
#

echo "🤩 VzoelFox Toggle Bot Startup Script"
echo "======================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Installing..."
    pkg install nodejs -y
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Node.js"
        exit 1
    fi
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not available. Installing..."
    pkg install nodejs-lts -y
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Navigate to userbot directory
cd /data/data/com.termux/files/home/vzoelfox

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "⏳ Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Make the bot executable
chmod +x vzoel_toggle_bot.js

# Create systemctl-like service management
SERVICE_NAME="vzoeltoggle"
PID_FILE="/tmp/vzoel_toggle_bot.pid"

case "${1:-start}" in
    start)
        echo "🔌 Starting VzoelFox Toggle Bot..."
        
        # Check if already running
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "⚠️ Toggle bot is already running (PID: $(cat $PID_FILE))"
            exit 1
        fi
        
        # Start the bot in background
        nohup node vzoel_toggle_bot.js > toggle_bot_output.log 2>&1 &
        BOT_PID=$!
        echo $BOT_PID > "$PID_FILE"
        
        # Wait a moment and check if it's running
        sleep 3
        if kill -0 $BOT_PID 2>/dev/null; then
            echo "✅ Toggle bot started successfully (PID: $BOT_PID)"
            echo "📱 Bot Token: 8380293227:AAHYbOVl5Mou_yJmqKO890lwNqvDyLMM_lE"
            echo "🔗 Telegram: @VzoelToggleBot"
            echo "📊 Logs: tail -f toggle_bot_output.log"
            echo ""
            echo "🚀 QUICK START:"
            echo "1. Open Telegram and search for your bot"
            echo "2. Send /start command"
            echo "3. Use the buttons to control your userbot"
            echo ""
            echo "⚡ Commands:"
            echo "  ./start_toggle_bot.sh stop    - Stop the bot"
            echo "  ./start_toggle_bot.sh restart - Restart the bot"
            echo "  ./start_toggle_bot.sh status  - Check bot status"
            echo "  ./start_toggle_bot.sh logs    - View logs"
        else
            echo "❌ Failed to start toggle bot"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
        
    stop)
        echo "🛑 Stopping VzoelFox Toggle Bot..."
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 $PID 2>/dev/null; then
                kill $PID
                sleep 2
                if kill -0 $PID 2>/dev/null; then
                    kill -9 $PID
                fi
                echo "✅ Toggle bot stopped"
            else
                echo "⚠️ Toggle bot was not running"
            fi
            rm -f "$PID_FILE"
        else
            echo "⚠️ No PID file found"
            # Try to kill by process name
            pkill -f "node.*vzoel_toggle_bot.js" && echo "✅ Killed toggle bot process"
        fi
        ;;
        
    restart)
        echo "🔄 Restarting VzoelFox Toggle Bot..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        echo "📊 VzoelFox Toggle Bot Status:"
        echo "=============================="
        
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            PID=$(cat "$PID_FILE")
            echo "✅ Status: Running (PID: $PID)"
            echo "⏱️ Started: $(ps -o lstart= -p $PID)"
            echo "💾 Memory: $(ps -o rss= -p $PID | awk '{printf "%.1f MB", $1/1024}')"
            echo "📊 CPU: $(ps -o %cpu= -p $PID)%"
        else
            echo "❌ Status: Not running"
        fi
        
        echo ""
        echo "📁 Files:"
        [ -f "vzoel_toggle_bot.js" ] && echo "✅ Bot script: vzoel_toggle_bot.js" || echo "❌ Bot script: Missing"
        [ -f "package.json" ] && echo "✅ Package.json: Found" || echo "❌ Package.json: Missing"
        [ -d "node_modules" ] && echo "✅ Dependencies: Installed" || echo "❌ Dependencies: Missing"
        [ -f "toggle_bot_config.json" ] && echo "✅ Config: Found" || echo "⚠️ Config: Will be created on first run"
        ;;
        
    logs)
        echo "📄 VzoelFox Toggle Bot Logs:"
        echo "============================"
        
        if [ -f "toggle_bot_output.log" ]; then
            echo "📊 Bot Output Log (Last 20 lines):"
            tail -20 toggle_bot_output.log
            echo ""
        fi
        
        if [ -f "toggle_bot.log" ]; then
            echo "📋 Bot Internal Log (Last 10 lines):"
            tail -10 toggle_bot.log
        fi
        ;;
        
    install)
        echo "📦 Installing VzoelFox Toggle Bot..."
        
        # Install system dependencies
        echo "⏳ Installing system dependencies..."
        pkg update && pkg install nodejs git python -y
        
        # Install npm dependencies
        echo "⏳ Installing npm dependencies..."
        npm install
        
        # Make scripts executable
        chmod +x start_toggle_bot.sh
        chmod +x vzoel_toggle_bot.js
        
        echo "✅ Installation complete!"
        echo "🚀 Run: ./start_toggle_bot.sh start"
        ;;
        
    *)
        echo "❓ Usage: $0 {start|stop|restart|status|logs|install}"
        echo ""
        echo "📖 Commands:"
        echo "  start   - Start the toggle bot"
        echo "  stop    - Stop the toggle bot"
        echo "  restart - Restart the toggle bot"
        echo "  status  - Show bot status and system info"
        echo "  logs    - View recent logs"
        echo "  install - Install all dependencies"
        echo ""
        echo "🤩 VzoelFox Toggle Bot v1.0.0"
        echo "© 2025 Vzoel Fox's (LTPN) - Premium Userbot"
        exit 1
        ;;
esac