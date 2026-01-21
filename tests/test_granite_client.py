"""
Tests for the GraniteClient service.
Tests AI integration, caching, and retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.services.granite_client import GraniteClient, ResponseCache, retry_with_backoff


class TestResponseCache:
    """Tests for the ResponseCache class."""

    def test_cache_initialization(self):
        """Test cache initializes correctly."""
        cache = ResponseCache(max_size=50, default_ttl=1800)
        assert cache.max_size == 50
        assert cache.default_ttl == 1800
        assert cache.size() == 0

    def test_cache_set_and_get(self):
        """Test setting and getting cached values."""
        cache = ResponseCache()

        cache.set("prompt", "context", "response", ttl=3600)
        result = cache.get("prompt", "context")

        assert result == "response"

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = ResponseCache()

        result = cache.get("nonexistent", "context")

        assert result is None

    def test_cache_different_keys(self):
        """Test different prompts have different cache entries."""
        cache = ResponseCache()

        cache.set("prompt1", "context", "response1")
        cache.set("prompt2", "context", "response2")

        assert cache.get("prompt1", "context") == "response1"
        assert cache.get("prompt2", "context") == "response2"
        assert cache.size() == 2

    def test_cache_eviction(self):
        """Test oldest entries are evicted when cache is full."""
        cache = ResponseCache(max_size=2)

        cache.set("prompt1", "context", "response1")
        cache.set("prompt2", "context", "response2")
        cache.set("prompt3", "context", "response3")  # Should evict prompt1

        assert cache.size() == 2
        assert cache.get("prompt3", "context") == "response3"

    def test_cache_clear(self):
        """Test clearing the cache."""
        cache = ResponseCache()

        cache.set("prompt", "context", "response")
        cache.clear()

        assert cache.size() == 0
        assert cache.get("prompt", "context") is None

    def test_cache_with_system_prompt(self):
        """Test cache distinguishes system prompts."""
        cache = ResponseCache()

        cache.set("prompt", "context", "response1", system_prompt="sys1")
        cache.set("prompt", "context", "response2", system_prompt="sys2")

        assert cache.get("prompt", "context", "sys1") == "response1"
        assert cache.get("prompt", "context", "sys2") == "response2"


class TestRetryDecorator:
    """Tests for the retry_with_backoff decorator."""

    def test_retry_on_exception(self):
        """Test function retries on specified exceptions."""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.RequestException("Network error")
            return "success"

        result = failing_function()

        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """Test exception raised after all retries exhausted."""
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_failing():
            raise requests.exceptions.RequestException("Always fails")

        with pytest.raises(requests.exceptions.RequestException):
            always_failing()

    def test_no_retry_on_success(self):
        """Test function doesn't retry on success."""
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def succeeding_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeeding_function()

        assert result == "success"
        assert call_count == 1

    def test_no_retry_on_non_retryable_exception(self):
        """Test function doesn't retry on non-retryable exceptions."""
        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.01,
            retryable_exceptions=(ValueError,)
        )
        def raises_type_error():
            raise TypeError("Not retryable")

        with pytest.raises(TypeError):
            raises_type_error()


