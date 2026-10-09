"""Schematy Pydantic profilu użytkownika: walidacja odpowiedzi z kwestionariusza.

Zakresy liczbowe chronią system przed błędnymi lub niebezpiecznymi danymi
(np. literówka "1800" zamiast "180" cm), zanim trafią do bazy i modeli AI.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    CARDIOVASCULAR_LIMITATIONS,
    ActivityLevel,
    Equipment,
    Gender,
    Limitation,
    TrainingExperience,
    TrainingGoal,
)


class UserProfileCreate(BaseModel):
    """Odpowiedzi użytkownika z kwestionariusza, z których powstaje profil."""

    # extra="forbid": nieznane pola są odrzucane zamiast cicho ignorowane.
    model_config = ConfigDict(extra="forbid")

    # Dane podstawowe (wymagane)
    age: int = Field(ge=16, le=100, description="Wiek w latach")
    gender: Gender
    height_cm: float = Field(ge=120, le=230, description="Wzrost w centymetrach")
    weight_kg: float = Field(ge=30, le=300, description="Waga w kilogramach")
    training_goal: TrainingGoal
    activity_level: ActivityLevel
    training_experience: TrainingExperience | None = None

    # Zdrowie i ograniczenia
    limitations: list[Limitation] = Field(default_factory=list)
    pain_level: int | None = Field(default=None, ge=1, le=10, description="Skala bólu 1–10")
    medical_clearance: bool | None = None

    # Testy sprawności (opcjonalne)
    pushups: int | None = Field(default=None, ge=0, le=150)
    squats: int | None = Field(default=None, ge=0, le=150)
    plank_seconds: int | None = Field(default=None, ge=0, le=600)
    resting_heart_rate: int | None = Field(default=None, ge=30, le=150)

    # Preferencje treningowe (opcjonalne)
    training_days_per_week: int | None = Field(default=None, ge=1, le=7)
    session_minutes: int | None = Field(default=None, ge=15, le=180)
    available_equipment: list[Equipment] | None = Field(default=None, min_length=1)

    @field_validator("limitations", "available_equipment")
    @classmethod
    def remove_duplicates(cls, value: list | None) -> list | None:
        """Usuwa powtórzone wartości z list, zachowując kolejność podaną przez użytkownika."""
        if value is None:
            return None
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def check_conditional_answers(self):
        """Odrzuca odpowiedzi na pytania warunkowe, których warunek nie jest spełniony.

        Pytanie o ból zadaje się tylko osobom z ograniczeniami, a o zgodę lekarza
        tylko osobom z chorobami układu krążenia (te same warunki co w definicji pytań).
        """
        if self.pain_level is not None and not self.limitations:
            raise ValueError("pain_level można podać tylko przy zgłoszonych ograniczeniach")
        has_cardio = any(item in CARDIOVASCULAR_LIMITATIONS for item in self.limitations)
        if self.medical_clearance is not None and not has_cardio:
            raise ValueError("medical_clearance dotyczy tylko chorób układu krążenia")
        return self


class UserProfileRead(UserProfileCreate):
    """Profil zwracany przez API: odpowiedzi uzupełnione o dane nadane przez serwer."""

    # from_attributes=True pozwala zbudować schemat bezpośrednio z obiektu SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_completeness: int
