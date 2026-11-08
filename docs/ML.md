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
| `pushups`             | pompki bez przerwy (opcjonalne)               | liczba; z kolan · 0,77*       |
| `squats`              | przysiady w 1 minutę (opcjonalne)             | liczba                        |
| `plank_seconds`       | czas deski (opcjonalne)                       | sekundy                       |
| `resting_heart_rate`  | tętno spoczynkowe (opcjonalne)                | uderzenia/min                 |
| `strength_index`      | serie w 5 ćwiczeniach z ciężarami (tylko trenujący) | wskaźnik siły względnej** |

Brak odpowiedzi na pytanie opcjonalne jest zapisywany jako wartość brakująca (NaN).

\* Pompki z kolan obciążają ok. 49% masy ciała, a klasyczne ok. 64% (Ebben i in., 2011), więc
wynik z kolan przeliczany jest na równoważną liczbę pompek klasycznych (· 0,49 / 0,64 ≈ 0,77).

\*\* Wskaźnik siły (`app/services/strength.py`): dla każdego podanego ćwiczenia 1RM ze wzoru Epleya
dzielony jest przez masę ciała i przez normę osoby średniozaawansowanej dla danej płci, a wyniki
są uśredniane. 1,0 oznacza poziom normy, 0,5 połowę normy. Normy (1RM / masa ciała):

| Ćwiczenie                   | Mężczyźni | Kobiety |
|-----------------------------|-----------|---------|
| przysiad ze sztangą         | 1,25      | 1,0     |
| martwy ciąg                 | 1,5       | 1,25    |
| wyciskanie sztangi leżąc    | 1,0       | 0,65    |
| wyciskanie nad głowę        | 0,65      | 0,45    |
| podciąganie (z masą ciała)  | 1,3       | 1,0     |

Uśrednienie sprawia, że wskaźnik działa przy dowolnej liczbie podanych ćwiczeń, a modele dostają
jedną cechę zamiast kilku silnie ze sobą powiązanych. Brak wskaźnika u osób, które nie trenują
z ciężarami, nie jest pominięciem odpowiedzi, dlatego nie liczy się do pustych odpowiedzi
(`CONDITIONAL_FEATURES` w `app/ml/features.py`).

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
5. Wskaźnik siły: osoba trenuje z ciężarami z prawdopodobieństwem zależnym od stażu
   (5%, 30%, 60%, 80% dla stażu 0–3, łącznie ok. 1/3 osób). U trenujących
   wskaźnik = 0,25 + 0,01·*S* + 0,05·*E* + N(0; 0,12), obcięty do 0,1–3; u pozostałych brak.
   Wskaźnik jest losowany osobnym generatorem liczb losowych, więc jego dodanie nie zmieniło
   pozostałych cech ani braków (te same osoby co w pierwszej wersji danych).
6. Etykieta: *S* < 42 → `beginner`, 42 ≤ *S* < 60 → `intermediate`, *S* ≥ 60 → `advanced`.
   Daje to zbliżone liczności klas (ok. 35% / 31% / 34%).
7. Braki danych: każda odpowiedź opcjonalna jest usuwana z prawdopodobieństwem `missing_rate`.

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
| wskaźnik siły         | < 0,7          | 0,7–0,99     | ≥ 1,0         |

Od 50. roku życia progi dla pompek są obniżone o 30%. Średnia punktów poniżej 2/3 oznacza
poziom `beginner`, poniżej 4/3 `intermediate`, w pozostałych przypadkach `advanced`.
Brakujące wskaźniki są pomijane przy liczeniu średniej.

Progi reguł są ustalone niezależnie od wzorów generatora (na wzór typowych norm sprawnościowych),
więc system regułowy nie ma z góry zagwarantowanej trafności.

## Modele uczenia maszynowego

`app/ml/models.py`. Oba modele to potoki scikit-learn, które zaczynają od uzupełnienia braków
medianą z dodaniem kolumn 0/1 oznaczających brak (`SimpleImputer(add_indicator=True)`).

