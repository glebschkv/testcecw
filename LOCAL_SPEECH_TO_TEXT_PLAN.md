# Local Speech-to-Text Implementation Plan

## Problem

The current `VoiceService` (`src/services/voice_service.py`) relies on **IBM Watson Speech-to-Text API**, which requires cloud API keys. Since OBD InsightBot is a locally-run desktop application, we need a fully offline STT solution that works without any API keys or internet connection.

---

## Recommended Solution: `faster-whisper`

**Primary choice:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — a CTranslate2-based reimplementation of OpenAI's Whisper model.

**Why faster-whisper over alternatives:**

| Solution | Accuracy | Speed | RAM Usage | Offline | Real-time | Python API |
|----------|----------|-------|-----------|---------|-----------|------------|
| **faster-whisper** | Excellent | Fast (4-8x Whisper) | 1-4 GB | Yes | Yes | Yes |
| OpenAI Whisper | Excellent | Slow | 2-10 GB | Yes | No | Yes |
| Vosk | Good | Very fast | 50-300 MB | Yes | Yes | Yes |
| whisper.cpp | Excellent | Very fast | 1-4 GB | Yes | Via bindings | Via bindings |
| SpeechRecognition + PocketSphinx | Poor | Fast | Low | Yes | Yes | Yes |

**faster-whisper** provides the best balance of accuracy, speed, and ease of integration. It's 4-8x faster than vanilla Whisper with comparable accuracy, has a clean Python API, and supports GPU acceleration when available.

**Fallback option:** Vosk can be offered as a lightweight alternative for machines with limited resources (< 4 GB RAM).

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     ChatScreen (UI)                       │
│  ┌──────────────────────────────────────────────────┐    │
│  │  [🎤 Mic Button]  [Text Input]  [Send Button]    │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────┬───────────────────────────────────┘
                       │ start_dictation() / stop_dictation()
                       ▼
┌──────────────────────────────────────────────────────────┐
│               VoiceService (Refactored)                   │
│                                                           │
│  ┌─────────────────┐    ┌──────────────────────────┐     │
│  │  AudioRecorder   │───▶│  LocalSTTEngine           │     │
│  │  (sounddevice)   │    │  (faster-whisper / Vosk)  │     │
│  │                  │    │                            │     │
│  │  - Record audio  │    │  - Load model on init     │     │
│  │  - Silence detect│    │  - Transcribe audio buffer│     │
│  │  - Stream chunks │    │  - Return text segments   │     │
│  └─────────────────┘    └──────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

---

## Detailed Implementation Steps

### Step 1: Add Dependencies

**File:** `requirements.txt`

```
# Local Speech-to-Text
faster-whisper>=1.0.0
```

Optional lightweight fallback:
```
# Lightweight STT alternative (optional)
vosk>=0.3.45
```

No changes needed to `pyaudio` or `sounddevice` — they're already present.

---

### Step 2: Create Local STT Engine Module

**New file:** `src/services/local_stt_engine.py`

This module encapsulates the local transcription logic, keeping it separate from audio recording and UI concerns.

