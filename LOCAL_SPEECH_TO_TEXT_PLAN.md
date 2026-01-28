# Local Speech-to-Text Implementation Plan

## Problem

The current `VoiceService` (`src/services/voice_service.py`) relies on **IBM Watson Speech-to-Text API**, which requires cloud API keys. Since OBD InsightBot is a locally-run desktop application, we need a fully offline STT solution that works without any API keys or internet connection.

---

## Solution: IBM Granite Speech 3.3 (Local)

**IBM Granite Speech 3.3** is an open-source (Apache 2.0) speech-to-text model from IBM, available on Hugging Face. It runs entirely locally via the `transformers` library — no API keys, no cloud services.

This keeps the entire application within the **IBM Granite ecosystem**: Granite for the LLM (already via Ollama) and Granite Speech for STT.

### Why Granite Speech?

- **#1 on Hugging Face Open ASR Leaderboard** — best-in-class accuracy for open-source STT
- **Same ecosystem** as the existing Granite LLM used by the app
- **Apache 2.0 license** — free for commercial and research use
- **Runs fully offline** after one-time model download
- **Two model sizes** to fit different hardware

### Model Options

| Model | Params | Download | RAM (bfloat16) | RAM (int4) | GPU Required? |
|-------|--------|----------|----------------|------------|---------------|
| `granite-speech-3.3-2b` | 2B | ~4 GB | ~5 GB | ~2 GB | No (CPU works) |
| `granite-speech-3.3-8b` | 8B | ~16 GB | ~17 GB | ~5 GB | Recommended |

**Recommended default: `granite-speech-3.3-2b`** — it runs on CPU-only machines while still delivering strong accuracy. The 8B variant can be offered as an option for users with a capable GPU.

### How Granite Speech Works

Granite Speech uses a **two-pass design**:
1. **Pass 1 (Audio → Text):** An acoustic encoder + speech projector converts audio into embeddings, which the underlying Granite LLM decodes into a transcript.
2. **Pass 2 (Text → Text):** The transcribed text can optionally be processed further by the Granite LLM (e.g., for summarization or translation).

For our use case (dictation into the chat input), we only need **Pass 1**.

### Dependencies

```
torch>=2.0.0
transformers>=4.52.4
torchaudio>=2.0.0
peft>=0.6.0
soundfile>=0.12.0
```

These replace the `ibm-watson` SDK dependency for STT. The existing `sounddevice` and `numpy` dependencies stay.

### Granite Speech vs Other Options

