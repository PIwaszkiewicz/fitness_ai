"""Schematy planu treningowego zwracanego przez API."""

from pydantic import BaseModel

from app.ml.predictor import ClassifierName
from app.models.enums import Equipment, FitnessLevel, MuscleGroup, TrainingGoal


class PlanExercise(BaseModel):
    """Ćwiczenie w planie wraz z parametrami wykonania."""

    exercise_id: int
    name: str
    muscle_group: MuscleGroup
    equipment: Equipment
    sets: int
    reps: str  # zakres powtórzeń, np. "8–12"
    rest_seconds: int


class PlanDay(BaseModel):
    """Jeden dzień treningowy."""

    day: int
    focus: str  # np. "Całe ciało", "Góra ciała"
    exercises: list[PlanExercise]


class TrainingPlan(BaseModel):
    """Tygodniowy plan treningowy z rekomendacjami progresji i ostrzeżeniami."""

    profile_id: int
    fitness_level: FitnessLevel
    classifier: ClassifierName  # klasyfikator, który wyznaczył poziom sprawności
    training_goal: TrainingGoal
    days_per_week: int
    session_minutes: int
    days: list[PlanDay]
    # Ile ćwiczeń pasujących do sprzętu i poziomu odrzucono z powodu przeciwwskazań.
    excluded_for_safety: int
    progression: list[str]
    warnings: list[str]
