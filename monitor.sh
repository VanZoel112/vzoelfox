#!/bin/bash

# ============= USERBOT ADVANCED MONITORING =============
# Real-time monitoring untuk performance dan kesehatan userbot

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
MONITOR_INTERVAL=5
LOG_FILE="monitor.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEM=85
ALERT_THRESHOLD_DISK=90

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

alert() {
    echo -e "${RED}[ALERT]${NC} $1"
    echo "[$(date)] ALERT: $1" >> "$LOG_FILE"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# Get userbot process info
get_userbot_pid() {
    if [[ -f "userbot.pid" ]]; then
        cat userbot.pid
    else
        pgrep -f "python.*main.py" | head -1
    fi
}

# Check userbot status
check_userbot_status() {
    PID=$(get_userbot_pid)
    
    if [[ -n "$PID" ]] && ps -p "$PID" > /dev/null 2>&1; then
        # Get process info
        CPU=$(ps -p "$PID" -o %cpu --no-headers | xargs)
        MEM=$(ps -p "$PID" -o %mem --no-headers | xargs)
        ETIME=$(ps -p "$PID" -o etime --no-headers | xargs)
        
        success "Userbot running (PID: $PID)"
        info "CPU: ${CPU}% | Memory: ${MEM}% | Uptime: $ETIME"
        
        # Check if CPU/Memory usage is high
        CPU_INT=${CPU%.*}
        MEM_INT=${MEM%.*}
        
        if [[ $CPU_INT -gt $ALERT_THRESHOLD_CPU ]]; then
            alert "High CPU usage: ${CPU}%"
        fi
        
        if [[ $MEM_INT -gt $ALERT_THRESHOLD_MEM ]]; then
            alert "High memory usage: ${MEM}%"
        fi
        
        return 0
    else
        error "Userbot not running!"
        return 1
    fi
}

# System resource monitoring
check_system_resources() {
    echo -e "\n${PURPLE}=== SYSTEM RESOURCES ===${NC}"
    
    # CPU Usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    echo -e "🖥️  CPU Usage: ${CPU_USAGE}%"
    
    # Memory Usage
    MEM_INFO=$(free | grep Mem)
    MEM_TOTAL=$(echo $MEM_INFO | awk '{print $2}')
    MEM_USED=$(echo $MEM_INFO | awk '{print $3}')
    MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))
    echo -e "💾 Memory: ${MEM_PERCENT}% ($(( MEM_USED / 1024 ))MB / $(( MEM_TOTAL / 1024 ))MB)"
    
    # Disk Usage
    DISK_INFO=$(df . | tail -1)
    DISK_PERCENT=$(echo $DISK_INFO | awk '{print $5}' | sed 's/%//')
    DISK_USED=$(echo $DISK_INFO | awk '{print $3}')
    DISK_TOTAL=$(echo $DISK_INFO | awk '{print $2}')
    echo -e "💿 Disk: ${DISK_PERCENT}% ($(( DISK_USED / 1024 ))MB / $(( DISK_TOTAL / 1024 ))MB)"
    
    # Load Average
    LOAD=$(uptime | awk -F'load average:' '{print $2}')
    echo -e "⚖️  Load Average:$LOAD"
    
    # Check thresholds
    if [[ $MEM_PERCENT -gt $ALERT_THRESHOLD_MEM ]]; then
        alert "High memory usage: ${MEM_PERCENT}%"
    fi
    
    if [[ $DISK_PERCENT -gt $ALERT_THRESHOLD_DISK ]]; then
        alert "High disk usage: ${DISK_PERCENT}%"
    fi
}

# Network connectivity check
check_network() {
    echo -e "\n${PURPLE}=== NETWORK STATUS ===${NC}"
    
    # Check Telegram API connectivity
    if curl -s --max-time 10 https://api.telegram.org > /dev/null; then
        success "Telegram API - Reachable"
    else
        alert "Telegram API - Unreachable!"
    fi
    
    # Check internet connectivity
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        success "Internet - Connected"
    else
        alert "Internet - Disconnected!"
    fi
    
    # Show active connections
    CONNECTIONS=$(ss -tuln | grep -E ":443|:80" | wc -l)
    info "Active connections: $CONNECTIONS"
}

