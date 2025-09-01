#!/usr/bin/env node
/**
 * VzoelFox Toggle Bot Assistant - Node.js Remote Control System
 * Author: Vzoel Fox's (Enhanced by Morgan)
 * Version: 1.0.0 - Remote Toggle Assistant
 * Description: Toggle bot untuk remote control userbot system
 */

const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

// Bot Configuration
const BOT_TOKEN = '8380293227:AAHYbOVl5Mou_yJmqKO890lwNqvDyLMM_lE';
const OWNER_IDS = []; // Will be auto-detected from userbot
const CONFIG_FILE = 'toggle_bot_config.json';
const LOG_FILE = 'toggle_bot.log';

// Initialize bot
const bot = new TelegramBot(BOT_TOKEN, { polling: true });
const execAsync = promisify(exec);

// Premium Emojis for consistent branding
const EMOJIS = {
    main: '🤩',
    check: '✅',
    cross: '❌',
    loading: '⏳',
    settings: '⚙️',
    power: '🔌',
    info: 'ℹ️',
    warning: '⚠️'
};

// Bot State Management
let botState = {
    userbot_running: false,
    last_check: null,
    authorized_users: new Set(),
    toggle_count: 0,
    start_time: Date.now()
};

// Configuration Management
async function loadConfig() {
    try {
        const data = await fs.readFile(CONFIG_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        return {
            version: "1.0.0",
            created: new Date().toISOString(),
            settings: {
                auto_detect_owner: true,
                userbot_script: "main.py",
                userbot_venv: "venv/bin/activate",
                max_restart_attempts: 3,
                restart_delay: 5000,
                log_retention_days: 7
            },
            authorized_users: [],
            statistics: {
                total_toggles: 0,
                last_toggle: null,
                uptime_start: new Date().toISOString()
            }
        };
    }
}

async function saveConfig(config) {
    try {
        config.last_updated = new Date().toISOString();
        await fs.writeFile(CONFIG_FILE, JSON.stringify(config, null, 2));
        return true;
    } catch (error) {
        console.error('Save config error:', error);
        return false;
    }
}

// Logging System
async function logMessage(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
        timestamp,
        level,
        message,
        data
    };
    
    console.log(`[${timestamp}] [${level}] ${message}`);
    
    try {
        const logLine = JSON.stringify(logEntry) + '\n';
        await fs.appendFile(LOG_FILE, logLine);
    } catch (error) {
        console.error('Logging error:', error);
    }
}

// Owner Detection
async function detectOwner() {
    try {
        // Try to read owner ID from userbot config
        const files = ['main.py', 'client.py', 'config.py'];
        
        for (const file of files) {
            try {
                const content = await fs.readFile(file, 'utf8');
                // Look for owner patterns
                const patterns = [
                    /OWNER_ID\s*=\s*(\d+)/,
                    /owner.*?(\d{8,})/i,
                    /admin.*?(\d{8,})/i
                ];
                
                for (const pattern of patterns) {
                    const match = content.match(pattern);
                    if (match) {
                        const ownerId = parseInt(match[1]);
                        if (ownerId > 100000) {
                            botState.authorized_users.add(ownerId);
                            await logMessage('INFO', `Owner detected: ${ownerId}`);
                            return ownerId;
                        }
                    }
                }
            } catch (err) {
                continue;
            }
        }
        
        return null;
    } catch (error) {
        await logMessage('ERROR', 'Owner detection failed', error.message);
        return null;
    }
}

// Userbot Management
async function checkUserbotStatus() {
    try {
        const { stdout } = await execAsync('pgrep -f "python.*main.py"');
        const running = stdout.trim().length > 0;
        
        botState.userbot_running = running;
        botState.last_check = Date.now();
        
        return running;
    } catch (error) {
        botState.userbot_running = false;
        return false;
    }
}

