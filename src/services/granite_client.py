"""
IBM Granite API Client via watsonx.ai.
Core integration for natural language generation.
"""

from typing import Optional, List, Dict, Any
import os

from ..config.settings import get_settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)

# Try to import IBM watsonx libraries
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    HAS_WATSONX = True
except ImportError:
    HAS_WATSONX = False
    logger.warning("ibm-watsonx-ai not installed. Using mock client.")

try:
    from langchain_ibm import ChatWatsonx, WatsonxEmbeddings
    HAS_LANGCHAIN_IBM = True
except ImportError:
    HAS_LANGCHAIN_IBM = False
    logger.warning("langchain-ibm not installed. Some features may be limited.")


class GraniteClient:
    """
    Client for IBM Granite models via watsonx.ai.

    Provides:
    - Text generation for chat responses
    - Embeddings for RAG pipeline
    - Streaming support for real-time responses
    """

    def __init__(self):
        """Initialize the Granite client."""
        self.settings = get_settings()
        self._chat_model = None
        self._embeddings = None
        self._api_client = None
        self._initialized = False

        # Validate configuration
        is_valid, errors = self.settings.validate()
        if not is_valid:
            logger.warning(f"Configuration incomplete: {errors}")
            logger.info("Running in demo mode with mock responses")

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        is_valid, _ = self.settings.validate()
        return is_valid and HAS_WATSONX

    def initialize(self) -> bool:
        """
        Initialize the API client and models.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        if not self.is_configured:
            logger.warning("Granite client not configured. Using mock mode.")
            return False

        try:
            # Initialize API client
            credentials = Credentials(
                url=self.settings.watsonx_url,
                api_key=self.settings.watsonx_api_key
            )
            self._api_client = APIClient(credentials)

            # Initialize chat model using LangChain integration
            if HAS_LANGCHAIN_IBM:
                self._chat_model = ChatWatsonx(
                    model_id=self.settings.granite_chat_model,
                    url=self.settings.watsonx_url,
                    apikey=self.settings.watsonx_api_key,
                    project_id=self.settings.watsonx_project_id,
                    params=self.settings.generation_params
                )

                self._embeddings = WatsonxEmbeddings(
                    model_id=self.settings.granite_embedding_model,
                    url=self.settings.watsonx_url,
                    apikey=self.settings.watsonx_api_key,
                    project_id=self.settings.watsonx_project_id
                )

            self._initialized = True
            logger.info("Granite client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Granite client: {e}")
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
        if not self.is_configured:
            return self._mock_response(prompt, context)

        if not self._initialized:
            self.initialize()

        try:
            # Build the full prompt
            full_prompt = self._build_prompt(prompt, context, system_prompt)

            if self._chat_model:
                response = self._chat_model.invoke(full_prompt)
                return response.content
            else:
                # Fallback to direct API call
                return self._generate_direct(full_prompt)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again. (Error: {str(e)})"

    def generate_streaming(self, prompt: str, context: str = ""):
        """
        Generate a streaming response.

        Args:
            prompt: User's input prompt
            context: Additional context

        Yields:
            Response text chunks
        """
        if not self.is_configured:
            # Mock streaming
            response = self._mock_response(prompt, context)
            for word in response.split():
                yield word + " "
            return

        if not self._initialized:
            self.initialize()

        try:
            full_prompt = self._build_prompt(prompt, context)

            if self._chat_model:
                for chunk in self._chat_model.stream(full_prompt):
                    if hasattr(chunk, 'content'):
                        yield chunk.content

        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not self.is_configured or not self._embeddings:
            # Return mock embeddings (random-ish but deterministic)
            return [[hash(t) % 100 / 100.0 for _ in range(384)] for t in texts]

        if not self._initialized:
            self.initialize()

        try:
            return self._embeddings.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return [[0.0] * 384 for _ in texts]

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings else [0.0] * 384

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

Remember: Your responses will be color-coded based on severity:
- Red (Critical): Immediate attention required
- Amber (Warning): Should be addressed soon
- Green (Normal): No immediate concern"""

    def _generate_direct(self, prompt: str) -> str:
        """Generate response using direct API call."""
        if not self._api_client:
            return self._mock_response(prompt, "")

        try:
            model = ModelInference(
                model_id=self.settings.granite_chat_model,
                api_client=self._api_client,
                project_id=self.settings.watsonx_project_id,
                params=self.settings.generation_params
            )
            response = model.generate_text(prompt)
            return response
        except Exception as e:
            logger.error(f"Direct generation failed: {e}")
            raise

    def _mock_response(self, prompt: str, context: str) -> str:
        """Generate a mock response for demo mode."""
        prompt_lower = prompt.lower()

        # Check for specific types of questions
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
        """Generate mock summary response."""
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
        """Generate mock fault code response."""
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

