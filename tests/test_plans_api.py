"""Testy endpointu planu treningowego."""

from app.ml import predictor
from app.seed import seed_exercises

PROFILE = {
    "age": 40,
    "gender": "male",
    "height_cm": 178,
    "weight_kg": 82,
    "training_goal": "general_fitness",
    "activity_level": "light",
    "limitations": ["knee"],
    "training_days_per_week": 2,
    "available_equipment": ["dumbbells"],
}


def test_plan_z_atlasu_w_bazie(client, db_session):
    seed_exercises(db_session)
    profile_id = client.post("/api/v1/profiles", json=PROFILE).json()["id"]
    response = client.get(f"/api/v1/profiles/{profile_id}/plan", params={"method": "rules"})
    assert response.status_code == 200
    plan = response.json()
    assert plan["classifier"] == "rules"
    assert plan["days_per_week"] == 2
    assert all(day["exercises"] for day in plan["days"])
    names = {e["name"] for day in plan["days"] for e in day["exercises"]}
    assert "Wykroki z hantlami" not in names  # przeciwwskazane przy kontuzji kolana


def test_brak_modelu_ml_daje_plan_z_systemu_regulowego(client, db_session, tmp_path, monkeypatch):
    seed_exercises(db_session)
    monkeypatch.setattr(predictor, "ARTIFACTS_DIR", tmp_path)  # pusty katalog modeli
    predictor.load_classifier.cache_clear()
    profile_id = client.post("/api/v1/profiles", json=PROFILE).json()["id"]
    response = client.get(f"/api/v1/profiles/{profile_id}/plan", params={"method": "mlp"})
    predictor.load_classifier.cache_clear()
    assert response.status_code == 200
    assert response.json()["classifier"] == "rules"


def test_plan_nieistniejacego_profilu_zwraca_404(client):
    assert client.get("/api/v1/profiles/999/plan").status_code == 404