async function startUserbot() {
    try {
        await logMessage('INFO', 'Starting userbot...');
        
        // Kill existing processes first
        try {
            await execAsync('pkill -f "python.*main.py"');
            await new Promise(resolve => setTimeout(resolve, 2000));
        } catch (err) {
            // Ignore if no process to kill
        }
        
        // Start userbot in background
        const startCommand = 'cd /data/data/com.termux/files/home/vzoelfox && nohup python3 main.py > userbot.log 2>&1 &';
        await execAsync(startCommand);
        
        // Wait a moment and check if it started
        await new Promise(resolve => setTimeout(resolve, 3000));
        const running = await checkUserbotStatus();
        
        if (running) {
            await logMessage('INFO', 'Userbot started successfully');
            botState.toggle_count++;
            return true;
        } else {
            await logMessage('ERROR', 'Userbot failed to start');
            return false;
        }
    } catch (error) {
        await logMessage('ERROR', 'Start userbot error', error.message);
        return false;
    }
}

async function stopUserbot() {
    try {
        await logMessage('INFO', 'Stopping userbot...');
        
        // Kill userbot processes
        await execAsync('pkill -f "python.*main.py"');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const running = await checkUserbotStatus();
        
        if (!running) {
            await logMessage('INFO', 'Userbot stopped successfully');
            botState.toggle_count++;
            return true;
        } else {
            await logMessage('WARNING', 'Userbot may still be running');
            return false;
        }
    } catch (error) {
        await logMessage('ERROR', 'Stop userbot error', error.message);
        // Force kill
        try {
            await execAsync('pkill -9 -f "python.*main.py"');
            return true;
        } catch (forceErr) {
            return false;
        }
    }
}

async function restartUserbot() {
    await logMessage('INFO', 'Restarting userbot...');
    
    const stopped = await stopUserbot();
    if (stopped) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        return await startUserbot();
    }
    
    return false;
}

// Authorization
async function isAuthorized(userId) {
    const config = await loadConfig();
    
    // Auto-detect owner on first use
    if (config.settings.auto_detect_owner && botState.authorized_users.size === 0) {
        const detectedOwner = await detectOwner();
        if (detectedOwner) {
            config.authorized_users.push(detectedOwner);
            await saveConfig(config);
        }
    }
    
    return botState.authorized_users.has(userId) || 
           config.authorized_users.includes(userId);
}

// Message Builders
function createStatusMessage() {
    const uptime = Math.floor((Date.now() - botState.start_time) / 1000);
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    
    return `${EMOJIS.main} **VzoelFox Toggle Bot Status**

${EMOJIS.power} **Userbot:** ${botState.userbot_running ? 'Running ✅' : 'Stopped ❌'}
${EMOJIS.info} **Last Check:** ${botState.last_check ? new Date(botState.last_check).toLocaleString() : 'Never'}
${EMOJIS.settings} **Toggles:** ${botState.toggle_count} times
${EMOJIS.check} **Uptime:** ${hours}h ${minutes}m

**Controls:**
• /start - Show this menu
• /toggle - Start/Stop userbot
• /restart - Restart userbot
• /status - Check userbot status
• /logs - View recent logs`;
}

function createInlineKeyboard(isRunning) {
    return {
        inline_keyboard: [
            [
                {
                    text: isRunning ? `${EMOJIS.cross} Stop Userbot` : `${EMOJIS.check} Start Userbot`,
                    callback_data: 'toggle_userbot'
                }
            ],
            [
                {
                    text: `${EMOJIS.loading} Restart Userbot`,
                    callback_data: 'restart_userbot'
                },
                {
                    text: `${EMOJIS.info} Check Status`,
                    callback_data: 'check_status'
                }
            ],
            [
                {
                    text: `${EMOJIS.settings} View Logs`,
                    callback_data: 'view_logs'
                }
            ]
        ]
    };
}

// Bot Event Handlers
bot.onText(/\/start/, async (msg) => {
    const userId = msg.from.id;
    
    if (!await isAuthorized(userId)) {
        bot.sendMessage(msg.chat.id, `${EMOJIS.cross} **Access Denied**\n\nThis bot is restricted to authorized users only.`, { parse_mode: 'Markdown' });
        await logMessage('WARNING', `Unauthorized access attempt from ${userId}`);
        return;
    }
    
    await checkUserbotStatus();
    const statusMessage = createStatusMessage();
    const keyboard = createInlineKeyboard(botState.userbot_running);
    
    bot.sendMessage(msg.chat.id, statusMessage, {
        parse_mode: 'Markdown',
        reply_markup: keyboard
    });
    
    await logMessage('INFO', `Bot started for user ${userId}`);
});

