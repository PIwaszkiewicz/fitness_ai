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
| `app/ml/`               | Moduły AI: klasyfikacja sprawności (opis: `docs/ML.md`)       |
| `app/data/`             | Dane: atlas ćwiczeń (`exercises.json`), pytania (`questions.py`) |
| `app/seed.py`           | Skrypt wypełniający bazę atlasem ćwiczeń                      |
| `experiments/`          | Eksperymenty badawcze i zapis do MLflow (opis: `docs/EXPERIMENTS.md`) |
| `tests/`                | Testy automatyczne (pytest)                                   |
| `docs/`                 | Dokumentacja projektu                                         |
| `.github/workflows/`    | Ciągła integracja (GitHub Actions)                            |
| `Dockerfile`            | Przepis na obraz kontenera z serwerem API                     |
| `docker-compose.yml`    | Uruchomienie całego systemu jednym poleceniem                 |
| `docs/PLAN.md`          | Plan projektu z listą kroków                                  |
| `CONTEXT.md`            | Opis projektu, cele i zakres pracy                            |
| `requirements.txt`      | Zależności potrzebne do działania serwera                     |
| `requirements-dev.txt`  | Dodatkowo testy, ruff i narzędzia do eksperymentów            |

## Uruchomienie lokalne

```bash
# 1. Utworzenie i aktywacja środowiska wirtualnego (Python 3.12)
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Instalacja zależności (serwer + testy, ruff, MLflow)
pip install -r requirements-dev.txt

# 3. Wypełnienie bazy startowym atlasem ćwiczeń (można uruchamiać wielokrotnie)
python -m app.seed

# 4. Uczenie modeli klasyfikacji sprawności (zapis do app/ml/artifacts/)
python -m app.ml.train

# 5. Uruchomienie serwera (adres: http://127.0.0.1:8000, dokumentacja: /docs)
uvicorn app.main:app --reload

# 6. Testy i sprawdzenie jakości kodu
pytest
ruff check .

# 7. Eksperymenty badawcze (wyniki w docs/experiments/) i ich przeglądanie w MLflow
python -m experiments.run
mlflow ui
```

## Uruchomienie w Dockerze

Wymaga zainstalowanego i uruchomionego Docker Desktop.

```bash
# Budowa obrazu i start serwera (adres: http://localhost:8000/docs)
docker compose up --build

# Zatrzymanie (dane w bazie zostają w wolumenie fitness_data)
docker compose down

# Zatrzymanie i usunięcie danych
docker compose down -v
```

Modele ML są uczone podczas budowy obrazu. Przy starcie kontener sam tworzy tabele i wgrywa atlas ćwiczeń. Baza SQLite leży w wolumenie
`fitness_data` (katalog `/data` w kontenerze), więc przetrwa usunięcie i ponowne utworzenie kontenera.
CI przy każdym pull requeście buduje obraz, uruchamia kontener i sprawdza endpoint `/health`.

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
| `user_profiles` | Odpowiedzi z kwestionariusza: dane podstawowe, zdrowie, testy, preferencje, kompletność |
| `exercises`     | Nazwa, grupa mięśniowa, sprzęt, poziom trudności, przeciwwskazania               |

Ograniczenia użytkownika i przeciwwskazania ćwiczeń korzystają z tego samego słownika
(`Limitation` w `app/models/enums.py`), więc konflikt wykrywa się porównaniem dwóch zbiorów.

Zakresy walidacji danych profilu: wiek 16–100 lat, wzrost 120–230 cm, waga 30–300 kg.

Tabele tworzy `create_all`, który nie modyfikuje istniejących tabel. Po zmianie modeli
lokalną bazę trzeba odtworzyć: usunąć plik `fitness_ai.db` i ponownie uruchomić `python -m app.seed`.

## Kwestionariusz

Pytania są zdefiniowane w `app/data/questions.py` i udostępniane przez `GET /api/v1/questionnaire`.
Frontend buduje z nich formularz, więc zmiana pytań nie wymaga zmian w interfejsie.

| Sekcja                 | Pytania                                                           | Wymagane |
|------------------------|-------------------------------------------------------------------|----------|
| Dane podstawowe        | wiek, płeć, wzrost, waga, cel, aktywność                          | tak      |
| Dane podstawowe        | staż treningowy                                                   | nie      |
| Zdrowie i ograniczenia | kontuzje i schorzenia, poziom bólu*, zgoda lekarza**              | nie      |
| Testy sprawności       | pompki, przysiady w 1 min, deska, tętno spoczynkowe               | nie      |
| Preferencje            | dni treningowe w tygodniu, długość treningu, dostępny sprzęt      | nie      |

\* tylko przy zgłoszonych ograniczeniach, \*\* tylko przy nadciśnieniu lub chorobie serca.
Odpowiedź na pytanie, którego warunek nie jest spełniony, jest odrzucana (422).

**Kompletność danych** (`data_completeness`, 0–100) to procent pytań opcjonalnych, na które
odpowiedziano, liczony tylko spośród pytań widocznych dla danego użytkownika.

**Ostrzeżenia zdrowotne** nie blokują zapisu profilu, a wskazują potrzebę konsultacji:
choroba układu krążenia bez zgody lekarza, ból od 7/10, tętno spoczynkowe powyżej 100/min.

Przeciwwskazania w atlasie są uproszczone i służą celom projektu; nie zastępują konsultacji
z lekarzem ani fizjoterapeutą.

## Plan treningowy

Plan jest generowany na żądanie z aktualnego profilu (`app/services/plan_generator.py`),
więc po aktualizacji profilu kolejne zapytanie zwraca plan dostosowany do nowych danych.

1. Poziom sprawności wyznacza wybrany klasyfikator (gdy model ML nie jest wytrenowany,
   używany jest system regułowy).
2. Dopuszczone są ćwiczenia z dostępnym sprzętem (masa ciała zawsze), o trudności
   nie większej niż poziom sprawności i **bez przeciwwskazań** dla ograniczeń użytkownika.
3. Serie, powtórzenia i przerwy zależą od celu (np. siła: 4 × 4–6, przerwa 150 s);
   osoby początkujące wykonują jedną serię mniej.
4. Liczba ćwiczeń (3–8) wynika z długości treningu po odjęciu 10 minut rozgrzewki.
5. Przy 1–3 dniach w tygodniu każdy trening obejmuje całe ciało, przy 4–7 dniach
   treningi góry i dołu ciała następują na zmianę. Ćwiczenia rotują między dniami.
6. Plan zawiera rekomendacje progresji i ostrzeżenia zdrowotne z kwestionariusza.

Domyślnie (gdy brak odpowiedzi): 3 dni w tygodniu, 45 minut, ćwiczenia z masą ciała.

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
| `GET /api/v1/questionnaire`        | Definicja pytań kwestionariusza z warunkami wyświetlania    |
| `POST /api/v1/questionnaire`       | Wysłanie odpowiedzi: profil, braki w danych, ostrzeżenia    |
| `GET /api/v1/profiles/{id}/fitness-level` | Poziom sprawności, `method`: `rules`, `decision_tree`, `mlp` |
| `GET /api/v1/profiles/{id}/plan`   | Tygodniowy plan treningowy (`method` jak wyżej)             |

Pełna, interaktywna dokumentacja jest dostępna po uruchomieniu serwera pod adresem `/docs`.