# File system monitoring
check_filesystem() {
    echo -e "\n${PURPLE}=== FILE SYSTEM ===${NC}"
    
    # Check critical files
    CRITICAL_FILES=(".env" "main.py" "*.session*")
    
    for pattern in "${CRITICAL_FILES[@]}"; do
        if compgen -G "$pattern" > /dev/null; then
            for file in $pattern; do
                if [[ -f "$file" ]]; then
                    SIZE=$(du -h "$file" | cut -f1)
                    PERM=$(stat -c %a "$file")
                    
                    case "$file" in
                        ".env"|*.session*)
                            if [[ "$PERM" == "600" ]]; then
                                success "$file ($SIZE) - Permissions OK"
                            else
                                alert "$file - Wrong permissions: $PERM (should be 600)"
                            fi
                            ;;
                        *)
                            info "$file ($SIZE) - Permissions: $PERM"
                            ;;
                    esac
                fi
            done
        fi
    done
    
    # Check log file size
    if [[ -f "userbot.log" ]]; then
        LOG_SIZE=$(du -h userbot.log | cut -f1)
        info "Log file size: $LOG_SIZE"
        
        # Alert if log file is too large
        LOG_SIZE_MB=$(du -m userbot.log | cut -f1)
        if [[ $LOG_SIZE_MB -gt 100 ]]; then
            warning "Log file is large: ${LOG_SIZE_MB}MB (consider rotation)"
        fi
    fi
}

# Performance metrics
show_performance_metrics() {
    echo -e "\n${PURPLE}=== PERFORMANCE METRICS ===${NC}"
    
    PID=$(get_userbot_pid)
    if [[ -n "$PID" ]] && ps -p "$PID" > /dev/null 2>&1; then
        # Detailed process info
        echo "Process ID: $PID"
        echo "Command: $(ps -p $PID -o cmd --no-headers)"
        echo "Started: $(ps -p $PID -o lstart --no-headers)"
        echo "CPU Time: $(ps -p $PID -o time --no-headers)"
        echo "Memory RSS: $(ps -p $PID -o rss --no-headers | awk '{print $1/1024 " MB"}')"
        echo "Memory VSZ: $(ps -p $PID -o vsz --no-headers | awk '{print $1/1024 " MB"}')"
        echo "Thread count: $(ps -p $PID -o nlwp --no-headers)"
        
        # File descriptors
        if [[ -d "/proc/$PID/fd" ]]; then
            FD_COUNT=$(ls /proc/$PID/fd | wc -l)
            echo "File descriptors: $FD_COUNT"
        fi
        
        # Network connections by process
        PROC_CONNECTIONS=$(ss -tulnp | grep "$PID" | wc -l)
        echo "Process connections: $PROC_CONNECTIONS"
    fi
}

# Log analysis
analyze_logs() {
    echo -e "\n${PURPLE}=== LOG ANALYSIS ===${NC}"
    
    if [[ -f "userbot.log" ]]; then
        # Recent errors
        ERROR_COUNT=$(grep -c "ERROR" userbot.log 2>/dev/null || echo 0)
        WARNING_COUNT=$(grep -c "WARNING" userbot.log 2>/dev/null || echo 0)
        
        echo "Total errors: $ERROR_COUNT"
        echo "Total warnings: $WARNING_COUNT"
        
        # Recent errors (last 10)
        if [[ $ERROR_COUNT -gt 0 ]]; then
            echo -e "\n🚨 Recent errors:"
            grep "ERROR" userbot.log | tail -5 | while read line; do
                echo "  $line"
            done
        fi
        
        # Log growth rate
        if [[ -f "$LOG_FILE" ]]; then
            PREV_SIZE=$(grep "LOG_SIZE:" "$LOG_FILE" 2>/dev/null | tail -1 | cut -d: -f2 || echo 0)
            CURR_SIZE=$(wc -c < userbot.log)
            
            if [[ $PREV_SIZE -gt 0 ]]; then
                GROWTH=$((CURR_SIZE - PREV_SIZE))
                echo "Log growth: +${GROWTH} bytes"
            fi
            
            echo "LOG_SIZE:$CURR_SIZE" >> "$LOG_FILE"
        fi
    else
        warning "No userbot.log file found"
    fi
}