Would you like me to explain what types of issues would trigger fault codes, or do you have questions about a specific system?"""

    def _mock_metric_response(self, metric: str, context: str) -> str:
        """Generate mock response for specific metrics."""
        metrics_info = {
            "engine_rpm": """**Engine RPM Analysis**

Your engine RPM (Revolutions Per Minute) reading shows normal operation:

- **Current Reading:** Within normal range
- **Normal Idle Range:** 600-1000 RPM
- **Normal Driving Range:** 1500-4000 RPM

**What RPM Tells You:**
RPM indicates how fast your engine is spinning. Consistent, smooth RPM readings suggest your engine is running properly.

**Signs of Problems:**
- Erratic RPM at idle (could indicate vacuum leak or sensor issue)
- RPM too high at idle (possible throttle or IAC valve issue)
- RPM too low (could cause stalling)

Your reading appears normal. Is there anything specific about engine performance you'd like to know?""",

            "coolant_temp": """**Coolant Temperature Analysis**

Your engine coolant temperature reading is within the normal operating range:

- **Normal Operating Range:** 195-220°F (90-105°C)
- **Warm-Up Period:** Temperature rises from cold to operating range

**What This Means:**
Your cooling system appears to be functioning correctly. The thermostat is regulating temperature properly, and there's no indication of overheating.

**Warning Signs to Watch:**
- Temperature consistently too high (overheating risk)
- Temperature too low (thermostat may be stuck open)
- Rapid temperature fluctuations (possible coolant issues)

**Recommendations:**
- Ensure coolant level is checked periodically
- Have cooling system inspected during routine maintenance

Any questions about your vehicle's cooling system?""",

            "vehicle_speed": """**Vehicle Speed Sensor Analysis**

Your vehicle speed sensor (VSS) readings appear normal:

- **Function:** Measures how fast your vehicle is traveling
- **Uses:** Speedometer, transmission shifting, cruise control, ABS

**Current Status:** Operating correctly

**Signs of VSS Problems:**
- Erratic speedometer readings
- Transmission shifting issues
- Cruise control not working
- ABS warning light

Your speed sensor data looks good. Let me know if you have any other questions!"""
        }

        return metrics_info.get(metric, self._mock_general_response(metric))

    def _mock_general_response(self, prompt: str) -> str:
        """Generate mock general response."""
        return f"""Thank you for your question about your vehicle.

Based on the OBD-II diagnostic data available, I can help you understand your vehicle's condition.

To give you the most accurate information, I'm analyzing the data from your uploaded log file. The OBD-II system monitors many aspects of your vehicle including:

- Engine performance and emissions
- Fuel system operation
- Ignition system
- Transmission (if applicable)
- Various sensors throughout the vehicle

Is there a specific aspect of your vehicle's diagnostics you'd like me to focus on? For example:
- Overall vehicle health summary
- Specific fault codes explanation
- Particular sensor readings
- Maintenance recommendations

Please let me know how I can help you better understand your vehicle's condition!"""
