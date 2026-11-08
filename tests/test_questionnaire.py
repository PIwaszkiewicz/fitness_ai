"""Testy kwestionariusza: definicja pytań, pytania warunkowe, kompletność i ostrzeżenia."""

import pytest
from pydantic import ValidationError

from app.data.questions import LIFTS_SHOWN, QUESTIONS
from app.schemas import UserProfileCreate

URL = "/api/v1/questionnaire"

BASIC_ANSWERS = {
    "age": 35,
    "gender": "male",
    "height_cm": 182,
    "weight_kg": 85,
    "training_goal": "general_fitness",
    "activity_level": "light",
}

FULL_ANSWERS = {
    **BASIC_ANSWERS,
    "training_experience": "less_than_1_year",
    "pushups": 15,
    "squats": 30,
    "plank_seconds": 60,
    "resting_heart_rate": 70,
    "training_days_per_week": 3,
    "session_minutes": 45,
    "available_equipment": ["none", "dumbbells"],
    "lifts_weights": False,
}

# Seria w przysiadzie ze sztangą (pytania o ciężary widzą tylko trenujący z ciężarami).
LIFTER_ANSWERS = {**BASIC_ANSWERS, "lifts_weights": True, "squat_kg": 100, "squat_reps": 5}


def test_pytania_odpowiadaja_polom_schematu():
    # Każde pole profilu ma pytanie, a każde pytanie trafia do istniejącego pola.
    assert {q.id for q in QUESTIONS} == set(UserProfileCreate.model_fields)


@pytest.mark.parametrize("question", [q for q in QUESTIONS if q.min is not None], ids=lambda q: q.id)
def test_zakresy_pytan_zgodne_ze_schematem(question):
    # Wartości graniczne z definicji pytań muszą przechodzić walidację, a wartości poza nimi nie.
    base = {**BASIC_ANSWERS, "limitations": ["knee"]}
    if question.show_if == LIFTS_SHOWN:
        # Ciężar i powtórzenia podaje się w parze, tylko przy treningu z ciężarami.
        lift = question.id.rsplit("_", 1)[0]
        base |= {"lifts_weights": True, f"{lift}_kg": 50, f"{lift}_reps": 5}
    UserProfileCreate(**{**base, question.id: question.min})
    UserProfileCreate(**{**base, question.id: question.max})
    with pytest.raises(ValidationError):
        UserProfileCreate(**{**base, question.id: question.min - 1})
    with pytest.raises(ValidationError):
        UserProfileCreate(**{**base, question.id: question.max + 1})


def test_pobranie_pytan(client):
    response = client.get(URL)
    assert response.status_code == 200
    questions = {q["id"]: q for q in response.json()}
    assert questions["gender"]["options"][0] == {"value": "male", "label": "Mężczyzna"}
    assert questions["medical_clearance"]["show_if"] == {
        "field": "limitations",
        "any_of": ["hypertension", "heart_condition"],
    }


def test_minimalne_odpowiedzi(client):
    response = client.post(URL, json=BASIC_ANSWERS)
    assert response.status_code == 201
    result = response.json()
    assert result["profile"]["data_completeness"] == 0
    assert len(result["missing_answers"]) == 9
    assert result["warnings"] == []


def test_pelne_odpowiedzi_daja_100_procent(client):
    result = client.post(URL, json=FULL_ANSWERS).json()
    assert result["profile"]["data_completeness"] == 100
    assert result["missing_answers"] == []


def test_profil_z_kwestionariusza_jest_zapisany(client):
    profile_id = client.post(URL, json=FULL_ANSWERS).json()["profile"]["id"]
    saved = client.get(f"/api/v1/profiles/{profile_id}").json()
    assert saved["available_equipment"] == ["none", "dumbbells"]
    assert saved["data_completeness"] == 100


def test_kontuzja_dodaje_pytanie_o_bol(client):
    result = client.post(URL, json={**FULL_ANSWERS, "limitations": ["knee"]}).json()
    assert result["missing_answers"] == ["pain_level"]
    assert result["profile"]["data_completeness"] == round(100 * 9 / 10)


def test_bol_bez_ograniczen_jest_odrzucany(client):
    assert client.post(URL, json={**BASIC_ANSWERS, "pain_level": 5}).status_code == 422


def test_zgoda_lekarza_bez_chorob_krazenia_jest_odrzucana(client):
    answers = {**BASIC_ANSWERS, "limitations": ["knee"], "medical_clearance": True}
    assert client.post(URL, json=answers).status_code == 422


def test_pusta_lista_sprzetu_jest_odrzucana(client):
    assert client.post(URL, json={**BASIC_ANSWERS, "available_equipment": []}).status_code == 422


def test_choroba_serca_bez_zgody_lekarza_daje_ostrzezenie(client):
    answers = {**BASIC_ANSWERS, "limitations": ["heart_condition"]}
    warnings = client.post(URL, json=answers).json()["warnings"]
    assert len(warnings) == 1
    assert "lekarzem" in warnings[0]


def test_choroba_serca_ze_zgoda_lekarza_bez_ostrzezenia(client):
    answers = {**BASIC_ANSWERS, "limitations": ["hypertension"], "medical_clearance": True}
    assert client.post(URL, json=answers).json()["warnings"] == []


@pytest.mark.parametrize(
    ("extra", "expected_warnings"),
    [
        ({"limitations": ["knee"], "pain_level": 6}, 0),
        ({"limitations": ["knee"], "pain_level": 7}, 1),
        ({"resting_heart_rate": 100}, 0),
        ({"resting_heart_rate": 101}, 1),
    ],
)
def test_progi_ostrzezen(client, extra, expected_warnings):
    warnings = client.post(URL, json={**BASIC_ANSWERS, **extra}).json()["warnings"]
    assert len(warnings) == expected_warnings


def test_pytania_o_ciezary_widzi_tylko_trenujacy(client):
    beginner = client.post(URL, json={**FULL_ANSWERS, "lifts_weights": False}).json()
    lifter = client.post(URL, json={**FULL_ANSWERS, **LIFTER_ANSWERS}).json()
    assert not any(item.endswith(("_kg", "_reps")) for item in beginner["missing_answers"])
    # Trenujący podał 1 z 5 ćwiczeń, więc brakuje 8 pól (4 ćwiczenia × ciężar i powtórzenia).
    assert len(lifter["missing_answers"]) == 8
    assert lifter["profile"]["squat_kg"] == 100


@pytest.mark.parametrize(
    "answers",
    [
        {**BASIC_ANSWERS, "squat_kg": 100, "squat_reps": 5},  # bez treningu z ciężarami
        {**BASIC_ANSWERS, "lifts_weights": False, "squat_kg": 100, "squat_reps": 5},
        {**BASIC_ANSWERS, "lifts_weights": True, "squat_kg": 100},  # brak powtórzeń
        {**LIFTER_ANSWERS, "squat_reps": 12},  # wzór 1RM dokładny do 10 powtórzeń
        {**BASIC_ANSWERS, "pushup_variant": "knees"},  # wariant bez wyniku pompek
    ],
)
def test_niespojne_odpowiedzi_o_ciezarach_sa_odrzucane(client, answers):
    assert client.post(URL, json=answers).status_code == 422


def test_wariant_pompek_nie_wplywa_na_kompletnosc(client):
    without = client.post(URL, json=FULL_ANSWERS).json()
    with_variant = client.post(URL, json={**FULL_ANSWERS, "pushup_variant": "knees"}).json()
    assert without["profile"]["data_completeness"] == with_variant["profile"]["data_completeness"]
    assert with_variant["profile"]["pushup_variant"] == "knees"
