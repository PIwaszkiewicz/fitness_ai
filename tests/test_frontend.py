"""Testy serwowania frontendu przez FastAPI."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_strona_glowna():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Fitness AI</title>" in response.text
    assert '<script src="/static/app.js">' in response.text


def test_pliki_statyczne():
    script = client.get("/static/app.js")
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert client.get("/static/style.css").status_code == 200


def test_strona_glowna_nie_trafia_do_dokumentacji_api():
    assert "/" not in client.get("/openapi.json").json()["paths"]
