"""Testy walidacji schematów Pydantic: poprawne dane, granice zakresów i błędne wartości."""

import pytest
from pydantic import ValidationError

from app.models.enums import Limitation
from app.schemas import ExerciseCreate, UserProfileCreate

VALID_PROFILE = {
    "age": 30,
    "gender": "male",
    "height_cm": 180,
    "weight_kg": 80,
    "training_goal": "muscle_gain",
    "activity_level": "moderate",
    "limitations": ["knee"],
}

VALID_EXERCISE = {
    "name": "Przysiad ze sztangą",
    "muscle_group": "legs",
    "equipment": "barbell",
    "difficulty": "intermediate",
    "contraindications": ["knee", "lower_back"],
}


def test_poprawny_profil():
    profile = UserProfileCreate(**VALID_PROFILE)
    assert profile.age == 30
    assert profile.limitations == [Limitation.KNEE]


def test_profil_bez_ograniczen_ma_pusta_liste():
    data = {key: value for key, value in VALID_PROFILE.items() if key != "limitations"}
    assert UserProfileCreate(**data).limitations == []


@pytest.mark.parametrize(
    ("field", "value"),
    [("age", 16), ("age", 100), ("height_cm", 120), ("height_cm", 230), ("weight_kg", 30), ("weight_kg", 300)],
)
def test_wartosci_graniczne_sa_akceptowane(field, value):
    UserProfileCreate(**{**VALID_PROFILE, field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age", 15),
        ("age", 101),
        ("height_cm", 119),
        ("height_cm", 231),
        ("weight_kg", 29),
        ("weight_kg", 301),
        ("gender", "inna"),
        ("training_goal", "latanie"),
        ("activity_level", "extreme"),
        ("limitations", ["glowa"]),
    ],
)
def test_bledne_wartosci_sa_odrzucane(field, value):
    with pytest.raises(ValidationError):
        UserProfileCreate(**{**VALID_PROFILE, field: value})


def test_nieznane_pole_jest_odrzucane():
    with pytest.raises(ValidationError):
        UserProfileCreate(**VALID_PROFILE, is_admin=True)


def test_duplikaty_ograniczen_sa_usuwane():
    profile = UserProfileCreate(**{**VALID_PROFILE, "limitations": ["knee", "hip", "knee"]})
    assert profile.limitations == [Limitation.KNEE, Limitation.HIP]


def test_poprawne_cwiczenie_i_przyciecie_nazwy():
    exercise = ExerciseCreate(**{**VALID_EXERCISE, "name": "  Pompki  "})
    assert exercise.name == "Pompki"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "A"),
        ("name", "x" * 101),
        ("muscle_group", "ogon"),
        ("equipment", "rower"),
        ("difficulty", "expert"),
        ("contraindications", ["nieznane"]),
    ],
)
def test_bledne_cwiczenie_jest_odrzucane(field, value):
    with pytest.raises(ValidationError):
        ExerciseCreate(**{**VALID_EXERCISE, field: value})