| Solution | Accuracy | Speed (CPU) | Ecosystem Fit | Local/Offline |
|----------|----------|-------------|---------------|---------------|
| **Granite Speech 3.3 2B** | Excellent (#1 ASR) | Moderate | IBM Granite (same as LLM) | Yes |
| faster-whisper | Excellent | Fast | Different (OpenAI) | Yes |
| Vosk | Good | Very fast | Different (Alpha Cephei) | Yes |
| IBM Watson STT API | Excellent | N/A (cloud) | IBM (but needs API key) | No |

Granite Speech is the right choice here: best accuracy, same IBM Granite ecosystem, fully local.

**Trade-off:** Granite Speech 2B is slower than dedicated lightweight STT models (it's a full 2B-parameter LLM doing transcription). For dictation of short utterances (5-30 seconds), this is acceptable. For users who need faster response, we provide a configurable model size setting.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     ChatScreen (UI)                       │
│  ┌──────────────────────────────────────────────────┐    │
│  │  [Mic Button]  [Text Input]  [Send Button]        │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────┬───────────────────────────────────┘
                       │ start_dictation() / stop_dictation()
                       ▼
┌──────────────────────────────────────────────────────────┐
│               VoiceService (Refactored)                   │
│                                                           │
│  ┌─────────────────┐    ┌──────────────────────────────┐ │
│  │  AudioRecorder   │───>│  GraniteSpeechEngine          │ │
│  │  (sounddevice)   │    │  (transformers + torchaudio)  │ │
│  │                  │    │                                │ │
│  │  - Record audio  │    │  - Load Granite Speech model  │ │
│  │  - Silence detect│    │  - Transcribe audio buffer    │ │
│  │  - PCM capture   │    │  - Return text transcript     │ │
│  └─────────────────┘    └──────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────┐
                    │  Hugging Face Model Cache │
                    │  ~/.cache/huggingface/    │
                    │                          │
                    │  granite-speech-3.3-2b   │
                    │  (downloaded on 1st use) │
                    └──────────────────────────┘
```

---

## Detailed Implementation Steps

### Step 1: Update Dependencies

**File:** `requirements.txt`

Add the Granite Speech dependencies. Remove `ibm-watson` if STT was its only use (keep if still needed for TTS):

```
# Local Speech-to-Text (IBM Granite Speech)
torch>=2.0.0
transformers>=4.52.4
torchaudio>=2.0.0
peft>=0.6.0
soundfile>=0.12.0
```

Note: `torch` is a large dependency (~2 GB). If it's not already in the project, this is the biggest addition. However, since the project may already pull it transitively via other AI dependencies, check first.

---

### Step 2: Create Granite Speech Engine Module

**New file:** `src/services/granite_speech_engine.py`

This module encapsulates the local Granite Speech transcription logic.

```python
"""
Granite Speech Engine for local speech-to-text.
Uses IBM Granite Speech 3.3 via Hugging Face Transformers.
Runs entirely offline after initial model download.
"""

import io
from typing import Optional, Tuple

from ..config.settings import get_settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)

# Try to import required libraries
try:
    import torch
    import torchaudio
    import soundfile as sf
    from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
    HAS_GRANITE_SPEECH = True
except ImportError as e:
    HAS_GRANITE_SPEECH = False
    logger.warning(f"Granite Speech dependencies not installed: {e}")


class GraniteSpeechEngine:
    """
    Local speech-to-text engine using IBM Granite Speech 3.3.

    Loads the model from Hugging Face on first use (cached locally
    at ~/.cache/huggingface/ for subsequent runs). No API keys needed.
    """

    # Supported model variants
    MODELS = {
        "2b": "ibm-granite/granite-speech-3.3-2b",
        "8b": "ibm-granite/granite-speech-3.3-8b",
    }

    def __init__(self, model_size: str = "2b"):
        """
        Initialize the Granite Speech engine.

        Args:
            model_size: Model variant to use.
                - "2b"  (~4 GB download, runs on CPU) [DEFAULT]
                - "8b"  (~16 GB download, GPU recommended)
        """
        self.settings = get_settings()
        self.model_size = model_size
        self.model_name = self.MODELS.get(model_size, self.MODELS["2b"])
        self._model = None
        self._processor = None
        self._device = None
        self.sample_rate = 16000

    def initialize(self) -> Tuple[bool, str]:
        """
        Load the Granite Speech model. Call once at startup or on first use.
        Separated from __init__ because model loading is slow and should
        happen in a background thread.

        On first run, downloads the model from Hugging Face (~4 GB for 2b).
        Subsequent runs load from cache (~5-15 seconds).

        Returns:
            Tuple of (success, status_message)
        """
        if not HAS_GRANITE_SPEECH:
            return False, (
                "Granite Speech dependencies not installed. "
                "Run: pip install torch transformers torchaudio peft soundfile"
            )

        try:
            # Select device: CUDA GPU > MPS (Apple Silicon) > CPU
            if torch.cuda.is_available():
                self._device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._device = "mps"
            else:
                self._device = "cpu"

            logger.info(
                f"Loading Granite Speech model: {self.model_name} "
                f"on device: {self._device}"
            )

            # Load processor (tokenizer + feature extractor)
            self._processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            # Load model with appropriate dtype for device
            dtype = torch.bfloat16 if self._device != "cpu" else torch.float32
            self._model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name,
                device_map=self._device,
                torch_dtype=dtype,
                trust_remote_code=True,
            )

            logger.info(
                f"Granite Speech model loaded: {self.model_name} "
                f"({self._device}, {dtype})"
            )
            return True, f"Granite Speech ({self.model_size}) ready on {self._device}"

        except Exception as e:
            logger.error(f"Failed to load Granite Speech model: {e}")
            return False, f"Failed to load Granite Speech: {e}"

    @property
    def is_available(self) -> bool:
        """Check if the engine is loaded and ready."""
        return self._model is not None and self._processor is not None

    @property
    def backend_name(self) -> str:
        """Return the backend identifier."""
        if self.is_available:
            return f"granite-speech-{self.model_size}"
        return "none"

    def transcribe(self, audio_data) -> str:
        """
        Transcribe audio data to text using Granite Speech.

        Args:
            audio_data: NumPy array of float32 audio samples at 16kHz mono.
                        Shape: (num_samples,) or (1, num_samples)

        Returns:
            Transcribed text string, or empty string on failure.
        """
        if not self.is_available:
            logger.error("Granite Speech model not loaded")
            return ""

        try:
            import torch
            import numpy as np

            # Ensure audio is a torch tensor with shape (1, num_samples)
            if isinstance(audio_data, np.ndarray):
                # Flatten if needed and convert to tensor
                if audio_data.ndim > 1:
                    audio_data = audio_data.flatten()
                wav = torch.from_numpy(audio_data).float().unsqueeze(0)
            elif isinstance(audio_data, torch.Tensor):
                wav = audio_data
                if wav.ndim == 1:
                    wav = wav.unsqueeze(0)
            else:
                logger.error(f"Unsupported audio type: {type(audio_data)}")
                return ""

            # Validate: must be mono 16kHz
            assert wav.shape[0] == 1, "Audio must be mono (1 channel)"

            # Build the transcription prompt using Granite Speech chat format
            tokenizer = self._processor.tokenizer
            prompt = tokenizer.apply_chat_template(
                [
                    {
                        "role": "system",
                        "content": "Knowledge Cutoff Date: April 2025.\nToday's Date: 2025-06-18.\nYou are a helpful AI assistant.",
                    },
                    {
                        "role": "user",
                        "content": "<|audio|>can you transcribe the speech into a written format?",
                    },
                ],
                tokenize=False,
                add_generation_prompt=True,
            )

            # Process audio + prompt through the processor
            inputs = self._processor(
                prompt,
                wav.squeeze(0),  # processor expects (num_samples,)
                self.sample_rate,
                return_tensors="pt",
            ).to(self._device)

            # Generate transcription
            num_input_tokens = inputs["input_ids"].shape[-1]

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=500,
                    do_sample=False,  # Greedy decoding for transcription
                )

            # Decode only the generated tokens (strip input prompt)
            generated_tokens = outputs[0, num_input_tokens:]
            transcript = tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True,
            ).strip()

            logger.debug(f"Granite Speech transcription: {transcript[:100]}...")
            return transcript

        except Exception as e:
            logger.error(f"Granite Speech transcription error: {e}")
            return ""

    def cleanup(self):
        """Release model resources and free GPU memory."""
        self._model = None
        self._processor = None
        if HAS_GRANITE_SPEECH:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self._device = None
        logger.info("Granite Speech engine cleaned up")