- **Drzewo decyzyjne:** głębokość maks. 6, min. 5 próbek w liściu (ograniczenie przeuczenia).
- **Sieć neuronowa (MLP):** standaryzacja cech, warstwy ukryte 64 i 32 neurony,
  wczesne zatrzymanie uczenia (`early_stopping`). Do czasu dodania wskaźnika siły stosowano
  warstwy 32 i 16 neuronów; zmianę opisuje dobór hiperparametrów.

Ustawienia dobrano walidacją krzyżową (`experiments/tuning.py`, opis w
[EXPERIMENTS.md](EXPERIMENTS.md#dobór-hiperparametrów)).

## Uczenie i wyniki wstępne

`python -m app.ml.train` (ok. 5 s): 5000 osób, 20% brakujących odpowiedzi opcjonalnych,
podział 75% / 25% ze stratyfikacją, `seed = 42`.

| Klasyfikator       | Accuracy | F1 makro |
|--------------------|----------|----------|
| System regułowy    | 0,804    | 0,802    |
| Drzewo decyzyjne   | 0,816    | 0,812    |
| Sieć neuronowa     | 0,874    | 0,871    |

Wyniki z jednego podziału zależą od losowania, dlatego porównanie metod opiera się na
eksperymentach z wieloma powtórzeniami ([EXPERIMENTS.md](EXPERIMENTS.md)).

Szczegółowe porównanie (macierze pomyłek, wpływ kompletności danych, wiele powtórzeń):
[EXPERIMENTS.md](EXPERIMENTS.md).

Następnie każdy klasyfikator jest oceniany na osobach testowych przy 0, 1, …, 5 pustych
odpowiedziach opcjonalnych (staż i cztery testy sprawności; które odpowiedzi znikają, jest
losowane). Ocena jest powtarzana 5 razy na różnie wylosowanych danych (`SELECTION_SEEDS`:
nowe osoby, nowy podział, modele uczone od nowa), a wyniki są uśredniane. Pojedynczy podział
nie wystarcza: przy 5 pustych odpowiedziach zwycięzca zmieniał się zależnie od losowania.
Dla każdej liczby braków wybierany jest klasyfikator z najwyższym średnim F1 makro
(przy remisie decyduje accuracy). Wdrażane są modele z pierwszego powtórzenia (`seed = 42`).
Wybór i metryki trafiają do `app/ml/artifacts/best_classifier.json`.

| Puste odpowiedzi | System regułowy | Drzewo decyzyjne | Sieć neuronowa | Wybrany  |
|------------------|-----------------|------------------|----------------|----------|
| 0                | 0,809 ± 0,014   | 0,825 ± 0,010    | 0,873 ± 0,004  | sieć     |
| 1                | 0,794 ± 0,008   | 0,814 ± 0,009    | 0,865 ± 0,004  | sieć     |
| 2                | 0,765 ± 0,011   | 0,793 ± 0,014    | 0,850 ± 0,007  | sieć     |
| 3                | 0,722 ± 0,016   | 0,741 ± 0,026    | 0,815 ± 0,012  | sieć     |
| 4                | 0,695 ± 0,006   | 0,646 ± 0,067    | 0,773 ± 0,005  | sieć     |
| 5                | 0,675 ± 0,003   | 0,452 ± 0,194    | 0,702 ± 0,013  | sieć     |

Przy obecnych danych i modelach sieć jest najlepsza przy każdej liczbie braków, także przy samych
danych podstawowych (0,702 wobec 0,675 reguł). W pierwszej wersji, bez wskaźnika siły i z siecią
(32, 16), przy 5 pustych odpowiedziach wybierany był system regułowy (0,654 wobec 0,650).
Mechanizm doboru pozostaje: przełączy klasyfikator, jeśli po zmianie danych lub modeli w ocenie
wygra inny.

Aplikacja liczy puste odpowiedzi w profilu użytkownika i klasyfikuje go klasyfikatorem wybranym
dla tej liczby. Gdy pliku nie ma (modele niewytrenowane), używany jest system regułowy.

## Użycie w API

`GET /api/v1/profiles/{id}/fitness-level` klasyfikuje klasyfikatorem wybranym dla liczby
pustych odpowiedzi w profilu.
Parametr `method` (`rules`, `decision_tree`, `mlp`) wymusza inny klasyfikator i służy
tylko eksperymentom porównawczym; interfejs użytkownika go nie używa.
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
