#!/bin/bash

# ============= VZOEL ASSISTANT BACKUP & RESTORE SYSTEM =============
# SANGAT KRUSIAL untuk melindungi session dan konfigurasi!

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKUP_DIR="$HOME/vzoel_assistant_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="vzoel_assistant_backup_$DATE"
CURRENT_DIR=$(pwd)

# Critical files to backup
CRITICAL_FILES=(
    ".env"
    "*.session*"
    "main.py"
    "requirements.txt"
    "start.sh"
    "vzoel_assistant.service"
    ".gitignore"
    "vzoel_assistant.log"
    "config/"
    "plugins/"
    "downloads/"
)

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory
create_backup_dir() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log "Creating backup directory..."
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"  # Only owner can access
        success "Backup directory created: $BACKUP_DIR"
    fi
}

# Create full backup
create_backup() {
    log "🔄 Creating backup: $BACKUP_NAME"
    
    create_backup_dir
    
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$BACKUP_PATH"
    
    # Backup critical files
    for pattern in "${CRITICAL_FILES[@]}"; do
        if compgen -G "$pattern" > /dev/null; then
            log "Backing up: $pattern"
            cp -r $pattern "$BACKUP_PATH/" 2>/dev/null || true
        fi
    done
    
    # Create info file
    cat > "$BACKUP_PATH/backup_info.txt" << EOF
Backup Created: $(