```

---

### Step 3: Refactor VoiceService to Use Granite Speech Engine

**File:** `src/services/voice_service.py`

Key changes:
1. Replace IBM Watson STT with `GraniteSpeechEngine`
2. Keep the existing public API (`start_dictation`, `stop_dictation`, `is_available`, etc.) unchanged so no UI code breaks
3. Add lazy model loading (first use triggers load in background)
4. Remove Watson SDK dependency for STT

```python
"""
Voice Service for Speech-to-Text and Text-to-Speech.
Uses local IBM Granite Speech engine for offline transcription (BR6).
"""

from typing import Optional, Callable, Tuple
import threading
import time

from ..config.settings import get_settings
from ..config.logging_config import get_logger
from .granite_speech_engine import GraniteSpeechEngine

logger = get_logger(__name__)

# Audio library imports (unchanged from current code)
try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

class VoiceService:
    """
    Service for voice input/output.
    Uses IBM Granite Speech locally for STT — no API keys required.
    """

    def __init__(self):
        self.settings = get_settings()
        self._stt_engine = GraniteSpeechEngine(
            model_size=self.settings.granite_speech_model_size
        )
        self._is_recording = False
        self._is_speaking = False
        self._model_loaded = False

        # Audio settings (unchanged)
        self.sample_rate = 16000
        self.channels = 1
        self.silence_threshold = self.settings.silence_threshold_seconds

    def _ensure_model_loaded(self) -> Tuple[bool, str]:
        """Lazy-load the Granite Speech model on first use."""
        if self._model_loaded:
            return self._stt_engine.is_available, "Ready"
        success, message = self._stt_engine.initialize()
        self._model_loaded = True
        return success, message

    @property
    def is_available(self) -> bool:
        """Check if voice services are available (no API key needed)."""
        return HAS_AUDIO

    # ... check_microphone_permission() — UNCHANGED
    # ... start_dictation()   — add _ensure_model_loaded() call
    # ... stop_dictation()    — UNCHANGED
    # ... _record_and_transcribe() — UNCHANGED (audio capture stays the same)

    def _transcribe_audio(self, audio_data) -> str:
        """Transcribe audio using local Granite Speech engine."""
        return self._stt_engine.transcribe(audio_data)

    # ... speak(), _speak_text(), etc. — keep Watson TTS or replace later
