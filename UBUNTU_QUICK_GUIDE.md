# 🚀 VzoelFox Ubuntu LTS 24 - Quick Setup Guide

## 📋 Your Exact Commands (Automated)

Instead of running commands manually, use these scripts:

### 🔧 One-time Setup
```bash
cd /home/ubuntu/vzoelfox
chmod +x setup_ubuntu.sh start_ubuntu.sh
./setup_ubuntu.sh
```

### 🚀 Daily Startup
```bash
cd /home/ubuntu/vzoelfox
./start_ubuntu.sh
```

## 📝 Manual Setup (Your Method)

If you prefer your exact commands:

```bash
cd vzoelfox
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install telethon
python3 main.py
```

## 🔄 Complete AWS Ubuntu Setup

### Step 1: Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/VanZoel112/vzoelfox.git
cd vzoelfox
```

### Step 2: System Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git ffmpeg
```

### Step 3: Install yt-dlp
```bash
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

### Step 4: Your Python Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install telethon yt-dlp mutagen aiohttp requests
```

### Step 5: Session Setup
```bash
# Option 1: Copy from your device
scp -i your-key.pem /path/to/userbot_session.session ubuntu@your-aws-ip:/home/ubuntu/vzoelfox/

# Option 2: Generate new session
python3 -c "
from telethon import TelegramClient
api_id = int(input('API ID: '))
api_hash = input('API Hash: ')
client = TelegramClient('userbot_session', api_id, api_hash)
client.start()
print('✅ Session created!')
"
```

### Step 6: Run VzoelFox
```bash
python3 main.py
```

## 🔁 Auto-restart Setup (Recommended)

### Create Systemd Service
```bash
sudo nano /etc/systemd/system/vzoelfox.service
```

**Service Content:**
```ini
[Unit]
Description=VzoelFox Userbot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/vzoelfox
Environment=PATH=/home/ubuntu/vzoelfox/venv/bin
ExecStart=/home/ubuntu/vzoelfox/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable vzoelfox.service
sudo systemctl start vzoelfox.service

# Check status
sudo systemctl status vzoelfox.service

# View logs
sudo journalctl -u vzoelfox.service -f
```

## 📊 Monitoring Commands

### Check Service Status
```bash
sudo systemctl status vzoelfox.service
```

### View Real-time Logs
```bash
sudo journalctl -u vzoelfox.service -f
```

### Restart Service
```bash
sudo systemctl restart vzoelfox.service
```

### Stop Service
```bash
sudo systemctl stop vzoelfox.service
```

## 🔧 Troubleshooting

### Common Issues:

#### Virtual Environment Not Found
```bash
cd /home/ubuntu/vzoelfox
python3 -m venv venv
source venv/bin/activate
pip install telethon
```

#### Session File Missing
```bash
# Check if session exists
ls -la *.session

# If not found, generate new one
python3 main.py
# Enter API credentials when prompted
```

#### Permission Denied
```bash
chmod +x setup_ubuntu.sh start_ubuntu.sh
sudo chown -R ubuntu:ubuntu /home/ubuntu/vzoelfox/
```

#### yt-dlp Not Working
```bash
# Update yt-dlp
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Or install via pip
pip install --upgrade yt-dlp
```

#### Database Locked
```bash
cd /home/ubuntu/vzoelfox
rm -f *.db-wal *.db-shm
python3 main.py
```

## 🔄 Update VzoelFox

```bash
cd /home/ubuntu/vzoelfox
git pull
source venv/bin/activate
pip install --upgrade telethon yt-dlp
sudo systemctl restart vzoelfox.service
```

## 💾 Backup Session

```bash
# Create backup
cp userbot_session.session userbot_session.session.backup

# Restore backup
cp userbot_session.session.backup userbot_session.session
```

## 🎯 Quick Commands Summary

| Action | Command |
|--------|---------|
| **Setup** | `./setup_ubuntu.sh` |
| **Start** | `./start_ubuntu.sh` |
| **Manual Start** | `source venv/bin/activate && python3 main.py` |
| **Service Start** | `sudo systemctl start vzoelfox.service` |
| **View Logs** | `sudo journalctl -u vzoelfox.service -f` |
| **Update** | `git pull && sudo systemctl restart vzoelfox.service` |

## ✅ Success Checklist

- [ ] Ubuntu LTS 24 server running
- [ ] Repository cloned to `/home/ubuntu/vzoelfox`
- [ ] Virtual environment created (`venv/`)
- [ ] Dependencies installed (telethon, yt-dlp)
- [ ] Session file present (`userbot_session.session`)
- [ ] yt-dlp installed system-wide
- [ ] FFmpeg installed for audio processing
- [ ] Systemd service configured (optional)
- [ ] Basic commands tested (`.help`, `.pink`)

**Your method is perfect!** The scripts just automate your exact workflow for easier deployment.