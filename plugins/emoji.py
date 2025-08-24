from telethon import events

EMOJI_PACK = {
    "love": "💖💘💞💓💕💝",
    "fire": "🔥⚡💥",
    "star": "⭐✨🌟💫"
}

@events.register(events.NewMessage(pattern=r"\.emoji (.+)"))
async def emoji(event):
    key = event.pattern_match.group(1).lower()
    if key in EMOJI_PACK:
        await event.reply(EMOJI_PACK[key])
    else:
        await event.reply("❌ Emoji pack tidak ditemukan")
      