```python
"""
Local Speech-to-Text Engine.
Provides offline transcription using faster-whisper (Whisper via CTranslate2).
"""

from typing import Optional, Tuple
import numpy as np
from ..config.settings import get_settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)

# Try to import faster-whisper
try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False
    logger.warning("faster-whisper not installed. Local STT unavailable.")

# Fallback: try Vosk
try:
    import vosk
    import json
    HAS_VOSK = True
except ImportError:
    HAS_VOSK = False


class LocalSTTEngine:
    """
    Local speech-to-text engine using faster-whisper.
    Falls back to Vosk if faster-whisper is unavailable.
    """

    def __init__(self, model_size: str = "base"):
        """
        Initialize the local STT engine.

        Args:
            model_size: Whisper model size. Options:
                - "tiny"    (~39 MB,  fastest, lowest accuracy)
                - "base"    (~74 MB,  good balance for desktop use) [DEFAULT]
                - "small"   (~244 MB, better accuracy)
                - "medium"  (~769 MB, high accuracy)
                - "large-v3"(~1.5 GB, best accuracy, needs good GPU/CPU)
        """
        self.settings = get_settings()
        self.model_size = model_size
        self._whisper_model = None
        self._vosk_model = None
        self._backend = None  # "whisper" or "vosk"
        self.sample_rate = 16000

    def initialize(self) -> Tuple[bool, str]:
        """
        Load the STT model. Call this once at startup or on first use.
        This is separated from __init__ because model loading is slow
        and should happen in a background thread.

        Returns:
            Tuple of (success, status_message)
        """
        # Try faster-whisper first
        if HAS_FASTER_WHISPER:
            try:
                # auto = use GPU if available (CUDA), else CPU
                self._whisper_model = WhisperModel(
                    self.model_size,
                    device="auto",
                    compute_type="int8"  # Quantized for speed on CPU
                )
                self._backend = "whisper"
                logger.info(
                    f"Loaded faster-whisper model: {self.model_size}"
                )
                return True, f"Whisper ({self.model_size}) ready"
            except Exception as e:
                logger.error(f"Failed to load faster-whisper: {e}")

        # Fallback to Vosk
        if HAS_VOSK:
            try:
                # Vosk models must be downloaded separately
                model_path = self.settings.vosk_model_path  # New setting
                self._vosk_model = vosk.Model(model_path)
                self._backend = "vosk"
                logger.info("Loaded Vosk model")
                return True, "Vosk model ready"
            except Exception as e:
                logger.error(f"Failed to load Vosk: {e}")

        return False, "No local STT engine available. Install faster-whisper."

    @property
    def is_available(self) -> bool:
        return self._backend is not None

    @property
    def backend_name(self) -> str:
        return self._backend or "none"

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: NumPy array of float32 audio samples at 16kHz mono.

        Returns:
            Transcribed text string, or empty string on failure.
        """
        if self._backend == "whisper":
            return self._transcribe_whisper(audio_data)
        elif self._backend == "vosk":
            return self._transcribe_vosk(audio_data)
        return ""

    def _transcribe_whisper(self, audio_data: np.ndarray) -> str:
        """Transcribe using faster-whisper."""
        try:
            # faster-whisper accepts float32 numpy array directly
            segments, info = self._whisper_model.transcribe(
                audio_data,
                beam_size=5,
                language="en",          # Set to None for auto-detect
                vad_filter=True,        # Filter out silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
            )

            # Collect all segment texts
            transcript = " ".join(
                segment.text.strip() for segment in segments
            )
            logger.debug(
                f"Whisper transcription ({info.language}, "
                f"{info.duration:.1f}s): {transcript[:80]}..."
            )
            return transcript.strip()

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""

    def _transcribe_vosk(self, audio_data: np.ndarray) -> str:
        """Transcribe using Vosk."""
        try:
            recognizer = vosk.KaldiRecognizer(
                self._vosk_model, self.sample_rate
            )

            # Vosk expects 16-bit PCM bytes
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()

            # Feed audio in chunks
            chunk_size = 4000
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                recognizer.AcceptWaveform(chunk)

            result = json.loads(recognizer.FinalResult())
            return result.get("text", "").strip()

        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            return ""

    def cleanup(self):
        """Release model resources."""
        self._whisper_model = None
        self._vosk_model = None
        self._backend = None
```

---

### Step 3: Refactor VoiceService to Use Local Engine

**File:** `src/services/voice_service.py`

Key changes:
1. Replace IBM Watson STT with `LocalSTTEngine`
2. Keep the existing public API (`start_dictation`, `stop_dictation`, `is_available`, etc.) unchanged
3. Add lazy model loading (first use triggers load, with progress indication)
4. Remove Watson SDK dependency for STT

```python
"""
Voice Service for Speech-to-Text and Text-to-Speech.
Uses local faster-whisper engine for offline transcription.
"""

from typing import Optional, Callable, Tuple
import threading
import time

from ..config.settings import get_settings
from ..config.logging_config import get_logger
from .local_stt_engine import LocalSTTEngine

logger = get_logger(__name__)

# Audio library imports (unchanged)
try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

class VoiceService:
    def __init__(self):
        self.settings = get_settings()
        self._stt_engine = LocalSTTEngine(
            model_size=self.settings.whisper_model_size  # New setting
        )
        self._is_recording = False
        self._model_loaded = False

        # Audio settings (unchanged)
        self.sample_rate = 16000
        self.channels = 1
        self.silence_threshold = self.settings.silence_threshold_seconds

    def _ensure_model_loaded(self) -> Tuple[bool, str]:
        """Lazy-load the STT model on first use."""
        if self._model_loaded:
            return self._stt_engine.is_available, "Ready"
        success, message = self._stt_engine.initialize()
        self._model_loaded = True
        return success, message

    @property
    def is_available(self) -> bool:
        return HAS_AUDIO  # No API key check needed anymore

    # ... rest of the methods stay the same structurally,
    # but _transcribe_audio() now calls:
    #     self._stt_engine.transcribe(audio_data)
    # instead of IBM Watson API
```

