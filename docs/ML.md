# Moduł klasyfikacji poziomu sprawności

Moduł przypisuje użytkownikowi jeden z trzech poziomów sprawności: `beginner`, `intermediate`,
`advanced`. Porównywane są trzy podejścia: system regułowy (punkt odniesienia), drzewo decyzyjne
i sieć neuronowa (perceptron wielowarstwowy).

## Cechy wejściowe

| Cecha                 | Źródło w kwestionariuszu                      | Kodowanie                     |
|-----------------------|-----------------------------------------------|-------------------------------|
| `age`                 | wiek                                          | liczba                        |
| `is_male`             | płeć                                          | 1 – mężczyzna, 0 – kobieta    |
| `bmi`                 | wzrost i masa ciała                           | masa / wzrost² (m)            |
| `activity_level`      | poziom aktywności                             | 0 (siedzący) – 4 (b. wysoki)  |
| `training_experience` | staż treningowy (opcjonalne)                  | 0 (brak) – 3 (ponad 3 lata)   |
| `pushups`             | pompki bez przerwy (opcjonalne)               | liczba                        |
| `squats`              | przysiady w 1 minutę (opcjonalne)             | liczba                        |
| `plank_seconds`       | czas deski (opcjonalne)                       | sekundy                       |
| `resting_heart_rate`  | tętno spoczynkowe (opcjonalne)                | uderzenia/min                 |

Brak odpowiedzi na pytanie opcjonalne jest zapisywany jako wartość brakująca (NaN).

## Generator danych syntetycznych

Nie istnieje publiczny zbiór danych łączący wyniki prostych testów sprawności z oceną poziomu,
dlatego dane są generowane według jawnego modelu (`app/ml/data_generator.py`).

**Założenie:** każda osoba ma ukrytą, „prawdziwą” sprawność *S* (0–100). Wyniki testów są jej
niedokładnymi pomiarami, a poziom sprawności (etykieta) wynika z *S*. Klasyfikatory nie widzą *S*,
tylko zaszumione wyniki testów, tak jak w rzeczywistości.

1. Cechy osoby:
   - płeć: 50% / 50%,
   - wiek: jednostajnie 16–75 lat,
   - wzrost: N(178, 7) cm u mężczyzn, N(165, 6,5) cm u kobiet,
   - aktywność *A* (0–4) z prawdopodobieństwami 25%, 25%, 25%, 15%, 10%,
   - staż *E* (0–3): zaokrąglone 0,6·*A* + N(0; 0,9), bo osoby aktywne częściej trenują dłużej.
2. Prawdziwa sprawność:
   *S* = 35 + 9·*A* + 7·*E* − 0,35·max(wiek − 30, 0) + N(0, 8), obcięta do 0–100.
3. Masa ciała: BMI = 26 − 0,08·(*S* − 50) + N(0; 3,5), obcięte do 16–45.
4. Wyniki testów (zaokrąglone i obcięte do zakresów kwestionariusza):
   - pompki: *S* · (0,5 u mężczyzn, 0,32 u kobiet) · N(1; 0,15) − 0,4·max(BMI − 25, 0),
   - przysiady: 0,55·*S* + 5 − 0,1·max(wiek − 40, 0) + N(0, 5),
   - deska: 2,2·*S* + N(0, 20) sekund,
   - tętno spoczynkowe: 85 − 0,3·*S* + N(0, 6).
5. Etykieta: *S* < 42 → `beginner`, 42 ≤ *S* < 60 → `intermediate`, *S* ≥ 60 → `advanced`.
   Daje to zbliżone liczności klas (ok. 35% / 31% / 34%).
6. Braki danych: każda odpowiedź opcjonalna jest usuwana z prawdopodobieństwem `missing_rate`.

Ten sam `seed` zawsze daje te same dane, co zapewnia powtarzalność eksperymentów.

## System regułowy (punkt odniesienia)

