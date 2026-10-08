"""Testy startowego atlasu ćwiczeń i skryptu seed."""

from app.models import Exercise
from app.models.enums import Limitation, MuscleGroup
from app.seed import load_atlas, seed_exercises


def test_atlas_jest_poprawny_i_kompletny():
    atlas = load_atlas()  # błędny wpis rzuciłby ValidationError
    assert len(atlas) >= 30
    assert len({exercise.name for exercise in atlas}) == len(atlas)
    # Każda grupa mięśniowa i każde ograniczenie występuje w atlasie co najmniej raz.
    assert {exercise.muscle_group for exercise in atlas} == set(MuscleGroup)
    assert {item for exercise in atlas for item in exercise.contraindications} == set(Limitation)


def test_seed_mozna_uruchomic_wielokrotnie(db_session):
    first = seed_exercises(db_session)
    second = seed_exercises(db_session)
    assert first == len(load_atlas())
    assert second == 0
    assert db_session.query(Exercise).count() == first
