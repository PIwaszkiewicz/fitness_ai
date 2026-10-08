"""Model tabeli profili użytkowników: dane zebrane podczas wywiadu."""

from sqlalchemy import JSON, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserProfile(Base):
    """Profil użytkownika: metryki zdrowotne, cel treningowy i ograniczenia ruchowe.

    Poprawność wartości (zakresy, dozwolone opcje) sprawdzają schematy Pydantic,
    zanim dane trafią do bazy.
    """

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(20))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    training_goal: Mapped[str] = mapped_column(String(30))
    activity_level: Mapped[str] = mapped_column(String(30))
    # Lista kontuzji zapisana jako JSON, np. ["knee", "lower_back"].
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
