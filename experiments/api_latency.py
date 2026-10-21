"""Pomiar czasu odpowiedzi API: pełne żądania HTTP, od walidacji danych po odpowiedź JSON.

Eksperyment 1 mierzy sam klasyfikator. Tutaj mierzymy całe żądanie: walidację Pydantic,
zapytania do bazy, klasyfikację, generowanie planu i zamianę wyniku na JSON.

Uruchomienie:
    python -m app.ml.train                    # modele ML muszą być wytrenowane
    python -m experiments.api_latency         # aplikacja w tym samym procesie, wynik w docs/experiments/
    python -m experiments.api_latency URL     # działające wdrożenie, np. https://...onrender.com
"""

import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import httpx
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (rejestruje tabele w Base.metadata)
from app.core.database import Base, get_db
from app.main import app
from app.ml.predictor import ClassifierName, model_path
from app.seed import seed_exercises

OUTPUT_PATH = Path("docs/experiments/api_latency.csv")
LOCAL_REQUESTS = 200
REMOTE_REQUESTS = 30  # mniej żądań, żeby nie obciążać darmowego serwera
# Pierwsze żądania wczytują modele z dysku i rozgrzewają połączenie, więc ich nie liczymy.
WARMUP_REQUESTS = 5

# Kompletny profil, żeby żądania wykonywały pełną ścieżkę obliczeń.
PROFILE = {
    "age": 35,
    "gender": "female",
    "height_cm": 168,
    "weight_kg": 64,
    "training_goal": "general_fitness",
    "activity_level": "moderate",
    "training_experience": "1_to_3_years",
    "limitations": ["knee"],
    "pain_level": 3,
    "pushups": 15,
    "squats": 35,
    "plank_seconds": 90,
    "resting_heart_rate": 68,
    "training_days_per_week": 4,
    "session_minutes": 60,
    "available_equipment": ["dumbbells", "resistance_band"],
}


def endpoints(profile_id: int) -> list[tuple[str, str, str, dict | None]]:
    """Mierzone żądania: (nazwa, metoda HTTP, adres, dane JSON)."""
    profile = f"/api/v1/profiles/{profile_id}"
    return [
        ("health check", "GET", "/health", None),
        ("pytania kwestionariusza", "GET", "/api/v1/questionnaire", None),
        ("wysłanie kwestionariusza", "POST", "/api/v1/questionnaire", PROFILE),
        ("poziom: system regułowy", "GET", f"{profile}/fitness-level?method=rules", None),
        ("poziom: drzewo decyzyjne", "GET", f"{profile}/fitness-level?method=decision_tree", None),
        ("poziom: sieć neuronowa", "GET", f"{profile}/fitness-level?method=mlp", None),
        ("plan treningowy (sieć)", "GET", f"{profile}/plan?method=mlp", None),
    ]


def timed_request(client: httpx.Client, method: str, url: str, payload: dict | None) -> float:
    """Wysyła żądanie i zwraca czas odpowiedzi w milisekundach. Błąd HTTP przerywa pomiar."""
    start = perf_counter()
    response = client.request(method, url, json=payload)
    elapsed = (perf_counter() - start) * 1000
    response.raise_for_status()
    return elapsed


def measure_api_latency(client: httpx.Client, n_requests: int) -> pd.DataFrame:
    """Zwraca średnią, medianę (p50), 95. percentyl (p95) i maksimum czasu dla każdego żądania.

    p95 oznacza, że 95% żądań było szybszych od tej wartości. Opisuje typowy
    najgorszy przypadek lepiej niż średnia, którą zawyżają pojedyncze opóźnienia.
    """
    response = client.post("/api/v1/questionnaire", json=PROFILE)
    response.raise_for_status()
    profile_id = response.json()["profile"]["id"]

    rows = []
    for name, method, url, payload in endpoints(profile_id):
        for _ in range(WARMUP_REQUESTS):
            timed_request(client, method, url, payload)
        times = [timed_request(client, method, url, payload) for _ in range(n_requests)]
        rows.append({
            "endpoint": name,
            "requests": n_requests,
            "mean_ms": float(np.mean(times)),
            "p50_ms": float(np.percentile(times, 50)),
            "p95_ms": float(np.percentile(times, 95)),
            "max_ms": float(np.max(times)),
        })
    return pd.DataFrame(rows)


@contextmanager
def local_client():
    """Klient aplikacji uruchomionej w tym samym procesie, z tymczasową bazą i atlasem ćwiczeń."""
    for name in (ClassifierName.DECISION_TREE, ClassifierName.MLP):
        if not model_path(name).exists():
            raise SystemExit("Brak wytrenowanych modeli. Uruchom najpierw: python -m app.ml.train")
    with TemporaryDirectory() as directory:
        engine = create_engine(f"sqlite:///{directory}/latency.db")
        Base.metadata.create_all(bind=engine)
        session = sessionmaker(bind=engine)()
        seed_exercises(session)
        app.dependency_overrides[get_db] = lambda: session
        try:
            yield TestClient(app)
        finally:
            app.dependency_overrides.clear()
            session.close()
            engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Wdrożenie: czas obejmuje sieć. Darmowy serwer po przerwie startuje do ok. minuty.
        with httpx.Client(base_url=sys.argv[1], timeout=120) as remote:
            print(measure_api_latency(remote, REMOTE_REQUESTS).round(1).to_string(index=False))
    else:
        with local_client() as client:
            results = measure_api_latency(client, LOCAL_REQUESTS)
        results.round(2).to_csv(OUTPUT_PATH, index=False)
        print(results.round(2).to_string(index=False))
