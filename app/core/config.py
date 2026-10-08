"""Ustawienia aplikacji czytane ze zmiennych środowiskowych.

Dzięki temu te same pliki kodu działają lokalnie, w CI i na serwerze,
a różnice (np. dozwolone adresy frontendu) ustawia się bez zmiany kodu.
"""

import os


class Settings:
    """Zbiór ustawień aplikacji. Każde pole ma wartość domyślną do pracy lokalnej."""

    def __init__(self) -> None:
        self.project_name: str = os.getenv("PROJECT_NAME", "Fitness AI")
        self.version: str = os.getenv("VERSION", "0.1.0")
        self.api_v1_prefix: str = "/api/v1"
        # Adresy frontendu, które mogą wysyłać żądania do API (CORS).
        # W zmiennej środowiskowej podaje się je po przecinku.
        cors = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        self.cors_origins: list[str] = [url.strip() for url in cors.split(",") if url.strip()]


# Jedna wspólna instancja ustawień importowana w całej aplikacji.
settings = Settings()