```

**Method-by-method changes:**

| Method | Change |
|--------|--------|
| `__init__` | Create `GraniteSpeechEngine` instead of Watson client |
| `_initialize_services` | **Remove entirely** (no API keys to configure) |
| `is_available` | Simplify to `HAS_AUDIO` only (no Watson check) |
| `start_dictation` | Add `_ensure_model_loaded()` before recording |
| `_record_and_transcribe` | **No change** (audio capture logic stays the same) |
| `_transcribe_audio` | Replace Watson API call with `self._stt_engine.transcribe()` |
| `check_microphone_permission` | **No change** |
| `speak` / `_speak_text` | Keep Watson TTS for now, or replace in a future PR |

---

### Step 4: Add Configuration Settings

**File:** `src/config/settings.py`

Add to the Settings dataclass:

```python
# Local Speech-to-Text (IBM Granite Speech)
granite_speech_model_size: str = "2b"  # "2b" (CPU-friendly) or "8b" (GPU recommended)
```

Maps to environment variable:
```
GRANITE_SPEECH_MODEL_SIZE=2b
```

---

### Step 5: Add Microphone Button to Chat UI

**File:** `src/ui/chat_screen.py`

Add a microphone toggle button to the input area, between the text input and send button:

```python
# In _create_chat_area(), inside input_layout, before self.send_btn:

# Microphone button for voice dictation (BR6)
self.mic_btn = QPushButton("Mic")
self.mic_btn.setObjectName("micButton")
self.mic_btn.setFixedSize(44, 44)
self.mic_btn.setCheckable(True)       # Toggle: click to start, click to stop
self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
self.mic_btn.clicked.connect(self._toggle_dictation)
self.mic_btn.setEnabled(False)        # Enabled when chat is open
input_layout.addWidget(self.mic_btn)
```

Add the toggle handler and result callback:

```python
def _toggle_dictation(self):
    """Toggle voice dictation on/off (BR6.1)."""
    from ..services.voice_service import get_voice_service
    voice = get_voice_service()

    if self.mic_btn.isChecked():
        # Start recording — style the button as "recording"
        self.mic_btn.setStyleSheet(MIC_BUTTON_RECORDING)
        success = voice.start_dictation(callback=self._on_dictation_result)
        if not success:
            self.mic_btn.setChecked(False)
            self.mic_btn.setStyleSheet(MIC_BUTTON_DEFAULT)
    else:
        # Stop recording
        voice.stop_dictation()
        self.mic_btn.setStyleSheet(MIC_BUTTON_DEFAULT)

def _on_dictation_result(self, text: str):
    """Insert transcribed text into the message input (BR6.2)."""
    if text and not text.startswith("["):
        cursor = self.message_input.textCursor()
        cursor.insertText(text)
        self.message_input.setTextCursor(cursor)
    # Reset mic button state
    self.mic_btn.setChecked(False)
    self.mic_btn.setStyleSheet(MIC_BUTTON_DEFAULT)
```

Also enable the mic button when a chat is loaded (in `_load_chat`):

```python
self.mic_btn.setEnabled(True)
```

---

### Step 6: Add Mic Button Styles

**File:** `src/ui/styles.py`

```python
# Microphone button — default state
MIC_BUTTON_DEFAULT = """
    QPushButton#micButton {
        background-color: #F4F4F5;
        color: #71717A;
        border: none;
        border-radius: 22px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton#micButton:hover {
        background-color: #E4E4E7;
        color: #52525B;
    }
    QPushButton#micButton:disabled {
        background-color: #FAFAFA;
        color: #D4D4D8;
    }
"""

# Microphone button — recording state (red pulse)
MIC_BUTTON_RECORDING = """
    QPushButton#micButton {
        background-color: #FEE2E2;
        color: #DC2626;
        border: 2px solid #DC2626;
        border-radius: 22px;
        font-size: 12px;
        font-weight: 600;
    }
"""
```

---

### Step 7: Handle First-Run Model Download

Granite Speech models are auto-downloaded from Hugging Face on first use and cached at `~/.cache/huggingface/`. The 2B model is ~4 GB.

**In `voice_service.py` (`start_dictation`):**

```python
def start_dictation(self, callback):
    # Ensure model is loaded (may trigger download on first run)
    model_ready, message = self._ensure_model_loaded()
    if not model_ready:
        callback(f"[Speech model not available: {message}]")
        return False

    # ... rest of existing logic (permission check, start recording thread)
