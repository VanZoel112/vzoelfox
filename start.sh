#!/bin/bash

# ============= USERBOT STARTUP SCRIPT =============
# Script untuk menjalankan userbot dengan auto-restart
# Usage: ./start.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_FILE="main.py"
VENV_DIR="telethon_env"
LOG_FILE="userbot.log"
PID_FILE="userbot.pid"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if script is run from correct directory
check_directory() {
    if [[ ! -f "$MAIN_FILE" ]]; then
        error "main.py not found! Make sure you're in the correct directory."
        exit 1
    fi
}

# Create virtual environment if it doesn't exist
setup_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        log "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        success "Virtual environment created!"
    fi
    
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    log "Installing/updating requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
    success "Dependencies installed!"
}

# Check if userbot is already running
check_running() {
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            error "Userbot is already running (PID: $PID)"
            echo "Use './start.sh stop' to stop it first"
            exit 1
        else
            warning "Stale PID file found, removing..."
            rm -f "$PID_FILE"
        fi
    fi
}

# Start userbot
start_userbot() {
    log "Starting userbot..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Start userbot in background
    nohup python3 "$MAIN_FILE" > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    success "Userbot started! PID: $(cat $PID_FILE)"
    log "Log file: $LOG_FILE"
    log "Use './start.sh logs' to view logs"
    log "Use './start.sh stop' to stop userbot"
}

# Stop userbot
stop_userbot() {
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Stopping userbot (PID: $PID)..."
            kill "$PID"
            rm -f "$PID_FILE"
            success "Userbot stopped!"
        else
            warning "Userbot not running"
            rm -f "$PID_FILE"
        fi
    else
        warning "PID file not found. Userbot may not be running."
    fi
}

# Restart userbot
restart_userbot() {
    log "Restarting userbot..."
    stop_userbot
    sleep 2
    start_userbot
}

# Show logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        tail -f "$LOG_FILE"
    else
        error "Log file not found!"
        exit 1
    fi
}

# Show status
show_status() {
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            success "Userbot is running (PID: $PID)"
            
            # Show process info
            echo "Process info:"
            ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem
            
            # Show log size
            if [[ -f "$LOG_FILE" ]]; then
                LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
                echo "Log file size: $LOG_SIZE"
            fi
        else
            error "Userbot not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        warning "Userbot not running"
    fi
}

# Auto-restart function
auto_restart() {
    log "Starting userbot with auto-restart..."
    
    while true; do
        log "Starting userbot process..."
        source "$VENV_DIR/bin/activate"
        python3 "$MAIN_FILE"
        
        EXIT_CODE=$?
        error "Userbot stopped with exit code: $EXIT_CODE"
        
        if [[ $EXIT_CODE -eq 130 ]]; then
            log "Received interrupt signal, stopping auto-restart"
            break
        fi
        
        warning "Restarting in 5 seconds..."
        sleep 5
    done
}

# Main script logic
case "${1:-start}" in
    "start")
        check_directory
        setup_venv
        check_running
        start_userbot
        ;;
    "stop")
        stop_userbot
        ;;
    "restart")
        restart_userbot
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "auto")
        check_directory
        setup_venv
        auto_restart
        ;;
    "install")
        check_directory
        setup_venv
        success "Setup completed! Run './start.sh' to start userbot"
        ;;
    "clean")
        log "Cleaning up..."
        stop_userbot
        rm -f "$LOG_FILE" "$PID_FILE"
        rm -rf __pycache__/
        success "Cleanup completed!"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|auto|install|clean}"
        echo ""
        echo "Commands:"
        echo "  start    - Start userbot in background"
        echo "  stop     - Stop userbot"
        echo "  restart  - Restart userbot"
        echo "  logs     - Show live logs"
        echo "  status   - Show userbot status"
        echo "  auto     - Start with auto-restart (foreground)"
        echo "  install  - Setup environment and install dependencies"
        echo "  clean    - Stop userbot and clean temporary files"
        echo ""
        echo "Examples:"
        echo "  ./start.sh install  # First time setup"
        echo "  ./start.sh start    # Start userbot"
        echo "  ./start.sh logs     # Monitor logs"
        exit 1
        ;;
esac
