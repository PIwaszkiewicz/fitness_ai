"""Testy endpointu klasyfikacji sprawności profilu."""

import json

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
    assert result["data_completeness"] == 56  # 5 z 9 pytań opcjonalnych


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


OPTIONAL_ANSWERS = ["training_experience", "pushups", "squats", "plank_seconds", "resting_heart_rate"]
BEST = {"0": "decision_tree", "1": "mlp", "2": "mlp", "3": "mlp", "4": "mlp", "5": "rules"}


@pytest.mark.parametrize("n_missing", range(6))
def test_klasyfikator_zalezy_od_liczby_pustych_odpowiedzi(client, trained_models, n_missing):
    predictor.best_classifier_path().write_text(json.dumps({"best_by_missing_answers": BEST}))
    skipped = OPTIONAL_ANSWERS[:n_missing]
    answers = {key: value for key, value in PROFILE.items() if key not in skipped}
    profile_id = client.post("/api/v1/profiles", json=answers).json()["id"]
    assert client.get(url(profile_id)).json()["method"] == BEST[str(n_missing)]


def test_bez_oceny_modeli_uzywany_jest_system_regulowy(client, profile_id, tmp_path, monkeypatch):
    monkeypatch.setattr(predictor, "ARTIFACTS_DIR", tmp_path)  # brak best_classifier.json
    assert client.get(url(profile_id)).json()["method"] == "rules"


def test_wynik_zawiera_uzasadnienie_wyboru_klasyfikatora(client, trained_models):
    metrics = {"mlp": {"f1_macro": 0.9, "accuracy": 0.9}, "rules": {"f1_macro": 0.8, "accuracy": 0.8}}
    predictor.best_classifier_path().write_text(json.dumps({
        "best_by_missing_answers": {str(n): "mlp" for n in range(6)},
        "metrics_by_missing_answers": {str(n): metrics for n in range(6)},
    }))
    answers = {key: value for key, value in PROFILE.items() if key not in ("squats", "plank_seconds")}
    profile_id = client.post("/api/v1/profiles", json=answers).json()["id"]
    result = client.get(url(profile_id)).json()
    assert result["missing_answers"] == 2  # przysiady i deska
    assert result["selection_scores"] == {"mlp": 0.9, "rules": 0.8}


def test_bez_oceny_modeli_brak_uzasadnienia(client, profile_id, tmp_path, monkeypatch):
    monkeypatch.setattr(predictor, "ARTIFACTS_DIR", tmp_path)
    result = client.get(url(profile_id)).json()
    assert result["selection_scores"] is None
    assert result["missing_answers"] == 0
