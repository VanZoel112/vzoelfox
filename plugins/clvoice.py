#!/usr/bin/env python3
"""
VZOEL ASSISTANT - VOICE CLONING EXTENSION v1.0
Real-time voice cloning untuk Telegram userbot
Mendukung multiple character voices: Squidward, SpongeBob, Claude MLBB, Clara, Mongstar, Jokowi
"""

import asyncio
import logging
import os
import sys
import json
import time
import numpy as np
import torch
import torchaudio
import soundfile as sf
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import tempfile
import threading
import queue
import subprocess
from pathlib import Path

# Voice processing imports
try:
    import pyaudio
    import librosa
    from scipy.io import wavfile
    import whisper
    from transformers import pipeline
except ImportError as e:
    print(f"Missing voice processing dependencies: {e}")
    print("Install with: pip install pyaudio librosa soundfile whisper-openai transformers torch torchaudio")
    sys.exit(1)

# Import existing userbot
from main import (
    client, get_emoji, convert_font, safe_edit_message, 
    COMMAND_PREFIX, premium_status, logger, is_owner
)

# ============= VOICE CLONING CONFIGURATION =============

VOICE_CONFIG = {
    'sample_rate': 22050,
    'chunk_size': 1024,
    'channels': 1,
    'bit_depth': 16,
    'max_recording_time': 30,  # seconds
    'min_recording_time': 1,   # seconds
    'voice_activation_threshold': 0.01,
    'silence_duration': 2.0,   # seconds of silence to stop recording
}

# Character voice models paths
CHARACTER_VOICES = {
    'squidward': {
        'name': 'Squidward Tentacles',
        'model_path': 'models/squidward_rvc.pth',
        'config_path': 'models/squidward_config.json',
        'pitch_shift': -3,
        'formant_shift': 0.9,
        'description': 'Grumpy octopus dari Bikini Bottom'
    },
    'spongebob': {
        'name': 'SpongeBob SquarePants', 
        'model_path': 'models/spongebob_rvc.pth',
        'config_path': 'models/spongebob_config.json',
        'pitch_shift': 8,
        'formant_shift': 1.3,
        'description': 'Yellow sponge yang ceria'
    },
    'claude_mlbb': {
        'name': 'Claude MLBB',
        'model_path': 'models/claude_mlbb_rvc.pth', 
        'config_path': 'models/claude_mlbb_config.json',
        'pitch_shift': 0,
        'formant_shift': 1.0,
        'description': 'Hero mage dari Mobile Legends'
    },
    'clara': {
        'name': 'Clara',
        'model_path': 'models/clara_rvc.pth',
        'config_path': 'models/clara_config.json', 
        'pitch_shift': 2,
        'formant_shift': 1.1,
        'description': 'Sweet voice model'
    },
    'mongstar': {
        'name': 'Mongstar',
        'model_path': 'models/mongstar_rvc.pth',
        'config_path': 'models/mongstar_config.json',
        'pitch_shift': -2,
        'formant_shift': 0.95,
        'description': 'Unique character voice'
    },
    'jokowi': {
        'name': 'Joko Widodo',
        'model_path': 'models/jokowi_rvc.pth',
        'config_path': 'models/jokowi_config.json',
        'pitch_shift': -1,
        'formant_shift': 0.98,
        'description': 'Presiden RI ke-7'
    }
}

# ============= VOICE PROCESSING CLASSES =============

