#!/bin/bash
"""
VzoelFox Userbot - Permanent Deployment Script
Founder: Vzoel Fox's Ltpn 🤩
Auto-deploy with systemd service, auto-restart, logging
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# VzoelFox Banner
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        🤩 VzoelFox Userbot Deployment 🤩                      ║"
echo "║                     Founder: Vzoel Fox's Ltpn - Auto Deploy                  ║"
echo "║                    Permanent Service with Auto-Restart                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
PROJECT_NAME="vzoelfox"
SERVICE_NAME="vzoelfox-userbot"
USER=$(whoami)
WORK_DIR=$(pwd)
PYTHON_BIN=$(which python3)
LOG_DIR="/var/log/$SERVICE_NAME"

echo -e "${BLUE}🔧 Starting VzoelFox Deployment...${NC}"
echo -e "${GREEN}📁 Working Directory: $WORK_DIR${NC}"
echo -e "${GREEN}👤 User: $USER${NC}"
echo -e "${GREEN}🐍 Python: $PYTHON_BIN${NC}"

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo -e "${RED}❌ This script should not be run as root for security reasons!${NC}"
        echo -e "${YELLOW}💡 Run as regular user, sudo will be used when needed${NC}"
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    echo -e "${BLUE}📦 Installing system dependencies...${NC}"
    
    # Update package list
    sudo apt update
    
    # Install required packages
    sudo apt install -y python3 python3-pip python3-venv git curl wget systemd supervisor htop nano
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# Function to setup Python environment
setup_python_env() {
    echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        $PYTHON_BIN -m pip install --upgrade pip
        $PYTHON_BIN -m pip install -r requirements.txt
        echo -e "${GREEN}✅ Python requirements installed${NC}"
    else
        echo -e "${YELLOW}⚠️  requirements.txt not found, installing basic dependencies...${NC}"
        $PYTHON_BIN -m pip install --upgrade pip
        $PYTHON_BIN -m pip install telethon python-dotenv asyncio
    fi
}

# Function to create log directory
setup_logging() {
    echo -e "${BLUE}📝 Setting up logging...${NC}"
    
    # Create log directory
    sudo mkdir -p $LOG_DIR
    sudo chown $USER:$USER $LOG_DIR
    
    echo -e "${GREEN}✅ Log directory created: $LOG_DIR${NC}"
}

# Function to create systemd service
create_systemd_service() {
    echo -e "${BLUE}⚙️  Creating systemd service...${NC}"
    
    # Create service file
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=VzoelFox Userbot - Premium Telegram Userbot by Vzoel Fox's Ltpn
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment=PATH=$PATH
Environment=PYTHONPATH=$WORK_DIR
ExecStart=$PYTHON_BIN $WORK_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/$SERVICE_NAME.log
StandardError=append:$LOG_DIR/$SERVICE_NAME-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$WORK_DIR $LOG_DIR /tmp
CapabilityBoundingSet=

# Resource limits
LimitNOFILE=65536
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${GREEN}✅ Systemd service created${NC}"
}

# Function to create supervisor config (alternative to systemd)
create_supervisor_config() {
    echo -e "${BLUE}👥 Creating supervisor configuration...${NC}"
    
    sudo tee /etc/supervisor/conf.d/$SERVICE_NAME.conf > /dev/null <<EOF
[program:$SERVICE_NAME]
command=$PYTHON_BIN $WORK_DIR/main.py
directory=$WORK_DIR
user=$USER
autostart=true
autorestart=true
startsecs=10
startretries=3
stdout_logfile=$LOG_DIR/$SERVICE_NAME.log
stderr_logfile=$LOG_DIR/$SERVICE_NAME-error.log
stdout_logfile_maxbytes=10MB
stderr_logfile_maxbytes=10MB
stdout_logfile_backups=5
stderr_logfile_backups=5
environment=PATH="$PATH",PYTHONPATH="$WORK_DIR"
EOF

    echo -e "${GREEN}✅ Supervisor configuration created${NC}"
}

# Function to start services
start_services() {
    echo -e "${BLUE}🚀 Starting VzoelFox services...${NC}"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable and start systemd service
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    
    # Also setup supervisor as backup
    sudo supervisorctl reread
    sudo supervisorctl update
    
    echo -e "${GREEN}✅ Services started and enabled${NC}"
}

# Function to create management scripts
create_management_scripts() {
    echo -e "${BLUE}📜 Creating management scripts...${NC}"
    
    # Create start script
    cat > start_vzoelfox.sh <<'EOF'
#!/bin/bash
echo "🚀 Starting VzoelFox Userbot..."
sudo systemctl start vzoelfox-userbot
sudo systemctl status vzoelfox-userbot --no-pager
EOF

    # Create stop script
    cat > stop_vzoelfox.sh <<'EOF'
#!/bin/bash
echo "⏹️  Stopping VzoelFox Userbot..."
sudo systemctl stop vzoelfox-userbot
sudo systemctl status vzoelfox-userbot --no-pager
EOF

    # Create restart script
    cat > restart_vzoelfox.sh <<'EOF'
#!/bin/bash
echo "🔄 Restarting VzoelFox Userbot..."
sudo systemctl restart vzoelfox-userbot
sleep 3
sudo systemctl status vzoelfox-userbot --no-pager
EOF

    # Create status script
    cat > status_vzoelfox.sh <<'EOF'
#!/bin/bash
echo "📊 VzoelFox Userbot Status:"
sudo systemctl status vzoelfox-userbot --no-pager
echo -e "\n📝 Recent logs:"
sudo tail -n 20 /var/log/vzoelfox-userbot/vzoelfox-userbot.log
EOF

    # Create logs script
    cat > logs_vzoelfox.sh <<'EOF'
#!/bin/bash
echo "📝 VzoelFox Userbot Logs (Press Ctrl+C to exit):"
sudo tail -f /var/log/vzoelfox-userbot/vzoelfox-userbot.log
EOF

    # Make scripts executable
    chmod +x *.sh
    
    echo -e "${GREEN}✅ Management scripts created${NC}"
}

# Function to create update script
create_update_script() {
    echo -e "${BLUE}🔄 Creating auto-update script...${NC}"
    
    cat > update_vzoelfox.sh <<'EOF'
#!/bin/bash
echo "🔄 Updating VzoelFox Userbot..."

# Stop service
sudo systemctl stop vzoelfox-userbot

# Pull latest changes
git pull origin main

# Install/update dependencies
python3 -m pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl start vzoelfox-userbot

echo "✅ VzoelFox updated and restarted!"

# Show status
sudo systemctl status vzoelfox-userbot --no-pager
EOF

    chmod +x update_vzoelfox.sh
    
    echo -e "${GREEN}✅ Update script created${NC}"
}

# Function to display service information
show_service_info() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        🎉 VzoelFox Deployment Complete! 🎉                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${GREEN}✅ VzoelFox Userbot deployed successfully!${NC}"
    echo -e "${BLUE}📊 Service Status:${NC}"
    sudo systemctl status $SERVICE_NAME --no-pager
    
    echo -e "\n${YELLOW}🛠️  Management Commands:${NC}"
    echo -e "${GREEN}  ./start_vzoelfox.sh${NC}     - Start the userbot"
    echo -e "${GREEN}  ./stop_vzoelfox.sh${NC}      - Stop the userbot"
    echo -e "${GREEN}  ./restart_vzoelfox.sh${NC}   - Restart the userbot"
    echo -e "${GREEN}  ./status_vzoelfox.sh${NC}    - Check status"
    echo -e "${GREEN}  ./logs_vzoelfox.sh${NC}      - View live logs"
    echo -e "${GREEN}  ./update_vzoelfox.sh${NC}    - Update from GitHub"
    
    echo -e "\n${YELLOW}🔧 Direct systemctl commands:${NC}"
    echo -e "${BLUE}  sudo systemctl start $SERVICE_NAME${NC}"
    echo -e "${BLUE}  sudo systemctl stop $SERVICE_NAME${NC}"
    echo -e "${BLUE}  sudo systemctl restart $SERVICE_NAME${NC}"
    echo -e "${BLUE}  sudo systemctl status $SERVICE_NAME${NC}"
    echo -e "${BLUE}  sudo journalctl -fu $SERVICE_NAME${NC}"
    
    echo -e "\n${YELLOW}📝 Log files:${NC}"
    echo -e "${BLUE}  $LOG_DIR/$SERVICE_NAME.log${NC} - Main logs"
    echo -e "${BLUE}  $LOG_DIR/$SERVICE_NAME-error.log${NC} - Error logs"
    
    echo -e "\n${PURPLE}🤩 VzoelFox is now running permanently in the background!${NC}"
}

# Main deployment function
main() {
    echo -e "${BLUE}Starting VzoelFox permanent deployment...${NC}"
    
    check_root
    install_dependencies
    setup_python_env
    setup_logging
    create_systemd_service
    create_supervisor_config
    create_management_scripts
    create_update_script
    start_services
    
    sleep 3
    show_service_info
}

# Run main function
main "$@"

echo -e "${PURPLE}🚀 VzoelFox Userbot is now deployed and running permanently! 🚀${NC}"
echo -e "${GREEN}Founder: Vzoel Fox's Ltpn 🤩${NC}"