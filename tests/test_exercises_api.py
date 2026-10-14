"""Testy endpointów CRUD atlasu ćwiczeń, filtrowania listy i podpowiedzi przeciwwskazań."""

from app.seed import seed_exercises

EXERCISE = {
    "name": "Pompki klasyczne",
    "muscle_group": "chest",
    "equipment": "none",
    "difficulty": "beginner",
    "movement_pattern": "horizontal_push",
    "contraindications": ["wrist"],
}


def test_tworzenie_i_odczyt_cwiczenia(client):
    created = client.post("/api/v1/exercises", json=EXERCISE)
    assert created.status_code == 201
    exercise_id = created.json()["id"]

    response = client.get(f"/api/v1/exercises/{exercise_id}")
    assert response.json() == {**EXERCISE, "id": exercise_id}


def test_duplikat_nazwy_zwraca_409(client):
    client.post("/api/v1/exercises", json=EXERCISE)
    assert client.post("/api/v1/exercises", json=EXERCISE).status_code == 409


def test_edycja_na_zajeta_nazwe_zwraca_409(client):
    client.post("/api/v1/exercises", json=EXERCISE)
    other_id = client.post("/api/v1/exercises", json={**EXERCISE, "name": "Deska"}).json()["id"]
    response = client.put(f"/api/v1/exercises/{other_id}", json=EXERCISE)
    assert response.status_code == 409


def test_edycja_cwiczenia_z_ta_sama_nazwa(client):
    exercise_id = client.post("/api/v1/exercises", json=EXERCISE).json()["id"]
    response = client.put(f"/api/v1/exercises/{exercise_id}", json={**EXERCISE, "difficulty": "intermediate"})
    assert response.status_code == 200
    assert response.json()["difficulty"] == "intermediate"


def test_filtrowanie_listy(client):
    client.post("/api/v1/exercises", json=EXERCISE)
    client.post(
        "/api/v1/exercises",
        json={**EXERCISE, "name": "Przysiad", "muscle_group": "legs", "difficulty": "intermediate"},
    )
    assert len(client.get("/api/v1/exercises").json()) == 2

    legs = client.get("/api/v1/exercises?muscle_group=legs").json()
    assert [item["name"] for item in legs] == ["Przysiad"]

    beginner_chest = client.get("/api/v1/exercises?muscle_group=chest&difficulty=beginner").json()
    assert [item["name"] for item in beginner_chest] == ["Pompki klasyczne"]


def test_nieznana_wartosc_filtra_zwraca_422(client):
    assert client.get("/api/v1/exercises?muscle_group=ogon").status_code == 422


def test_usuwanie_cwiczenia(client):
    exercise_id = client.post("/api/v1/exercises", json=EXERCISE).json()["id"]
    assert client.delete(f"/api/v1/exercises/{exercise_id}").status_code == 204
    assert client.get(f"/api/v1/exercises/{exercise_id}").status_code == 404


FEATURES = {"muscle_group": "legs", "equipment": "barbell", "difficulty": "advanced", "movement_pattern": "squat"}


def test_podpowiedz_przeciwwskazan_przy_pustym_atlasie_uzywa_regul(client):
    response = client.post("/api/v1/exercises/suggest-contraindications", json=FEATURES)
    assert response.status_code == 200
    assert response.json() == {
        "contraindications": ["knee", "lower_back", "hypertension"],
        "detector": "rules",
    }


def test_podpowiedz_przeciwwskazan_z_atlasu(client, db_session):
    seed_exercises(db_session)
    result = client.post("/api/v1/exercises/suggest-contraindications", json=FEATURES).json()
    assert result["detector"] == "hybrid"
    assert "knee" in result["contraindications"]


def test_podpowiedz_odrzuca_bledne_cechy(client):
    response = client.post(
        "/api/v1/exercises/suggest-contraindications", json={**FEATURES, "movement_pattern": "taniec"}
    )
    assert response.status_code == 422