class TestGraniteClient:
    """Tests for the GraniteClient class."""

    def test_client_initialization(self):
        """Test client initializes with default settings."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        assert client.ollama_model == "granite3.3:2b"
        assert client._cache is not None

    def test_client_with_cache_disabled(self):
        """Test client can be initialized with cache disabled."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient(enable_cache=False)

        assert client._cache is None

    def test_client_with_custom_model(self):
        """Test client accepts custom model."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient(ollama_model="granite3.3:8b")

        assert client.ollama_model == "granite3.3:8b"

    def test_is_configured_with_ollama(self):
        """Test is_configured returns True when Ollama is available."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=True):
            client = GraniteClient()

        assert client.is_configured is True
        assert client.is_using_ollama is True

    def test_mock_response_for_summary(self):
        """Test mock response for summary queries."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        response = client._mock_response("Give me a health summary", "context")

        assert "status" in response.lower() or "summary" in response.lower()

    def test_mock_response_for_fault_code(self):
        """Test mock response for fault code queries."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        response = client._mock_response("What is fault code P0300?", "context")

        assert "fault" in response.lower() or "code" in response.lower()

    def test_mock_response_for_rpm(self):
        """Test mock response for RPM queries."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        response = client._mock_response("What is the RPM reading?", "context")

        assert "rpm" in response.lower()

    def test_generate_response_uses_cache(self):
        """Test generate_response uses cache when available."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        # First call
        response1 = client.generate_response("test prompt", "context")

        # Second call should use cache
        response2 = client.generate_response("test prompt", "context")

        assert response1 == response2

    def test_generate_response_bypasses_cache(self):
        """Test generate_response can bypass cache."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        # Pre-populate cache
        client._cache.set("test prompt", "context", "cached response")

        # Call with use_cache=False
        response = client.generate_response("test prompt", "context", use_cache=False)

        # Should not return cached response
        assert response != "cached response"

    def test_clear_cache(self):
        """Test clearing the cache."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        client._cache.set("prompt", "context", "response")
        client.clear_cache()

        assert client._cache.size() == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        client._cache.set("prompt", "context", "response")
        stats = client.get_cache_stats()

        assert stats["enabled"] is True
        assert stats["size"] == 1

    def test_get_cache_stats_when_disabled(self):
        """Test cache stats when cache is disabled."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient(enable_cache=False)

        stats = client.get_cache_stats()

        assert stats["enabled"] is False

    def test_default_system_prompt(self):
        """Test default system prompt is generated correctly."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        prompt = client._get_default_system_prompt()

        assert "OBD InsightBot" in prompt
        assert "diagnostic" in prompt.lower()

    def test_build_prompt(self):
        """Test prompt building with context."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        full_prompt = client._build_prompt(
            "What is my vehicle status?",
            "Engine RPM: 2500",
            "You are a helpful assistant."
        )

        assert "You are a helpful assistant." in full_prompt
        assert "Engine RPM: 2500" in full_prompt
        assert "What is my vehicle status?" in full_prompt

    @patch('requests.get')
    def test_check_ollama_available_success(self, mock_get):
        """Test Ollama availability check when available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "granite3.3:2b"}]}
        mock_get.return_value = mock_response

        client = GraniteClient()

        assert client._use_ollama is True

    @patch('requests.get')
    def test_check_ollama_available_failure(self, mock_get):
        """Test Ollama availability check when not available."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        client = GraniteClient()

        assert client._use_ollama is False

    @patch('requests.get')
    def test_list_available_models(self, mock_get):
        """Test listing available Ollama models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "granite3.3:2b"},
                {"name": "llama2:7b"}
            ]
        }
        mock_get.return_value = mock_response

        with patch.object(GraniteClient, '_check_ollama_available', return_value=True):
            client = GraniteClient()

        models = client.list_available_models()

        assert "granite3.3:2b" in models
        assert "llama2:7b" in models

    def test_get_embeddings_mock(self):
        """Test embeddings returns deterministic mock when no backend available."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        embeddings = client.get_embeddings(["test text"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384  # Default embedding dimension

    def test_get_embedding_single(self):
        """Test getting embedding for single text."""
        with patch.object(GraniteClient, '_check_ollama_available', return_value=False):
            client = GraniteClient()

        embedding = client.get_embedding("test text")

        assert len(embedding) == 384


class TestGraniteClientWithOllama:
    """Tests for GraniteClient with mocked Ollama backend."""

    @patch('requests.post')
    @patch('requests.get')
    def test_generate_ollama_success(self, mock_get, mock_post):
        """Test successful Ollama generation."""
        # Mock availability check
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": [{"name": "granite3.3:2b"}]}
        )

        # Mock generation
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"message": {"content": "Generated response"}}
        )

        client = GraniteClient()
        response = client.generate_response("test prompt", use_cache=False)

        assert response == "Generated response"

    @patch('requests.post')
    @patch('requests.get')
    def test_generate_ollama_timeout(self, mock_get, mock_post):
        """Test Ollama timeout handling."""
        # Mock availability check
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": [{"name": "granite3.3:2b"}]}
        )

        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout()

        client = GraniteClient()
        response = client.generate_response("test prompt", use_cache=False)

        assert "timed out" in response.lower()

    @patch('requests.post')
    @patch('requests.get')
    def test_ollama_embeddings_success(self, mock_get, mock_post):
        """Test successful Ollama embeddings."""
        # Mock availability check
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": [{"name": "granite3.3:2b"}]}
        )

        # Mock embeddings
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"embedding": [0.1] * 384}
        )

        client = GraniteClient()
        embeddings = client.get_embeddings(["test"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384