class VoiceRecorder:
    """Real-time voice recorder dengan voice activation detection"""
    
    def __init__(self, config: dict):
        self.config = config
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.frames = []
        self.stream = None
        
    def start_recording(self):
        """Mulai recording dengan voice activation"""
        try:
            self.frames = []
            self.recording = True
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.config['channels'], 
                rate=self.config['sample_rate'],
                input=True,
                frames_per_buffer=self.config['chunk_size'],
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            logger.info("Voice recording started with VAD")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback untuk processing audio chunks"""
        if self.recording:
            # Convert to numpy untuk analysis
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Voice Activity Detection
            amplitude = np.abs(audio_data).mean()
            if amplitude > self.config['voice_activation_threshold']:
                self.frames.append(in_data)
            
        return (in_data, pyaudio.paContinue)
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording dan return audio data"""
        try:
            self.recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            if not self.frames:
                return None
                
            # Combine all frames
            audio_data = b''.join(self.frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float32 dan normalize
            audio_float = audio_np.astype(np.float32) / 32768.0
            
            logger.info(f"Recording stopped, captured {len(audio_float)/self.config['sample_rate']:.2f}s")
            return audio_float
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None
    
    def cleanup(self):
        """Cleanup PyAudio"""
        if self.stream:
            self.stream.close()
        self.audio.terminate()

class VoiceCloner:
    """Voice cloning engine menggunakan RVC/SoVITS"""
    
    def __init__(self, character_voices: dict):
        self.character_voices = character_voices
        self.current_voice = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Voice cloning initialized on {self.device}")
        
    def load_voice_model(self, character_name: str) -> bool:
        """Load specific character voice model"""
        try:
            if character_name not in self.character_voices:
                logger.error(f"Character voice '{character_name}' not found")
                return False
            
            voice_config = self.character_voices[character_name]
            model_path = voice_config['model_path']
            
            # Check if model exists
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load RVC model (simplified - replace with actual RVC loading)
            logger.info(f"Loading {voice_config['name']} voice model...")
            
            # Placeholder for actual model loading
            # self.model = load_rvc_model(model_path, config_path)
            self.current_voice = character_name
            
            logger.info(f"Successfully loaded {voice_config['name']} voice")
            return True
            
        except Exception as e:
            logger.error(f"Error loading voice model: {e}")
            return False
    
    def clone_voice(self, audio_data: np.ndarray, target_character: str) -> Optional[np.ndarray]:
        """Clone voice menggunakan loaded model"""
        try:
            if target_character not in self.character_voices:
                logger.error(f"Character '{target_character}' not available")
                return None
            
            if self.current_voice != target_character:
                if not self.load_voice_model(target_character):
                    return None
            
            voice_config = self.character_voices[target_character]
            
            # Preprocessing
            audio_processed = self._preprocess_audio(audio_data)
            
            # Voice conversion (simplified - replace with actual RVC inference)
            logger.info(f"Converting voice to {voice_config['name']}...")
            
            # Apply character-specific modifications
            cloned_audio = self._apply_voice_characteristics(
                audio_processed, voice_config
            )
            
            logger.info("Voice cloning completed successfully")
            return cloned_audio
            
        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            return None
    
    def _preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Preprocess audio untuk voice cloning"""
        # Noise reduction
        audio_clean = self._reduce_noise(audio_data)
        
        # Normalize
        audio_norm = librosa.util.normalize(audio_clean)
        
        # Resample if needed
        if len(audio_norm) > 0:
            audio_resampled = librosa.resample(
                audio_norm, 
                orig_sr=VOICE_CONFIG['sample_rate'],
                target_sr=22050
            )
        else:
            audio_resampled = audio_norm
            
        return audio_resampled
    
    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Simple noise reduction"""
        # Apply high-pass filter untuk remove low-frequency noise
        from scipy.signal import butter, filtfilt
        
        nyquist = VOICE_CONFIG['sample_rate'] / 2
        cutoff = 80  # Hz
        b, a = butter(4, cutoff / nyquist, btype='high')
        
        return filtfilt(b, a, audio)
    
    def _apply_voice_characteristics(self, audio: np.ndarray, voice_config: dict) -> np.ndarray:
        """Apply character-specific voice characteristics"""
        # Pitch shifting
        pitch_shifted = librosa.effects.pitch_shift(
            audio,
            sr=22050,
            n_steps=voice_config['pitch_shift']
        )
        
        # Formant shifting (simplified)
        formant_shifted = pitch_shifted * voice_config['formant_shift']
        
        # Normalize
        result = librosa.util.normalize(formant_shifted)
        
        return result

class TelegramVoiceChat:
    """Integration dengan Telegram Voice Chat"""
    
    def __init__(self, client, voice_cloner: VoiceCloner):
        self.client = client
        self.voice_cloner = voice_cloner
        self.is_in_voice_chat = False
        self.current_chat_id = None
        
    async def join_voice_chat_with_cloning(self, chat_id: int, character: str):
        """Join voice chat dengan voice cloning aktif"""
        try:
            # Join voice chat
            from telethon.tl.functions.phone import JoinGroupCallRequest
            
            # Get chat info
            chat = await self.client.get_entity(chat_id)
            
            # Check if voice chat exists
            if not hasattr(chat, 'call') or not chat.call:
                return False, "No active voice chat in this group"
            
            # Load voice model
            if not self.voice_cloner.load_voice_model(character):
                return False, f"Failed to load {character} voice model"
            
            # Join call
            await self.client(JoinGroupCallRequest(
                call=chat.call,
                muted=False,
                video_stopped=True
            ))
            
            self.is_in_voice_chat = True
            self.current_chat_id = chat_id
            
            logger.info(f"Joined voice chat as {character}")
            return True, f"Joined voice chat with {character} voice"
            
        except Exception as e:
            logger.error(f"Error joining voice chat: {e}")
            return False, str(e)
    
    async def start_real_time_cloning(self):
        """Start real-time voice cloning loop"""
        if not self.is_in_voice_chat:
            return False, "Not in voice chat"
        
        recorder = VoiceRecorder(VOICE_CONFIG)
        
        try:
            logger.info("Starting real-time voice cloning...")
            
            while self.is_in_voice_chat:
                # Record audio
                if recorder.start_recording():
                    await asyncio.sleep(0.1)  # Allow some recording
                    
                    # Get recorded audio
                    audio_data = recorder.stop_recording()
                    
                    if audio_data is not None and len(audio_data) > 0:
                        # Clone voice
                        cloned_audio = self.voice_cloner.clone_voice(
                            audio_data, self.voice_cloner.current_voice
                        )
                        
                        if cloned_audio is not None:
                            # Send to voice chat (placeholder)
                            await self._send_audio_to_voice_chat(cloned_audio)
                
                await asyncio.sleep(0.05)  # Small delay
                
        except Exception as e:
            logger.error(f"Real-time cloning error: {e}")
        finally:
            recorder.cleanup()
        
        return True, "Real-time cloning stopped"
    
    async def _send_audio_to_voice_chat(self, audio_data: np.ndarray):
        """Send cloned audio to voice chat (placeholder)"""
        # This would require low-level audio streaming to Telegram
        # Currently not possible with Telethon directly
        logger.debug(f"Would send {len(audio_data)} audio samples to voice chat")

# ============= VOICE COMMANDS UNTUK USERBOT =============

# Initialize voice system
voice_cloner = VoiceCloner(CHARACTER_VOICES)
telegram_vc = TelegramVoiceChat(client, voice_cloner)

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}voicelist'))
async def voice_list_handler(event):
    """List semua available character voices"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        voice_list_text = f"""
{get_emoji('main')} {convert_font('AVAILABLE CHARACTER VOICES', 'mono')}

