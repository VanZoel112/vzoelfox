#!/bin/bash

# ============= USERBOT SECURITY HARDENING =============
# KRUSIAL untuk melindungi userbot di AWS Ubuntu

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "Don't run userbot as root! Use regular user."
        exit 1
    fi
}

# Secure file permissions
secure_permissions() {
    log "🔐 Setting secure file permissions..."
    
    # Session files - MOST CRITICAL
    if ls *.session* 1> /dev/null 2>&1; then
        chmod 600 *.session*
        success "Session files secured (600)"
    fi
    
    # Environment file
    if [[ -f ".env" ]]; then
        chmod 600 .env
        success ".env file secured (600)"
    fi
    
    # Main script
    if [[ -f "main.py" ]]; then
        chmod 644 main.py
    fi
    
    # Executable scripts
    for script in start.sh backup.sh security.sh; do
        if [[ -f "$script" ]]; then
            chmod 700 "$script"
        fi
    done
    
    # Log files
    if ls *.log 1> /dev/null 2>&1; then
        chmod 640 *.log
    fi
    
    # Database files
    if ls *.db *.sqlite* 1> /dev/null 2>&1; then
        chmod 600 *.db *.sqlite* 2>/dev/null || true
    fi
    
    success "File permissions secured!"
}

# Setup UFW firewall
setup_firewall() {
    log "🔥 Configuring UFW firewall..."
    
    # Install UFW if not present
    if ! command -v ufw &> /dev/null; then
        log "Installing UFW..."
        sudo apt update
        sudo apt install -y ufw
    fi
    
    # Reset UFW to defaults
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (be careful!)
    SSH_PORT=$(ss -tlnp | grep sshd | awk '{print $4}' | cut -d: -f2 | head -1)
    SSH_PORT=${SSH_PORT:-22}
    sudo ufw allow $SSH_PORT/tcp comment 'SSH'
    
    # Allow Telegram API (important!)
    sudo ufw allow out 443/tcp comment 'Telegram HTTPS'
    sudo ufw allow out 80/tcp comment 'Telegram HTTP'
    
    # Enable UFW
    sudo ufw --force enable
    
    success "Firewall configured and enabled!"
    sudo ufw status verbose
}

# Secure SSH (if applicable)
secure_ssh() {
    log "🔑 Securing SSH configuration..."
    
    SSH_CONFIG="/etc/ssh/sshd_config"
    
    if [[ ! -f "$SSH_CONFIG" ]]; then
        warning "SSH config not found, skipping SSH hardening"
        return
    fi
    
    # Backup original config
    sudo cp "$SSH_CONFIG" "${SSH_CONFIG}.backup.$(date +%Y%m%d)"
    
    # Secure SSH settings
    cat << 'EOF' | sudo tee /etc/ssh/sshd_config.d/99-userbot-security.conf
# Userbot Security Hardening
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
TCPKeepAlive yes
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
LoginGraceTime 60
EOF
    
    # Restart SSH service
    sudo systemctl restart sshd
    success "SSH configuration hardened!"
}

# Install fail2ban
install_fail2ban() {
    log "🛡️ Installing and configuring Fail2Ban..."
    
    # Install fail2ban
    sudo apt update
    sudo apt install -y fail2ban
    
    # Create custom jail for userbot
    cat << 'EOF' | sudo tee /etc/fail2ban/jail.d/userbot.conf
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1800
EOF
    
    # Start and enable fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    success "Fail2Ban installed and configured!"
}

# Setup log rotation
setup_log_rotation() {
    log "📋 Setting up log rotation..."
    
    cat << EOF | sudo tee /etc/logrotate.d/userbot
$(pwd)/userbot.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
    su $(whoami) $(whoami)
}

$(pwd)/debug.log {
    daily
    missingok
    rotate 3
    compress
    delaycompress
    notifempty
    copytruncate
    su $(whoami) $(whoami)
}
EOF
    
    success "Log rotation configured!"
}

