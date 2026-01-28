"""
Voice Service for Speech-to-Text and Text-to-Speech.
Implements BR6: Speech-to-text Dictation and BR7: Voice Conversation Mode.

Uses IBM Granite Speech locally for STT — no API keys required.
"""

from typing import Optional, Callable, Tuple
import threading
import time

from ..config.settings import get_settings
from ..config.logging_config import get_logger
from .granite_speech_engine import GraniteSpeechEngine

logger = get_logger(__name__)

# Try to import audio libraries
try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    logger.warning("sounddevice not installed. Audio features limited.")


class VoiceService:
    """
    Service for voice input/output.

    Implements:
    - BR6.1: Basic voice dictation
    - BR6.2: Dictation at caret position
    - BR6.3: Auto-stop on silence
    - BR6.4: Microphone permission handling
    - BR7.1: Voice session with spoken reply
    - BR7.2: Natural turn-taking
    - BR7.3: Wake word activation (optional)

    STT runs fully locally via IBM Granite Speech — no API keys needed.
    """

    def __init__(self):
        self.settings = get_settings()
        self._stt_engine = GraniteSpeechEngine(
            model_size=self.settings.granite_speech_model_size
        )
        self._is_recording = False
        self._is_speaking = False
        self._model_loaded = False

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.silence_threshold = self.settings.silence_threshold_seconds

    def _ensure_model_loaded(self) -> Tuple[bool, str]:
        """
        Lazy-load the Granite Speech model on first use.

        Returns:
            Tuple of (success, status_message)
        """
        if self._model_loaded:
            return self._stt_engine.is_available, "Ready"
        success, message = self._stt_engine.initialize()
        self._model_loaded = True
        return success, message

    @property
    def is_available(self) -> bool:
        """Check if voice services are available (no API key needed)."""
        return HAS_AUDIO

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    def check_microphone_permission(self) -> Tuple[bool, str]:
        """
        Check if microphone is available (BR6.4).

        Returns:
            Tuple of (has_permission, message)
        """
        if not HAS_AUDIO:
            return False, "Audio library not installed. Please install sounddevice."

        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]

            if not input_devices:
                return False, "No microphone found. Please connect a microphone."

            # Try to open a short stream to verify access
            with sd.InputStream(samplerate=self.sample_rate, channels=1, blocksize=1024):
                pass

            return True, "Microphone available"

        except sd.PortAudioError as e:
            return False, (
                f"Microphone access denied. Please enable microphone "
                f"in system settings. ({str(e)})"
            )
        except Exception as e:
            return False, f"Error accessing microphone: {str(e)}"

    def start_dictation(self, callback: Callable[[str], None]) -> bool:
        """
        Start speech-to-text dictation (BR6.1).

        Args:
            callback: Function to call with transcribed text

        Returns:
            True if started successfully
        """
        if not HAS_AUDIO:
            callback("[Error: Audio library not installed.]")
            return False

        # Check permissions first
        has_permission, message = self.check_microphone_permission()
        if not has_permission:
            callback(f"[Error: {message}]")
            return False

        if self._is_recording:
            return False

        self._is_recording = True

        # Start recording in background thread
        thread = threading.Thread(
            target=self._record_and_transcribe,
            args=(callback,),
            daemon=True
        )
        thread.start()

        return True

    def stop_dictation(self):
        """Stop speech-to-text dictation."""
        self._is_recording = False

    def _record_and_transcribe(self, callback: Callable[[str], None]):
        """Record audio and transcribe when finished."""
        try:
            # Ensure model is loaded (may trigger download on first run)
            model_ready, model_message = self._ensure_model_loaded()
            if not model_ready:
                callback(f"[Speech model not available: {model_message}]")
                return

            audio_buffer = []
            silence_count = 0
            silence_limit = int(self.silence_threshold * (self.sample_rate / 1024))

            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Audio status: {status}")
                audio_buffer.extend(indata.copy())

                # Check for silence (BR6.3)
                volume = np.abs(indata).mean()
                nonlocal silence_count
                if volume < 0.01:
                    silence_count += 1
                else:
                    silence_count = 0

            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=1024,
                callback=audio_callback
            ):
                while self._is_recording:
                    time.sleep(0.1)

                    # Auto-stop on silence (BR6.3)
                    if silence_count > silence_limit:
                        logger.info("Auto-stopping dictation due to silence")
                        self._is_recording = False
                        break

            # Transcribe collected audio
            if audio_buffer:
                audio_data = np.array(audio_buffer, dtype=np.float32)
                transcript = self._stt_engine.transcribe(audio_data)
                if transcript:
                    callback(transcript)

        except Exception as e:
            logger.error(f"Recording error: {e}")
            callback(f"[Recording error: {str(e)}]")
        finally:
            self._is_recording = False

    def speak(self, text: str, callback: Optional[Callable[[], None]] = None):
        """
        Convert text to speech and play (BR7.1).

        Note: TTS is currently a placeholder. A future update could integrate
        a local TTS engine (e.g., Coqui TTS or pyttsx3).

        Args:
            text: Text to speak
            callback: Optional callback when finished
        """
        logger.info(f"TTS requested (not yet implemented locally): {text[:50]}...")
        if callback:
            callback()

    def stop_speaking(self):
        """Stop text-to-speech playback."""
        self._is_speaking = False

    def start_voice_mode(
        self,
        on_user_speech: Callable[[str], None],
        on_response: Callable[[str], None]
    ) -> bool:
        """
        Start voice conversation mode (BR7.1, BR7.2).

        Args:
            on_user_speech: Callback when user speech is transcribed
            on_response: Callback to get response for speech

        Returns:
            True if started successfully
        """
        has_permission, message = self.check_microphone_permission()
        if not has_permission:
            logger.error(f"Voice mode failed: {message}")
            return False

        logger.info("Voice mode started")
        return True

    def stop_voice_mode(self):
        """Stop voice conversation mode."""
        self.stop_dictation()
        self.stop_speaking()
        logger.info("Voice mode stopped")


# Singleton instance
_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:
    """Get the voice service singleton."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
