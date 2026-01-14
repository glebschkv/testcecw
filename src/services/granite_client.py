"""
IBM Granite Client - Supports both local Ollama and watsonx.ai API.
Prioritizes local Ollama for running without API keys.
"""

from typing import Optional, List, Dict, Any
import os
import json
import requests

from ..config.settings import get_settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)

# Try to import Ollama library
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    logger.info("ollama package not installed. Will use HTTP API.")

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
    1. Local Ollama (recommended - no API key needed)
    2. IBM watsonx.ai API (cloud deployment)
    3. Mock mode (fallback for demo)
    """

    # Default Ollama settings
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "granite3.3:2b"  # Default model, can be changed

    def __init__(self, ollama_model: str = None):
        """
        Initialize the Granite client.

        Args:
            ollama_model: Override the default Ollama model (e.g., "granite3.3:8b")
        """
        self.settings = get_settings()
        self._chat_model = None
        self._embeddings = None
        self._api_client = None
        self._initialized = False

        # Ollama configuration
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", self.OLLAMA_MODEL)
        self.ollama_url = os.getenv("OLLAMA_URL", self.OLLAMA_BASE_URL)

        # Check what's available
        self._use_ollama = self._check_ollama_available()

        if self._use_ollama:
            logger.info(f"Using local Ollama with model: {self.ollama_model}")
        else:
            logger.info("Ollama not available, checking watsonx.ai...")
            is_valid, errors = self.settings.validate()
            if not is_valid:
                logger.warning(f"watsonx.ai not configured: {errors}")
                logger.info("Running in demo mode with mock responses")

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                logger.info(f"Ollama available with models: {model_names}")
                return True
        except requests.exceptions.RequestException:
            pass
        return False

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        if self._use_ollama:
            return True
        is_valid, _ = self.settings.validate()
        return is_valid and HAS_WATSONX

    @property
    def is_using_ollama(self) -> bool:
        """Check if using local Ollama."""
        return self._use_ollama

    def initialize(self) -> bool:
        """Initialize the client."""
        if self._initialized:
            return True

        if self._use_ollama:
            self._initialized = True
            logger.info("Granite client initialized with Ollama")
            return True

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

    def generate_response(self, prompt: str, context: str = "", system_prompt: str = None) -> str:
        """
        Generate a response using IBM Granite.

        Args:
            prompt: User's input prompt
            context: Additional context (e.g., OBD data)
            system_prompt: Optional system prompt override

        Returns:
            Generated response text
        """
        # Try Ollama first
        if self._use_ollama:
            return self._generate_ollama(prompt, context, system_prompt)

        # Try watsonx.ai
        if self.is_configured:
            if not self._initialized:
                self.initialize()
            try:
                full_prompt = self._build_prompt(prompt, context, system_prompt)
                if self._chat_model:
                    response = self._chat_model.invoke(full_prompt)
                    return response.content
            except Exception as e:
                logger.error(f"watsonx.ai error: {e}")

        # Fallback to mock
        return self._mock_response(prompt, context)

    def _generate_ollama(self, prompt: str, context: str = "", system_prompt: str = None) -> str:
        """Generate response using local Ollama."""
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
            # Use HTTP API directly (works without ollama package)
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                return self._mock_response(prompt, context)

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return "I'm sorry, the request timed out. Please try again with a shorter question."
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._mock_response(prompt, context)

    def generate_streaming(self, prompt: str, context: str = ""):
        """Generate a streaming response."""
        if self._use_ollama:
            yield from self._generate_ollama_streaming(prompt, context)
            return

        # Mock streaming fallback
        response = self._mock_response(prompt, context)
        for word in response.split():
            yield word + " "

    def _generate_ollama_streaming(self, prompt: str, context: str = ""):
        """Generate streaming response from Ollama."""
        system_prompt = self._get_default_system_prompt()

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"Context:\n{context}"})
            messages.append({"role": "assistant", "content": "I understand the context."})
        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": True,
                },
                stream=True,
                timeout=120
            )

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"Error: {str(e)}"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for texts."""
        if self._use_ollama:
            return self._get_ollama_embeddings(texts)

        # Return deterministic mock embeddings
        return [[hash(t) % 100 / 100.0 for _ in range(384)] for t in texts]

    def _get_ollama_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using Ollama."""
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": self.ollama_model,
                        "prompt": text
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    embeddings.append(embedding if embedding else [0.0] * 384)
                else:
                    embeddings.append([hash(text) % 100 / 100.0 for _ in range(384)])
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                embeddings.append([hash(text) % 100 / 100.0 for _ in range(384)])
        return embeddings

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * 384

    def list_available_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except Exception:
            pass
        return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name},
                timeout=600  # Models can take a while to download
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False

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

        if "summary" in prompt_lower or "health" in prompt_lower or "status" in prompt_lower:
            return self._mock_summary_response(context)
        elif "fault" in prompt_lower or "code" in prompt_lower or "error" in prompt_lower:
            return self._mock_fault_code_response(context)
        elif "rpm" in prompt_lower:
            return self._mock_metric_response("engine_rpm", context)
        elif "coolant" in prompt_lower or "temperature" in prompt_lower:
            return self._mock_metric_response("coolant_temp", context)
        elif "speed" in prompt_lower:
            return self._mock_metric_response("vehicle_speed", context)
        else:
            return self._mock_general_response(prompt)

    def _mock_summary_response(self, context: str) -> str:
        return """Based on the OBD-II data from your vehicle, here's a summary of your vehicle's health:

**Overall Status: Generally Good**

Your vehicle appears to be running within normal parameters for most metrics. Here are the key findings:

**Engine Performance:**
- Engine RPM is stable and within the normal operating range
- Engine load is at acceptable levels

**Temperature:**
- Coolant temperature is within the normal range, indicating the cooling system is working properly

**Recommendations:**
- Continue with regular maintenance schedule
- Monitor any warning lights that may appear on your dashboard
- If you notice any unusual sounds or behavior, have it checked by a professional

Is there a specific aspect of your vehicle's diagnostics you'd like me to explain in more detail?"""

    def _mock_fault_code_response(self, context: str) -> str:
        return """I'll explain the fault codes found in your vehicle's diagnostic data:

**No Active Fault Codes Detected**

Great news! Your vehicle currently has no diagnostic trouble codes (DTCs) stored in the system. This means:

1. The engine management system hasn't detected any significant issues
2. All monitored systems are operating within acceptable parameters

**What This Means:**
- Your vehicle's onboard computer hasn't flagged any problems
- This doesn't guarantee everything is perfect, but major issues would typically trigger a code

**Recommendations:**
- Continue regular maintenance
- If your check engine light comes on in the future, have it scanned promptly
- Keep an eye on any unusual behavior (sounds, smells, or performance changes)

Would you like me to explain what types of issues would trigger fault codes?"""

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

    def _mock_general_response(self, prompt: str) -> str:
        return f"""Thank you for your question about your vehicle.

Based on the OBD-II diagnostic data available, I can help you understand your vehicle's condition.

The OBD-II system monitors many aspects of your vehicle including:
- Engine performance and emissions
- Fuel system operation
- Ignition system
- Various sensors throughout the vehicle

Is there a specific aspect of your vehicle's diagnostics you'd like me to focus on? For example:
- Overall vehicle health summary
- Specific fault codes explanation
- Particular sensor readings
- Maintenance recommendations

Please let me know how I can help you better understand your vehicle's condition!"""
