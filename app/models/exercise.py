"""Model tabeli ćwiczeń: atlas ćwiczeń, z którego budowane są plany treningowe."""

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Exercise(Base):
    """Ćwiczenie z atlasu wraz z informacją, komu nie powinno być zalecane."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    muscle_group: Mapped[str] = mapped_column(String(30))
    equipment: Mapped[str] = mapped_column(String(30))
    difficulty: Mapped[str] = mapped_column(String(20))
    # Ograniczenia, przy których ćwiczenie jest przeciwwskazane, np. ["knee"].
    contraindications: Mapped[list[str]] = mapped_column(JSON, default=list)