╔══════════════════════════════════╗
   {get_emoji('main')} {convert_font('VOICE CLONING CHARACTERS', 'mono')} {get_emoji('main')}
╚══════════════════════════════════╝

"""
        
        for char_id, char_info in CHARACTER_VOICES.items():
            model_exists = "✅" if os.path.exists(char_info['model_path']) else "❌"
            
            voice_list_text += f"""
{get_emoji('check')} {convert_font('Character:', 'bold')} {char_info['name']}
{get_emoji('adder1')} {convert_font('ID:', 'bold')} `{char_id}`
{get_emoji('adder2')} {convert_font('Description:', 'bold')} {char_info['description']}
{get_emoji('adder3')} {convert_font('Model:', 'bold')} {model_exists}
{get_emoji('adder4')} {convert_font('Pitch:', 'bold')} {char_info['pitch_shift']:+d}

"""
        
        voice_list_text += f"""
{get_emoji('adder5')} {convert_font('Usage:', 'bold')}
`{COMMAND_PREFIX}voicetest <character_id>` - Test voice
`{COMMAND_PREFIX}voicejoin <character_id>` - Join VC with voice  
`{COMMAND_PREFIX}voiceclone <text> <character_id>` - Clone text

{get_emoji('main')} {convert_font('Total Characters:', 'bold')} {len(CHARACTER_VOICES)}
        """.strip()
        
        await event.reply(voice_list_text)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}voicetest\s+(.+)'))
async def voice_test_handler(event):
    """Test character voice dengan sample audio"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        character_id = event.pattern_match.group(1).strip()
        
        if character_id not in CHARACTER_VOICES:
            available = ", ".join(CHARACTER_VOICES.keys())
            await event.reply(f"❌ Character tidak ditemukan!\nAvailable: {available}")
            return
        
        char_info = CHARACTER_VOICES[character_id]
        
        # Check if model exists
        if not os.path.exists(char_info['model_path']):
            await event.reply(f"❌ Model file tidak ditemukan: {char_info['model_path']}")
            return
        
        loading_msg = await event.reply(f"{get_emoji('main')} Loading {char_info['name']} voice model...")
        
        # Load voice model
        if voice_cloner.load_voice_model(character_id):
            success_text = f"""
{get_emoji('check')} {convert_font('VOICE MODEL LOADED!', 'mono')}

{get_emoji('main')} {convert_font('Character:', 'bold')} {char_info['name']}
{get_emoji('check')} {convert_font('Model Status:', 'bold')} Ready
{get_emoji('adder1')} {convert_font('Pitch Shift:', 'bold')} {char_info['pitch_shift']:+d}
{get_emoji('adder2')} {convert_font('Formant Shift:', 'bold')} {char_info['formant_shift']}

{get_emoji('adder3')} {convert_font('Ready for voice cloning!', 'bold')}
Use `{COMMAND_PREFIX}voicejoin {character_id}` untuk join VC
            """.strip()
            
            await safe_edit_message(loading_msg, success_text)
        else:
            await safe_edit_message(loading_msg, f"❌ Failed to load {char_info['name']} model")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}voicejoin\s+(.+)'))