**What changes in existing methods:**

| Method | Change |
|--------|--------|
| `__init__` | Create `LocalSTTEngine` instead of Watson client |
| `_initialize_services` | Remove entirely (no API keys to configure) |
| `is_available` | Check `HAS_AUDIO` only (no Watson dependency) |
| `start_dictation` | Add `_ensure_model_loaded()` call before recording |
| `_transcribe_audio` | Replace Watson API call with `self._stt_engine.transcribe()` |
| `check_microphone_permission` | Unchanged |
| `_record_and_transcribe` | Unchanged (audio capture logic stays the same) |

---

### Step 4: Add Configuration Settings

**File:** `src/config/settings.py`

Add new settings to the Settings dataclass:

```python
# Local STT Settings
whisper_model_size: str = "base"       # tiny, base, small, medium, large-v3
vosk_model_path: str = "./models/vosk" # Path to Vosk model (fallback)
```

These map to environment variables:
```
WHISPER_MODEL_SIZE=base
VOSK_MODEL_PATH=./models/vosk
```

---

### Step 5: Add Microphone Button to Chat UI

**File:** `src/ui/chat_screen.py`

Add a microphone toggle button to the input area (next to the send button):

```python
# In _create_chat_area(), inside input_layout, before send_btn:

# Microphone button for voice dictation (BR6)
self.mic_btn = QPushButton("mic")  # Or use an icon
self.mic_btn.setObjectName("micButton")
self.mic_btn.setFixedSize(44, 44)
self.mic_btn.setCheckable(True)       # Toggle on/off
self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
self.mic_btn.clicked.connect(self._toggle_dictation)
self.mic_btn.setEnabled(False)        # Enabled when chat is open
input_layout.addWidget(self.mic_btn)
```

Add the toggle handler:

```python
def _toggle_dictation(self):
    """Toggle voice dictation on/off."""
    from ..services.voice_service import get_voice_service
    voice = get_voice_service()

    if self.mic_btn.isChecked():
        # Start recording
        self.mic_btn.setStyleSheet("/* active/recording style (red) */")
        success = voice.start_dictation(callback=self._on_dictation_result)
        if not success:
            self.mic_btn.setChecked(False)
    else:
        # Stop recording
        voice.stop_dictation()
        self.mic_btn.setStyleSheet("/* default style */")

def _on_dictation_result(self, text: str):
    """Insert dictated text into the message input."""
    if text and not text.startswith("["):
        # Insert at cursor position (BR6.2)
        cursor = self.message_input.textCursor()
        cursor.insertText(text)
        self.message_input.setTextCursor(cursor)
```

---

### Step 6: Add Model Download / First-Run Experience

Since faster-whisper auto-downloads models from Hugging Face on first use, we need to handle the first-run experience gracefully.

**File:** `src/services/voice_service.py` (in `_ensure_model_loaded`)

```python
def _ensure_model_loaded(self, status_callback=None) -> Tuple[bool, str]:
    """
    Lazy-load the STT model. On first run, this downloads the model
    (~74 MB for 'base') which requires a one-time internet connection.
    Subsequent runs use the cached model from ~/.cache/huggingface/.
    """
    if self._model_loaded:
        return self._stt_engine.is_available, "Ready"

    if status_callback:
        status_callback("Loading speech recognition model...")

    success, message = self._stt_engine.initialize()
    self._model_loaded = True

    if status_callback:
        status_callback(message)

    return success, message
```

**UI feedback during model load:**
- Show a brief "Loading speech model..." tooltip or status message on the mic button
- After first load, subsequent uses are instant (model stays in memory)

---

### Step 7: Update Styles

**File:** `src/ui/styles.py`

Add styling for the mic button in both default and recording states:

```python
# Microphone button styles
MIC_BUTTON_DEFAULT = """
    QPushButton#micButton {
        background-color: #F4F4F5;
        color: #71717A;
        border: none;
        border-radius: 22px;
        font-size: 14px;
    }
    QPushButton#micButton:hover {
        background-color: #E4E4E7;
    }
"""

MIC_BUTTON_RECORDING = """
    QPushButton#micButton {
        background-color: #FEE2E2;
        color: #DC2626;
        border: 2px solid #DC2626;
        border-radius: 22px;
        font-size: 14px;
    }
"""
```

---