bot.onText(/\/toggle/, async (msg) => {
    const userId = msg.from.id;
    
    if (!await isAuthorized(userId)) {
        bot.sendMessage(msg.chat.id, `${EMOJIS.cross} Access denied`);
        return;
    }
    
    const statusMsg = await bot.sendMessage(msg.chat.id, `${EMOJIS.loading} **Checking userbot status...**`, { parse_mode: 'Markdown' });
    
    await checkUserbotStatus();
    
    let result;
    if (botState.userbot_running) {
        bot.editMessageText(`${EMOJIS.loading} **Stopping userbot...**`, {
            chat_id: msg.chat.id,
            message_id: statusMsg.message_id,
            parse_mode: 'Markdown'
        });
        result = await stopUserbot();
    } else {
        bot.editMessageText(`${EMOJIS.loading} **Starting userbot...**`, {
            chat_id: msg.chat.id,
            message_id: statusMsg.message_id,
            parse_mode: 'Markdown'
        });
        result = await startUserbot();
    }
    
    await checkUserbotStatus();
    const successEmoji = result ? EMOJIS.check : EMOJIS.cross;
    const status = botState.userbot_running ? 'Running' : 'Stopped';
    const action = botState.userbot_running ? 'started' : 'stopped';
    
    bot.editMessageText(`${successEmoji} **Userbot ${action}**\n\n**Current Status:** ${status}`, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown'
    });
});

bot.onText(/\/restart/, async (msg) => {
    const userId = msg.from.id;
    
    if (!await isAuthorized(userId)) {
        bot.sendMessage(msg.chat.id, `${EMOJIS.cross} Access denied`);
        return;
    }
    
    const statusMsg = await bot.sendMessage(msg.chat.id, `${EMOJIS.loading} **Restarting userbot...**`, { parse_mode: 'Markdown' });
    
    const result = await restartUserbot();
    await checkUserbotStatus();
    
    const successEmoji = result ? EMOJIS.check : EMOJIS.cross;
    const status = botState.userbot_running ? 'Running' : 'Stopped';
    
    bot.editMessageText(`${successEmoji} **Userbot restart ${result ? 'successful' : 'failed'}**\n\n**Current Status:** ${status}`, {
        chat_id: msg.chat.id,
        message_id: statusMsg.message_id,
        parse_mode: 'Markdown'
    });
});

bot.onText(/\/status/, async (msg) => {
    const userId = msg.from.id;
    
    if (!await isAuthorized(userId)) {
        bot.sendMessage(msg.chat.id, `${EMOJIS.cross} Access denied`);
        return;
    }
    
    await checkUserbotStatus();
    const statusMessage = createStatusMessage();
    const keyboard = createInlineKeyboard(botState.userbot_running);
    
    bot.sendMessage(msg.chat.id, statusMessage, {
        parse_mode: 'Markdown',
        reply_markup: keyboard
    });
});

bot.onText(/\/logs/, async (msg) => {
    const userId = msg.from.id;
    
    if (!await isAuthorized(userId)) {
        bot.sendMessage(msg.chat.id, `${EMOJIS.cross} Access denied`);
        return;
    }
    
    try {
        const logs = await fs.readFile(LOG_FILE, 'utf8');
        const recentLogs = logs.split('\n').slice(-20).join('\n');
        
        if (recentLogs.trim()) {
            bot.sendMessage(msg.chat.id, `${EMOJIS.info} **Recent Logs:**\n\n\`\`\`\n${recentLogs}\n\`\`\``, { parse_mode: 'Markdown' });
        } else {
            bot.sendMessage(msg.chat.id, `${EMOJIS.warning} No logs available`);
        }
    } catch (error) {
        bot.sendMessage(msg.chat.id, `${EMOJIS.cross} Error reading logs: ${error.message}`);
    }
});