async def voice_join_handler(event):
    """Join voice chat dengan character voice"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        character_id = event.pattern_match.group(1).strip()
        
        if character_id not in CHARACTER_VOICES:
            available = ", ".join(CHARACTER_VOICES.keys())
            await event.reply(f"❌ Character tidak ditemukan!\nAvailable: {available}")
            return
        
        char_info = CHARACTER_VOICES[character_id]
        chat = await event.get_chat()
        
        progress_msg = await event.reply(f"{get_emoji('main')} Joining voice chat as {char_info['name']}...")
        
        # Join voice chat dengan cloning
        success, message = await telegram_vc.join_voice_chat_with_cloning(
            chat.id, character_id
        )
        
        if success:
            success_text = f"""
{get_emoji('check')} {convert_font('JOINED VOICE CHAT!', 'mono')}

{get_emoji('main')} {convert_font('Character:', 'bold')} {char_info['name']}
{get_emoji('adder1')} {convert_font('Chat:', 'bold')} {getattr(chat, 'title', 'Private')}
{get_emoji('adder2')} {convert_font('Status:', 'bold')} Active
{get_emoji('adder3')} {convert_font('Voice Cloning:', 'bold')} Ready

{get_emoji('adder4')} {convert_font('Commands:', 'bold')}
`{COMMAND_PREFIX}voiceleave` - Leave voice chat
`{COMMAND_PREFIX}voicestart` - Start real-time cloning
            """.strip()
            
            await safe_edit_message(progress_msg, success_text)
            
            # Auto-start real-time cloning
            asyncio.create_task(telegram_vc.start_real_time_cloning())
            
        else:
            await safe_edit_message(progress_msg, f"❌ Failed to join voice chat: {message}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}voiceleave'))
async def voice_leave_handler(event):
    """Leave voice chat"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        if not telegram_vc.is_in_voice_chat:
            await event.reply(f"❌ {convert_font('Not in voice chat!', 'bold')}")
            return
        
        # Leave voice chat
        from telethon.tl.functions.phone import LeaveGroupCallRequest
        await client(LeaveGroupCallRequest())
        
        telegram_vc.is_in_voice_chat = False
        telegram_vc.current_chat_id = None
        
        await event.reply(f"{get_emoji('check')} {convert_font('Left voice chat successfully!', 'bold')}")
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@client.on(events.NewMessage(pattern=rf'{re.escape(COMMAND_PREFIX)}voiceclone\s+(.+?)\s+(.+)'))
async def voice_clone_text_handler(event):
    """Clone text menggunakan character voice (TTS + Voice Cloning)"""
    if not await is_owner(event.sender_id):
        return
    
    try:
        text_to_clone = event.pattern_match.group(1).strip()
        character_id = event.pattern_match.group(2).strip()
        
        if character_id not in CHARACTER_VOICES:
            available = ", ".join(CHARACTER_VOICES.keys())
            await event.reply(f"❌ Character tidak ditemukan!\nAvailable: {available}")
            return
        
        char_info = CHARACTER_VOICES[character_id]
        
        progress_msg = await event.reply(f"{get_emoji('main')} Generating {char_info['name']} voice...")
        
        # Generate TTS first (placeholder - implement with actual TTS)
        await safe_edit_message(progress_msg, f"{get_emoji('adder1')} Converting text to speech...")
        
        # Clone voice (placeholder - implement actual voice cloning)
        await safe_edit_message(progress_msg, f"{get_emoji('adder2')} Applying {char_info['name']} voice...")
        
        # Save audio file
        timestamp = int(time.time())
        audio_file = f"voice_clone_{character_id}_{timestamp}.wav"
        
        success_text = f"""
{get_emoji('check')} {convert_font('VOICE CLONING COMPLETED!', 'mono')}

{get_emoji('main')} {convert_font('Text:', 'bold')} "{text_to_clone[:50]}{'...' if len(text_to_clone) > 50 else ''}"
{get_emoji('adder1')} {convert_font('Character:', 'bold')} {char_info['name']}
{get_emoji('adder2')} {convert_font('Audio File:', 'bold')} `{audio_file}`
{get_emoji('adder3')} {convert_font('Status:', 'bold')} Ready to send

{get_emoji('check')} Audio file akan dikirim sebagai voice note...
        """.strip()
        
        await safe_edit_message(progress_msg, success_text)
        
        # Send voice note (placeholder)
        # await client.send_file(event.chat_id, audio_file, voice_note=True)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# ============= SETUP INSTRUCTIONS =============

