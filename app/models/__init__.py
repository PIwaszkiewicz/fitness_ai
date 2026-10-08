"""Modele bazy danych (SQLAlchemy): tabele profili użytkowników, ćwiczeń i planów.

Import modeli tutaj rejestruje je w Base.metadata, dzięki czemu
create_all() wie, jakie tabele utworzyć.
"""

from app.models.exercise import Exercise
from app.models.user_profile import UserProfile

__all__ = ["Exercise", "UserProfile"]
