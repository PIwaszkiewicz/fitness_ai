"""Operacje na profilach użytkowników (CRUD).

Endpointy nie korzystają z bazy bezpośrednio, tylko przez te funkcje.
Dzięki temu logikę można testować i używać ponownie, np. w kwestionariuszu.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import UserProfile
from app.schemas import UserProfileCreate


def create_profile(db: Session, data: UserProfileCreate) -> UserProfile:
    """Zapisuje nowy profil i zwraca go z nadanym identyfikatorem."""
    profile = UserProfile(**data.model_dump())
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
    """Nadpisuje wszystkie pola profilu nowymi danymi."""
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, profile: UserProfile) -> None:
    """Usuwa profil z bazy."""
    db.delete(profile)
    db.commit()