### Step 8: Handle Threading and UI Updates Safely

Since transcription runs in a background thread but UI updates must happen on the main thread, use PyQt6 signals:

```python
# In ChatScreen or a helper class:
class DictationWorker(QThread):
    """Worker thread for dictation model loading + recording."""
    transcription_ready = pyqtSignal(str)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, voice_service):
        super().__init__()
        self.voice_service = voice_service

    def run(self):
        self.status_update.emit("Listening...")
        # Recording + transcription happens here
        # Results emitted via transcription_ready signal
```

---

### Step 9: Write Tests

**New file:** `tests/test_local_stt.py`

```python
"""Tests for LocalSTTEngine."""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

class TestLocalSTTEngine:
    def test_initialize_with_whisper(self):
        """Test engine initializes with faster-whisper when available."""
        ...

    def test_initialize_fallback_to_vosk(self):
        """Test engine falls back to Vosk when whisper unavailable."""
        ...

    def test_initialize_no_backend(self):
        """Test engine reports unavailable when no backend exists."""
        ...

    def test_transcribe_returns_string(self):
        """Test transcription returns a string from audio data."""
        ...

    def test_transcribe_empty_audio(self):
        """Test transcription handles empty audio gracefully."""
        ...

    def test_transcribe_silence(self):
        """Test transcription of silence returns empty string."""
        ...
```

**Update existing test:** `tests/test_voice_service.py` (if it exists) to mock `LocalSTTEngine` instead of Watson.

---

### Step 10: Update Documentation

**File:** `.env.example`

```bash
# Local Speech-to-Text (no API key needed!)
# Model size: tiny, base, small, medium, large-v3
# Smaller = faster + less RAM, larger = more accurate
WHISPER_MODEL_SIZE=base
```

Remove or mark as optional:
```bash
# WATSON_SPEECH_API_KEY=     (no longer required for STT)
# WATSON_SPEECH_URL=         (no longer required for STT)
```

---

## File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | **Modify** | Add `faster-whisper>=1.0.0`, optionally `vosk>=0.3.45` |
| `src/services/local_stt_engine.py` | **Create** | New module: local transcription engine |
| `src/services/voice_service.py` | **Modify** | Replace Watson STT with LocalSTTEngine |
| `src/config/settings.py` | **Modify** | Add `whisper_model_size` setting |
| `src/ui/chat_screen.py` | **Modify** | Add microphone button + dictation toggle |
| `src/ui/styles.py` | **Modify** | Add mic button styles (default + recording) |
| `tests/test_local_stt.py` | **Create** | Unit tests for LocalSTTEngine |
| `.env.example` | **Modify** | Add whisper settings, deprecate Watson STT keys |

---

## Model Size Guide (for users)

| Model | Size | RAM | Speed | Best For |
|-------|------|-----|-------|----------|
| `tiny` | 39 MB | ~1 GB | Very fast | Low-end machines, quick dictation |
| `base` | 74 MB | ~1 GB | Fast | **Recommended default** |
| `small` | 244 MB | ~2 GB | Moderate | Better accuracy when needed |
| `medium` | 769 MB | ~4 GB | Slower | High accuracy requirements |
| `large-v3` | 1.5 GB | ~6 GB | Slowest | Maximum accuracy (GPU recommended) |

The `base` model provides the best trade-off for a desktop diagnostic tool: fast enough for real-time dictation with solid accuracy on English speech.

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| First-run model download needs internet | Clear UI message; models are cached permanently after download. Could also bundle the model with PyInstaller. |
| Slow transcription on low-end CPUs | Default to `base` model; allow `tiny` via settings; use `int8` quantization. |
| Large model increases app bundle size | Don't bundle by default; auto-download on first use. Offer bundled builds optionally. |
| GPU/CUDA not available | faster-whisper gracefully falls back to CPU; `int8` compute type optimized for CPU. |
| Accuracy not as good as cloud Watson | faster-whisper with `base` model is competitive with cloud APIs for English dictation. |

---

## Implementation Order

1. **Add `faster-whisper` dependency** to `requirements.txt`
2. **Create `local_stt_engine.py`** with the transcription logic
3. **Refactor `voice_service.py`** to use the local engine
4. **Add settings** to `settings.py`
5. **Add mic button** to `chat_screen.py`
6. **Add styles** for the mic button
7. **Write tests** for the new engine
8. **Update `.env.example`** and documentation
9. **Test end-to-end** with real microphone input
10. **Package with PyInstaller** and verify standalone build works
