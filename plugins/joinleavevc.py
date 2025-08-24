from telethon import events
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream.quality import MediumQualityAudio
import config

client = None
pytgcalls = None

@events.register(events.NewMessage(pattern=r"\.joinvc"))
async def join_vc(event):
    global client, pytgcalls
    if not pytgcalls:
        client = event.client
        pytgcalls = PyTgCalls(client)
        await pytgcalls.start()
    chat = await event.get_chat()
    await pytgcalls.join_group_call(
        chat.id,
        InputAudioStream("sample.mp3", MediumQualityAudio())  # contoh play file
    )
    await event.reply("🔊 Bergabung ke VC!")

@events.register(events.NewMessage(pattern=r"\.leavevc"))
async def leave_vc(event):
    chat = await event.get_chat()
    await pytgcalls.leave_group_call(chat.id)
    await event.reply("👋 Keluar dari VC!")
