"""
Tests for GraniteSpeechEngine — local speech-to-text using IBM Granite Speech.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


class TestGraniteSpeechEngineInit:
    """Test initialization and configuration."""

    def test_default_model_size(self):
        """Engine defaults to 2b model."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        assert engine.model_size == "2b"
        assert engine.model_name == "ibm-granite/granite-speech-3.3-2b"

    def test_8b_model_size(self):
        """Engine accepts 8b variant."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine(model_size="8b")
        assert engine.model_size == "8b"
        assert engine.model_name == "ibm-granite/granite-speech-3.3-8b"

    def test_invalid_model_falls_back_to_2b(self):
        """Invalid model size falls back to 2b."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine(model_size="invalid")
        assert engine.model_size == "2b"
        assert engine.model_name == "ibm-granite/granite-speech-3.3-2b"

    def test_not_available_before_init(self):
        """Engine is not available before initialize() is called."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        assert not engine.is_available

    def test_backend_name_before_init(self):
        """Backend name is 'none' before initialization."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        assert engine.backend_name == "none"

    def test_sample_rate(self):
        """Default sample rate is 16 kHz."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        assert engine.sample_rate == 16000


class TestGraniteSpeechEngineInitialize:
    """Test model loading behavior."""

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", False)
    def test_initialize_without_dependencies(self):
        """Returns failure when torch/transformers not installed."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        success, message = engine.initialize()
        assert not success
        assert "not installed" in message

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", True)
    @patch("src.services.granite_speech_engine.torch", create=True)
    @patch("src.services.granite_speech_engine.AutoModelForSpeechSeq2Seq", create=True)
    @patch("src.services.granite_speech_engine.AutoProcessor", create=True)
    def test_initialize_success(self, mock_processor_cls, mock_model_cls, mock_torch):
        """Successful initialization loads model and processor."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.float32 = "float32"

        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        success, message = engine.initialize()

        assert success
        assert "ready" in message.lower()
        assert engine.is_available
        assert engine._device == "cpu"
        mock_processor_cls.from_pretrained.assert_called_once()
        mock_model_cls.from_pretrained.assert_called_once()

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", True)
    @patch("src.services.granite_speech_engine.torch", create=True)
    @patch("src.services.granite_speech_engine.AutoModelForSpeechSeq2Seq", create=True)
    @patch("src.services.granite_speech_engine.AutoProcessor", create=True)
    def test_initialize_selects_cuda(self, mock_processor_cls, mock_model_cls, mock_torch):
        """Selects CUDA device when available."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"

        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        success, _ = engine.initialize()

        assert success
        assert engine._device == "cuda"

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", True)
    @patch("src.services.granite_speech_engine.torch", create=True)
    @patch("src.services.granite_speech_engine.AutoProcessor", create=True)
    def test_initialize_failure_cleans_up(self, mock_processor_cls, mock_torch):
        """Failed initialization cleans up partial state."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.float32 = "float32"
        mock_processor_cls.from_pretrained.side_effect = RuntimeError("download failed")

        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        success, message = engine.initialize()

        assert not success
        assert "Failed" in message
        assert not engine.is_available

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", True)
    @patch("src.services.granite_speech_engine.torch", create=True)
    @patch("src.services.granite_speech_engine.AutoModelForSpeechSeq2Seq", create=True)
    @patch("src.services.granite_speech_engine.AutoProcessor", create=True)
    def test_backend_name_after_init(self, mock_proc, mock_model, mock_torch):
        """Backend name reflects model size after init."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.float32 = "float32"

        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine(model_size="2b")
        engine.initialize()
        assert engine.backend_name == "granite-speech-2b"


class TestGraniteSpeechEngineTranscribe:
    """Test transcription behavior."""

    def test_transcribe_without_model(self):
        """Returns empty string when model not loaded."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        result = engine.transcribe(np.zeros(16000, dtype=np.float32))
        assert result == ""

    def test_transcribe_empty_array(self):
        """Returns empty string for empty audio (model not loaded)."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        result = engine.transcribe(np.array([], dtype=np.float32))
        assert result == ""


class TestGraniteSpeechEngineCleanup:
    """Test resource cleanup."""

    def test_cleanup_releases_references(self):
        """Cleanup sets model and processor to None."""
        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        engine._model = MagicMock()
        engine._processor = MagicMock()
        engine._device = "cpu"

        engine.cleanup()

        assert engine._model is None
        assert engine._processor is None
        assert engine._device is None
        assert not engine.is_available

    @patch("src.services.granite_speech_engine.HAS_GRANITE_SPEECH", True)
    @patch("src.services.granite_speech_engine.torch", create=True)
    def test_cleanup_clears_cuda_cache(self, mock_torch):
        """Cleanup calls torch.cuda.empty_cache() when CUDA available."""
        mock_torch.cuda.is_available.return_value = True

        from src.services.granite_speech_engine import GraniteSpeechEngine
        engine = GraniteSpeechEngine()
        engine._model = MagicMock()
        engine._processor = MagicMock()

        engine.cleanup()

        mock_torch.cuda.empty_cache.assert_called_once()


class TestVoiceServiceIntegration:
    """Test VoiceService with GraniteSpeechEngine."""

    @patch("src.services.voice_service.GraniteSpeechEngine")
    def test_voice_service_creates_engine(self, mock_engine_cls):
        """VoiceService creates GraniteSpeechEngine on init."""
        # Reset singleton
        import src.services.voice_service as vs
        vs._voice_service = None

        service = vs.VoiceService()
        mock_engine_cls.assert_called_once()

    @patch("src.services.voice_service.GraniteSpeechEngine")
    def test_is_available_without_audio(self, mock_engine_cls):
        """is_available is False when sounddevice not installed."""
        import src.services.voice_service as vs
        original = vs.HAS_AUDIO
        try:
            vs.HAS_AUDIO = False
            vs._voice_service = None
            service = vs.VoiceService()
            assert not service.is_available
        finally:
            vs.HAS_AUDIO = original
            vs._voice_service = None

    @patch("src.services.voice_service.GraniteSpeechEngine")
    def test_ensure_model_loaded_calls_initialize(self, mock_engine_cls):
        """_ensure_model_loaded calls engine.initialize() once."""
        mock_engine = MagicMock()
        mock_engine.initialize.return_value = (True, "Ready")
        mock_engine.is_available = True
        mock_engine_cls.return_value = mock_engine

        import src.services.voice_service as vs
        vs._voice_service = None
        service = vs.VoiceService()

        # First call triggers initialize
        success, msg = service._ensure_model_loaded()
        assert success
        mock_engine.initialize.assert_called_once()

        # Second call skips initialize
        success2, _ = service._ensure_model_loaded()
        assert success2
        assert mock_engine.initialize.call_count == 1