# Real-time monitoring
realtime_monitor() {
    log "Starting real-time monitoring (Ctrl+C to stop)"
    echo "Update interval: ${MONITOR_INTERVAL}s"
    
    while true; do
        clear
        echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${CYAN}║                    USERBOT REAL-TIME MONITOR                         ║${NC}"
        echo -e "${CYAN}║                    $(date +'%Y-%m-%d %H:%M:%S')                            ║${NC}"
        echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
        
        # Userbot status
        echo -e "\n${PURPLE}=== USERBOT STATUS ===${NC}"
        if check_userbot_status; then
            echo ""
        else
            alert "Userbot is not running!"
            echo ""
        fi
        
        # System resources
        check_system_resources
        
        # Network status
        check_network
        
        # Quick log check
        if [[ -f "userbot.log" ]]; then
            echo -e "\n${PURPLE}=== RECENT ACTIVITY ===${NC}"
            tail -3 userbot.log | sed 's/^/  /'
        fi
        
        # Wait for next update
        echo -e "\n${CYAN}Press Ctrl+C to exit | Next update in ${MONITOR_INTERVAL}s${NC}"
        sleep $MONITOR_INTERVAL
    done
}

# Dashboard view
show_dashboard() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                      USERBOT DASHBOARD                               ║${NC}"
    echo -e "${CYAN}║                    $(date +'%Y-%m-%d %H:%M:%S')                            ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
    
    check_userbot_status
    check_system_resources
    check_network
    check_filesystem
    show_performance_metrics
    analyze_logs
    
    echo -e "\n${CYAN}Dashboard updated at $(date)${NC}"
}

# Create monitoring report
create_report() {
    REPORT_FILE="monitoring_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log "Creating monitoring report: $REPORT_FILE"
    
    {
        echo "USERBOT MONITORING REPORT"
        echo "========================="
        echo "Generated: $(date)"
        echo "Hostname: $(hostname)"
        echo "User: $(whoami)"
        echo ""
        
        echo "=== USERBOT STATUS ==="
        if check_userbot_status 2>&1; then
            echo "Status: Running"
        else
            echo "Status: Not Running"
        fi
        echo ""
        
        echo "=== SYSTEM RESOURCES ==="
        check_system_resources 2>&1
        echo ""
        
        echo "=== NETWORK STATUS ==="
        check_network 2>&1
        echo ""
        
        echo "=== FILE SYSTEM ==="
        check_filesystem 2>&1
        echo ""
        
        echo "=== PERFORMANCE METRICS ==="
        show_performance_metrics 2>&1
        echo ""
        
        echo "=== LOG ANALYSIS ==="
        analyze_logs 2>&1
        echo ""
        
        echo "=== SYSTEM INFO ==="
        echo "Uptime: $(uptime)"
        echo "Disk usage:"
        df -h
        echo ""
        echo "Memory info:"
        free -h
        
    } > "$REPORT_FILE"
    
    success "Report saved: $REPORT_FILE"
}

