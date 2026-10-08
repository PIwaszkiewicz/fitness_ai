"""Punkt wejścia aplikacji: tworzy obiekt FastAPI i łączy wszystkie elementy.

Architektura warstw (model klient-serwer):
    api/       - endpointy HTTP, przyjmują żądania i zwracają odpowiedzi
    schemas/   - walidacja danych wejściowych i format odpowiedzi (Pydantic)
    services/  - logika biznesowa, wywoływana przez endpointy
    ml/        - modele AI: klasyfikacja sprawności i generowanie planów
    models/    - tabele bazy danych (SQLAlchemy)
    core/      - konfiguracja wspólna dla całej aplikacji

Przepływ żądania:
    klient -> CORS -> router /api/v1 -> walidacja (schemas)
           -> serwis (services) -> baza danych (models) / model AI (ml)
           -> odpowiedź JSON -> klient

Uruchomienie: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.project_name, version=settings.version)

# CORS pozwala frontendowi z innego adresu (np. localhost:3000) wywoływać API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wszystkie endpointy wersji 1 dostępne są pod prefiksem /api/v1.
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    """Sprawdzenie stanu serwera, np. dla monitoringu lub platformy hostingowej."""
    return {"status": "ok", "version": settings.version}