```

**UI feedback options for first-run download:**
- Show a tooltip on the mic button: "Downloading speech model (one-time)..."
- Or show a QProgressDialog while the model loads
- After first download, model loads from cache in ~5-15 seconds

---

### Step 8: Handle Threading and UI Updates

Transcription via Granite Speech takes a few seconds on CPU. The existing `_record_and_transcribe` method already runs in a background thread, so this works out-of-the-box. The callback delivers the text to the UI thread.

For the model loading step (which can take 15-60 seconds on first run), add a `DictationWorker` QThread:

```python
class DictationWorker(QThread):
    """Worker for loading model + recording + transcription."""
    transcription_ready = pyqtSignal(str)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, voice_service):
        super().__init__()
        self.voice_service = voice_service

    def run(self):
        # 1. Ensure model loaded
        self.status_update.emit("Loading speech model...")
        ready, msg = self.voice_service._ensure_model_loaded()
        if not ready:
            self.error_occurred.emit(msg)
            return

        # 2. Start recording (VoiceService handles this)
        self.status_update.emit("Listening...")
        self.voice_service.start_dictation(
            callback=lambda text: self.transcription_ready.emit(text)
        )
```

---

### Step 9: Write Tests

**New file:** `tests/test_granite_speech_engine.py`

```python
"""Tests for GraniteSpeechEngine."""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock


class TestGraniteSpeechEngine:
    """Unit tests for the local Granite Speech engine."""

    def test_init_default_model(self):
        """Test engine initializes with 2b model by default."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        assert engine.model_size == "2b"
        assert engine.model_name == "ibm-granite/granite-speech-3.3-2b"
        assert not engine.is_available  # Not loaded yet

    def test_init_8b_model(self):
        """Test engine accepts 8b model variant."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine(model_size="8b")
        assert engine.model_name == "ibm-granite/granite-speech-3.3-8b"

    def test_init_invalid_model_falls_back(self):
        """Test invalid model size falls back to 2b."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine(model_size="invalid")
        assert engine.model_name == "ibm-granite/granite-speech-3.3-2b"

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", False)
    def test_initialize_without_dependencies(self):
        """Test initialize fails gracefully without torch/transformers."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        success, message = engine.initialize()
        assert not success
        assert "not installed" in message

    def test_transcribe_without_model(self):
        """Test transcribe returns empty string when model not loaded."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        result = engine.transcribe(np.zeros(16000, dtype=np.float32))
        assert result == ""

    def test_backend_name_before_init(self):
        """Test backend_name is 'none' before initialization."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        assert engine.backend_name == "none"

    @patch("src.services.granite_speech_engine.AutoModelForSpeechSeq2Seq")
    @patch("src.services.granite_speech_engine.AutoProcessor")
    def test_initialize_mocks_model(self, mock_processor, mock_model):
        """Test initialize loads model and processor."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        success, message = engine.initialize()
        assert success
        assert "ready" in message.lower()
        assert engine.is_available

    def test_cleanup_releases_resources(self):
        """Test cleanup sets model references to None."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        engine._model = MagicMock()
        engine._processor = MagicMock()
        engine.cleanup()
        assert engine._model is None
        assert engine._processor is None
```

---

### Step 10: Update Documentation and Config

**File:** `.env.example`

```bash
# ── Local Speech-to-Text (IBM Granite Speech) ──────────────
# Model runs locally, NO API key required!
# Options: "2b" (CPU-friendly, ~4GB download) or "8b" (GPU recommended, ~16GB)
GRANITE_SPEECH_MODEL_SIZE=2b

