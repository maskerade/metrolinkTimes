"""Tests for the FastAPI application"""

import pytest
from fastapi.testclient import TestClient

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
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data
    assert isinstance(data["stations"], list)


def test_debug_endpoint():
    """Test the debug endpoint"""
    response = client.get("/debug/")
    assert response.status_code == 200
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