# Health score calculation
calculate_health_score() {
    SCORE=0
    TOTAL=100
    
    echo -e "\n${PURPLE}=== HEALTH SCORE CALCULATION ===${NC}"
    
    # Userbot running (25 points)
    if check_userbot_status >/dev/null 2>&1; then
        ((SCORE+=25))
        success "Userbot running (+25 points)"
    else
        error "Userbot not running (0 points)"
    fi
    
    # System resources (25 points)
    MEM_PERCENT=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    DISK_PERCENT=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $MEM_PERCENT -lt 80 ]]; then
        ((SCORE+=15))
        success "Memory usage OK (+15 points)"
    else
        warning "High memory usage (-0 points)"
    fi
    
    if [[ $DISK_PERCENT -lt 85 ]]; then
        ((SCORE+=10))
        success "Disk usage OK (+10 points)"
    else
        warning "High disk usage (-0 points)"
    fi
    
    # Network connectivity (20 points)
    if curl -s --max-time 5 https://api.telegram.org > /dev/null; then
        ((SCORE+=20))
        success "Network connectivity OK (+20 points)"
    else
        error "Network connectivity issues (0 points)"
    fi
    
    # File permissions (20 points)
    PERM_SCORE=0
    if [[ -f ".env" ]] && [[ "$(stat -c %a .env)" == "600" ]]; then
        ((PERM_SCORE+=10))
    fi
    
    for session in *.session*; do
        if [[ -f "$session" ]] && [[ "$(stat -c %a "$session")" == "600" ]]; then
            ((PERM_SCORE+=10))
            break
        fi
    done
    
    ((SCORE+=PERM_SCORE))
    if [[ $PERM_SCORE -eq 20 ]]; then
        success "File permissions secure (+20 points)"
    else
        warning "File permissions issues (+${PERM_SCORE} points)"
    fi
    
    # Log health (10 points)
    if [[ -f "userbot.log" ]]; then
        ERROR_COUNT=$(grep -c "ERROR" userbot.log 2>/dev/null || echo 0)
        if [[ $ERROR_COUNT -lt 5 ]]; then
            ((SCORE+=10))
            success "Low error count (+10 points)"
        else
            warning "High error count (+0 points)"
        fi
    fi
    
    # Display final score
    echo -e "\n${CYAN}╔═══════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║            HEALTH SCORE               ║${NC}"
    echo -e "${CYAN}║                                       ║${NC}"
    
    if [[ $SCORE -ge 90 ]]; then
        echo -e "${CYAN}║${GREEN}              $SCORE / $TOTAL                   ${CYAN}║${NC}"
        echo -e "${CYAN}║${GREEN}            EXCELLENT!                ${CYAN}║${NC}"
    elif [[ $SCORE -ge 75 ]]; then
        echo -e "${CYAN}║${YELLOW}              $SCORE / $TOTAL                   ${CYAN}║${NC}"
        echo -e "${CYAN}║${YELLOW}              GOOD                    ${CYAN}║${NC}"
    elif [[ $SCORE -ge 50 ]]; then
        echo -e "${CYAN}║${YELLOW}              $SCORE / $TOTAL                   ${CYAN}║${NC}"
        echo -e "${CYAN}║${YELLOW}              FAIR                    ${CYAN}║${NC}"
    else
        echo -e "${CYAN}║${RED}              $SCORE / $TOTAL                   ${CYAN}║${NC}"
        echo -e "${CYAN}║${RED}              POOR                    ${CYAN}║${NC}"
    fi
    
    echo -e "${CYAN}╚═══════════════════════════════════════╝${NC}"
}

# Main command handler
case "${1:-dashboard}" in
    "status")
        check_userbot_status
        ;;
    "system")
        check_system_resources
        ;;
    "network")
        check_network
        ;;
    "filesystem")
        check_filesystem
        ;;
    "performance")
        show_performance_metrics
        ;;
    "logs")
        analyze_logs
        ;;
    "realtime")
        realtime_monitor
        ;;
    "dashboard")
        show_dashboard
        ;;
    "report")
        create_report
        ;;
    "health")
        calculate_health_score
        ;;
    "full")
        show_dashboard
        calculate_health_score
        ;;
    *)
        echo -e "${CYAN}🖥️  USERBOT MONITORING SYSTEM${NC}"
        echo "=============================="
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "📊 Available Commands:"
        echo "  dashboard    - Show complete dashboard (default)"
        echo "  status       - Check userbot status only"
        echo "  system       - Show system resources"
        echo "  network      - Check network connectivity"
        echo "  filesystem   - Check file system status"
        echo "  performance  - Show performance metrics"
        echo "  logs         - Analyze log files"
        echo "  realtime     - Real-time monitoring (interactive)"
        echo "  report       - Generate monitoring report"
        echo "  health       - Calculate health score"
        echo "  full         - Dashboard + health score"
        echo ""
        echo "🚀 Quick commands:"
        echo "  ./monitor.sh              # Show dashboard"
        echo "  ./monitor.sh realtime     # Real-time monitor"
        echo "  ./monitor.sh health       # Health check"
        echo ""
        ;;
esac
