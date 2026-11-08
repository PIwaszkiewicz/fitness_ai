"""Skrypt wypełniający bazę startowym atlasem ćwiczeń z pliku app/data/exercises.json.

Uruchomienie: python -m app.seed
Skrypt można uruchamiać wielokrotnie: brakujące ćwiczenia są dodawane, a istniejące (po nazwie)
są aktualizowane, jeśli ich dane w pliku się zmieniły (np. poprawiona grupa mięśniowa).
Plik atlasu jest więc źródłem prawdy dla swoich ćwiczeń; ćwiczenia dodane przez API
spoza atlasu pozostają bez zmian.
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


def seed_exercises(db: Session) -> tuple[int, int]:
    """Dodaje brakujące ćwiczenia z atlasu, aktualizuje zmienione i zwraca (dodane, zaktualizowane)."""
    added = updated = 0
    for exercise in load_atlas():
        existing = exercise_service.get_exercise_by_name(db, exercise.name)
        if existing is None:
            exercise_service.create_exercise(db, exercise)
            added += 1
            continue
        saved = {field: getattr(existing, field) for field in exercise.model_dump()}
        if saved != exercise.model_dump():
            exercise_service.update_exercise(db, existing, exercise)
            updated += 1
    return added, updated


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        added, updated = seed_exercises(session)
    print(f"Dodano ćwiczeń: {added}, zaktualizowano: {updated}")
