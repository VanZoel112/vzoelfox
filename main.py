from telethon import TelegramClient, events
import importlib, os
import config

# Init Client
client = TelegramClient(config.SESSION, config.API_ID, config.API_HASH)

# Load Plugins Otomatis
for plugin in os.listdir("plugins"):
    if plugin.endswith(".py"):
        importlib.import_module("plugins." + plugin[:-3])

# Start Bot
print("🔥 Vzoel Assistant Aktif 🔥")
client.start()
client.run_until_disconnected()
