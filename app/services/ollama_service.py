"""Ollama service for interacting with Ollama API"""

import requests
import logging
from typing import Optional, Iterator, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import get_settings
from app.utils.exceptions import OllamaConnectionError, OllamaError
from app.utils.logger import log_ollama_call

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for communicating with Ollama API"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_host
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _is_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except (requests.RequestException, Exception):
            return False

    def health_check(self) -> bool:
        """Health check for Ollama server"""
        return self._is_ollama_running()

    def generate(
        self,
        prompt: str,
        model: str = "llama3",
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        num_predict: int = 128,
        stream: bool = False
    ) -> Dict[str, Any] | Iterator[Dict[str, Any]]:
        """
        Generate response from Ollama model

        Args:
            prompt: The prompt to generate response for
            model: Model name
            temperature: Sampling temperature
            top_p: Top-p sampling
            top_k: Top-k sampling
            num_predict: Number of tokens to predict
            stream: Whether to stream response

        Returns:
            Generated response or iterator for streaming

        Raises:
            OllamaConnectionError: If unable to connect to Ollama
            OllamaError: If Ollama returns an error
        """
        if not self.health_check():
            logger.error("Ollama server is not running")
            raise OllamaConnectionError(
                "Ollama server is not accessible at " + self.base_url
            )

        log_ollama_call(logger, model, len(prompt))

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "num_predict": num_predict,
            "stream": stream
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.settings.ollama_timeout,
                stream=stream
            )
            response.raise_for_status()

            if stream:
                return self._handle_streaming_response(response)
            else:
                return response.json()

        except requests.Timeout:
            error_msg = f"Ollama request timed out (timeout: {self.settings.ollama_timeout}s)"
            logger.error(error_msg)
            raise OllamaError(error_msg)
        except requests.RequestException as e:
            error_msg = f"Ollama request failed: {str(e)}"
            logger.error(error_msg)
            raise OllamaConnectionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during Ollama call: {str(e)}"
            logger.error(error_msg)
            raise OllamaError(error_msg)

    def _handle_streaming_response(self, response: requests.Response) -> Iterator[Dict[str, Any]]:
        """Handle streaming response from Ollama"""
        try:
            for line in response.iter_lines():
                if line:
                    yield response.json() if hasattr(response, 'json') else {}
        except Exception as e:
            logger.error(f"Error handling streaming response: {e}")
            raise OllamaError(f"Error during streaming: {str(e)}")

    def list_models(self) -> list:
        """List available models in Ollama"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            logger.info(f"Retrieved {len(models)} models from Ollama")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create Ollama service instance"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
