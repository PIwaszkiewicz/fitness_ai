"""Schematy Pydantic profilu użytkownika: walidacja danych z wywiadu.

Zakresy liczbowe chronią system przed błędnymi lub niebezpiecznymi danymi
(np. literówka "1800" zamiast "180" cm), zanim trafią do bazy i modeli AI.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ActivityLevel, Gender, Limitation, TrainingGoal


class UserProfileCreate(BaseModel):
    """Dane przesyłane przez klienta przy tworzeniu profilu."""

    # extra="forbid": nieznane pola są odrzucane zamiast cicho ignorowane.
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=16, le=100, description="Wiek w latach")
    gender: Gender
    height_cm: float = Field(ge=120, le=230, description="Wzrost w centymetrach")
    weight_kg: float = Field(ge=30, le=300, description="Waga w kilogramach")
    training_goal: TrainingGoal
    activity_level: ActivityLevel
    limitations: list[Limitation] = Field(default_factory=list)

    @field_validator("limitations")
    @classmethod
    def remove_duplicates(cls, value: list[Limitation]) -> list[Limitation]:
        """Usuwa powtórzone ograniczenia, zachowując kolejność podaną przez użytkownika."""
        return list(dict.fromkeys(value))


class UserProfileRead(UserProfileCreate):
    """Profil zwracany przez API: dane wejściowe uzupełnione o identyfikator z bazy."""

    # from_attributes=True pozwala zbudować schemat bezpośrednio z obiektu SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    id: int
