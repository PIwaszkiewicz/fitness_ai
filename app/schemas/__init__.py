"""Schematy Pydantic: walidacja danych wejściowych i format odpowiedzi API."""

from app.schemas.exercise import ExerciseCreate, ExerciseRead
from app.schemas.user_profile import UserProfileCreate, UserProfileRead

__all__ = ["ExerciseCreate", "ExerciseRead", "UserProfileCreate", "UserProfileRead"]
