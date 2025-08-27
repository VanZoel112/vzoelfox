# voice.py (plugin)
import re
import threading
import asyncio
import numpy as np
import sounddevice as sd
from scipy.signal import resample, butter, filtfilt
import logging
from pathlib import Path
from telethon import events

# Character voice configurations
VOICE_CHARACTERS = {
    "jokowi":   {"name": "Joko Widodo",        "pitch_factor": 0.85, "formant_shift": 0.9,  "speaking_rate": 0.9, "tone_profile": "authoritative"},
    "squidward":{"name": "Squidward Tentacles","pitch_factor": 0.7,  "formant_shift": 1.1,  "speaking_rate": 0.8, "tone_profile": "nasal"},
    "spongebob":{"name": "SpongeBob SquarePants","pitch_factor": 1.4,"formant_shift": 1.3,  "speaking_rate": 1.2, "tone_profile": "excited"},
    "ganjar":   {"name": "Ganjar Pranowo",     "pitch_factor": 0.9,  "formant_shift": 0.95, "speaking_rate": 1.0, "tone_profile": "friendly"},
    "clara":    {"name": "Clara Mongstar",     "pitch_factor": 1.2,  "formant_shift": 1.15, "speaking_rate": 1.1, "tone_profile": "energetic"}
}

class VoiceCloneEngine:
    def __init__(self):
        self.is_active = False
        self.current_character = "normal"
        self.processing_lock = threading.Lock()
        self.sample_rate = 44100  # default sample rate
        self.buffer_size = 1024

    def apply_character_voice(self, audio_data, character):
        if character == "normal" or character not in VOICE_CHARACTERS:
            return audio_data
        char_config = VOICE_CHARACTERS[character]
        processed = audio_data.copy()
        try:
            if char_config["pitch_factor"] != 1.0:
                processed = self.pitch_shift(processed, char_config["pitch_factor"])
            if char_config["formant_shift"] != 1.0:
                processed = self.formant_shift(processed, char_config["formant_shift"])
            tone = char_config["tone_profile"]
            if tone == "nasal":
                processed = self.apply_nasal_effect(processed)
            elif tone == "excited":
                processed = self.apply_excitement_effect(processed)
            elif tone == "authoritative":
                processed = self.apply_authority_effect(processed)
            elif tone == "friendly":
                processed = self.apply_warmth_effect(processed)
            elif tone == "energetic":
                processed = self.apply_energy_effect(processed)
            return processed
        except Exception as e:
            logging.error(f"Character voice processing error: {e}")
            return audio_data

    def pitch_shift(self, audio_data, factor):
        if factor == 1.0:
            return audio_data
        new_length = int(len(audio_data) * factor)
        if new_length > 0:
            shifted = resample(audio_data, new_length)
            if len(shifted) < len(audio_data):
                padded = np.zeros(len(audio_data))
                padded[:len(shifted)] = shifted
                return padded
            else:
                return shifted[:len(audio_data)]
        return audio_data

    def formant_shift(self, audio_data, factor):
        if factor == 1.0:
            return audio_data
        nyquist = self.sample_rate / 2
        if factor > 1.0:
            low = 200 / nyquist
            high = min(3000 * factor, nyquist - 100) / nyquist
            b, a = butter(4, [low, high], btype='band')
            return filtfilt(b, a, audio_data)
        else:
            cutoff = min(2000 * factor, nyquist - 100) / nyquist
            b, a = butter(4, cutoff, btype='low')
            return filtfilt(b, a, audio_data)

    def apply_nasal_effect(self, audio_data):
        nyquist = self.sample_rate / 2
        low = 1000 / nyquist
        high = 2000 / nyquist
        b, a = butter(2, [low, high], btype='band')
        filtered = filtfilt(b, a, audio_data)
        return audio_data + 0.3 * filtered

    def apply_excitement_effect(self, audio_data):
        t = np.arange(len(audio_data)) / self.sample_rate
        tremolo = 1 + 0.1 * np.sin(2 * np.pi * 5 * t)  # 5 Hz tremolo
        nyquist = self.sample_rate / 2
        cutoff = 2000 / nyquist
        b, a = butter(2, cutoff, btype='high')
        high_boost = filtfilt(b, a, audio_data)
        return (audio_data + 0.2 * high_boost) * tremolo

    def apply_authority_effect(self, audio_data):
        nyquist = self.sample_rate / 2
        low = 150 / nyquist
        high = 800 / nyquist
        b, a = butter(3, [low, high], btype='band')
        filtered = filtfilt(b, a, audio_data)
        return audio_data + 0.25 * filtered

    def apply_warmth_effect(self, audio_data):
        nyquist = self.sample_rate / 2
        cutoff = 500 / nyquist
        b, a = butter(2, cutoff, btype='low')
        warm = filtfilt(b, a, audio_data)
        return audio_data + 0.15 * warm

    def apply_energy_effect(self, audio_data):
        nyquist = self.sample_rate / 2
        cutoff = 1500 / nyquist
        b, a = butter(2, cutoff, btype='high')
        bright = filtfilt(b, a, audio_data)
        threshold = 0.3
        compressed = np.where(np.abs(audio_data) > threshold,
                              threshold + (audio_data - threshold) * 0.5,
                              audio_data)
        return compressed + 0.2 * bright

    def audio_callback(self, indata, outdata, frames, time_info, status):
        if status:
            logging.warning(f"Audio status: {status}")
        try:
            with self.processing_lock:
                mono_input = indata[:, 0] if indata.ndim > 1 else indata
                processed = self.apply_character_voice(mono_input, self.current_character)
                processed = np.clip(processed, -0.95, 0.95)
                outdata[:, 0] = processed
        except Exception as e:
            logging.error(f"Audio callback error: {e}")
            outdata[:] = indata

    def start_voice_clone(self, character="normal"):
        if self.is_active:
            self.stop_voice_clone()
        self.current_character = character
        self.is_active = True
        try:
            with sd.InputStream(callback=self.audio_callback,
                                channels=1, samplerate=self.sample_rate, blocksize=self.buffer_size):
                with sd.OutputStream(callback=self.audio_callback,
                                     channels=1, samplerate=self.sample_rate, blocksize=self.buffer_size):
                    logging.info(f"Voice clone started with character: {character}")
                    while self.is_active:
                        sd.sleep(100)
        except Exception as e:
            logging.error(f"Voice clone start error: {e}")
            self.is_active = False

    def stop_voice_clone(self):
        self.is_active = False
        logging.info("Voice clone stopped")

