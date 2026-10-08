"""Operacje na atlasie ćwiczeń (CRUD) wraz z filtrowaniem listy."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Exercise
from app.models.enums import Difficulty, Equipment, MuscleGroup
from app.schemas import ExerciseCreate


def create_exercise(db: Session, data: ExerciseCreate) -> Exercise:
    """Dodaje ćwiczenie do atlasu. Unikalność nazwy sprawdza wcześniej endpoint."""
    exercise = Exercise(**data.model_dump())
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def get_exercise(db: Session, exercise_id: int) -> Exercise | None:
    """Zwraca ćwiczenie o podanym id albo None."""
    return db.get(Exercise, exercise_id)


def get_exercise_by_name(db: Session, name: str) -> Exercise | None:
    """Wyszukuje ćwiczenie po nazwie (używane do wykrywania duplikatów)."""
    return db.scalars(select(Exercise).where(Exercise.name == name)).first()


def list_exercises(
    db: Session,
    muscle_group: MuscleGroup | None = None,
    equipment: Equipment | None = None,
    difficulty: Difficulty | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Exercise]:
    """Zwraca ćwiczenia, opcjonalnie zawężone do grupy mięśniowej, sprzętu i trudności."""
    query = select(Exercise)
    if muscle_group:
        query = query.where(Exercise.muscle_group == muscle_group)
    if equipment:
        query = query.where(Exercise.equipment == equipment)
    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)
    query = query.order_by(Exercise.id).offset(skip).limit(limit)
    return list(db.scalars(query))


def update_exercise(db: Session, exercise: Exercise, data: ExerciseCreate) -> Exercise:
    """Nadpisuje wszystkie pola ćwiczenia nowymi danymi."""
    for field, value in data.model_dump().items():
        setattr(exercise, field, value)
    db.commit()
    db.refresh(exercise)
    return exercise


def delete_exercise(db: Session, exercise: Exercise) -> None:
    """Usuwa ćwiczenie z atlasu."""
    db.delete(exercise)
    db.commit()