`app/ml/rule_based.py`. Każdy dostępny wskaźnik dostaje 0, 1 lub 2 punkty:

| Wskaźnik              | 0 pkt          | 1 pkt        | 2 pkt         |
|-----------------------|----------------|--------------|---------------|
| aktywność             | siedząca, niska| umiarkowana  | wysoka, b. wysoka |
| staż                  | brak, < 1 rok  | 1–3 lata     | > 3 lata      |
| pompki (mężczyźni)    | < 15           | 15–29        | ≥ 30          |
| pompki (kobiety)      | < 8            | 8–19         | ≥ 20          |
| przysiady / min       | < 25           | 25–39        | ≥ 40          |
| deska                 | < 60 s         | 60–119 s     | ≥ 120 s       |
| tętno spoczynkowe     | > 80           | 65–80        | < 65          |

Od 50. roku życia progi dla pompek są obniżone o 30%. Średnia punktów poniżej 2/3 oznacza
poziom `beginner`, poniżej 4/3 `intermediate`, w pozostałych przypadkach `advanced`.
Brakujące wskaźniki są pomijane przy liczeniu średniej.

Progi reguł są ustalone niezależnie od wzorów generatora (na wzór typowych norm sprawnościowych),
więc system regułowy nie ma z góry zagwarantowanej trafności.

## Modele uczenia maszynowego

`app/ml/models.py`. Oba modele to potoki scikit-learn, które zaczynają od uzupełnienia braków
medianą z dodaniem kolumn 0/1 oznaczających brak (`SimpleImputer(add_indicator=True)`).

- **Drzewo decyzyjne:** głębokość maks. 6, min. 20 próbek w liściu (ograniczenie przeuczenia).
- **Sieć neuronowa (MLP):** standaryzacja cech, warstwy ukryte 32 i 16 neuronów,
  wczesne zatrzymanie uczenia (`early_stopping`).

## Uczenie i wyniki wstępne

`python -m app.ml.train`: 5000 osób, 20% brakujących odpowiedzi opcjonalnych,
podział 75% / 25% ze stratyfikacją, `seed = 42`.

| Klasyfikator       | Accuracy | F1 makro |
|--------------------|----------|----------|
| System regułowy    | 0,794    | 0,792    |
| Drzewo decyzyjne   | 0,820    | 0,817    |
| Sieć neuronowa     | 0,861    | 0,857    |

Szczegółowe porównanie (macierze pomyłek, wpływ kompletności danych, wiele powtórzeń):
[EXPERIMENTS.md](EXPERIMENTS.md).

## Użycie w API

`GET /api/v1/profiles/{id}/fitness-level?method=mlp` (`rules`, `decision_tree`, `mlp`).
Zwraca poziom, prawdopodobieństwa poziomów (dla modeli ML) i kompletność danych profilu.
Modele są wczytywane z `app/ml/artifacts/` przy pierwszym użyciu i zapamiętywane w pamięci.
Gdy plik modelu nie istnieje, endpoint zwraca 503. System regułowy działa zawsze.

## Ograniczenia

- Dane są syntetyczne: wyniki pokazują, jak dobrze klasyfikatory odtwarzają przyjęty model
  generowania, a nie trafność na prawdziwych użytkownikach.
- Współczynniki generatora i progi reguł są założeniami projektowymi i wymagają uzasadnienia
  w literaturze dotyczącej norm sprawności.

## Wykrywanie przeciwwskazań ćwiczeń

`app/ml/contraindication_detection.py` przewiduje przeciwwskazania nowego ćwiczenia na podstawie
wzorca ruchu, grupy mięśniowej, sprzętu i trudności. Dostępne są: reguły eksperckie, drzewo
decyzyjne uczone na atlasie i detektor hybrydowy (suma obu). Porównanie: [EXPERIMENTS.md](EXPERIMENTS.md),
eksperyment 3.
