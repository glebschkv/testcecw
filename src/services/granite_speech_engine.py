"""
Granite Speech Engine for local speech-to-text.
Uses IBM Granite Speech 3.3 via Hugging Face Transformers.
Runs entirely offline after initial model download — no API keys needed.

Implements BR6: Speech-to-text Dictation (transcription backend).
"""

from typing import Optional, Tuple

from ..config.settings import get_settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)

# Try to import required libraries
try:
    import torch
    import torchaudio  # noqa: F401 — needed for audio processing support
    import soundfile  # noqa: F401 — needed by transformers for audio I/O
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

    Supports two model sizes:
        - "2b": ~4 GB download, runs on CPU (default)
        - "8b": ~16 GB download, GPU recommended
    """

    MODELS = {
        "2b": "ibm-granite/granite-speech-3.3-2b",
        "8b": "ibm-granite/granite-speech-3.3-8b",
    }

    def __init__(self, model_size: str = "2b"):
        """
        Initialize the Granite Speech engine.

        Args:
            model_size: Model variant — "2b" (CPU-friendly) or "8b" (GPU).
        """
        self.settings = get_settings()
        self.model_size = model_size if model_size in self.MODELS else "2b"
        self.model_name = self.MODELS[self.model_size]
        self._model = None
        self._processor = None
        self._device = None
        self.sample_rate = 16000

    def initialize(self) -> Tuple[bool, str]:
        """
        Load the Granite Speech model.

        Should be called once, ideally in a background thread since model
        loading takes several seconds. On first run it downloads the model
        from Hugging Face (~4 GB for 2b).

        Returns:
            Tuple of (success, status_message)
        """
        if not HAS_GRANITE_SPEECH:
            return False, (
                "Granite Speech dependencies not installed. "
                "Run: pip install torch transformers torchaudio peft soundfile"
            )

        try:
            # Select best available device
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

            # Use bfloat16 on GPU, float32 on CPU for compatibility
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
            self._model = None
            self._processor = None
            return False, f"Failed to load speech model: {e}"

    @property
    def is_available(self) -> bool:
        """Check if the engine is loaded and ready."""
        return self._model is not None and self._processor is not None

    @property
    def backend_name(self) -> str:
        """Return a human-readable backend identifier."""
        if self.is_available:
            return f"granite-speech-{self.model_size}"
        return "none"

    def transcribe(self, audio_data) -> str:
        """
        Transcribe audio data to text using Granite Speech.

        Args:
            audio_data: NumPy array of float32 audio at 16 kHz mono.
                        Shape: (num_samples,) or (N, num_samples).

        Returns:
            Transcribed text, or empty string on failure.
        """
        if not self.is_available:
            logger.error("Granite Speech model not loaded — call initialize() first")
            return ""

        try:
            import numpy as np

            # Convert numpy array to torch tensor (1, num_samples)
            if hasattr(audio_data, 'numpy'):
                # Already a tensor
                wav = audio_data.float()
            else:
                if audio_data.ndim > 1:
                    audio_data = audio_data.flatten()
                wav = torch.from_numpy(audio_data.copy()).float()

            if wav.ndim == 1:
                wav = wav.unsqueeze(0)

            # Build transcription prompt in Granite Speech chat format
            tokenizer = self._processor.tokenizer
            prompt = tokenizer.apply_chat_template(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful AI assistant. "
                            "Transcribe the audio accurately."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "<|audio|>can you transcribe the speech "
                            "into a written format?"
                        ),
                    },
                ],
                tokenize=False,
                add_generation_prompt=True,
            )

            # Process audio + prompt
            inputs = self._processor(
                prompt,
                wav.squeeze(0),  # processor expects 1-D waveform
                self.sample_rate,
                return_tensors="pt",
            ).to(self._device)

            num_input_tokens = inputs["input_ids"].shape[-1]

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=500,
                    do_sample=False,
                )

            # Decode only the newly generated tokens
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
        if HAS_GRANITE_SPEECH and torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._device = None
        logger.info("Granite Speech engine cleaned up")
