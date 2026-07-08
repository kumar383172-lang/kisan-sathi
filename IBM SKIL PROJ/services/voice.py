"""
services/voice.py
──────────────────
Voice I/O helpers:
  - speech_to_text(): transcribes uploaded audio via OpenAI Whisper (local)
  - text_to_speech(): converts text to MP3 via gTTS, returns path
"""

import os
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
AUDIO_DIR = Path("static/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def speech_to_text(audio_file_path: str, language: str = "hi") -> str:
    """
    Transcribe audio file to text using OpenAI Whisper (local model).
    Requires: pip install openai-whisper
    Falls back gracefully if Whisper is not installed.
    """
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_file_path, language=language)
        return result.get("text", "").strip()
    except ImportError:
        logger.warning("Whisper not installed. Returning empty transcription.")
        return ""
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return ""


def text_to_speech(text: str, language: str = "hi") -> str | None:
    """
    Convert text to speech MP3 using gTTS.
    Returns the relative URL path to the audio file, or None on failure.
    Supported language codes: hi, mr, ta, te, pa, en, bn, gu, kn, ml
    """
    # Map to gTTS-compatible language codes
    lang_map = {
        "hi": "hi", "mr": "mr", "ta": "ta", "te": "te",
        "pa": "pa", "en": "en", "bn": "bn", "gu": "gu",
        "kn": "kn", "ml": "ml",
    }
    gtts_lang = lang_map.get(language, "hi")

    try:
        from gtts import gTTS
        filename = f"tmp_{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename
        tts = gTTS(text=text[:500], lang=gtts_lang, slow=False)  # cap at 500 chars
        tts.save(str(filepath))
        return f"/static/audio/{filename}"
    except ImportError:
        logger.warning("gTTS not installed. Voice output disabled.")
        return None
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None
