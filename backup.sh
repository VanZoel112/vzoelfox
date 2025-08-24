#!/bin/bash

# ============= USERBOT BACKUP & RESTORE SYSTEM =============
# SANGAT KRUSIAL untuk melindungi session dan konfigurasi!

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKUP_DIR="$HOME/userbot_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="userbot_backup_$DATE"
CURRENT_DIR=$(pwd)

# Critical files to backup
CRITICAL_FILES=(
    ".env"
    "*.session*"
    "main.py"
    "requirements.txt"
    "start.sh"
    "userbot.service"
    ".gitignore"
    "userbot.log"
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
Backup Created: $(date)
Hostname: $(hostname)
User: $(whoami)
Directory: $CURRENT_DIR
Python Version: $(python3 --version 2>/dev/null || echo "Not found")
Telethon Version: $(python3 -c "import telethon; print(telethon.__version__)" 2>/dev/null || echo "Not installed")
EOF
    
    # Create archive
    log "Creating compressed archive..."
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    rm -rf "$BACKUP_NAME"
    cd "$CURRENT_DIR"
    
    # Set permissions
    chmod 600 "$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    success "✅ Backup created: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    log "📊 Backup size: $BACKUP_SIZE"
}

# Auto backup (keep last 5 backups)
auto_backup() {
    log "🔄 Creating automatic backup..."
    
    create_backup
    
    # Clean old backups (keep last 5)
    cd "$BACKUP_DIR"
    log "🧹 Cleaning old backups (keeping last 5)..."
    ls -t userbot_backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
    
    success "✅ Auto backup completed!"
    
    # List remaining backups
    echo -e "\n📋 Available backups:"
    ls -la userbot_backup_*.tar.gz 2>/dev/null || echo "No backups found"
}

# List backups
list_backups() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        warning "No backup directory found!"
        return
    fi
    
    cd "$BACKUP_DIR"
    echo -e "\n📋 Available backups:"
    echo "=================================="
    
    for backup in userbot_backup_*.tar.gz; do
        if [[ -f "$backup" ]]; then
            SIZE=$(du -h "$backup" | cut -f1)
            DATE_CREATED=$(stat -c %y "$backup" | cut -d. -f1)
            echo "📦 $backup"
            echo "   Size: $SIZE"
            echo "   Created: $DATE_CREATED"
            echo ""
        fi
    done
}

# Restore backup
restore_backup() {
    if [[ -z "$1" ]]; then
        error "Usage: $0 restore <backup_filename>"
        list_backups
        return 1
    fi
    
    RESTORE_FILE="$1"
    RESTORE_PATH="$BACKUP_DIR/$RESTORE_FILE"
    
    if [[ ! -f "$RESTORE_PATH" ]]; then
        error "Backup file not found: $RESTORE_PATH"
        list_backups
        return 1
    fi
    
    warning "⚠️  RESTORE WILL OVERWRITE CURRENT FILES!"
    echo -n "Are you sure? (yes/no): "
    read -r confirmation
    
    if [[ "$confirmation" != "yes" ]]; then
        log "Restore cancelled by user"
        return 0
    fi
    
    log "🔄 Stopping userbot (if running)..."
    ./start.sh stop 2>/dev/null || true
    
    log "🔄 Creating current backup before restore..."
    TEMP_BACKUP="pre_restore_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$BACKUP_DIR/$TEMP_BACKUP" "${CRITICAL_FILES[@]}" 2>/dev/null || true
    
    log "🔄 Extracting backup..."
    cd "$BACKUP_DIR"
    tar -xzf "$RESTORE_FILE"
    
    # Get extracted directory name
    EXTRACTED_DIR=$(basename "$RESTORE_FILE" .tar.gz)
    
    log "🔄 Restoring files..."
    cd "$EXTRACTED_DIR"
    cp -r * "$CURRENT_DIR/"
    
    # Cleanup
    cd "$BACKUP_DIR"
    rm -rf "$EXTRACTED_DIR"
    cd "$CURRENT_DIR"
    
    # Restore permissions
    chmod +x start.sh 2>/dev/null || true
    chmod 600 .env 2>/dev/null || true
    chmod 600 *.session* 2>/dev/null || true
    
    success "✅ Restore completed!"
    warning "💡 You may need to reinstall dependencies: ./start.sh install"
    
    log "📋 Restore info:"
    cat backup_info.txt 2>/dev/null || echo "No restore info available"
}

