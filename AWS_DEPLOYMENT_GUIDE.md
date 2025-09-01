# 🚀 VzoelFox Userbot 24/7 AWS Ubuntu LTS 24 Deployment Guide

## 📋 Prerequisites

### AWS Requirements
- AWS Account with billing enabled
- EC2 instance access (t3.micro for free tier)
- Security Group configured for SSH access
- Key pair for SSH authentication

### Local Requirements
- SSH client (PuTTY on Windows, Terminal on Linux/Mac)
- Basic Linux command knowledge

## 🛠️ Step 1: Launch EC2 Instance

### Instance Configuration
```bash
# Instance Type: t3.micro (free tier eligible)
# AMI: Ubuntu Server 24.04 LTS (HVM), SSD Volume Type
# Storage: 8GB gp3 (free tier)
# Security Group: Allow SSH (port 22) from your IP
```

### Launch Steps:
1. **Login to AWS Console** → EC2 Dashboard
2. **Launch Instance** → Choose Ubuntu 24.04 LTS
3. **Instance Type** → t3.micro (free tier)
4. **Key Pair** → Create or use existing key pair
5. **Security Groups** → Allow SSH (22) from your IP
6. **Storage** → 8GB gp3 (default)
7. **Launch Instance**

## 🔑 Step 2: Connect to Instance

```bash
# Download your key pair (e.g., vzoelfox-key.pem)
chmod 400 vzoelfox-key.pem

# Connect to instance
ssh -i vzoelfox-key.pem ubuntu@YOUR-INSTANCE-PUBLIC-IP
```

## 📦 Step 3: System Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv curl wget unzip
```

### Install Node.js (for toggle bot)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Install FFmpeg & yt-dlp (for music features)
```bash
sudo apt install -y ffmpeg
pip3 install yt-dlp mutagen
```

## 📱 Step 4: Setup VzoelFox Userbot

### Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/VanZoel112/vzoelfox.git
cd vzoelfox
```

### Setup Python Environment
```bash
python3 -m venv vzoelbot_env
source vzoelbot_env/bin/activate
pip install -r requirements.txt
```

### Configure Userbot
```bash
# Copy your session files from Termux
# Method 1: SCP from your device
scp -i vzoelfox-key.pem /path/to/userbot_session.session ubuntu@YOUR-INSTANCE-IP:/home/ubuntu/vzoelfox/

# Method 2: Generate new session on AWS
python3 -c "
from telethon import TelegramClient
api_id = int(input('API ID: '))
api_hash = input('API Hash: ')
client = TelegramClient('userbot_session', api_id, api_hash)
client.start()
print('Session created successfully!')
"
```

### Setup Configuration Files
```bash
# Copy essential config files
cp emoji_config.json.example emoji_config.json
cp gcast_blacklist.json.example gcast_blacklist.json

# Edit configurations as needed
nano emoji_config.json
nano gcast_blacklist.json
```

## 🔧 Step 5: Install System Services

### Create Systemd Service
```bash
sudo nano /etc/systemd/system/vzoelfox.service
```

**Service File Content:**
```ini
[Unit]
Description=VzoelFox Userbot Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=ubuntu
WorkingDirectory=/home/ubuntu/vzoelfox
Environment=PATH=/home/ubuntu/vzoelfox/vzoelbot_env/bin
ExecStartPre=/home/ubuntu/vzoelfox/vzoelbot_env/bin/pip install -r requirements.txt
ExecStart=/home/ubuntu/vzoelfox/vzoelbot_env/bin/python main.py
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vzoelfox

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable vzoelfox.service
sudo systemctl start vzoelfox.service
```

### Check Service Status
```bash
sudo systemctl status vzoelfox.service
sudo journalctl -u vzoelfox.service -f  # Follow logs
```

## 🤖 Step 6: Setup Toggle Bot (Optional)

### Install Dependencies
```bash
npm install node-telegram-bot-api
```

### Create Toggle Bot Service
```bash
sudo nano /etc/systemd/system/vzoelfox-toggle.service
```

