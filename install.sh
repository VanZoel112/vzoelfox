#!/bin/bash
"""
VzoelFox Userbot - Quick Installation Script
Founder: Vzoel Fox's Ltpn 🤩
One-command install dari GitHub
"""

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# VzoelFox Banner
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                     🤩 VzoelFox Userbot Installer 🤩                         ║"
echo "║                       Founder: Vzoel Fox's Ltpn                              ║"
echo "║                     Quick Install dari GitHub                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
REPO_URL="https://github.com/VanZoel112/vzoelfox.git"
PROJECT_DIR="vzoelfox"
PYTHON_CMD="python3"

echo -e "${BLUE}🚀 Starting VzoelFox installation...${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies based on OS
install_system_deps() {
    echo -e "${BLUE}🔧 Installing system dependencies...${NC}"
    
    if command_exists apt; then
        # Ubuntu/Debian
        sudo apt update
        sudo apt install -y python3 python3-pip git curl wget
        echo -e "${GREEN}✅ Ubuntu/Debian dependencies installed${NC}"
        
    elif command_exists yum; then
        # CentOS/RHEL
        sudo yum update -y
        sudo yum install -y python3 python3-pip git curl wget
        echo -e "${GREEN}✅ CentOS/RHEL dependencies installed${NC}"
        
    elif command_exists apk; then
        # Alpine Linux
        sudo apk update
        sudo apk add python3 py3-pip git curl wget
        echo -e "${GREEN}✅ Alpine Linux dependencies installed${NC}"
        
    elif command_exists pkg; then
        # Termux
        pkg update
        pkg install -y python git curl wget
        PYTHON_CMD="python"
        echo -e "${GREEN}✅ Termux dependencies installed${NC}"
        
    elif command_exists pacman; then
        # Arch Linux
        sudo pacman -Sy --noconfirm python python-pip git curl wget
        echo -e "${GREEN}✅ Arch Linux dependencies installed${NC}"
        
    else
        echo -e "${YELLOW}⚠️  Unknown package manager. Please install manually:${NC}"
        echo -e "${YELLOW}   - Python 3${NC}"
        echo -e "${YELLOW}   - pip3${NC}"
        echo -e "${YELLOW}   - git${NC}"
        echo -e "${YELLOW}   - curl${NC}"
        echo -e "${YELLOW}   - wget${NC}"
        read -p "Press Enter to continue after installing dependencies..."
    fi
}

# Function to clone repository
clone_repository() {
    echo -e "${BLUE}📥 Cloning VzoelFox repository...${NC}"
    
    if [ -d "$PROJECT_DIR" ]; then
        echo -e "${YELLOW}📁 Directory $PROJECT_DIR already exists${NC}"
        read -p "Do you want to remove it and clone fresh? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
            git clone "$REPO_URL" "$PROJECT_DIR"
        else
            echo -e "${BLUE}📂 Using existing directory${NC}"
        fi
    else
        git clone "$REPO_URL" "$PROJECT_DIR"
    fi
    
    cd "$PROJECT_DIR"
    echo -e "${GREEN}✅ Repository cloned successfully${NC}"
}

# Function to install Python dependencies
install_python_deps() {
    echo -e "${BLUE}🐍 Installing Python dependencies...${NC}"
    
    # Upgrade pip
    $PYTHON_CMD -m pip install --upgrade pip
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements.txt
        echo -e "${GREEN}✅ Requirements installed from requirements.txt${NC}"
    else
        echo -e "${YELLOW}⚠️  requirements.txt not found, installing basic dependencies${NC}"
        $PYTHON_CMD -m pip install telethon python-dotenv asyncio
        echo -e "${GREEN}✅ Basic dependencies installed${NC}"
    fi
}

# Function to create .env file
create_env_file() {
    echo -e "${BLUE}⚙️  Setting up configuration...${NC}"
    
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}🔧 Creating .env configuration file${NC}"
        cat > .env <<'EOF'
# VzoelFox Userbot Configuration
# Founder: Vzoel Fox's Ltpn 🤩

# Telegram API Configuration (Get from https://my.telegram.org)
API_ID=your_api_id_here
API_HASH=your_api_hash_here

# Session Configuration
SESSION_NAME=vzoel_session

# Owner Configuration (Your Telegram User ID)
OWNER_ID=your_user_id_here

# Bot Configuration
COMMAND_PREFIX=.
LOG_LEVEL=INFO
ENABLE_LOGGING=true

