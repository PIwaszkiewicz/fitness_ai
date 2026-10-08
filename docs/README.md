# Dokumentacja techniczna

## Struktura katalogów

| Katalog / plik          | Rola                                                          |
|-------------------------|---------------------------------------------------------------|
| `app/main.py`           | Punkt wejścia: tworzy aplikację FastAPI, CORS, routery        |
| `app/api/v1/`           | Endpointy HTTP wersji 1 API (prefiks `/api/v1`)               |
| `app/core/`             | Konfiguracja aplikacji i połączenie z bazą danych             |
| `app/models/`           | Modele bazy danych (SQLAlchemy) i słowniki wartości (enumy)   |
| `app/schemas/`          | Schematy walidacji danych wejściowych i odpowiedzi (Pydantic) |
| `app/services/`         | Logika biznesowa łącząca API, bazę danych i moduły ML         |
| `app/ml/`               | Moduły AI: klasyfikacja sprawności, generowanie planów        |
| `tests/`                | Testy automatyczne (pytest)                                   |
| `docs/`                 | Dokumentacja projektu                                         |
| `.github/workflows/`    | Ciągła integracja (GitHub Actions)                            |
| `CONTEXT.md`            | Opis projektu, cele i zakres pracy                            |
| `requirements.txt`      | Lista zależności Pythona                                      |

## Uruchomienie lokalne

```bash
# 1. Utworzenie i aktywacja środowiska wirtualnego (Python 3.12)
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Instalacja zależności
pip install -r requirements.txt

# 3. Uruchomienie serwera (adres: http://127.0.0.1:8000, dokumentacja: /docs)
uvicorn app.main:app --reload

# 4. Testy i sprawdzenie jakości kodu
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