// Callback Query Handler
bot.on('callback_query', async (query) => {
    const userId = query.from.id;
    
    if (!await isAuthorized(userId)) {
        bot.answerCallbackQuery(query.id, { text: 'Access denied', show_alert: true });
        return;
    }
    
    const data = query.data;
    
    if (data === 'toggle_userbot') {
        bot.answerCallbackQuery(query.id, { text: 'Processing...' });
        
        await checkUserbotStatus();
        
        let result;
        if (botState.userbot_running) {
            result = await stopUserbot();
        } else {
            result = await startUserbot();
        }
        
        await checkUserbotStatus();
        const statusMessage = createStatusMessage();
        const keyboard = createInlineKeyboard(botState.userbot_running);
        
        bot.editMessageText(statusMessage, {
            chat_id: query.message.chat.id,
            message_id: query.message.message_id,
            parse_mode: 'Markdown',
            reply_markup: keyboard
        });
        
    } else if (data === 'restart_userbot') {
        bot.answerCallbackQuery(query.id, { text: 'Restarting...' });
        
        const result = await restartUserbot();
        await checkUserbotStatus();
        
        const statusMessage = createStatusMessage();
        const keyboard = createInlineKeyboard(botState.userbot_running);
        
        bot.editMessageText(statusMessage, {
            chat_id: query.message.chat.id,
            message_id: query.message.message_id,
            parse_mode: 'Markdown',
            reply_markup: keyboard
        });
        
    } else if (data === 'check_status') {
        bot.answerCallbackQuery(query.id, { text: 'Checking status...' });
        
        await checkUserbotStatus();
        const statusMessage = createStatusMessage();
        const keyboard = createInlineKeyboard(botState.userbot_running);
        
        bot.editMessageText(statusMessage, {
            chat_id: query.message.chat.id,
            message_id: query.message.message_id,
            parse_mode: 'Markdown',
            reply_markup: keyboard
        });
        
    } else if (data === 'view_logs') {
        bot.answerCallbackQuery(query.id, { text: 'Loading logs...' });
        
        try {
            const logs = await fs.readFile(LOG_FILE, 'utf8');
            const recentLogs = logs.split('\n').slice(-10).join('\n');
            
            if (recentLogs.trim()) {
                bot.sendMessage(query.message.chat.id, `${EMOJIS.info} **Recent Logs:**\n\n\`\`\`\n${recentLogs}\n\`\`\``, { parse_mode: 'Markdown' });
            } else {
                bot.sendMessage(query.message.chat.id, `${EMOJIS.warning} No logs available`);
            }
        } catch (error) {
            bot.sendMessage(query.message.chat.id, `${EMOJIS.cross} Error reading logs: ${error.message}`);
        }
    }
});

// Error Handling
bot.on('polling_error', (error) => {
    logMessage('ERROR', 'Polling error', error.message);
});

// Auto Status Check
setInterval(async () => {
    await checkUserbotStatus();
}, 30000); // Check every 30 seconds

// Initialization
async function initialize() {
    await logMessage('INFO', 'VzoelFox Toggle Bot starting...');
    
    const config = await loadConfig();
    await saveConfig(config);
    
    // Load authorized users
    config.authorized_users.forEach(id => botState.authorized_users.add(id));
    
    // Detect owner if needed
    if (config.settings.auto_detect_owner) {
        const detectedOwner = await detectOwner();
        if (detectedOwner && !botState.authorized_users.has(detectedOwner)) {
            botState.authorized_users.add(detectedOwner);
            config.authorized_users.push(detectedOwner);
            await saveConfig(config);
        }
    }
    
    // Initial status check
    await checkUserbotStatus();
    
    await logMessage('INFO', `Toggle bot initialized - Authorized users: ${Array.from(botState.authorized_users)}`);
    console.log(`🤩 VzoelFox Toggle Bot is running!`);
    console.log(`✅ Token: ${BOT_TOKEN.substring(0, 20)}...`);
    console.log(`⚙️ Authorized users: ${Array.from(botState.authorized_users).join(', ')}`);
}

// Start the bot
initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    await logMessage('INFO', 'Toggle bot shutting down...');
    process.exit(0);
});

process.on('SIGTERM', async () => {
    await logMessage('INFO', 'Toggle bot terminated');
    process.exit(0);
});