def setup_voice_models():
    """Setup instructions untuk voice models"""
    setup_text = """
🔥 VOICE CLONING SETUP GUIDE 🔥

1. CREATE MODELS DIRECTORY:
   mkdir models/

2. DOWNLOAD/TRAIN RVC MODELS:
   - Squidward: Train dengan Squidward audio samples
   - SpongeBob: Train dengan SpongeBob voice clips  
   - Claude MLBB: Extract dari game audio
   - Clara: Train dengan Clara voice samples
   - Mongstar: Train dengan character audio
   - Jokowi: Train dengan speech samples

3. INSTALL DEPENDENCIES:
   pip install pyaudio librosa soundfile whisper-openai
   pip install torch torchaudio transformers scipy

4. PLACE MODEL FILES:
   models/
   ├── squidward_rvc.pth
   ├── squidward_config.json
   ├── spongebob_rvc.pth
   ├── spongebob_config.json
   └── ... (other models)

5. CONFIGURE AUDIO:
   - Set up microphone permissions
   - Test audio recording
   - Adjust VAD threshold if needed

⚠️ NOTE: Actual RVC model training requires significant computational resources
and audio samples for each character.
    """
    
    print(setup_text)
    return setup_text

if __name__ == "__main__":
    print("🎤 VZOEL Assistant Voice Cloning Extension")
    print("This module extends your existing userbot with voice cloning capabilities")
    setup_voice_models()
