"""Model tabeli profili użytkowników: dane zebrane podczas wywiadu."""

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserProfile(Base):
    """Profil użytkownika: metryki zdrowotne, cel, ograniczenia, testy i preferencje.

    Poprawność wartości (zakresy, dozwolone opcje) sprawdzają schematy Pydantic,
    zanim dane trafią do bazy. Pola z `| None` są opcjonalne w kwestionariuszu.
    """

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Dane podstawowe (wymagane)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(20))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    training_goal: Mapped[str] = mapped_column(String(30))
    activity_level: Mapped[str] = mapped_column(String(30))
    training_experience: Mapped[str | None] = mapped_column(String(30))

    # Zdrowie i ograniczenia. Lista zapisana jako JSON, np. ["knee", "lower_back"].
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    pain_level: Mapped[int | None] = mapped_column(Integer)
    medical_clearance: Mapped[bool | None] = mapped_column(Boolean)

    # Testy sprawności wykonywane samodzielnie przez użytkownika
    pushups: Mapped[int | None] = mapped_column(Integer)
    squats: Mapped[int | None] = mapped_column(Integer)
    plank_seconds: Mapped[int | None] = mapped_column(Integer)
    resting_heart_rate: Mapped[int | None] = mapped_column(Integer)

    # Preferencje treningowe
    training_days_per_week: Mapped[int | None] = mapped_column(Integer)
    session_minutes: Mapped[int | None] = mapped_column(Integer)
    available_equipment: Mapped[list[str] | None] = mapped_column(JSON)

    # Procent odpowiedzi udzielonych na pytania opcjonalne (0–100), liczony przez serwer.
    data_completeness: Mapped[int] = mapped_column(Integer, default=0)
