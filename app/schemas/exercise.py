"""Schematy Pydantic ćwiczenia: walidacja wpisów w atlasie ćwiczeń."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    Difficulty,
    Equipment,
    Limitation,
    MovementPattern,
    MuscleGroup,
)


class ExerciseFeatures(BaseModel):
    """Cechy opisujące ćwiczenie, na podstawie których można przewidywać jego przeciwwskazania."""

    model_config = ConfigDict(extra="forbid")

    muscle_group: MuscleGroup
    equipment: Equipment
    difficulty: Difficulty
    movement_pattern: MovementPattern


class ExerciseCreate(ExerciseFeatures):
    """Dane potrzebne do dodania ćwiczenia do atlasu: nazwa, cechy i przeciwwskazania."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    contraindications: list[Limitation] = Field(default_factory=list)

    @field_validator("contraindications")
    @classmethod
    def remove_duplicates(cls, value: list[Limitation]) -> list[Limitation]:
        """Usuwa powtórzone przeciwwskazania, zachowując kolejność."""
        return list(dict.fromkeys(value))


class ExerciseRead(ExerciseCreate):
    """Ćwiczenie zwracane przez API wraz z identyfikatorem z bazy."""

    model_config = ConfigDict(from_attributes=True)

    id: int