# Secure backup (encrypted)
secure_backup() {
    if ! command -v gpg &> /dev/null; then
        error "GPG not installed! Install with: sudo apt install gnupg"
        return 1
    fi
    
    log "🔄 Creating encrypted backup..."
    
    # Create normal backup first
    create_backup
    
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/userbot_backup_*.tar.gz | head -n1)
    ENCRYPTED_NAME="${LATEST_BACKUP%.tar.gz}_encrypted.gpg"
    
    echo -n "Enter encryption password: "
    read -s password
    echo
    
    log "🔐 Encrypting backup..."
    echo "$password" | gpg --batch --yes --passphrase-fd 0 --symmetric --cipher-algo AES256 --output "$ENCRYPTED_NAME" "$LATEST_BACKUP"
    
    if [[ -f "$ENCRYPTED_NAME" ]]; then
        success "✅ Encrypted backup created: $ENCRYPTED_NAME"
        rm -f "$LATEST_BACKUP"  # Remove unencrypted version
        
        ENCRYPTED_SIZE=$(du -h "$ENCRYPTED_NAME" | cut -f1)
        log "📊 Encrypted backup size: $ENCRYPTED_SIZE"
    else
        error "Failed to create encrypted backup!"
        return 1
    fi
}

# Health check
health_check() {
    log "🔍 Running userbot health check..."
    
    # Check critical files
    echo -e "\n📋 Critical Files Check:"
    for pattern in "${CRITICAL_FILES[@]}"; do
        if compgen -G "$pattern" > /dev/null; then
            echo "✅ $pattern - Found"
        else
            echo "❌ $pattern - Missing"
        fi
    done
    
    # Check permissions
    echo -e "\n🔐 Permissions Check:"
    if [[ -f ".env" ]]; then
        PERM=$(stat -c %a .env)
        if [[ "$PERM" == "600" ]]; then
            echo "✅ .env permissions - Secure (600)"
        else
            echo "⚠️  .env permissions - $PERM (should be 600)"
        fi
    fi
    
    # Check dependencies
    echo -e "\n📦 Dependencies Check:"
    if python3 -c "import telethon" 2>/dev/null; then
        VERSION=$(python3 -c "import telethon; print(telethon.__version__)")
        echo "✅ Telethon - v$VERSION"
    else
        echo "❌ Telethon - Not installed"
    fi
    
    if python3 -c "import dotenv" 2>/dev/null; then
        echo "✅ python-dotenv - Installed"
    else
        echo "❌ python-dotenv - Not installed"
    fi
    
    # Check userbot status
    echo -e "\n🤖 Userbot Status:"
    if [[ -f "userbot.pid" ]]; then
        PID=$(cat userbot.pid)
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Userbot - Running (PID: $PID)"
        else
            echo "❌ Userbot - Not running (stale PID file)"
        fi
    else
        echo "❌ Userbot - Not running"
    fi
    
    # Check disk space
    echo -e "\n💾 Disk Space:"
    df -h . | tail -1 | awk '{print "📊 Available: " $4 " / " $2 " (" $5 " used)"}'
    
    # Check backup space
    if [[ -d "$BACKUP_DIR" ]]; then
        BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/userbot_backup_*.tar.gz 2>/dev/null | wc -l)
        BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
        echo "💾 Backups: $BACKUP_COUNT files, $BACKUP_SIZE total"
    fi
}

# Quick recovery (restore from latest backup)
quick_recovery() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "No backup directory found!"
        return 1
    fi
    
    LATEST=$(ls -t "$BACKUP_DIR"/userbot_backup_*.tar.gz 2>/dev/null | head -n1)
    if [[ -z "$LATEST" ]]; then
        error "No backups found!"
        return 1
    fi
    
    LATEST_NAME=$(basename "$LATEST")
    warning "🚨 EMERGENCY RECOVERY: Restoring from latest backup"
    log "Latest backup: $LATEST_NAME"
    
    restore_backup "$LATEST_NAME"
}

# Main menu
case "${1:-menu}" in
    "backup"|"create")
        create_backup
        ;;
    "auto")
        auto_backup
        ;;
    "list")
        list_backups
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "secure")
        secure_backup
        ;;
    "health")
        health_check
        ;;
    "recovery")
        quick_recovery
        ;;
    "clean")
        log "🧹 Cleaning old backups..."
        if [[ -d "$BACKUP_DIR" ]]; then
            cd "$BACKUP_DIR"
            echo -n "Delete backups older than how many days? (7): "
            read -r days
            days=${days:-7}
            find . -name "userbot_backup_*.tar.gz" -mtime +$days -delete
            success "Cleaned backups older than $days days"
        fi
        ;;
    "menu"|*)
        echo "🛡️  USERBOT BACKUP & RECOVERY SYSTEM"
        echo "===================================="
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "📋 Available Commands:"
        echo "  backup     - Create new backup"
        echo "  auto       - Auto backup (keep last 5)"
        echo "  list       - List all backups"  
        echo "  restore    - Restore from backup"
        echo "  secure     - Create encrypted backup"
        echo "  health     - Run health check"
        echo "  recovery   - Quick recovery (latest backup)"
        echo "  clean      - Clean old backups"
        echo ""
        echo "🔧 Examples:"
        echo "  ./backup.sh backup"
        echo "  ./backup.sh restore userbot_backup_20250824_120000.tar.gz"
        echo "  ./backup.sh auto"
        echo ""
        echo "⚠️  CRITICAL: Run backup before any major changes!"
        ;;
esac
