"""Testy endpointu klasyfikacji sprawności profilu."""

import pytest

from app.ml import predictor

PROFILE = {
    "age": 28,
    "gender": "male",
    "height_cm": 180,
    "weight_kg": 75,
    "training_goal": "strength",
    "activity_level": "active",
    "training_experience": "more_than_3_years",
    "pushups": 45,
    "squats": 50,
    "plank_seconds": 200,
    "resting_heart_rate": 55,
}


@pytest.fixture
def profile_id(client):
    return client.post("/api/v1/profiles", json=PROFILE).json()["id"]


def url(profile_id: int) -> str:
    return f"/api/v1/profiles/{profile_id}/fitness-level"


def test_system_regulowy_dziala_bez_wytrenowanych_modeli(client, profile_id):
    response = client.get(url(profile_id), params={"method": "rules"})
    assert response.status_code == 200
    result = response.json()
    assert result["level"] == "advanced"
    assert result["probabilities"] is None
    assert result["data_completeness"] == 62  # 5 z 8 pytań opcjonalnych


@pytest.mark.parametrize("method", ["decision_tree", "mlp"])
def test_modele_ml_zwracaja_poziom_i_prawdopodobienstwa(client, profile_id, trained_models, method):
    result = client.get(url(profile_id), params={"method": method}).json()
    assert result["method"] == method
    assert result["level"] == "advanced"
    assert set(result["probabilities"]) == {"beginner", "intermediate", "advanced"}
    assert sum(result["probabilities"].values()) == pytest.approx(1, abs=0.01)


def test_brak_modelu_zwraca_503(client, profile_id, tmp_path, monkeypatch):
    monkeypatch.setattr(predictor, "ARTIFACTS_DIR", tmp_path)  # pusty katalog
    predictor.load_classifier.cache_clear()
    response = client.get(url(profile_id), params={"method": "mlp"})
    predictor.load_classifier.cache_clear()
    assert response.status_code == 503


def test_nieznana_metoda_zwraca_422(client, profile_id):
    assert client.get(url(profile_id), params={"method": "magia"}).status_code == 422


def test_nieistniejacy_profil_zwraca_404(client):
    assert client.get(url(999), params={"method": "rules"}).status_code == 404
