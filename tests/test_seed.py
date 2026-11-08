"""Testy startowego atlasu ćwiczeń i skryptu seed."""

import json

from app.models import Exercise
from app.models.enums import Limitation, MovementPattern, MuscleGroup
from app.schemas import ExerciseCreate
from app.seed import ATLAS_PATH, load_atlas, seed_exercises


def test_atlas_jest_poprawny_i_kompletny():
    atlas = load_atlas()  # błędny wpis rzuciłby ValidationError
    assert len(atlas) >= 60
    assert len({exercise.name for exercise in atlas}) == len(atlas)
    # Każda grupa mięśniowa i każde ograniczenie występuje w atlasie co najmniej raz.
    assert {exercise.muscle_group for exercise in atlas} == set(MuscleGroup)
    assert {item for exercise in atlas for item in exercise.contraindications} == set(Limitation)
    assert {exercise.movement_pattern for exercise in atlas} == set(MovementPattern)


def test_seed_mozna_uruchomic_wielokrotnie(db_session):
    first = seed_exercises(db_session)
    second = seed_exercises(db_session)
    assert first == len(load_atlas())
    assert second == 0
    assert db_session.query(Exercise).count() == first


def test_plik_atlasu_bez_duplikatow_i_z_poprawnymi_wartosciami():
    with ATLAS_PATH.open(encoding="utf-8") as file:
        entries = json.load(file)
    # Nazwy nie mogą się powtarzać, także przy innej wielkości liter.
    names = [entry["name"].lower() for entry in entries]
    assert len(set(names)) == len(names)
    # Schemat Pydantic odrzuca wartości spoza enumów (ValidationError).
    for entry in entries:
        ExerciseCreate(**entry)