**Toggle Bot Service:**
```ini
[Unit]
Description=VzoelFox Toggle Bot
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=5
User=ubuntu
WorkingDirectory=/home/ubuntu/vzoelfox
ExecStart=/usr/bin/node vzoel_toggle_bot.js
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Start Toggle Bot
```bash
sudo systemctl daemon-reload
sudo systemctl enable vzoelfox-toggle.service
sudo systemctl start vzoelfox-toggle.service
```

## 📊 Step 7: Monitoring & Maintenance

### Setup Log Rotation
```bash
sudo nano /etc/logrotate.d/vzoelfox
```

**Log Rotation Config:**
```
/home/ubuntu/vzoelfox/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
```

### Create Monitoring Script
```bash
nano /home/ubuntu/monitor_vzoelfox.sh
chmod +x /home/ubuntu/monitor_vzoelfox.sh
```

**Monitor Script:**
```bash
#!/bin/bash
# VzoelFox Health Monitor

LOG_FILE="/home/ubuntu/vzoelfox_monitor.log"
TELEGRAM_TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"

# Function to send Telegram notification
send_notification() {
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
         -d chat_id="$CHAT_ID" \
         -d text="🚨 VzoelFox Alert: $1"
}

# Check if service is running
if ! systemctl is-active --quiet vzoelfox.service; then
    echo "$(date): VzoelFox service is down, restarting..." >> $LOG_FILE
    sudo systemctl start vzoelfox.service
    send_notification "VzoelFox service was down and has been restarted"
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    send_notification "Disk usage is at ${DISK_USAGE}% on VzoelFox server"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f"), $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 90 ]; then
    send_notification "Memory usage is at ${MEM_USAGE}% on VzoelFox server"
fi
```

### Setup Cron Jobs
```bash
crontab -e

# Add these lines:
# Check every 5 minutes
*/5 * * * * /home/ubuntu/monitor_vzoelfox.sh

# Auto-update daily at 3 AM
0 3 * * * cd /home/ubuntu/vzoelfox && git pull && sudo systemctl restart vzoelfox.service

# Clean logs weekly
0 0 * * 0 find /home/ubuntu/vzoelfox -name "*.log" -type f -mtime +7 -delete
```

## 🔒 Step 8: Security Hardening

### Setup Firewall
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from YOUR_HOME_IP to any port 22
sudo ufw deny ssh  # Deny SSH from other IPs
```

### Disable Root Login
```bash
sudo nano /etc/ssh/sshd_config

# Add/modify these lines:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

sudo systemctl restart ssh
```

### Setup Automatic Security Updates
```bash
sudo apt install unattended-upgrades
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Enable security updates
sudo systemctl enable unattended-upgrades
```

## 💾 Step 9: Backup Strategy

### Create Backup Script
```bash
nano /home/ubuntu/backup_vzoelfox.sh
chmod +x /home/ubuntu/backup_vzoelfox.sh
```

**Backup Script:**
```bash
#!/bin/bash
# VzoelFox Backup Script

BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
USERBOT_DIR="/home/ubuntu/vzoelfox"

mkdir -p $BACKUP_DIR

# Create backup archive
tar -czf $BACKUP_DIR/vzoelfox_backup_$DATE.tar.gz \
    $USERBOT_DIR/*.db \
    $USERBOT_DIR/*.session* \
    $USERBOT_DIR/*.json \
    $USERBOT_DIR/data/ \
    $USERBOT_DIR/plugins/ \
    $USERBOT_DIR/utils/

# Keep only last 7 backups
find $BACKUP_DIR -name "vzoelfox_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: vzoelfox_backup_$DATE.tar.gz"
```

### Schedule Daily Backup
```bash
# Add to crontab
0 2 * * * /home/ubuntu/backup_vzoelfox.sh
```

## 🚀 Step 10: Final Testing

### Test All Services
```bash
# Check userbot service
sudo systemctl status vzoelfox.service

# Check logs
sudo journalctl -u vzoelfox.service --since "1 hour ago"

# Test commands in Telegram
# Send .pink to test basic functionality
# Send .help to test navigation system
# Send .musictest to test music system
```

## 🔧 Troubleshooting

### Common Issues:

#### Service Won't Start
```bash
# Check logs
sudo journalctl -u vzoelfox.service -n 50

# Check permissions
ls -la /home/ubuntu/vzoelfox/
sudo chown -R ubuntu:ubuntu /home/ubuntu/vzoelfox/
```

#### Database Lock Errors
```bash
# Stop service and clean locks
sudo systemctl stop vzoelfox.service
rm -f /home/ubuntu/vzoelfox/*.db-wal /home/ubuntu/vzoelfox/*.db-shm
sudo systemctl start vzoelfox.service
```

