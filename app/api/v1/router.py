"""Główny router wersji 1 API. Zbiera wszystkie endpointy dostępne pod prefiksem /api/v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    exercises,
    fitness_level,
    plans,
    profiles,
    questionnaire,
)

api_router = APIRouter()
api_router.include_router(profiles.router)
api_router.include_router(exercises.router)
api_router.include_router(questionnaire.router)
api_router.include_router(fitness_level.router)
api_router.include_router(plans.router)


@api_router.get("/ping")
def ping() -> dict[str, str]:
    """Testowy endpoint sprawdzający, czy router v1 jest poprawnie podłączony."""
    return {"message": "pong"}
