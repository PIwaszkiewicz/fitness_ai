# Eksperymenty: porównanie klasyfikatorów sprawności

Opis klasyfikatorów i generatora danych: [ML.md](ML.md).
Kod: `experiments/evaluation.py` (eksperymenty), `experiments/run.py` (zapis wyników i wykresów).

## Metodyka

- Każdy eksperyment (poza doborem hiperparametrów) powtórzono dla 5 ziaren losowania
  (`seed` 1–5). Dla każdego ziarna wygenerowano nowy zbiór 5000 osób i podzielono go na część
  uczącą (75%) i testową (25%) z zachowaniem proporcji poziomów. Wyniki podano jako średnią ± odchylenie standardowe.
- Klasyfikatory ML uczą się na danych, w których 20% odpowiedzi opcjonalnych jest pominiętych
  (typowa kompletność kwestionariusza).
- Metryki:
  - **accuracy:** odsetek poprawnych klasyfikacji,
  - **F1 makro:** średnia miar F1 dla trzech poziomów (każdy poziom ma tę samą wagę),
  - **macierz pomyłek:** jaka część osób z danego poziomu trafiła do każdej klasy,
  - **czas uczenia** i **czas klasyfikacji jednej osoby** (odpowiada jednemu żądaniu API).
- Wszystkie przebiegi są zapisywane w MLflow (eksperymenty `dobor-hiperparametrow`,
  `porownanie-klasyfikatorow`, `wplyw-kompletnosci`, `istotnosc-roznic`, `wykrywanie-przeciwwskazan`
  i `jakosc-planu`).

Odtworzenie wyników:

```bash
pip install -r requirements-dev.txt
python -m experiments.run      # ok. 1 min, wyniki w docs/experiments/
python -m experiments.api_latency   # czas odpowiedzi API (wymaga python -m app.ml.train)
mlflow ui                      # przeglądanie przebiegów: http://127.0.0.1:5000
```

## Dobór hiperparametrów

**Pytanie:** jakie ustawienia modeli ML (głębokość drzewa, rozmiar sieci) przyjąć?

**Metodyka** (`experiments/tuning.py`):
- Przeszukiwanie siatki (`GridSearchCV`) z 5-krotną walidacją krzyżową: dane uczące dzielone są
  na 5 części, model uczy się na 4 i jest oceniany na piątej, kolejno dla każdej części.
- Dane: część ucząca zbioru z `seed = 42` (3750 osób, 20% braków), ten sam zbiór co przy uczeniu
  modeli dla aplikacji. Dane testowe nie biorą udziału w doborze, więc nie zawyżają późniejszej oceny.
- Miara: F1 makro (średnia ± odchylenie z 5 części).
- Siatki: drzewo – głębokość {3, 4, 6, 8, 10, bez limitu} × min. próbek w liściu {1, 5, 20, 50};
  sieć – warstwy ukryte {(16), (32), (32, 16), (64, 32)} × regularyzacja L2 `alpha` {0,0001; 0,001; 0,01}.
- Wybór według **reguły jednego odchylenia standardowego**: spośród ustawień, których wynik jest
  gorszy od najlepszego o mniej niż jego odchylenie standardowe, wybiera się najprostsze. Różnica
  mniejsza niż odchylenie mieści się w losowej zmienności, a prostszy model łatwiej zinterpretować
  i trudniej go przeuczyć.

Wyniki (`docs/experiments/tuning.csv`, pięć najlepszych ustawień każdego modelu):

| Model            | Ustawienia                            | F1 makro (CV)   |
|------------------|---------------------------------------|-----------------|
| Drzewo decyzyjne | głębokość 10, min. 5 w liściu         | 0,816 ± 0,009   |
| Drzewo decyzyjne | głębokość 8, min. 5 w liściu          | 0,814 ± 0,013   |
| Drzewo decyzyjne | bez limitu, min. 5 w liściu           | 0,811 ± 0,013   |
| Drzewo decyzyjne | głębokość 10, min. 1 w liściu         | 0,810 ± 0,008   |
| Drzewo decyzyjne | **głębokość 6, min. 5 w liściu**      | **0,809 ± 0,008** |
| Sieć neuronowa   | **(32, 16), alpha 0,0001**            | **0,860 ± 0,008** |
| Sieć neuronowa   | (32, 16), alpha 0,001                 | 0,858 ± 0,006   |
| Sieć neuronowa   | (32, 16), alpha 0,01                  | 0,857 ± 0,007   |
| Sieć neuronowa   | (64, 32), alpha 0,01                  | 0,855 ± 0,021   |
| Sieć neuronowa   | (16), alpha 0,001                     | 0,851 ± 0,016   |

