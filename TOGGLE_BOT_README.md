# VzoelFox Toggle Bot Assistant

🤩 **Remote Control System untuk VzoelFox Userbot**

## 📖 Description

Toggle Bot Assistant adalah sistem remote control berbasis Node.js yang memungkinkan Anda mengontrol userbot VzoelFox dari Telegram bot. Fitur ini sangat berguna untuk start/stop userbot dari HP lain atau saat tidak bisa akses langsung ke server.

## ✨ Features

- 🔌 **Remote Start/Stop** - Kontrol userbot dari Telegram
- 📊 **Real-time Status** - Monitor status userbot secara real-time  
- 🔒 **Secure Authorization** - Sistem otorisasi yang aman
- 📱 **Interactive Buttons** - Interface yang user-friendly
- 📋 **Detailed Logs** - Logging system yang lengkap
- ⚡ **Auto Installation** - Setup otomatis untuk dependencies

## 🚀 Quick Start

### 1. Installation

```bash
# Method 1: Via userbot plugin
.togglebot install

# Method 2: Manual installation  
./start_toggle_bot.sh install
```

### 2. Start Toggle Bot

```bash
# Via userbot plugin
.togglebot start

# Via script
./start_toggle_bot.sh start
```

### 3. Use in Telegram

1. Open Telegram
2. Search for bot menggunakan token: `8380293227:AAHYbOVl5Mou_yJmqKO890lwNqvDyLMM_lE`
3. Send `/start` command
4. Use buttons untuk kontrol userbot

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show control panel dengan buttons |
| `/toggle` | Start/Stop userbot |
| `/restart` | Restart userbot |
| `/status` | Check userbot status |
| `/logs` | View recent logs |

## 🔧 Userbot Integration

### Plugin Commands

| Command | Description |
|---------|-------------|
| `.togglebot` | Show toggle bot status |
| `.togglebot status` | Detailed status information |
| `.togglebot start` | Start the toggle bot |
| `.togglebot stop` | Stop the toggle bot |
| `.togglebot install` | Install all dependencies |

## 📁 File Structure

```
vzoelfox/
├── vzoel_toggle_bot.js           # Main Node.js bot script
├── start_toggle_bot.sh           # Management script
├── package.json                  # Node.js dependencies
├── plugins/
│   └── toggle_bot_integration.py # Userbot integration plugin
├── toggle_bot_config.json        # Bot configuration (auto-created)
├── toggle_bot.log                # Internal bot logs
└── toggle_bot_output.log         # Bot output logs
```

## ⚙️ Configuration

### Bot Token
Default token sudah ter-embed di script. Jika ingin menggunakan bot sendiri, edit file:
- `vzoel_toggle_bot.js` - line `const BOT_TOKEN`
- `plugins/toggle_bot_integration.py` - variable `BOT_TOKEN`

### Owner Detection
Bot akan otomatis detect owner dari:
- Environment variables (`OWNER_ID`)
- File `main.py`, `client.py`, `config.py`
- Pattern matching untuk owner ID

## 📊 Management Commands

### Script Management
```bash
./start_toggle_bot.sh start    # Start bot
./start_toggle_bot.sh stop     # Stop bot  
./start_toggle_bot.sh restart  # Restart bot
./start_toggle_bot.sh status   # Check status
./start_toggle_bot.sh logs     # View logs
./start_toggle_bot.sh install  # Install dependencies
```

### Process Management
```bash
# Check if running
ps aux | grep vzoel_toggle_bot

# Kill manually if needed
pkill -f "node.*vzoel_toggle_bot.js"

# View logs
tail -f toggle_bot_output.log
tail -f toggle_bot.log
```

## 🔒 Security

### Authorization
- Owner auto-detection dari userbot config
- Whitelist system untuk authorized users
- Access denied untuk unauthorized users

### Best Practices
- Jangan share bot token di public
- Monitor logs untuk unauthorized access attempts
- Gunakan private bot (jangan set sebagai public)

## 🐛 Troubleshooting

### Common Issues

**Node.js not installed:**
```bash
pkg install nodejs
```

**npm dependencies missing:**
```bash
npm install node-telegram-bot-api
```

**Bot tidak respond:**
```bash
# Check if bot is running
./start_toggle_bot.sh status

# Check logs
./start_toggle_bot.sh logs

# Restart bot
./start_toggle_bot.sh restart
```

**Permission denied:**
```bash
chmod +x start_toggle_bot.sh
chmod +x vzoel_toggle_bot.js
```

**Userbot tidak start/stop:**
- Pastikan userbot script `main.py` ada
- Check userbot logs: `tail -f userbot.log`
- Verify working directory correct

### Log Analysis

**Bot Logs:**
```bash
# Internal bot logs (JSON format)
cat toggle_bot.log

# Bot output logs (console)
cat toggle_bot_output.log
```

**Common Error Patterns:**
- `ECONNREFUSED` - Network connectivity issues
- `Unauthorized` - Bot token invalid
- `Process not found` - Userbot process missing
- `Permission denied` - File permission issues

## 📈 Monitoring

### Status Indicators
- ✅ **Running** - Bot berjalan normal
- ❌ **Stopped** - Bot tidak berjalan
- ⚠️ **Warning** - Bot berjalan tapi ada issue
- 🔄 **Restarting** - Bot dalam proses restart

### Metrics Tracking
- Total toggles performed
- Uptime tracking
- Memory usage monitoring
- CPU usage tracking

## 🔄 Auto-Start Setup

### Systemd Service (Optional)
Create service file untuk auto-start on boot:

```bash
# Create service file
cat > ~/.config/systemd/user/vzoeltoggle.service << EOF
[Unit]
Description=VzoelFox Toggle Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/data/data/com.termux/files/home/vzoelfox
ExecStart=/data/data/com.termux/files/home/vzoelfox/start_toggle_bot.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable vzoeltoggle
systemctl --user start vzoeltoggle
```

### Cron Job (Alternative)
```bash
# Add to crontab
echo "@reboot /data/data/com.termux/files/home/vzoelfox/start_toggle_bot.sh start" | crontab -
```

## 🤝 Integration Examples

### Custom Commands
Extend bot functionality dengan custom commands:

```javascript
// Add to vzoel_toggle_bot.js
bot.onText(/\/custom/, async (msg) => {
    // Your custom functionality here
});
```

### Webhook Integration
Setup webhook untuk external notifications:

```javascript
// Add webhook endpoint
const express = require('express');
const app = express();

app.post('/webhook', (req, res) => {
    // Handle webhook data
    console.log('Webhook received:', req.body);
    res.status(200).send('OK');
});
```

## 📞 Support

### Getting Help
- Check logs first: `./start_toggle_bot.sh logs`
- Verify all files present: `./start_toggle_bot.sh status`
- Try reinstalling: `./start_toggle_bot.sh install`

### Contact Information
- **Author:** Vzoel Fox's (Enhanced by Morgan)
- **Version:** 1.0.0
- **License:** MIT

## 📝 Changelog

### v1.0.0
- ✅ Initial release
- ✅ Remote start/stop functionality  
- ✅ Interactive Telegram interface
- ✅ Automatic owner detection
- ✅ Comprehensive logging system
- ✅ Easy installation process

---

**© 2025 Vzoel Fox's (LTPN) - Premium Userbot System** 🤩