"""Endpointy REST atlasu ćwiczeń: CRUD oraz filtrowanie listy."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import DbSession, Limit, Skip
from app.models import Exercise
from app.models.enums import Difficulty, Equipment, MuscleGroup
from app.schemas import ExerciseCreate, ExerciseRead
from app.services import exercise_service as service

router = APIRouter(prefix="/exercises", tags=["Atlas ćwiczeń"])


def get_exercise_or_404(exercise_id: int, db: DbSession) -> Exercise:
    """Pobiera ćwiczenie albo kończy żądanie błędem 404."""
    exercise = service.get_exercise(db, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono ćwiczenia")
    return exercise


# Ćwiczenie wskazane w adresie URL, pobrane przez get_exercise_or_404.
ExerciseFromPath = Annotated[Exercise, Depends(get_exercise_or_404)]


def ensure_name_is_free(db: Session, name: str, current_id: int | None = None) -> None:
    """Zwraca błąd 409, jeśli nazwa jest już zajęta przez inne ćwiczenie."""
    existing = service.get_exercise_by_name(db, name)
    if existing is not None and existing.id != current_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ćwiczenie o tej nazwie już istnieje",
        )


@router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def create_exercise(data: ExerciseCreate, db: DbSession):
    """Dodaje ćwiczenie do atlasu."""
    ensure_name_is_free(db, data.name)
    return service.create_exercise(db, data)


@router.get("", response_model=list[ExerciseRead])
def list_exercises(
    db: DbSession,
    muscle_group: MuscleGroup | None = None,
    equipment: Equipment | None = None,
    difficulty: Difficulty | None = None,
    skip: Skip = 0,
    limit: Limit = 50,
):
    """Zwraca ćwiczenia, opcjonalnie przefiltrowane, np. ?muscle_group=legs&difficulty=beginner."""
    return service.list_exercises(db, muscle_group, equipment, difficulty, skip, limit)


@router.get("/{exercise_id}", response_model=ExerciseRead)
def read_exercise(exercise: ExerciseFromPath):
    """Zwraca jedno ćwiczenie."""
    return exercise


@router.put("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(data: ExerciseCreate, exercise: ExerciseFromPath, db: DbSession):
    """Zastępuje dane ćwiczenia nowymi."""
    ensure_name_is_free(db, data.name, current_id=exercise.id)
    return service.update_exercise(db, exercise, data)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise: ExerciseFromPath, db: DbSession):
    """Usuwa ćwiczenie z atlasu."""
    service.delete_exercise(db, exercise)
