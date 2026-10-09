"""Testy endpointów CRUD profili użytkowników."""

PROFILE = {
    "age": 30,
    "gender": "female",
    "height_cm": 170,
    "weight_kg": 65,
    "training_goal": "strength",
    "activity_level": "moderate",
    "limitations": ["knee"],
}


def test_tworzenie_i_odczyt_profilu(client):
    created = client.post("/api/v1/profiles", json=PROFILE)
    assert created.status_code == 201
    profile_id = created.json()["id"]

    response = client.get(f"/api/v1/profiles/{profile_id}")
    assert response.status_code == 200
    body = response.json()
    assert {key: body[key] for key in PROFILE} == PROFILE
    assert body["id"] == profile_id
    assert body["pushups"] is None  # pole opcjonalne bez odpowiedzi
    assert body["data_completeness"] == 0


def test_bledne_dane_zwracaja_422(client):
    response = client.post("/api/v1/profiles", json={**PROFILE, "age": 12})
    assert response.status_code == 422


def test_lista_profili_z_paginacja(client):
    for _ in range(3):
        client.post("/api/v1/profiles", json=PROFILE)
    assert len(client.get("/api/v1/profiles").json()) == 3
    assert len(client.get("/api/v1/profiles?skip=1&limit=1").json()) == 1
    assert client.get("/api/v1/profiles?limit=0").status_code == 422


def test_edycja_profilu(client):
    profile_id = client.post("/api/v1/profiles", json=PROFILE).json()["id"]
    response = client.put(f"/api/v1/profiles/{profile_id}", json={**PROFILE, "weight_kg": 62})
    assert response.status_code == 200
    assert response.json()["weight_kg"] == 62


def test_edycja_przelicza_kompletnosc(client):
    profile_id = client.post("/api/v1/profiles", json=PROFILE).json()["id"]
    updated = {**PROFILE, "pushups": 20, "squats": 30, "pain_level": 3}
    response = client.put(f"/api/v1/profiles/{profile_id}", json=updated)
    # Widocznych pytań opcjonalnych jest 9 (8 stałych + ból przy kontuzji), odpowiedzi 3.
    assert response.json()["data_completeness"] == 33


def test_usuwanie_profilu(client):
    profile_id = client.post("/api/v1/profiles", json=PROFILE).json()["id"]
    assert client.delete(f"/api/v1/profiles/{profile_id}").status_code == 204
    assert client.get(f"/api/v1/profiles/{profile_id}").status_code == 404


def test_nieistniejacy_profil_zwraca_404(client):
    assert client.get("/api/v1/profiles/999").status_code == 404
    assert client.put("/api/v1/profiles/999", json=PROFILE).status_code == 404
    assert client.delete("/api/v1/profiles/999").status_code == 404
