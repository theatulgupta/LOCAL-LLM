"""Tests for API routes"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import create_app
from app.models import QueryRequest


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Local LLM Server Running 🚀"
    assert "version" in response.json()


def test_health_check(client):
    """Test health check endpoint"""
    with patch("app.routes.llm.get_ollama_service") as mock_service:
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = True
        mock_service.return_value = mock_instance

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["ollama_status"] == "healthy"


def test_health_check_ollama_unhealthy(client):
    """Test health check when Ollama is unhealthy"""
    with patch("app.routes.llm.get_ollama_service") as mock_service:
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = False
        mock_service.return_value = mock_instance

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["ollama_status"] == "unhealthy"


def test_list_models(client):
    """Test list models endpoint"""
    with patch("app.routes.llm.get_ollama_service") as mock_service:
        mock_instance = MagicMock()
        mock_instance.list_models.return_value = ["llama3", "mistral"]
        mock_service.return_value = mock_instance

        response = client.get("/api/models")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert "llama3" in data["models"]
        assert "mistral" in data["models"]


def test_ask_llm_valid_request(client):
    """Test asking LLM with valid request"""
    with patch("app.routes.llm.get_ollama_service") as mock_service:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = {
            "response": "This is a test response",
            "total_duration": 1000000000,
            "load_duration": 500000000
        }
        mock_service.return_value = mock_instance

        query = {
            "prompt": "What is machine learning?",
            "model": "llama3"
        }

        response = client.post("/api/ask", json=query)

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "This is a test response"
        assert data["model"] == "llama3"
        assert data["prompt"] == "What is machine learning?"


def test_ask_llm_empty_prompt(client):
    """Test asking LLM with empty prompt"""
    query = {
        "prompt": "",
        "model": "llama3"
    }

    response = client.post("/api/ask", json=query)

    assert response.status_code == 422  # Validation error


def test_ask_llm_missing_prompt(client):
    """Test asking LLM without prompt"""
    query = {
        "model": "llama3"
    }

    response = client.post("/api/ask", json=query)

    assert response.status_code == 422  # Validation error


def test_ask_llm_ollama_connection_error(client):
    """Test asking LLM when Ollama is unavailable"""
    with patch("app.routes.llm.get_ollama_service") as mock_service:
        from app.utils.exceptions import OllamaConnectionError

        mock_instance = MagicMock()
        mock_instance.generate.side_effect = OllamaConnectionError(
            "Unable to connect to Ollama server"
        )
        mock_service.return_value = mock_instance

        query = {
            "prompt": "What is X?",
            "model": "llama3"
        }

        response = client.post("/api/ask", json=query)

        assert response.status_code == 503


def test_rate_limiting(client):
    """Test rate limiting functionality"""
    with patch("app.middleware.rate_limit.get_rate_limiter") as mock_limiter:
        from app.utils.exceptions import RateLimitExceededError

        mock_instance = MagicMock()
        # Simulate exceeding rate limit on 3rd request
        mock_instance.is_allowed.side_effect = [True, True, RateLimitExceededError()]
        mock_limiter.return_value = mock_instance

        query = {"prompt": "Test"}

        # First two requests should work
        with patch("app.routes.llm.get_ollama_service") as mock_service:
            mock_service.return_value.generate.return_value = {"response": "test"}
            response1 = client.post("/api/ask", json=query)
            response2 = client.post("/api/ask", json=query)

        # Third should be rate limited
        response3 = client.post("/api/ask", json=query)
        assert response3.status_code == 429


def test_query_validation_temperature(client):
    """Test temperature parameter validation"""
    query = {
        "prompt": "Test",
        "temperature": 3.0  # Should be 0.0-2.0
    }

    response = client.post("/api/ask", json=query)
    assert response.status_code == 422


def test_query_validation_top_p(client):
    """Test top_p parameter validation"""
    query = {
        "prompt": "Test",
        "top_p": 1.5  # Should be 0.0-1.0
    }

    response = client.post("/api/ask", json=query)
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