#### High Memory Usage
```bash
# Add swap space
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 📱 Management Commands

### Start/Stop/Restart
```bash
sudo systemctl start vzoelfox.service      # Start
sudo systemctl stop vzoelfox.service       # Stop  
sudo systemctl restart vzoelfox.service    # Restart
sudo systemctl status vzoelfox.service     # Status
```

### View Logs
```bash
sudo journalctl -u vzoelfox.service -f     # Follow logs
sudo journalctl -u vzoelfox.service -n 100 # Last 100 lines
```

### Update Userbot
```bash
cd /home/ubuntu/vzoelfox
git pull
sudo systemctl restart vzoelfox.service
```

## 💰 Cost Optimization

### Free Tier Limits
- **750 hours/month** of t3.micro (24/7 for 1 month)
- **30GB** of EBS storage
- **15GB** of bandwidth out

### Monthly Costs (After Free Tier)
- **t3.micro**: ~$8.50/month
- **8GB EBS**: ~$0.80/month
- **Data Transfer**: $0.09/GB (first 10TB)

### Cost Saving Tips
1. **Use Spot Instances** (can save 90% but may terminate)
2. **Schedule shutdown** during inactive hours
3. **Monitor usage** with AWS Cost Explorer
4. **Set billing alerts** to avoid surprises

## 🎯 Production Optimizations

### Performance Tuning
```bash
# Increase file limits
echo "ubuntu soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "ubuntu hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize Python
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

### Database Optimization
```bash
# Add to main.py or config
sqlite3 settings:
- WAL mode enabled
- Busy timeout: 60s
- Cache size: 10000 pages
- Auto checkpoint: 1000
```

## ✅ Success Checklist

- [ ] EC2 instance running Ubuntu 24.04 LTS
- [ ] Python 3.12+ with virtual environment
- [ ] All dependencies installed (telethon, yt-dlp, etc.)
- [ ] Session files transferred/generated
- [ ] Systemd service configured and running
- [ ] Monitoring script active with cron jobs
- [ ] Security hardening applied
- [ ] Backup strategy implemented
- [ ] Basic commands tested in Telegram
- [ ] Log rotation configured
- [ ] Cost monitoring enabled

## 📞 Support

If you encounter issues:

1. **Check logs first**: `sudo journalctl -u vzoelfox.service -n 100`
2. **Verify internet connection**: `ping -c 4 google.com`
3. **Check Telegram API**: `curl https://api.telegram.org`
4. **Monitor resources**: `htop`, `df -h`, `free -h`

## 🚀 Going Live!

After completing all steps, your VzoelFox userbot will:

- ✅ **Run 24/7** without interruption
- ✅ **Auto-restart** if crashes occur
- ✅ **Auto-update** daily via cron
- ✅ **Send alerts** when issues arise
- ✅ **Backup data** automatically
- ✅ **Scale resources** as needed

**Your VzoelFox is now live in the cloud! 🎉**

---

## 📄 Quick Deploy Script

Save this as `quick_deploy.sh` for rapid deployment:

```bash
#!/bin/bash
# VzoelFox Quick Deploy Script

set -e

echo "🚀 VzoelFox AWS Deployment Starting..."

# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv curl wget unzip ffmpeg

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install yt-dlp
pip3 install yt-dlp mutagen

# Clone repository
cd /home/ubuntu
git clone https://github.com/VanZoel112/vzoelfox.git
cd vzoelfox

# Setup Python environment
python3 -m venv vzoelbot_env
source vzoelbot_env/bin/activate
pip install -r requirements.txt

echo "✅ Basic setup completed!"
echo "📋 Next steps:"
echo "1. Transfer your session files"
echo "2. Configure emoji_config.json"
echo "3. Setup systemd service"
echo "4. Start the userbot"

echo "🔧 Run: sudo nano /etc/systemd/system/vzoelfox.service"
echo "📱 Then: sudo systemctl enable vzoelfox.service"
echo "🚀 Finally: sudo systemctl start vzoelfox.service"
```

Make executable and run:
```bash
chmod +x quick_deploy.sh
./quick_deploy.sh
```

---

**🎉 Congratulations! Your VzoelFox userbot is now ready for 24/7 operation on AWS!**