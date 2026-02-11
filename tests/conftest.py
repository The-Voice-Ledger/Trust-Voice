"""
Shared pytest fixtures for TrustVoice tests.
"""
import os
import pytest


@pytest.fixture
def base_url():
    """Base URL for the running FastAPI server."""
    host = os.getenv("APP_HOST", "localhost")
    port = os.getenv("APP_PORT", "8001")
    return f"http://{host}:{port}"