**Wnioski:**

1. **Sieć neuronowa:** wstępnie przyjęte ustawienia (32 i 16 neuronów, `alpha` 0,0001) okazały się
   najlepsze. Sieć z jedną warstwą wypada wyraźnie gorzej, a większa (64, 32) nie daje poprawy.
2. **Drzewo decyzyjne:** najlepsze jest drzewo o głębokości 10 (0,816), ale drzewo o głębokości 6
   mieści się w granicy jednego odchylenia (próg 0,807), a ma do 16 razy mniej liści, więc jego
   reguły da się przeczytać. Wstępne ustawienie (min. 20 próbek w liściu, 0,799) było poza tą
   granicą, dlatego zmieniono je na **min. 5 próbek w liściu**.
3. Na zbiorach testowych zmiana drzewa nie przyniosła wyraźnej poprawy (accuracy 0,806 wobec
   0,808 wcześniej, w granicach odchylenia), więc dobór parametrów potwierdza przede wszystkim,
   że wyniki porównania nie wynikają z przypadkowo złych ustawień modeli.

## Eksperyment 1: porównanie klasyfikatorów

Dane testowe z 20% pominiętych odpowiedzi opcjonalnych (`docs/experiments/comparison.csv`).

| Klasyfikator       | Accuracy        | F1 makro        | Czas uczenia | Czas klasyfikacji 1 osoby |
|--------------------|-----------------|-----------------|--------------|---------------------------|
| System regułowy    | 0,792 ± 0,003   | 0,792 ± 0,003   | —            | 0,02 ms                   |
| Drzewo decyzyjne   | 0,806 ± 0,010   | 0,806 ± 0,011   | 0,01 s       | 0,41 ms                   |
| Sieć neuronowa     | 0,866 ± 0,012   | 0,864 ± 0,012   | 0,14 s       | 0,52 ms                   |

![Macierze pomyłek](experiments/confusion_matrices.png)

**Obserwacje:**

