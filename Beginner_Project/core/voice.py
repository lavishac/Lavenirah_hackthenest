import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
CACHE = Path('.audio_cache')
CACHE.mkdir(exist_ok=True)
NARRATOR = 'JBFqnCBsd6RMkjVDRZzb'
VOICES = {  # speaker -> ElevenLabs voice id (copy ids from the Voices page)
    'narrator': NARRATOR,
    'crow': 'PASTE-VOICE-ID',
    'raccoon': 'PASTE-VOICE-ID',
    'mother': 'PASTE-VOICE-ID',
    'owl': 'PASTE-VOICE-ID',
}
_client = None


def _voice_for(speaker):
    v = VOICES.get(speaker, NARRATOR)
    return NARRATOR if v.startswith('PASTE') else v


def speak(text, speaker='narrator'):
    """Return mp3 bytes (cached on disk), or None if ElevenLabs fails."""
    global _client
    voice = _voice_for(speaker)
    path = CACHE / (hashlib.sha1((voice + '|' + text).encode()).hexdigest() + '.mp3')
    if path.exists():
        return path.read_bytes()
    try:
        from elevenlabs.client import ElevenLabs

        _client = _client or ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        chunks = _client.text_to_speech.convert(
            text=text,
            voice_id=voice,
            model_id='eleven_multilingual_v2',
            output_format='mp3_44100_128',
        )
        audio = b''.join(chunks)
    except Exception as err:
        print('ElevenLabs failed:', err)
        return None
    path.write_bytes(audio)
    return audio


def speak_scene(scene):
    """Narration in the narrator voice, then the character line in its own voice."""
    parts = [speak(scene['narration'])]
    dia = scene.get('dialogue')
    if dia:
        parts.append(speak(dia['line'], dia['speaker'].lower()))
    parts = [p for p in parts if p]
    return b''.join(parts) if parts else None
