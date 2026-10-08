"""Główny router wersji 1 API. Zbiera wszystkie endpointy dostępne pod prefiksem /api/v1."""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/ping")
def ping() -> dict[str, str]:
    """Testowy endpoint sprawdzający, czy router v1 jest poprawnie podłączony."""
    return {"message": "pong"}