# Setup automatic updates (security only)
setup_auto_updates() {
    log "🔄 Setting up automatic security updates..."
    
    # Install unattended-upgrades
    sudo apt update
    sudo apt install -y unattended-upgrades
    
    # Configure for security updates only
    cat << 'EOF' | sudo tee /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
    
    # Enable automatic updates
    echo 'APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";' | sudo tee /etc/apt/apt.conf.d/20auto-upgrades
    
    success "Automatic security updates enabled!"
}

# Create security monitoring script
create_monitoring() {
    log "👁️ Creating security monitoring script..."
    
    cat << 'EOF' > monitor_security.sh
#!/bin/bash

# Security monitoring for userbot
LOG_FILE="security_monitor.log"
ALERT_EMAIL=""  # Add email if needed

log_event() {
    echo "[$(date)] $1" >> "$LOG_FILE"
}

# Check for suspicious activity
check_failed_logins() {
    FAILED=$(grep "Failed password" /var/log/auth.log | tail -10 | wc -l)
    if [[ $FAILED -gt 5 ]]; then
        log_event "WARNING: $FAILED recent failed login attempts"
    fi
}

# Check userbot process
check_userbot() {
    if [[ -f "userbot.pid" ]]; then
        PID=$(cat userbot.pid)
        if ! ps -p "$PID" > /dev/null 2>&1; then
            log_event "ALERT: Userbot process died unexpectedly"
        fi
    fi
}

# Check file integrity
check_integrity() {
    if [[ -f ".env" ]]; then
        PERM=$(stat -c %a .env)
        if [[ "$PERM" != "600" ]]; then
            log_event "SECURITY: .env file has wrong permissions: $PERM"
        fi
    fi
    
    for session in *.session*; do
        if [[ -f "$session" ]]; then
            PERM=$(stat -c %a "$session")
            if [[ "$PERM" != "600" ]]; then
                log_event "SECURITY: Session file $session has wrong permissions: $PERM"
            fi
        fi
    done
}

# Check disk space
check_disk() {
    USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $USAGE -gt 90 ]]; then
        log_event "WARNING: Disk usage is ${USAGE}%"
    fi
}

# Run checks
check_failed_logins
check_userbot
check_integrity
check_disk

# Show recent events
if [[ -f "$LOG_FILE" ]]; then
    echo "Recent security events:"
    tail -5 "$LOG_FILE"
fi
EOF
    
    chmod +x monitor_security.sh
    success "Security monitoring script created!"
}

