"""Endpointy REST profili użytkowników: tworzenie, odczyt, edycja i usuwanie."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, Limit, Skip
from app.models import UserProfile
from app.schemas import UserProfileCreate, UserProfileRead
from app.services import user_profile_service as service

router = APIRouter(prefix="/profiles", tags=["Profile użytkowników"])


def get_profile_or_404(profile_id: int, db: DbSession) -> UserProfile:
    """Pobiera profil albo kończy żądanie błędem 404. Wspólne dla GET, PUT i DELETE."""
    profile = service.get_profile(db, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono profilu")
    return profile


# Profil wskazany w adresie URL, pobrany przez get_profile_or_404.
ProfileFromPath = Annotated[UserProfile, Depends(get_profile_or_404)]


@router.post("", response_model=UserProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(data: UserProfileCreate, db: DbSession):
    """Tworzy nowy profil. Dane są wcześniej walidowane przez schemat Pydantic."""
    return service.create_profile(db, data)


@router.get("", response_model=list[UserProfileRead])
def list_profiles(db: DbSession, skip: Skip = 0, limit: Limit = 50):
    """Zwraca listę profili ze stronicowaniem."""
    return service.list_profiles(db, skip, limit)


@router.get("/{profile_id}", response_model=UserProfileRead)
def read_profile(profile: ProfileFromPath):
    """Zwraca jeden profil."""
    return profile


@router.put("/{profile_id}", response_model=UserProfileRead)
def update_profile(data: UserProfileCreate, profile: ProfileFromPath, db: DbSession):
    """Zastępuje dane profilu nowymi (wymaga przesłania wszystkich pól)."""
    return service.update_profile(db, profile, data)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile: ProfileFromPath, db: DbSession):
    """Usuwa profil. Odpowiedź 204 nie ma treści."""
    service.delete_profile(db, profile)
