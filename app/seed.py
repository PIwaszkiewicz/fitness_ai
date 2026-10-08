"""Skrypt wypełniający bazę startowym atlasem ćwiczeń z pliku app/data/exercises.json.

Uruchomienie: python -m app.seed
Skrypt można uruchamiać wielokrotnie: ćwiczenia już istniejące (po nazwie) są pomijane.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app import models  # noqa: F401  (rejestruje tabele w Base.metadata)
from app.core.database import Base, SessionLocal, engine
from app.schemas import ExerciseCreate
from app.services import exercise_service

ATLAS_PATH = Path(__file__).parent / "data" / "exercises.json"


def load_atlas() -> list[ExerciseCreate]:
    """Wczytuje atlas z pliku JSON i waliduje każdy wpis tym samym schematem co API."""
    with ATLAS_PATH.open(encoding="utf-8") as file:
        return [ExerciseCreate(**item) for item in json.load(file)]


def seed_exercises(db: Session) -> int:
    """Dodaje brakujące ćwiczenia z atlasu i zwraca liczbę dodanych."""
    added = 0
    for exercise in load_atlas():
        if exercise_service.get_exercise_by_name(db, exercise.name) is None:
            exercise_service.create_exercise(db, exercise)
            added += 1
    return added


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        count = seed_exercises(session)
    print(f"Dodano ćwiczeń: {count}")
