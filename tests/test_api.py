"""Tests for the FastAPI application"""

import os
import pytest
from fastapi.testclient import TestClient

# Set environment variable to force Lambda mode for tests
os.environ["METROLINK_MODE"] = "lambda"

from metrolinkTimes.api import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns expected paths"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "debug/" in data["paths"]
    assert "health/" in data["paths"]
    assert "station/" in data["paths"]


def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    # Note: This will return 503 if the service hasn't initialized yet
    # since we don't have the TfGM API key configured in tests
    assert response.status_code in [200, 503]
    if response.status_code == 503:
        assert "not yet initialized" in response.json()["detail"] or "not updating" in response.json()["detail"]


def test_station_list_endpoint():
    """Test the station list endpoint"""
    response = client.get("/station/")
    # In test environment without API key, expect 503
    # In production with API key, expect 200
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "stations" in data
        assert isinstance(data["stations"], list)
    else:
        # 503 response should have error detail about API key
        data = response.json()
        assert "detail" in data
        assert "TfGM API" in data["detail"] or "API key" in data["detail"]


def test_debug_endpoint():
    """Test the debug endpoint"""
    response = client.get("/debug/")
    # In test environment without TramGraph (Lambda mode), debug endpoint
    # should not be available or should return appropriate error
    assert response.status_code in [200, 503, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "missingAverages" in data
        assert "trams" in data


def test_openapi_docs():
    """Test that OpenAPI docs are available"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200