1. Sieć neuronowa osiąga najwyższą trafność, o ok. 7 punktów procentowych wyższą od systemu
   regułowego i o ok. 6 p.p. wyższą od drzewa decyzyjnego. Obie różnice są istotne statystycznie
   (zob. [test McNemara](#istotność-statystyczna-różnic-między-klasyfikatorami)).
2. Żadna osoba początkująca nie została zaklasyfikowana jako zaawansowana. Pomyłka odwrotna
   (zaawansowany uznany za początkującego) zdarzyła się sporadycznie: 0,1–0,2% osób, czyli kilka
   na ok. 2000 zaawansowanych. Pozostałe błędy dotyczą poziomów sąsiednich. Ma to znaczenie dla
   bezpieczeństwa: osoba początkująca nie dostanie planu dla zaawansowanych.
3. Najtrudniejszy do rozpoznania jest poziom średni (70–78% poprawnych), bo graniczy z oboma
   pozostałymi.
4. Czas klasyfikacji jednej osoby jest poniżej 1 ms dla wszystkich metod, więc wybór
   klasyfikatora nie wpływa na czas odpowiedzi API.

## Eksperyment 2: wpływ kompletności danych

Te same osoby testowe oceniane przy coraz większym odsetku pominiętych odpowiedzi opcjonalnych
(staż i cztery testy sprawności). Przy 100% zostają tylko dane podstawowe: wiek, płeć, BMI
i poziom aktywności (`docs/experiments/completeness.csv`).

| Pominięte odpowiedzi | System regułowy | Drzewo decyzyjne | Sieć neuronowa  |
|----------------------|-----------------|------------------|-----------------|
| 0%                   | 0,806 ± 0,009   | 0,825 ± 0,013    | 0,879 ± 0,011   |
| 20%                  | 0,789 ± 0,005   | 0,798 ± 0,012    | 0,860 ± 0,010   |
| 40%                  | 0,760 ± 0,009   | 0,765 ± 0,014    | 0,832 ± 0,016   |
| 60%                  | 0,732 ± 0,005   | 0,710 ± 0,031    | 0,800 ± 0,007   |
| 80%                  | 0,695 ± 0,005   | 0,610 ± 0,065    | 0,733 ± 0,020   |
| 100%                 | 0,675 ± 0,004   | 0,484 ± 0,125    | 0,648 ± 0,054   |

![Wpływ kompletności danych](experiments/completeness.png)

**Obserwacje:**

1. Trafność wszystkich metod spada wraz z ubywaniem danych. Wyniki testów sprawności niosą
   istotną informację, której nie zastąpią same dane podstawowe.
2. Do ok. 60% braków sieć neuronowa pozostaje najlepsza.
3. System regułowy traci trafność najwolniej i przy samych danych podstawowych (100% braków)
   jest najlepszy. Reguły pomijają brakujące wskaźniki, a modele ML uczone przy 20% braków
   trafiają na dane wyraźnie inne niż w czasie uczenia.
4. Drzewo decyzyjne jest najbardziej wrażliwe na braki: przy 100% braków trafność spada do
   0,48 i silnie zależy od losowania (odchylenie 0,125). Gdy brakuje cechy z górnych podziałów
   drzewa, wszystkie osoby trafiają do gałęzi wybranej przez wartość wstawioną (medianę).

**Wniosek projektowy:** przy niskiej kompletności danych bezpieczniej jest korzystać z systemu
regułowego albo poinformować użytkownika, że wynik jest mało wiarygodny. API zwraca w tym celu
kompletność danych (`data_completeness`) razem z wynikiem klasyfikacji.

## Istotność statystyczna różnic między klasyfikatorami

**Pytanie:** czy różnice trafności z eksperymentów 1 i 2 są rzeczywiste, czy mogą wynikać
z przypadku (losowego doboru osób testowych)?

**Metodyka** (`experiments/significance.py`):
- **Dokładny test McNemara** dla każdej pary klasyfikatorów. Oba klasyfikatory oceniane są na tych
  samych osobach, więc liczy się tylko osoby, na których się różnią: *b* – poprawnie sklasyfikował
  tylko pierwszy, *c* – tylko drugi. Hipoteza zerowa (metody równie dobre) oznacza, że każda
  rozbieżność z prawdopodobieństwem 50% przypada każdej metodzie, co sprawdza test dwumianowy.
- Dane i modele jak w eksperymencie 2; osoby testowe z 5 ziaren łączone są w jeden test
  (6250 osób dla każdego odsetka braków).
- 18 porównań (3 pary × 6 odsetków braków), więc zastosowano **poprawkę Bonferroniego**: różnica
  jest istotna, gdy *p* < 0,05 / 18 ≈ 0,0028. Bez poprawki przy wielu testach łatwo o przypadkowo
  „istotny” wynik.
- Test McNemara wybrano zamiast testu Wilcoxona dla 5 powtórzeń, bo przy 5 parach test Wilcoxona
  nie może dać *p* mniejszego niż 0,0625, czyli nigdy nie wykazałby istotności.

Wyniki (`docs/experiments/significance.csv`). W komórce: metoda lepsza w danej parze i wartość *p*
(„–”: różnica nieistotna).

| Pominięte odpowiedzi | Sieć vs reguły        | Sieć vs drzewo        | Drzewo vs reguły        |
|----------------------|-----------------------|-----------------------|-------------------------|
| 0%                   | sieć, *p* < 0,001     | sieć, *p* < 0,001     | drzewo, *p* < 0,001     |
| 20%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | – (*p* = 0,12)          |
| 40%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | – (*p* = 0,54)          |
| 60%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | reguły, *p* = 0,002     |
| 80%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | reguły, *p* < 0,001     |
| 100%                 | reguły, *p* < 0,001   | sieć, *p* < 0,001     | reguły, *p* < 0,001     |

**Obserwacje:**

1. Przewaga sieci neuronowej nad obiema pozostałymi metodami jest istotna statystycznie przy
   każdej kompletności danych poza samymi danymi podstawowymi.
2. Przy samych danych podstawowych (100% braków) system regułowy jest istotnie lepszy od sieci
   (*p* < 0,001), co potwierdza wniosek z eksperymentu 2.
3. Przy typowej kompletności (20–40% braków) drzewo decyzyjne **nie jest** istotnie lepsze od
   systemu regułowego. Różnica ok. 1 p.p. z eksperymentu 1 mieści się w granicach przypadku, więc
   drzewo nie daje przewagi trafności, a jego zaletą pozostaje tylko interpretowalność.

## Eksperyment 3: wykrywanie przeciwwskazań dla nowych ćwiczeń

**Pytanie:** czy przeciwwskazania ćwiczenia da się przewidzieć z jego cech (wzorzec ruchu,
grupa mięśniowa, sprzęt, trudność), np. przy dodawaniu do atlasu nowego ćwiczenia?

**Metodyka:**
- Wzorzec: ręczne etykiety przeciwwskazań 164 ćwiczeń atlasu (`app/data/exercises.json`).
- Walidacja krzyżowa *leave-one-out*: każde ćwiczenie po kolei jest traktowane jak nowe,
  a detektor uczy się na pozostałych 163.
- Każda para (ćwiczenie, ograniczenie) to jedna decyzja binarna, łącznie 1640 decyzji
  (268 przeciwwskazań w atlasie). Metryki: precyzja, recall, F1 (mikro) oraz liczba
  przeoczonych przeciwwskazań i fałszywych alarmów.
- Porównane detektory (`app/ml/contraindication_detection.py`):
  - **reguły eksperckie:** 5 reguł opartych na budowie ćwiczenia (np. przysiad → kolano,
    sztanga w ciężkich ćwiczeniach → lędźwie i nadciśnienie, ćwiczenia dynamiczne → serce),
  - **drzewo decyzyjne** uczone na atlasie (klasyfikacja wieloetykietowa, cechy one-hot),
  - **hybryda:** suma wyników reguł i drzewa.

Wyniki (`docs/experiments/contraindications.csv`):

| Detektor           | Precyzja | Recall | F1    | Przeoczone | Fałszywe alarmy | Całe ćwiczenie poprawnie |
|--------------------|----------|--------|-------|------------|-----------------|--------------------------|
| Reguły eksperckie  | 0,784    | 0,649  | 0,710 | 94         | 48              | 45%                      |
| Drzewo decyzyjne   | 0,755    | 0,679  | 0,715 | 86         | 59              | 44%                      |
| Hybryda (suma)     | 0,697    | 0,754  | 0,724 | 66         | 88              | 43%                      |

![Wykrywanie przeciwwskazań](experiments/contraindications.png)

**Obserwacje:**

1. Wszystkie trzy detektory mają zbliżone F1 (0,710–0,724), żaden nie jest wyraźnie lepszy.
   Reguły zachowują najwyższą precyzję (najmniej fałszywych alarmów), a hybryda najwyższy recall.
2. **Wpływ rozbudowy atlasu.** W pierwszej wersji atlasu (67 ćwiczeń) reguły miały wyraźnie
   najwyższe F1 (0,749 wobec 0,663 drzewa). Po rozbudowie do 164 ćwiczeń F1 drzewa wzrosło
   do 0,715, bo ma więcej przykładów do nauki, a F1 reguł spadło do 0,710. Metoda ucząca się
   zyskuje na większym zbiorze danych, a reguły zapisane raz przez eksperta nie.
3. **Reguły słabo uogólniają się na ćwiczenia, których autor nie przewidział.** Nowe ćwiczenia
   ujawniły luki reguł, np. reguła „ćwiczenie izolowane na nogi → kolano” nie pasuje do wspięć
   na palce (staw skokowy) ani przywodzenia nóg (biodro). Recall reguł dla stawu skokowego
   spadł z 0,50 do 0,19, a precyzja dla kolana z 0,93 do 0,68. Drzewo wygrywa tam, gdzie atlas
   zawiera wiele spójnych przykładów: łokieć (F1 0,85 wobec 0,75 reguł), nadgarstek i choroba
   serca (recall 1,00).
4. Hybryda ma najwyższy recall (0,754, o 28 przeoczeń mniej niż reguły) kosztem precyzji.
   W kontekście bezpieczeństwa to korzystna wymiana: fałszywy alarm tylko zawęża wybór
   ćwiczeń, a przeoczenie oznacza ryzyko kontuzji.
5. Żadna metoda nie jest wystarczająco dokładna, by działać bez człowieka: nawet hybryda
   przeocza ok. 1/4 przeciwwskazań. Najsłabiej wykrywane są staw skokowy, biodro i szyja,
   które zależą od szczegółów techniki, a nie od ogólnych cech ćwiczenia.
6. Górną granicę trafności wyznaczają same dane: 114 ze 164 ćwiczeń ma identyczne cechy jak
   inne ćwiczenie, a 80 z nich ma przy tym inne przeciwwskazania. Przykład: siedem izolowanych
   ćwiczeń na nogi na maszynie dla początkujących ma te same cechy, a obciąża kolano (wyprosty,
   uginanie nóg), biodro (przywodzenie) albo staw skokowy (wspięcia na palce). Żadna metoda oparta na tych cechach
   nie rozróżni takich ćwiczeń; poprawa wymagałaby cech dokładniej opisujących ruch.

**Wniosek projektowy:** w aplikacji detektor hybrydowy służy wyłącznie jako **podpowiedź**
przy dodawaniu ćwiczenia (`POST /api/v1/exercises/suggest-contraindications`). Plan treningowy
korzysta zawsze z przeciwwskazań zatwierdzonych przez człowieka, więc filtr bezpieczeństwa
w planie nie przepuszcza żadnego ćwiczenia przeciwwskazanego według atlasu.

## Eksperyment 4: jakość planu a kompletność danych

**Pytanie:** jak błędy klasyfikacji przy brakach danych przekładają się na plan treningowy?

**Metodyka** (`experiments/plan_quality.py`):
- Osoby testowe i braki danych jak w eksperymencie 2. Każda osoba dostaje losowe preferencje:
  cel, 2–5 dni treningowych, 30–90 minut, dostępny sprzęt (każdy rodzaj z prawdopodobieństwem 50%)
  i u połowy osób jedno lub dwa ograniczenia zdrowotne.
- Dla każdej osoby generator buduje **plan wzorcowy** (dla prawdziwego poziomu) i plan dla poziomu
  przewidzianego przez klasyfikator. Atlas: 164 ćwiczenia z `app/data/exercises.json`.
- Metryki:
  - **plan dla prawdziwego poziomu:** część osób, których plan jest identyczny z wzorcowym,
  - **plan za trudny / za łatwy:** plan zbudowany dla wyższego / niższego poziomu,
  - **ćwiczenie trudniejsze niż poziom:** część osób, w których planie jest co najmniej jedno
    ćwiczenie o trudności wyższej niż ich prawdziwy poziom (miara ryzyka przeciążenia),
  - **podobieństwo ćwiczeń:** średni indeks Jaccarda zbiorów ćwiczeń obu planów
    (część wspólna / suma, 1 oznacza identyczny dobór ćwiczeń),
  - **ćwiczenia przeciwwskazane:** liczba ćwiczeń w planach sprzecznych z ograniczeniami osoby.

Wyniki: średnia z 5 ziaren (`docs/experiments/plan_quality.csv`).

| Pominięte odpowiedzi | Klasyfikator     | Plan dla prawdziwego poziomu | Za trudny | Za łatwy | Ćwiczenie trudniejsze niż poziom | Podobieństwo ćwiczeń |
|----------------------|------------------|------------------------------|-----------|----------|----------------------------------|----------------------|
| 0%                   | System regułowy  | 0,806                        | 0,149     | 0,045    | 0,127                            | 0,928                |
| 0%                   | Drzewo decyzyjne | 0,825                        | 0,081     | 0,094    | 0,067                            | 0,938                |
| 0%                   | Sieć neuronowa   | 0,879                        | 0,061     | 0,060    | 0,051                            | 0,957                |
| 60%                  | System regułowy  | 0,732                        | 0,125     | 0,143    | 0,104                            | 0,900                |
| 60%                  | Drzewo decyzyjne | 0,703                        | 0,168     | 0,129    | 0,150                            | 0,891                |
| 60%                  | Sieć neuronowa   | 0,798                        | 0,093     | 0,109    | 0,079                            | 0,926                |
| 100%                 | System regułowy  | 0,675                        | 0,068     | 0,257    | 0,056                            | 0,875                |
| 100%                 | Drzewo decyzyjne | 0,484                        | 0,315     | 0,200    | 0,292                            | 0,802                |
| 100%                 | Sieć neuronowa   | 0,648                        | 0,180     | 0,172    | 0,161                            | 0,871                |

We wszystkich przebiegach liczba ćwiczeń przeciwwskazanych wyniosła **0**.

![Jakość planu a kompletność danych](experiments/plan_quality.png)

**Obserwacje:**

1. **Bezpieczeństwo nie zależy od kompletności danych.** Ograniczenia zdrowotne są pytaniem
   obowiązkowym, a filtr przeciwwskazań działa niezależnie od klasyfikatora, więc żaden plan nie
   zawierał ćwiczenia przeciwwskazanego, nawet przy błędnie wyznaczonym poziomie.
2. **Błędny poziom zmienia plan w niewielkim stopniu.** Nawet przy samych danych podstawowych
   plany mają 80–88% wspólnych ćwiczeń z planem wzorcowym. Po rozbudowie atlasu z 67 do 164
   ćwiczeń podobieństwo spadło tylko o 0,4–1,8 punktu procentowego: przy większym wyborze
   ćwiczeń zmiana poziomu częściej podmienia ćwiczenie na inne, ale trafność poziomu i odsetki
   planów za trudnych i za łatwych są identyczne, bo zależą tylko od klasyfikatora. Ćwiczenia dla poziomu niższego są
   dostępne także na wyższych poziomach, więc pomyłka o jeden poziom zmienia tylko część ćwiczeń
   (i liczbę serii u początkujących).
3. **Kierunek błędu zależy od metody.** System regułowy przy brakach danych częściej zaniża poziom
   (przy 100% braków 26% planów za łatwych i tylko 6% z ćwiczeniem za trudnym). Drzewo decyzyjne
   myli się w obie strony, a przy 100% braków aż 29% osób dostaje ćwiczenie trudniejsze niż ich
   poziom. Z punktu widzenia bezpieczeństwa plan za łatwy jest lepszy niż za trudny.
4. Przy pełnych danych system regułowy częściej zawyża poziom (15% planów za trudnych) niż modele
   ML (6–8%). Progi reguł są więc dla tej populacji zbyt łagodne, co wskazuje kierunek ich korekty.
5. Do ok. 60% braków sieć neuronowa daje plany najbliższe wzorcowym i najrzadziej za trudne.

**Wniosek projektowy:** przy kompletnych danych najlepsze plany daje sieć neuronowa, a przy
bardzo niekompletnych system regułowy, który myli się „w bezpieczną stronę”. Uzasadnia to
dobór klasyfikatora do liczby pustych odpowiedzi w aplikacji: sieć neuronowa, a przy samych
danych podstawowych system regułowy (opis w [ML.md](ML.md#uczenie-i-wyniki-wstępne)).

## Czas odpowiedzi API

**Pytanie:** czy system odpowiada wystarczająco szybko? Eksperyment 1 mierzy sam klasyfikator,
tutaj mierzony jest cały czas obsługi żądania HTTP: walidacja Pydantic, zapytania do bazy,
klasyfikacja, generowanie planu i zamiana wyniku na JSON.

**Metodyka** (`experiments/api_latency.py`):
- Kompletny profil (wszystkie testy sprawności, ograniczenie kolana, 4 dni treningowe, sprzęt),
  atlas 164 ćwiczeń w bazie SQLite.
- Dla każdego endpointu 5 żądań rozgrzewkowych (wczytanie modeli z dysku, połączenie), które nie
  są liczone, a potem właściwy pomiar.
- Miary: średnia, mediana (p50), 95. percentyl (p95: 95% żądań było szybszych) i maksimum.
- Dwa warianty:
  - **lokalnie:** aplikacja w tym samym procesie, bez sieci (200 żądań na endpoint),
    czyli czas pracy samego serwera,
  - **wdrożenie:** aplikacja na Render (plan darmowy, Frankfurt), żądania z komputera w Polsce
    (30 żądań na endpoint, pomiar z 8.11.2026), czyli czas widziany przez użytkownika.

Wyniki lokalne (`docs/experiments/api_latency.csv`), w milisekundach:

| Żądanie                                   | Średnia | p50  | p95  | Maks. |
|-------------------------------------------|---------|------|------|-------|
| `GET /health`                             | 0,76    | 0,76 | 0,83 | 1,37  |
| `GET /api/v1/questionnaire`               | 0,81    | 0,80 | 0,89 | 0,98  |
| `POST /api/v1/questionnaire`              | 1,68    | 1,66 | 1,84 | 2,14  |
| `GET .../fitness-level?method=rules`      | 1,71    | 1,68 | 1,93 | 2,22  |
| `GET .../fitness-level?method=decision_tree` | 2,73 | 2,67 | 3,13 | 4,57  |
| `GET .../fitness-level?method=mlp`        | 2,91    | 2,86 | 3,19 | 3,82  |
| `GET .../plan?method=mlp`                 | 5,25    | 4,99 | 5,78 | 37,50 |

Wyniki dla wdrożenia, w milisekundach:

| Żądanie                                   | Średnia | p50  | p95   | Maks. |
|-------------------------------------------|---------|------|-------|-------|
| `GET /health`                             | 66      | 53   | 140   | 148   |
| `GET /api/v1/questionnaire`               | 59      | 52   | 106   | 137   |
| `POST /api/v1/questionnaire`              | 64      | 57   | 117   | 130   |
| `GET .../fitness-level?method=rules`      | 63      | 54   | 123   | 145   |
| `GET .../fitness-level?method=decision_tree` | 74   | 59   | 141   | 147   |
| `GET .../fitness-level?method=mlp`        | 80      | 70   | 133   | 138   |
| `GET .../plan?method=mlp`                 | 146     | 99   | 380   | 817   |

Powtórzony pomiar dał dla planu podobny wynik: mediana 106 ms, p95 285 ms, maksimum 333 ms.

**Obserwacje:**

1. Najcięższe żądanie, wygenerowanie planu z klasyfikacją siecią neuronową, zajmuje serwerowi
   ok. 5 ms (p95 ok. 6 ms). Klasyfikacja sieci to ok. 0,5 ms (eksperyment 1), a resztę zajmują
   baza danych, generowanie planu i obsługa HTTP. Po rozbudowie atlasu z 67 do 164 ćwiczeń
   czas planu wzrósł z ok. 4,3 do 5,3 ms, bo generator filtruje i układa więcej ćwiczeń.
   Pojedyncze żądanie trwające 37,5 ms to jednorazowe opóźnienie (prawdopodobnie po stronie
   systemu operacyjnego lub odśmiecania pamięci), a nie stała cecha endpointu: 95% żądań trwało poniżej 6 ms.
2. Po wdrożeniu czas odpowiedzi to ok. 50–100 ms (mediana), z czego większość to sieć i serwer
   z planu darmowego (pusty `GET /health` trwa ok. 53 ms). Wszystkie żądania mieszczą się
   poniżej 1 s, a 95% żądań poza planem w ok. 0,15 s, czyli w granicach, które użytkownik
   odbiera jako natychmiastową reakcję interfejsu (ok. 0,1–1 s).
3. Plan treningowy ma po wdrożeniu wyraźnie dłuższy „ogon” niż lokalnie (p95 0,3–0,4 s,
   maksimum 0,8 s). Lokalnie plan jest tylko ok. 2 ms wolniejszy od klasyfikacji, więc różnicę
   najprawdopodobniej tłumaczy słabszy, współdzielony procesor serwera w planie darmowym,
   na którym praca generatora trwa wielokrotnie dłużej. Wybór klasyfikatora praktycznie nie wpływa na czas
   odpowiedzi: różnica między regułami a siecią to ok. 1 ms lokalnie i mieści się w zmienności
   sieci po wdrożeniu.
4. Wyjątkiem jest pierwsze żądanie po uśpieniu serwera w planie darmowym (start kontenera,
   ok. 1 minuty). To ograniczenie planu hostingu, a nie aplikacji: w planie płatnym serwer
   nie jest usypiany.

## Ograniczenia

- Etykiety przeciwwskazań w atlasie i reguły eksperckie pochodzą od autora systemu,
  a nie od niezależnego eksperta (fizjoterapeuty), co może zawyżać wyniki reguł.
- Dane są syntetyczne, więc wyniki porównują metody w kontrolowanych warunkach przyjętego
  modelu generowania, a nie trafność na prawdziwych użytkownikach.
- Braki danych są losowe i niezależne od siebie. W rzeczywistości użytkownicy mogą częściej
  pomijać konkretne testy (np. osoby słabsze – pompki), co może zmienić wyniki.
- W eksperymencie 4 preferencje osób są losowane niezależnie od ich sprawności, a jakość planu
  oceniana jest względem planu wzorcowego z tego samego generatora, a nie przez trenera.
- Czasy lokalne zmierzono na jednym komputerze deweloperskim i służą do porównania metod.
  Pomiar wdrożenia zależy od łącza i obciążenia serwera w chwili pomiaru, a żądania były
  wysyłane kolejno (bez równoczesnych użytkowników), więc nie jest to test obciążeniowy.