# Watson Speech keys are NO LONGER REQUIRED for STT:
# WATSON_SPEECH_API_KEY=     (deprecated for STT, may still be used for TTS)
# WATSON_SPEECH_URL=         (deprecated for STT)
```

---

## File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `requirements.txt` | **Modify** | Add `torch`, `transformers>=4.52.4`, `torchaudio`, `peft`, `soundfile` |
| `src/services/granite_speech_engine.py` | **Create** | New module: local Granite Speech transcription engine |
| `src/services/voice_service.py` | **Modify** | Replace Watson STT with GraniteSpeechEngine, keep same public API |
| `src/config/settings.py` | **Modify** | Add `granite_speech_model_size` setting |
| `src/ui/chat_screen.py` | **Modify** | Add microphone toggle button to chat input area |
| `src/ui/styles.py` | **Modify** | Add mic button styles (default + recording states) |
| `tests/test_granite_speech_engine.py` | **Create** | Unit tests for the Granite Speech engine |
| `.env.example` | **Modify** | Add granite speech config, deprecate Watson STT keys |

---

## Hardware Requirements

### Minimum (2B model on CPU)
- **CPU:** Any modern x86_64 or ARM64 processor
- **RAM:** 8 GB (5 GB for model + 3 GB for OS/app)
- **Disk:** ~4 GB for model cache (one-time download)
- **GPU:** Not required

### Recommended (2B model with GPU)
- **GPU:** NVIDIA with 6+ GB VRAM, or Apple Silicon (MPS)
- **RAM:** 8+ GB
- Transcription will be significantly faster with GPU acceleration

### High Accuracy (8B model)
- **GPU:** NVIDIA with 16+ GB VRAM
- **RAM:** 16+ GB
- Best accuracy, but requires capable hardware

---

## Performance Expectations

| Scenario | Model | Hardware | Transcription Time (10s audio) |
|----------|-------|----------|-------------------------------|
| Basic desktop | 2B | CPU only | ~5-10 seconds |
| Desktop + GPU | 2B | NVIDIA RTX 3060 | ~1-2 seconds |
| High-end | 8B | NVIDIA RTX 4090 | ~1-2 seconds |
| Apple Silicon | 2B | M1/M2 Mac (MPS) | ~2-4 seconds |

For dictation use (speaking a short question into the chat), 5-10 seconds of processing on CPU is acceptable. The user speaks, stops, and sees the text appear shortly after.

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| First-run model download is ~4 GB | Show progress indicator in UI. Model is cached permanently after download. Could pre-bundle with PyInstaller for offline installs. |
| Slow transcription on CPU-only machines | Default to 2B model. Consider int4 quantization. Acceptable for short dictation. |
| `torch` adds ~2 GB to install size | Necessary trade-off for local ML. Consider `torch` CPU-only build (`pip install torch --index-url https://download.pytorch.org/whl/cpu`) to reduce size. |
| CUDA not available | Automatic fallback to CPU. MPS support for Apple Silicon. |
| Model accuracy vs Watson cloud | Granite Speech 3.3 is #1 on Hugging Face Open ASR Leaderboard — accuracy is excellent. |
| `transformers>=4.52.4` may conflict with existing deps | Check compatibility with existing `langchain`/`chromadb` dependencies. Pin if needed. |

---

## Implementation Order

1. **Update `requirements.txt`** — add torch, transformers, torchaudio, peft, soundfile
2. **Create `granite_speech_engine.py`** — the local transcription engine
3. **Refactor `voice_service.py`** — swap Watson STT for GraniteSpeechEngine
4. **Add settings** to `settings.py` — `granite_speech_model_size`
5. **Add mic button** to `chat_screen.py` — UI toggle for dictation
6. **Add styles** to `styles.py` — mic button default + recording states
7. **Write tests** for `granite_speech_engine.py`
8. **Update `.env.example`** — document new setting, deprecate Watson STT keys
9. **Test end-to-end** — record real audio, verify transcription
10. **Package with PyInstaller** — verify standalone build works with torch

---

## References

- [IBM Granite Speech 3.3 8B — Hugging Face](https://huggingface.co/ibm-granite/granite-speech-3.3-8b)
- [IBM Granite Speech 3.3 2B — Hugging Face](https://huggingface.co/ibm-granite/granite-speech-3.3-2b)
- [Granite Speech Models — GitHub](https://github.com/ibm-granite/granite-speech-models)
- [IBM Granite Speech Documentation](https://www.ibm.com/granite/docs/models/speech)
- [IBM Granite tops Hugging Face ASR Leaderboard](https://research.ibm.com/blog/granite-speech-recognition-hugging-face-chart)
- [Granite Speech ASR Guide — DEV Community](https://dev.to/aairom/from-speech-to-text-a-guide-to-ibm-granite-speech-for-audio-transcriptions-37nc)