# Setup cron jobs for security
setup_security_cron() {
    log "⏰ Setting up security cron jobs..."
    
    # Add cron jobs
    (crontab -l 2>/dev/null; echo "# Userbot Security Jobs") | crontab -
    (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/backup.sh auto >/dev/null 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "*/15 * * * * $(pwd)/monitor_security.sh >/dev/null 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "0 4 * * 0 $(pwd)/security.sh audit >/dev/null 2>&1") | crontab -
    
    success "Security cron jobs installed!"
    crontab -l | grep -E "(backup|monitor|security)"
}

# Security audit
security_audit() {
    log "🔍 Running comprehensive security audit..."
    
    echo -e "\n=== USERBOT SECURITY AUDIT ==="
    echo "Audit Time: $(date)"
    echo "Hostname: $(hostname)"
    echo "User: $(whoami)"
    echo ""
    
    # File permissions check
    echo "📁 File Permissions:"
    echo "===================="
    
    for file in .env *.session* main.py; do
        if [[ -f "$file" ]]; then
            PERM=$(stat -c "%a %n" "$file")
            case "$file" in
                ".env"|*.session*)
                    if [[ "${PERM:0:3}" == "600" ]]; then
                        echo "✅ $PERM - SECURE"
                    else
                        echo "❌ $PERM - INSECURE!"
                    fi
                    ;;
                *)
                    echo "ℹ️  $PERM"
                    ;;
            esac
        fi
    done
    
    echo ""
    echo "🔥 Firewall Status:"
    echo "=================="
    sudo ufw status
    
    echo ""
    echo "🛡️ Fail2Ban Status:"
    echo "==================="
    sudo fail2ban-client status 2>/dev/null || echo "Fail2Ban not running"
    
    echo ""
    echo "🔑 SSH Security:"
    echo "==============="
    if sudo sshd -T 2>/dev/null | grep -E "(permitrootlogin|passwordauthentication)" | head -2; then
        :
    else
        echo "SSH configuration check failed"
    fi
    
    echo ""
    echo "💾 Disk Usage:"
    echo "============="
    df -h .
    
    echo ""
    echo "🔄 Running Processes:"
    echo "===================="
    ps aux | grep -E "(python|userbot)" | grep -v grep
    
    echo ""
    echo "📋 Recent Login Attempts:"
    echo "========================"
    sudo tail -5 /var/log/auth.log | grep -E "(Accepted|Failed)"
    
    echo ""
    echo "🎯 Security Score:"
    echo "=================="
    
    SCORE=0
    
    # Check file permissions
    if [[ -f ".env" ]] && [[ "$(stat -c %a .env)" == "600" ]]; then
        ((SCORE+=20))
    fi
    
    # Check session files
    SESSION_COUNT=0
    SECURE_SESSIONS=0
    for session in *.session*; do
        if [[ -f "$session" ]]; then
            ((SESSION_COUNT++))
            if [[ "$(stat -c %a "$session")" == "600" ]]; then
                ((SECURE_SESSIONS++))
            fi
        fi
    done
    
    if [[ $SESSION_COUNT -eq $SECURE_SESSIONS ]] && [[ $SESSION_COUNT -gt 0 ]]; then
        ((SCORE+=20))
    fi
    
    # Check firewall
    if sudo ufw status | grep -q "Status: active"; then
        ((SCORE+=15))
    fi
    
    # Check fail2ban
    if systemctl is-active fail2ban >/dev/null 2>&1; then
        ((SCORE+=15))
    fi
    
    # Check SSH security
    if sudo sshd -T 2>/dev/null | grep -q "permitrootlogin no"; then
        ((SCORE+=15))
    fi
    
    # Check auto updates
    if [[ -f "/etc/apt/apt.conf.d/20auto-upgrades" ]]; then
        ((SCORE+=15))
    fi
    
    echo "Security Score: $SCORE/100"
    
    if [[ $SCORE -ge 80 ]]; then
        echo "✅ EXCELLENT - Your userbot is well secured!"
    elif [[ $SCORE -ge 60 ]]; then
        echo "⚠️  GOOD - Consider implementing remaining security measures"
    else
        echo "❌ POOR - URGENT: Implement security measures immediately!"
    fi
}

# Main command handler
case "${1:-menu}" in
    "permissions")
        check_root
        secure_permissions
        ;;
    "firewall")
        setup_firewall
        ;;
    "ssh")
        secure_ssh
        ;;
    "fail2ban")
        install_fail2ban
        ;;
    "logs")
        setup_log_rotation
        ;;
    "updates")
        setup_auto_updates
        ;;
    "monitor")
        create_monitoring
        ;;
    "cron")
        setup_security_cron
        ;;
    "audit")
        security_audit
        ;;
    "full")
        log "🔐 Running FULL security hardening..."
        check_root
        secure_permissions
        setup_firewall
        secure_ssh
        install_fail2ban
        setup_log_rotation
        setup_auto_updates
        create_monitoring
        setup_security_cron
        success "🎯 FULL security hardening completed!"
        echo ""
        security_audit
        ;;
    "menu"|*)
        echo "🛡️  USERBOT SECURITY HARDENING SYSTEM"
        echo "====================================="
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "🔧 Available Commands:"
        echo "  permissions - Secure file permissions"
        echo "  firewall    - Configure UFW firewall" 
        echo "  ssh         - Harden SSH configuration"
        echo "  fail2ban    - Install & configure Fail2Ban"
        echo "  logs        - Setup log rotation"
        echo "  updates     - Enable automatic security updates"
        echo "  monitor     - Create security monitoring"
        echo "  cron        - Setup security cron jobs"
        echo "  audit       - Run security audit"
        echo "  full        - Apply ALL security measures"
        echo ""
        echo "🚨 CRITICAL: Run 'full' for complete hardening!"
        echo ""
        echo "⚡ Quick start:"
        echo "  ./security.sh full"
        ;;
esac