# Gcast Configuration
MAX_CONCURRENT_GCAST=10
GCAST_DELAY=0.5

# Database Configuration
DATABASE_URL=sqlite:///vzoel_assistant.db
EOF
        
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env file with your credentials:${NC}"
        echo -e "${BLUE}   nano .env${NC}"
        echo -e "${YELLOW}   You need to add:${NC}"
        echo -e "${YELLOW}   - API_ID (from https://my.telegram.org)${NC}"
        echo -e "${YELLOW}   - API_HASH (from https://my.telegram.org)${NC}"
        echo -e "${YELLOW}   - OWNER_ID (Your Telegram User ID)${NC}"
        echo
        read -p "Press Enter after editing .env file..."
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
}

# Function to create requirements.txt if not exists
create_requirements() {
    if [ ! -f "requirements.txt" ]; then
        echo -e "${BLUE}📝 Creating requirements.txt...${NC}"
        cat > requirements.txt <<'EOF'
# VzoelFox Userbot Requirements
# Founder: Vzoel Fox's Ltpn 🤩

telethon>=1.28.0
python-dotenv>=0.19.0
asyncio
aiohttp>=3.8.0
requests>=2.28.0
Pillow>=9.0.0
cryptg>=0.4.0
hachoir>=3.1.0
python-dateutil>=2.8.0
pytz>=2022.1
gitpython>=3.1.0
psutil>=5.9.0
humanize>=4.0.0
colorama>=0.4.0
tqdm>=4.64.0
EOF
        echo -e "${GREEN}✅ requirements.txt created${NC}"
    fi
}

# Function to test installation
test_installation() {
    echo -e "${BLUE}🧪 Testing installation...${NC}"
    
    # Test Python import
    if $PYTHON_CMD -c "import telethon; print('✅ Telethon import OK')"; then
        echo -e "${GREEN}✅ Python dependencies working${NC}"
    else
        echo -e "${RED}❌ Python dependencies failed${NC}"
        exit 1
    fi
    
    # Check main.py exists
    if [ -f "main.py" ]; then
        echo -e "${GREEN}✅ main.py found${NC}"
    else
        echo -e "${RED}❌ main.py not found${NC}"
        exit 1
    fi
    
    # Test basic syntax
    if $PYTHON_CMD -m py_compile main.py; then
        echo -e "${GREEN}✅ main.py syntax OK${NC}"
    else
        echo -e "${RED}❌ main.py syntax error${NC}"
        exit 1
    fi
}

# Function to show usage instructions
show_usage() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                      🎉 VzoelFox Installation Complete! 🎉                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${GREEN}✅ VzoelFox Userbot installed successfully!${NC}"
    echo
    echo -e "${YELLOW}📋 Next steps:${NC}"
    echo -e "${BLUE}   1. cd $PROJECT_DIR${NC}"
    echo -e "${BLUE}   2. nano .env${NC} (edit your credentials)"
    echo -e "${BLUE}   3. $PYTHON_CMD main.py${NC} (run manually)"
    echo
    echo -e "${YELLOW}🚀 For permanent deployment:${NC}"
    echo -e "${BLUE}   chmod +x deploy.sh${NC}"
    echo -e "${BLUE}   ./deploy.sh${NC}"
    echo
    echo -e "${YELLOW}🛠️  Available scripts:${NC}"
    echo -e "${GREEN}   $PYTHON_CMD main.py${NC}          - Run userbot"
    echo -e "${GREEN}   ./deploy.sh${NC}              - Deploy permanently"
    echo -e "${GREEN}   git pull origin main${NC}      - Update from GitHub"
    echo
    echo -e "${PURPLE}🤩 Founder: Vzoel Fox's Ltpn${NC}"
    echo -e "${PURPLE}📧 Support: https://github.com/VanZoel112/vzoelfox${NC}"
}

# Main installation function
main() {
    echo -e "${BLUE}Starting VzoelFox installation...${NC}"
    
    install_system_deps
    clone_repository
    create_requirements
    install_python_deps
    create_env_file
    test_installation
    
    show_usage
}

# Check if running with curl/wget (remote install)
if [ "$0" = "bash" ] || [ "$0" = "/bin/bash" ] || [ "$0" = "-bash" ]; then
    echo -e "${BLUE}🌐 Running remote installation...${NC}"
    main
else
    echo -e "${BLUE}💽 Running local installation...${NC}"
    main
fi

echo -e "${PURPLE}🚀 VzoelFox Userbot installation completed! 🚀${NC}"