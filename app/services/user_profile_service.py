"""Operacje na profilach użytkowników (CRUD).

Endpointy nie korzystają z bazy bezpośrednio, tylko przez te funkcje.
Dzięki temu logikę można testować i używać ponownie, np. w kwestionariuszu.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserProfile
from app.schemas import UserProfileCreate
from app.services.completeness import calculate_completeness


def create_profile(db: Session, data: UserProfileCreate) -> UserProfile:
    """Zapisuje nowy profil (z wyliczoną kompletnością danych) i zwraca go z identyfikatorem."""
    answers = data.model_dump()
    profile = UserProfile(**answers, data_completeness=calculate_completeness(answers))
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, profile_id: int) -> UserProfile | None:
    """Zwraca profil o podanym id albo None, jeśli nie istnieje."""
    return db.get(UserProfile, profile_id)


def list_profiles(db: Session, skip: int = 0, limit: int = 50) -> list[UserProfile]:
    """Zwraca stronę listy profili (skip/limit chronią przed pobraniem całej tabeli)."""
    query = select(UserProfile).order_by(UserProfile.id).offset(skip).limit(limit)
    return list(db.scalars(query))


def update_profile(db: Session, profile: UserProfile, data: UserProfileCreate) -> UserProfile:
    """Nadpisuje wszystkie pola profilu nowymi danymi i przelicza kompletność."""
    answers = data.model_dump()
    for field, value in answers.items():
        setattr(profile, field, value)
    profile.data_completeness = calculate_completeness(answers)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, profile: UserProfile) -> None:
    """Usuwa profil z bazy."""
    db.delete(profile)
    db.commit()
