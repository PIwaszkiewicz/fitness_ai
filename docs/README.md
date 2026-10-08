# Dokumentacja techniczna

## Struktura katalogów

| Katalog / plik          | Rola                                                          |
|-------------------------|---------------------------------------------------------------|
| `app/main.py`           | Punkt wejścia: tworzy aplikację FastAPI, CORS, routery        |
| `app/api/deps.py`       | Wspólne zależności endpointów (sesja bazy, stronicowanie)     |
| `app/api/v1/endpoints/` | Endpointy HTTP wersji 1 API (prefiks `/api/v1`)               |
| `app/core/`             | Konfiguracja aplikacji i połączenie z bazą danych             |
| `app/models/`           | Modele bazy danych (SQLAlchemy) i słowniki wartości (enumy)   |
| `app/schemas/`          | Schematy walidacji danych wejściowych i odpowiedzi (Pydantic) |
| `app/services/`         | Logika biznesowa łącząca API, bazę danych i moduły ML         |
| `app/ml/`               | Moduły AI: klasyfikacja sprawności, generowanie planów        |
| `app/data/`             | Dane startowe, m.in. atlas ćwiczeń (`exercises.json`)         |
| `app/seed.py`           | Skrypt wypełniający bazę atlasem ćwiczeń                      |
| `tests/`                | Testy automatyczne (pytest)                                   |
| `docs/`                 | Dokumentacja projektu                                         |
| `.github/workflows/`    | Ciągła integracja (GitHub Actions)                            |
| `docs/PLAN.md`          | Plan projektu z listą kroków                                  |
| `CONTEXT.md`            | Opis projektu, cele i zakres pracy                            |
| `requirements.txt`      | Lista zależności Pythona                                      |

## Uruchomienie lokalne

```bash
# 1. Utworzenie i aktywacja środowiska wirtualnego (Python 3.12)
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Instalacja zależności
pip install -r requirements.txt

# 3. Wypełnienie bazy startowym atlasem ćwiczeń (można uruchamiać wielokrotnie)
python -m app.seed

# 4. Uruchomienie serwera (adres: http://127.0.0.1:8000, dokumentacja: /docs)
uvicorn app.main:app --reload

# 5. Testy i sprawdzenie jakości kodu
pytest
ruff check .
```

## Zmienne środowiskowe

| Zmienna        | Domyślnie                                     | Opis                         |
|----------------|-----------------------------------------------|------------------------------|
| `PROJECT_NAME` | `Fitness AI`                                  | Nazwa wyświetlana w API      |
| `VERSION`      | `0.1.0`                                       | Wersja zwracana przez /health |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Dozwolone adresy frontendu   |
| `DATABASE_URL` | `sqlite:///./fitness_ai.db`                   | Adres bazy danych            |

## Baza danych

Tabele tworzone są automatycznie przy starcie serwera (plik `fitness_ai.db`, wykluczony z repozytorium).

| Tabela          | Zawartość                                                                       |
|-----------------|---------------------------------------------------------------------------------|
| `user_profiles` | Wiek, płeć, wzrost, waga, cel treningowy, poziom aktywności, ograniczenia        |
| `exercises`     | Nazwa, grupa mięśniowa, sprzęt, poziom trudności, przeciwwskazania               |

Ograniczenia użytkownika i przeciwwskazania ćwiczeń korzystają z tego samego słownika
(`Limitation` w `app/models/enums.py`), więc konflikt wykrywa się porównaniem dwóch zbiorów.

Zakresy walidacji danych profilu: wiek 16–100 lat, wzrost 120–230 cm, waga 30–300 kg.

Przeciwwskazania w atlasie są uproszczone i służą celom projektu; nie zastępują konsultacji
z lekarzem ani fizjoterapeutą.

## Endpointy API v1

| Metoda i ścieżka                   | Opis                                                        |
|------------------------------------|-------------------------------------------------------------|
| `GET /api/v1/ping`                 | Test działania routera                                      |
| `POST /api/v1/profiles`            | Utworzenie profilu (201, błędne dane: 422)                  |
| `GET /api/v1/profiles`             | Lista profili (`skip`, `limit`)                             |
| `GET /api/v1/profiles/{id}`        | Odczyt profilu (brak: 404)                                  |
| `PUT /api/v1/profiles/{id}`        | Zastąpienie danych profilu                                  |
| `DELETE /api/v1/profiles/{id}`     | Usunięcie profilu (204)                                     |
| `POST /api/v1/exercises`           | Dodanie ćwiczenia (zajęta nazwa: 409)                       |
| `GET /api/v1/exercises`            | Lista ćwiczeń, filtry `muscle_group`, `equipment`, `difficulty` |
| `GET /api/v1/exercises/{id}`       | Odczyt ćwiczenia                                            |
| `PUT /api/v1/exercises/{id}`       | Zastąpienie danych ćwiczenia                                |
| `DELETE /api/v1/exercises/{id}`    | Usunięcie ćwiczenia (204)                                   |

Pełna, interaktywna dokumentacja jest dostępna po uruchomieniu serwera pod adresem `/docs`.
