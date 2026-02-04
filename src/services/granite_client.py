"""
IBM Granite Client - Runs Granite models locally via llama-cpp-python.
No external server (like Ollama) required. Falls back to watsonx.ai or mock mode.
"""

from typing import Optional, List, Dict, Any, Callable
import os
import json
import time
import hashlib
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path

from ..config.settings import get_settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,)
):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retryable_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts: {e}")
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

            raise last_exception

        return wrapper
    return decorator


class ResponseCache:
    """Simple in-memory cache for AI responses with TTL."""

    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries to cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, prompt: str, context: str, system_prompt: str = None) -> str:
        """Generate a cache key from the input parameters."""
        key_data = f"{prompt}|{context}|{system_prompt or ''}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def get(self, prompt: str, context: str, system_prompt: str = None) -> Optional[str]:
        """
        Get a cached response if available and not expired.

        Returns:
            Cached response string or None
        """
        key = self._generate_key(prompt, context, system_prompt)

        if key not in self._cache:
            return None

        entry = self._cache[key]
        if datetime.utcnow() > entry['expires_at']:
            del self._cache[key]
            return None

        logger.debug(f"Cache hit for key {key[:8]}...")
        return entry['response']

    def set(self, prompt: str, context: str, response: str, system_prompt: str = None, ttl: int = None) -> None:
        """
        Cache a response.

        Args:
            prompt: The user prompt
            context: The context string
            response: The response to cache
            system_prompt: Optional system prompt
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        key = self._generate_key(prompt, context, system_prompt)
        ttl = ttl or self.default_ttl

        self._cache[key] = {
            'response': response,
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl),
            'created_at': datetime.utcnow()
        }
        logger.debug(f"Cached response for key {key[:8]}...")

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['created_at'])
        del self._cache[oldest_key]

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def size(self) -> int:
        """Return the current cache size."""
        return len(self._cache)


# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    HAS_LLAMA_CPP = False
    logger.info("llama-cpp-python not installed. pip install llama-cpp-python")

# Try to import huggingface_hub for model downloads
try:
    from huggingface_hub import hf_hub_download
    HAS_HF_HUB = True
except ImportError:
    HAS_HF_HUB = False
    logger.info("huggingface-hub not installed. pip install huggingface-hub")

# Try to import IBM watsonx libraries (optional, for cloud deployment)
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    HAS_WATSONX = True
except ImportError:
    HAS_WATSONX = False

try:
    from langchain_ibm import ChatWatsonx, WatsonxEmbeddings
    HAS_LANGCHAIN_IBM = True
except ImportError:
    HAS_LANGCHAIN_IBM = False


class GraniteClient:
    """
    Client for IBM Granite models.

    Supports:
    1. Local llama-cpp-python (recommended - no server or API key needed)
    2. IBM watsonx.ai API (cloud deployment)
    3. Mock mode (fallback for demo)

    Features:
    - Automatic model download from HuggingFace
    - Response caching for repeated queries
    - Graceful degradation to mock mode
    """

    # Default model settings
    DEFAULT_MODEL_REPO = "ibm-granite/granite-4.0-tiny-preview-GGUF"
    DEFAULT_MODEL_FILE = "granite-4.0-tiny-preview.Q4_K_M.gguf"

    def __init__(self, model_path: str = None, enable_cache: bool = True):
        """
        Initialize the Granite client.

        Args:
            model_path: Path to a local GGUF model file (auto-downloads if not provided)
            enable_cache: Enable response caching (default: True)
        """
        self.settings = get_settings()
        self._llm = None
        self._chat_model = None
        self._embeddings = None
        self._api_client = None
        self._initialized = False

        # Response cache
        self._cache = ResponseCache(max_size=100, default_ttl=3600) if enable_cache else None

        # Model configuration
        self._model_path = model_path or self.settings.granite_model_path or None
        self._model_repo = self.settings.granite_model_repo or self.DEFAULT_MODEL_REPO
        self._model_file = self.settings.granite_model_file or self.DEFAULT_MODEL_FILE
        self._n_ctx = self.settings.granite_n_ctx
        self._n_gpu_layers = self.settings.granite_n_gpu_layers

        # Check what's available
        self._use_local = self._check_local_model_available()

        if self._use_local:
            logger.info(f"Using local Granite model: {self._model_path}")
        else:
            logger.info("Local model not available, checking watsonx.ai...")
            is_valid, errors = self.settings.validate()
            if not is_valid:
                logger.warning(f"watsonx.ai not configured: {errors}")
                logger.info("Running in demo mode with mock responses")

    def _check_local_model_available(self) -> bool:
        """Check if a local GGUF model is available (or can be downloaded)."""
        if not HAS_LLAMA_CPP:
            logger.info("llama-cpp-python not installed")
            return False

        # If explicit path provided, check it exists
        if self._model_path and Path(self._model_path).is_file():
            return True

        # Try to find model in models directory
        models_dir = self.settings.models_dir
        candidate = models_dir / self._model_file
        if candidate.is_file():
            self._model_path = str(candidate)
            return True

        # Try to download from HuggingFace
        if HAS_HF_HUB:
            try:
                logger.info(
                    f"Downloading Granite model: {self._model_repo}/{self._model_file} ..."
                )
                downloaded_path = hf_hub_download(
                    repo_id=self._model_repo,
                    filename=self._model_file,
                    cache_dir=str(models_dir),
                    local_dir=str(models_dir),
                )
                self._model_path = downloaded_path
                logger.info(f"Model downloaded to: {self._model_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to download model: {e}")

        return False

    def _load_model(self) -> bool:
        """Load the GGUF model into memory."""
        if self._llm is not None:
            return True

        if not self._model_path:
            return False

        try:
            logger.info(f"Loading model from {self._model_path} ...")
            self._llm = Llama(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_gpu_layers=self._n_gpu_layers,
                verbose=False,
                embedding=True,
            )
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        if self._use_local:
            return True
        is_valid, _ = self.settings.validate()
        return is_valid and HAS_WATSONX

    @property
    def is_using_local(self) -> bool:
        """Check if using local llama-cpp-python model."""
        return self._use_local

    @property
    def model_path(self) -> Optional[str]:
        """Get the path to the loaded model."""
        return self._model_path

    def initialize(self) -> bool:
        """Initialize the client."""
        if self._initialized:
            return True

        if self._use_local:
            if self._load_model():
                self._initialized = True
                logger.info("Granite client initialized with local model")
                return True
            else:
                logger.warning("Failed to load local model, falling back...")
                self._use_local = False

        if not self.is_configured:
            logger.warning("Granite client not configured. Using mock mode.")
            return False

        # Initialize watsonx.ai (cloud mode)
        try:
            credentials = Credentials(
                url=self.settings.watsonx_url,
                api_key=self.settings.watsonx_api_key
            )
            self._api_client = APIClient(credentials)

            if HAS_LANGCHAIN_IBM:
                self._chat_model = ChatWatsonx(
                    model_id=self.settings.granite_chat_model,
                    url=self.settings.watsonx_url,
                    apikey=self.settings.watsonx_api_key,
                    project_id=self.settings.watsonx_project_id,
                    params=self.settings.generation_params
                )

            self._initialized = True
            logger.info("Granite client initialized with watsonx.ai")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize watsonx.ai client: {e}")
            return False

    def generate_response(self, prompt: str, context: str = "", system_prompt: str = None, use_cache: bool = True) -> str:
        """
        Generate a response using IBM Granite.

        Args:
            prompt: User's input prompt
            context: Additional context (e.g., OBD data)
            system_prompt: Optional system prompt override
            use_cache: Whether to use cached responses (default: True)

        Returns:
            Generated response text
        """
        # Check cache first
        if use_cache and self._cache:
            cached = self._cache.get(prompt, context, system_prompt)
            if cached:
                return cached

        response = None

        # Try local model first
        if self._use_local:
            response = self._generate_local(prompt, context, system_prompt)
        # Try watsonx.ai
        elif self.is_configured:
            if not self._initialized:
                self.initialize()
            try:
                full_prompt = self._build_prompt(prompt, context, system_prompt)
                if self._chat_model:
                    result = self._chat_model.invoke(full_prompt)
                    response = result.content
            except Exception as e:
                logger.error(f"watsonx.ai error: {e}")

        # Fallback to mock
        if response is None:
            response = self._mock_response(prompt, context)

        # Cache the response
        if use_cache and self._cache and response:
            self._cache.set(prompt, context, response, system_prompt)

        return response

    def _generate_local(self, prompt: str, context: str = "", system_prompt: str = None) -> str:
        """Generate response using local llama-cpp-python model."""
        if not self._load_model():
            return None

        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        # Build messages for chat
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Here is the vehicle diagnostic context:\n{context}"
            })
            messages.append({
                "role": "assistant",
                "content": "I understand. I'll analyze this OBD-II data to help answer your questions."
            })

        messages.append({"role": "user", "content": prompt})

        try:
            result = self._llm.create_chat_completion(
                messages=messages,
                max_tokens=self.settings.max_new_tokens,
                temperature=self.settings.temperature,
                top_p=self.settings.top_p,
                repeat_penalty=self.settings.repetition_penalty,
            )
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Local model generation error: {e}")
            return self._mock_response(prompt, context)

    def generate_streaming(self, prompt: str, context: str = ""):
        """Generate a streaming response."""
        if self._use_local:
            yield from self._generate_local_streaming(prompt, context)
            return

        # Mock streaming fallback
        response = self._mock_response(prompt, context)
        for word in response.split():
            yield word + " "

    def _generate_local_streaming(self, prompt: str, context: str = ""):
        """Generate streaming response from local model."""
        if not self._load_model():
            yield self._mock_response(prompt, context)
            return

        system_prompt = self._get_default_system_prompt()

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
            messages.append({"role": "assistant", "content": "I understand the context."})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self._llm.create_chat_completion(
                messages=messages,
                max_tokens=self.settings.max_new_tokens,
                temperature=self.settings.temperature,
                top_p=self.settings.top_p,
                repeat_penalty=self.settings.repetition_penalty,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content

        except Exception as e:
            logger.error(f"Local model streaming error: {e}")
            yield f"Error: {str(e)}"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        if self._use_local:
            return self._get_local_embeddings(texts)

        # Return deterministic mock embeddings
        return [[hash(t) % 100 / 100.0 for _ in range(384)] for t in texts]

    def _get_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using local model."""
        if not self._load_model():
            return [[hash(t) % 100 / 100.0 for _ in range(384)] for t in texts]

        embeddings = []
        for text in texts:
            try:
                result = self._llm.embed(text)
                # llama-cpp-python embed() returns a list of floats or list of list of floats
                if result and isinstance(result[0], list):
                    embeddings.append(result[0])
                else:
                    embeddings.append(result)
            except Exception as e:
                logger.error(f"Embedding error for text: {e}")
                embeddings.append([hash(text) % 100 / 100.0 for _ in range(384)])
        return embeddings

    def clear_cache(self) -> None:
        """Clear the response cache."""
        if self._cache:
            self._cache.clear()
            logger.info("Response cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._cache:
            return {"enabled": False}
        return {
            "enabled": True,
            "size": self._cache.size(),
            "max_size": self._cache.max_size
        }

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * 384

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self._use_local and self._model_path:
            model_size = Path(self._model_path).stat().st_size if Path(self._model_path).exists() else 0
            return {
                "backend": "llama-cpp-python",
                "model_path": self._model_path,
                "model_repo": self._model_repo,
                "model_file": self._model_file,
                "model_size_mb": round(model_size / (1024 * 1024), 1),
                "n_ctx": self._n_ctx,
                "n_gpu_layers": self._n_gpu_layers,
                "loaded": self._llm is not None,
            }
        return {
            "backend": "mock",
            "model_path": None,
            "loaded": False,
        }

    def _build_prompt(self, user_prompt: str, context: str = "", system_prompt: str = None) -> str:
        """Build the full prompt with system instructions."""
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        parts = [system_prompt]
        if context:
            parts.append(f"\n\nCONTEXT:\n{context}")
        parts.append(f"\n\nUSER QUESTION:\n{user_prompt}")
        parts.append("\n\nRESPONSE:")

        return "".join(parts)

    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for OBD InsightBot."""
        return """You are OBD InsightBot, a friendly and knowledgeable automotive diagnostic assistant.

Your role is to help users understand their vehicle's OBD-II diagnostic data in simple, non-technical language.

Guidelines:
1. Always explain technical terms in simple language that anyone can understand
2. Be clear about the severity of any issues (critical, warning, or normal)
3. Provide practical recommendations when issues are detected
4. If you don't have information about something, say so clearly
5. Prioritize safety - always recommend professional inspection for serious issues
6. Be conversational and supportive, as users may be worried about their vehicle

Response Severity Levels:
- CRITICAL (Red): Immediate attention required - stop driving
- WARNING (Amber): Should be addressed soon
- NORMAL (Green): No immediate concern

Always be helpful and provide actionable advice."""

    def _mock_response(self, prompt: str, context: str) -> str:
        """Generate a mock response for demo mode."""
        prompt_lower = prompt.lower()

        # More specific keyword matching to avoid false positives
        # Check for fault code queries first (must have "fault" or specific code patterns)
        fault_keywords = ["fault code", "error code", "dtc", "diagnostic code", "trouble code"]
        code_pattern = any(f"p0" in prompt_lower or f"p1" in prompt_lower or
                          f"c0" in prompt_lower or f"b0" in prompt_lower or
                          f"u0" in prompt_lower for _ in [1])

        if any(kw in prompt_lower for kw in fault_keywords) or code_pattern:
            return self._mock_fault_code_response(context)
        elif any(kw in prompt_lower for kw in ["summary", "health", "status", "overview", "how is my", "check my"]):
            return self._mock_summary_response(context)
        elif "rpm" in prompt_lower or "revolution" in prompt_lower:
            return self._mock_metric_response("engine_rpm", context)
        elif "coolant" in prompt_lower or "temperature" in prompt_lower or "overheating" in prompt_lower:
            return self._mock_metric_response("coolant_temp", context)
        elif "speed" in prompt_lower or "mph" in prompt_lower or "kph" in prompt_lower:
            return self._mock_metric_response("vehicle_speed", context)
        elif "battery" in prompt_lower or "voltage" in prompt_lower:
            return self._mock_battery_response(context)
        elif "fuel" in prompt_lower or "gas" in prompt_lower or "mileage" in prompt_lower:
            return self._mock_fuel_response(context)
        else:
            return self._mock_general_response(prompt, context)

    def _mock_summary_response(self, context: str) -> str:
        """Generate context-aware summary response."""
        # Parse context to determine actual status
        has_critical = "🔴" in context or "(critical)" in context.lower() if context else False
        has_warning = "🟡" in context or "(warning)" in context.lower() if context else False
        has_faults = "FAULT CODES:" in context and "None detected" not in context if context else False

        if has_critical:
            status = "Needs Immediate Attention"
            status_emoji = "🔴"
            status_detail = "Critical issues were detected that require prompt attention."
        elif has_warning:
            status = "Needs Attention"
            status_emoji = "🟡"
            status_detail = "Some readings are outside normal ranges and should be monitored."
        else:
            status = "Generally Good"
            status_emoji = "🟢"
            status_detail = "Your vehicle appears to be running within normal parameters."

        response = f"""Based on the OBD-II data from your vehicle, here's a summary of your vehicle's health:

**Overall Status: {status_emoji} {status}**

{status_detail}

**Key Findings:**
"""
        if has_critical:
            response += """- ⚠️ Critical readings detected - see details below
- Recommend having vehicle inspected soon
"""
        if has_warning:
            response += """- Some metrics are showing warning-level values
- Monitor these readings and consider service if they persist
"""
        if has_faults:
            response += """- Fault codes are present in the system
- Ask me about "fault codes" for detailed explanations
"""
        if not has_critical and not has_warning and not has_faults:
            response += """- Engine performance metrics are within normal ranges
- No fault codes detected
- Temperature readings are normal
"""

        response += """
**Recommendations:**
"""
        if has_critical:
            response += """- Have vehicle inspected by a professional soon
- Avoid long trips until issues are diagnosed
- Monitor for any unusual sounds or behavior
"""
        elif has_warning:
            response += """- Schedule a maintenance check when convenient
- Continue monitoring the warning indicators
- Keep an eye on your dashboard warning lights
"""
        else:
            response += """- Continue with regular maintenance schedule
- Monitor any warning lights that may appear
- Your vehicle is performing well!
"""

        response += """
Is there a specific aspect of your vehicle's diagnostics you'd like me to explain in more detail?"""

        return response

    def _mock_fault_code_response(self, context: str) -> str:
        """Generate context-aware fault code response."""
        # Check if there are actual fault codes in the context
        has_faults = "FAULT CODES:" in context and "None detected" not in context if context else False

        if has_faults:
            # Extract fault code info from context if available
            response = """**Fault Code Analysis**

Based on your vehicle's diagnostic data, fault codes have been detected.

**Understanding Fault Codes:**
Fault codes (also called DTCs - Diagnostic Trouble Codes) are stored by your vehicle's computer when it detects a problem. They follow a standard format:

- **P codes** - Powertrain (engine, transmission)
- **C codes** - Chassis (ABS, steering)
- **B codes** - Body (airbags, A/C)
- **U codes** - Network (communication issues)

**Severity Levels:**
- 🔴 **Critical** - Should be addressed immediately
- 🟡 **Warning** - Schedule service soon
- 🟢 **Minor** - Monitor but not urgent

**Recommendations:**
1. Note down any codes shown in your data
2. Research the specific code meanings
3. Consider having a mechanic diagnose the root cause
4. Don't ignore persistent check engine lights

Would you like me to explain a specific fault code? Just ask about it by name (e.g., "What does P0300 mean?")."""
        else:
            response = """**Fault Code Analysis**

Great news! **No active fault codes** were detected in your vehicle's diagnostic data.

**What This Means:**
✅ The engine management system hasn't flagged any problems
✅ All monitored systems are operating within acceptable parameters
✅ No pending diagnostic trouble codes (DTCs)

**Important Notes:**
- This doesn't guarantee everything is perfect mechanically
- Some issues may not trigger fault codes
- Cleared codes won't show until the issue recurs

**Recommendations:**
- Continue regular maintenance schedule
- If your check engine light comes on, have it scanned promptly
- Pay attention to any unusual sounds, smells, or performance changes

**Want to know more?**
Ask me about your vehicle's health summary or specific sensor readings!"""

        return response

    def _mock_metric_response(self, metric: str, context: str) -> str:
        metrics_info = {
            "engine_rpm": """**Engine RPM Analysis**

Your engine RPM (Revolutions Per Minute) reading shows normal operation:

- **Current Reading:** Within normal range
- **Normal Idle Range:** 600-1000 RPM
- **Normal Driving Range:** 1500-4000 RPM

**What RPM Tells You:**
RPM indicates how fast your engine is spinning. Consistent, smooth RPM readings suggest your engine is running properly.

Your reading appears normal. Is there anything specific about engine performance you'd like to know?""",

            "coolant_temp": """**Coolant Temperature Analysis**

Your engine coolant temperature reading is within the normal operating range:

- **Normal Operating Range:** 195-220°F (90-105°C)

**What This Means:**
Your cooling system appears to be functioning correctly. The thermostat is regulating temperature properly.

**Recommendations:**
- Ensure coolant level is checked periodically
- Have cooling system inspected during routine maintenance

Any questions about your vehicle's cooling system?""",

            "vehicle_speed": """**Vehicle Speed Sensor Analysis**

Your vehicle speed sensor (VSS) readings appear normal:

- **Function:** Measures how fast your vehicle is traveling
- **Uses:** Speedometer, transmission shifting, cruise control, ABS

**Current Status:** Operating correctly

Your speed sensor data looks good. Let me know if you have any other questions!"""
        }
        return metrics_info.get(metric, self._mock_general_response(metric))

    def _mock_battery_response(self, context: str) -> str:
        """Generate mock battery response."""
        return """**Battery & Electrical System Analysis**

Based on your vehicle's diagnostic data:

**Current Status:** Normal Operation

- **Battery Voltage:** Within acceptable range (typically 12.4-12.7V when off, 13.7-14.7V when running)
- **Charging System:** Alternator appears to be functioning properly

**What This Means:**
Your vehicle's electrical system is operating within normal parameters. The battery is holding charge and the alternator is providing adequate power.

**Tips for Battery Health:**
- Have battery tested if vehicle is slow to start
- Check terminals for corrosion periodically
- Most batteries last 3-5 years

Would you like me to explain any specific electrical readings?"""

    def _mock_fuel_response(self, context: str) -> str:
        """Generate mock fuel system response."""
        return """**Fuel System Analysis**

Based on your vehicle's OBD-II data:

**Current Status:** Operating Normally

**Key Readings:**
- **Fuel System:** Closed loop operation (normal)
- **Fuel Trim:** Within acceptable range
- **Fuel Pressure:** Normal operating pressure

**What This Means:**
Your fuel system is functioning correctly. The engine is receiving the proper air-fuel mixture for efficient combustion.

**Fuel Efficiency Tips:**
- Maintain proper tire pressure
- Replace air filter as recommended
- Use the recommended fuel grade for your vehicle

Any specific fuel-related concerns you'd like me to address?"""

    def _mock_general_response(self, prompt: str, context: str = "") -> str:
        """Generate context-aware general response."""
        # Parse context to provide more relevant response
        has_metrics = "VEHICLE METRICS:" in context if context else False
        has_faults = "FAULT CODES:" in context and "None detected" not in context if context else False

        response = f"""Thank you for your question: "{prompt[:50]}{'...' if len(prompt) > 50 else ''}"

Based on your vehicle's OBD-II diagnostic data, here's what I can tell you:

"""
        if has_metrics:
            response += """**Available Data:**
Your uploaded diagnostic file contains vehicle sensor readings that I can analyze. I can help you understand:
- Engine performance metrics (RPM, load, temperatures)
- Emission system readings
- Fuel system status
- Various sensor values

"""
        if has_faults:
            response += """**Fault Codes Detected:**
Your vehicle has diagnostic trouble codes stored. Ask me about "fault codes" for a detailed explanation.

"""
        elif context:
            response += """**Good News:**
No fault codes were detected in your diagnostic data.

"""

        response += """**How I Can Help:**
Try asking me specific questions like:
- "What's my vehicle health summary?"
- "Explain my RPM readings"
- "What does my coolant temperature mean?"
- "Are there any fault codes?"

**Note:** I'm currently running in demo mode. For full AI-powered analysis, the local Granite model needs to be installed.

What would you like to know about your vehicle?"""

        return response
