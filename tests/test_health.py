"""Testy podstawowych endpointów: czy serwer działa i czy router v1 jest podłączony."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

# TestClient wysyła żądania do aplikacji bez uruchamiania prawdziwego serwera.
client = TestClient(app)


def test_health_zwraca_status_i_wersje():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": settings.version}


def test_ping_w_api_v1():
    response = client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