# Instantiate the voice engine
voice_engine = VoiceCloneEngine()

# Command: .voice
@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}voice(?:\s+(.*))?', re.DOTALL)))
async def voice_handler(event):
    if not await is_owner(event.sender_id):
        return
    args_text = event.pattern_match.group(1)
    args = args_text.split() if args_text else []
    if not args:
        await event.reply("🎤 **Voice Clone Commands:**\n\n"
                          f"`{COMMAND_PREFIX}voice start <character>` - Start voice clone\n"
                          f"`{COMMAND_PREFIX}voice stop` - Stop voice clone\n"
                          f"`{COMMAND_PREFIX}voice list` - List characters\n"
                          f"`{COMMAND_PREFIX}voice status` - Show status")
        return
    cmd = args[0].lower()
    if cmd == "start":
        character = args[1] if len(args) > 1 else "normal"
        if character != "normal" and character not in VOICE_CHARACTERS:
            await event.reply(f"❌ Character '{character}' not found!\n"
                              f"Available: normal, " + ", ".join(VOICE_CHARACTERS.keys()))
            return
        def start_clone():
            voice_engine.start_voice_clone(character)
        if not voice_engine.is_active:
            threading.Thread(target=start_clone, daemon=True).start()
            char_name = VOICE_CHARACTERS.get(character, {}).get("name", character)
            await event.reply(f"🎭 **Voice Clone Started!**\n"
                              f"Character: **{char_name}**\n"
                              f"Status: **Active** ✅")
        else:
            await event.reply("⚠️ Voice clone already active!")
    elif cmd == "stop":
        voice_engine.stop_voice_clone()
        await event.reply("🛑 **Voice Clone Stopped!**")
    elif cmd == "list":
        char_list = "🎭 **Available Characters:**\n\n"
        for key, info in VOICE_CHARACTERS.items():
            char_list += f"• `{key}` - {info['name']}\n"
        char_list += "• `normal` - Original Voice"
        await event.reply(char_list)
    elif cmd == "status":
        status = "Active ✅" if voice_engine.is_active else "Inactive ❌"
        char = voice_engine.current_character
        char_name = VOICE_CHARACTERS.get(char, {}).get("name", char)
        await event.reply(f"🎤 **Voice Clone Status:**\n\n"
                          f"Status: **{status}**\n"
                          f"Character: **{char_name}**\n"
                          f"Sample Rate: {voice_engine.sample_rate} Hz")
    else:
        await event.reply(f"❌ Unknown subcommand: {cmd}")

# Command: .quick
@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}quick(?:\s+(.+))?', re.DOTALL)))
async def quick_handler(event):
    if not await is_owner(event.sender_id):
        return
    text = event.pattern_match.group(1)
    args = text.split() if text else []
    if not args:
        await event.reply(f"Usage: `{COMMAND_PREFIX}quick <character>`")
        return
    character = args[0]
    if character in VOICE_CHARACTERS:
        voice_engine.current_character = character
        char_name = VOICE_CHARACTERS[character]["name"]
        await event.reply(f"🎭 Switched to: **{char_name}**")
    else:
        await event.reply(f"❌ Character not found: {character}")

# Command: .session
@client.on(events.NewMessage(pattern=re.compile(rf'{re.escape(COMMAND_PREFIX)}session(?:\s+(.+))?', re.DOTALL)))
async def session_handler(event):
    if not await is_owner(event.sender_id):
        return
    args_text = event.pattern_match.group(1)
    args = args_text.split() if args_text else []
    if not args or args[0] == "info":
        me = await client.get_me()
        session_file = Path(f"{SESSION_NAME}.session")
        info = f"📋 **Session Information:**\n\n"
        info += f"👤 Name: {me.first_name or ''} {me.last_name or ''}\n"
        info += f"📱 Phone: {me.phone_number}\n"
        info += f"🆔 User ID: {me.id}\n"
        info += f"📁 Session File: {'✅ Exists' if session_file.exists() else '❌ Not Found'}\n"
        info += f"🔗 Status: Connected ✅"
        await event.reply(info)
    elif args[0] == "reset":
        await event.reply("🔄 **Resetting session...**\n⚠️ Bot will restart after reset.")
        session_file = Path(f"{SESSION_NAME}.session")
        if session_file.exists():
            session_file.unlink()
        await asyncio.sleep(2)
        await event.reply("✅ Session reset complete!\n🔄 Please restart the bot.")
        await client.stop()
        sys.exit(0)
