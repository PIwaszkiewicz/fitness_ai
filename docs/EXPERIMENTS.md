# Eksperymenty: porównanie klasyfikatorów sprawności

Opis klasyfikatorów i generatora danych: [ML.md](ML.md).
Kod: `experiments/evaluation.py` (eksperymenty), `experiments/run.py` (zapis wyników i wykresów).

## Metodyka

- Każdy eksperyment (poza doborem hiperparametrów) powtórzono dla 5 ziaren losowania
  (`seed` 1–5). Dla każdego ziarna wygenerowano nowy zbiór 5000 osób i podzielono go na część
  uczącą (75%) i testową (25%) z zachowaniem proporcji poziomów. Wyniki podano jako średnią ± odchylenie standardowe.
- Klasyfikatory ML uczą się na danych, w których 20% odpowiedzi opcjonalnych jest pominiętych
  (typowa kompletność kwestionariusza).
- Dane obejmują wskaźnik siły z pytań o ciężary (ok. 1/3 osób, głównie ze stażem, zob. [ML.md](ML.md)).
  Ta cecha nie jest usuwana jako „pominięta odpowiedź”, bo pytania o ciężary widzą tylko osoby
  trenujące z ciężarami; jej wpływ bada osobno eksperyment 5.
- Metryki:
  - **accuracy:** odsetek poprawnych klasyfikacji,
  - **F1 makro:** średnia miar F1 dla trzech poziomów (każdy poziom ma tę samą wagę),
  - **macierz pomyłek:** jaka część osób z danego poziomu trafiła do każdej klasy,
  - **czas uczenia** i **czas klasyfikacji jednej osoby** (odpowiada jednemu żądaniu API).
- Wszystkie przebiegi są zapisywane w MLflow (eksperymenty `dobor-hiperparametrow`,
  `porownanie-klasyfikatorow`, `wplyw-kompletnosci`, `istotnosc-roznic`, `wykrywanie-przeciwwskazan`,
  `jakosc-planu` i `wskaznik-sily`).

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

Wyniki (`docs/experiments/tuning.csv`, pięć najlepszych ustawień każdego modelu i poprzednie ustawienie sieci):

| Model            | Ustawienia                            | F1 makro (CV)   |
|------------------|---------------------------------------|-----------------|
| Drzewo decyzyjne | głębokość 10, min. 5 w liściu         | 0,815 ± 0,011   |
| Drzewo decyzyjne | głębokość 8, min. 5 w liściu          | 0,814 ± 0,012   |
| Drzewo decyzyjne | głębokość 8, min. 1 w liściu          | 0,809 ± 0,012   |
| Drzewo decyzyjne | głębokość 10, min. 1 w liściu         | 0,809 ± 0,005   |
| Drzewo decyzyjne | **głębokość 6, min. 5 w liściu**      | **0,807 ± 0,007** |
| Sieć neuronowa   | (64, 32), alpha 0,01                  | 0,861 ± 0,014   |
| Sieć neuronowa   | (64, 32), alpha 0,001                 | 0,861 ± 0,014   |
| Sieć neuronowa   | (64, 32), alpha 0,0001                | 0,861 ± 0,013   |
| Sieć neuronowa   | **(32), alpha 0,0001**                | **0,853 ± 0,009** |
| Sieć neuronowa   | (32), alpha 0,001                     | 0,853 ± 0,009   |
| …                |                                       |                 |
| Sieć neuronowa   | (32, 16), alpha 0,0001 (poprzednio)   | 0,845 ± 0,035   |

**Wnioski:**

1. **Sieć neuronowa:** w pierwszej wersji (bez wskaźnika siły) najlepsza była sieć (32, 16)
   i tę stosowano. Po dodaniu wskaźnika siły sieć (32, 16) spadła na 12. miejsce (0,845) i wypadła
   poza granicą jednego odchylenia (próg 0,861 − 0,014 = 0,847). Duże odchylenie (0,035) wynika
   z jednej z pięciu części walidacji, w której sieć nauczyła się wyraźnie gorzej, czyli z niestabilności
   uczenia. Zgodnie z regułą wybrano najprostszą sieć w granicy: **jedna warstwa 32 neuronów**.
   Sieć (64, 32) ma o ok. 0,008 wyższy wynik, ale ma ok. 5 razy więcej wag (3267 wobec 643), a różnica mieści się
   w odchyleniu. Na zbiorach testowych eksperymentu 1 wszystkie trzy warianty dały zbliżone F1
   makro: (32) 0,856, (32, 16) 0,860, (64, 32) 0,866 (odchylenia ok. 0,01).
2. **Drzewo decyzyjne:** najlepsze jest drzewo o głębokości 10 (0,815), ale drzewo o głębokości 6
   mieści się w granicy jednego odchylenia (próg 0,804), a ma do 16 razy mniej liści, więc jego
   reguły da się przeczytać. Pozostaje głębokość 6 i min. 5 próbek w liściu.
3. Dobór parametrów potwierdza przede wszystkim, że wyniki porównania nie wynikają z przypadkowo
   złych ustawień modeli: różnice między dobrymi ustawieniami są mniejsze niż różnice między metodami.

## Eksperyment 1: porównanie klasyfikatorów

Dane testowe z 20% pominiętych odpowiedzi opcjonalnych (`docs/experiments/comparison.csv`).

| Klasyfikator       | Accuracy        | F1 makro        | Czas uczenia | Czas klasyfikacji 1 osoby |
|--------------------|-----------------|-----------------|--------------|---------------------------|
| System regułowy    | 0,800 ± 0,004   | 0,801 ± 0,005   | —            | 0,02 ms                   |
| Drzewo decyzyjne   | 0,805 ± 0,009   | 0,804 ± 0,010   | 0,01 s       | 0,43 ms                   |
| Sieć neuronowa     | 0,857 ± 0,012   | 0,856 ± 0,012   | 0,13 s       | 0,52 ms                   |

![Macierze pomyłek](experiments/confusion_matrices.png)

**Obserwacje:**

1. Sieć neuronowa osiąga najwyższą trafność, o ok. 6 punktów procentowych wyższą od systemu
   regułowego i od drzewa decyzyjnego. Obie różnice są istotne statystycznie
   (zob. [test McNemara](#istotność-statystyczna-różnic-między-klasyfikatorami)).
2. Pomyłki o dwa poziomy są skrajnie rzadkie: na ok. 2200 osób początkujących (5 powtórzeń) system
   regułowy i drzewo uznały za zaawansowaną po jednej osobie, a sieć żadnej. Pomyłka odwrotna
   (zaawansowany uznany za początkującego) dotyczy 0,05–0,2% zaawansowanych. Pozostałe błędy dotyczą
   poziomów sąsiednich. Ma to znaczenie dla bezpieczeństwa: osoba początkująca praktycznie nie
   dostanie planu dla zaawansowanych.
3. Najtrudniejszy do rozpoznania jest poziom średni (71–76% poprawnych), bo graniczy z oboma
   pozostałymi.
4. Czas klasyfikacji jednej osoby jest poniżej 1 ms dla wszystkich metod, więc wybór
   klasyfikatora nie wpływa na czas odpowiedzi API.
5. W porównaniu z pierwszą wersją (bez wskaźnika siły) trafność systemu regułowego wzrosła
   (0,792 → 0,800), bo reguły od razu korzystają z nowego wskaźnika. Sieć ma wynik nieco niższy
   (0,866 → 0,857) z powodu zmiany architektury na mniejszą (zob. dobór hiperparametrów); różnica
   mieści się w odchyleniu.

## Eksperyment 2: wpływ kompletności danych

Te same osoby testowe oceniane przy coraz większym odsetku pominiętych odpowiedzi opcjonalnych
(staż i cztery testy sprawności). Przy 100% zostają tylko dane podstawowe: wiek, płeć, BMI
i poziom aktywności, a u osób trenujących z ciężarami także wskaźnik siły
(`docs/experiments/completeness.csv`).

| Pominięte odpowiedzi | System regułowy | Drzewo decyzyjne | Sieć neuronowa  |
|----------------------|-----------------|------------------|-----------------|
| 0%                   | 0,813 ± 0,009   | 0,824 ± 0,013    | 0,877 ± 0,014   |
| 20%                  | 0,793 ± 0,004   | 0,801 ± 0,013    | 0,858 ± 0,016   |
| 40%                  | 0,767 ± 0,004   | 0,764 ± 0,012    | 0,831 ± 0,012   |
| 60%                  | 0,743 ± 0,008   | 0,716 ± 0,022    | 0,800 ± 0,010   |
| 80%                  | 0,713 ± 0,003   | 0,624 ± 0,044    | 0,749 ± 0,024   |
| 100%                 | 0,696 ± 0,006   | 0,513 ± 0,073    | 0,688 ± 0,039   |

![Wpływ kompletności danych](experiments/completeness.png)

**Obserwacje:**

1. Trafność wszystkich metod spada wraz z ubywaniem danych. Wyniki testów sprawności niosą
   istotną informację, której nie zastąpią same dane podstawowe.
2. Do ok. 80% braków sieć neuronowa pozostaje najlepsza.
3. System regułowy traci trafność najwolniej i przy samych danych podstawowych (100% braków)
   ma wynik zbliżony do sieci (0,696 wobec 0,688; różnica nieistotna statystycznie). Reguły pomijają
   brakujące wskaźniki, a modele ML uczone przy 20% braków trafiają na dane wyraźnie inne niż
   w czasie uczenia. W pierwszej wersji (bez wskaźnika siły) reguły były przy 100% braków istotnie
   lepsze od sieci (0,675 wobec 0,648); wskaźnik siły zmniejszył tę różnicę, bo u osób trenujących
   zostaje mocna cecha nawet bez testów.
4. Drzewo decyzyjne jest najbardziej wrażliwe na braki: przy 100% braków trafność spada do
   0,51 i silnie zależy od losowania (odchylenie 0,073). Gdy brakuje cechy z górnych podziałów
   drzewa, wszystkie osoby trafiają do gałęzi wybranej przez wartość wstawioną (medianę).

**Wniosek projektowy:** przy niskiej kompletności danych sieć i reguły dają podobne wyniki, a drzewo
jest wyraźnie gorsze. Aplikacja dobiera klasyfikator do liczby pustych odpowiedzi według oceny
z uczenia ([ML.md](ML.md#uczenie-i-wyniki-wstępne)) i zwraca kompletność danych
(`data_completeness`) razem z wynikiem, żeby użytkownik wiedział, jak wiarygodny jest wynik.

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
| 0%                   | sieć, *p* < 0,001     | sieć, *p* < 0,001     | – (*p* = 0,051)         |
| 20%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | – (*p* = 0,17)          |
| 40%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | – (*p* = 0,67)          |
| 60%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | reguły, *p* < 0,001     |
| 80%                  | sieć, *p* < 0,001     | sieć, *p* < 0,001     | reguły, *p* < 0,001     |
| 100%                 | – (*p* = 0,24)        | sieć, *p* < 0,001     | reguły, *p* < 0,001     |

**Obserwacje:**

1. Przewaga sieci neuronowej nad obiema pozostałymi metodami jest istotna statystycznie przy
   każdej kompletności danych poza samymi danymi podstawowymi.
2. Przy samych danych podstawowych (100% braków) sieć i system regułowy **nie różnią się**
   istotnie (*p* = 0,24). W pierwszej wersji, bez wskaźnika siły, reguły były tu istotnie lepsze
   (*p* < 0,001).
3. Przy pełnych i typowych danych (0–40% braków) drzewo decyzyjne **nie jest** istotnie lepsze od
   systemu regułowego. Różnica ok. 0,5 p.p. z eksperymentu 1 mieści się w granicach przypadku, więc
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
| 0%                   | System regułowy  | 0,813                        | 0,129     | 0,058    | 0,112                            | 0,931                |
| 0%                   | Drzewo decyzyjne | 0,824                        | 0,085     | 0,091    | 0,069                            | 0,938                |
| 0%                   | Sieć neuronowa   | 0,877                        | 0,059     | 0,064    | 0,048                            | 0,956                |
| 60%                  | System regułowy  | 0,744                        | 0,120     | 0,136    | 0,099                            | 0,905                |
| 60%                  | Drzewo decyzyjne | 0,710                        | 0,169     | 0,121    | 0,150                            | 0,892                |
| 60%                  | Sieć neuronowa   | 0,802                        | 0,091     | 0,108    | 0,074                            | 0,928                |
| 100%                 | System regułowy  | 0,696                        | 0,072     | 0,232    | 0,057                            | 0,883                |
| 100%                 | Drzewo decyzyjne | 0,513                        | 0,316     | 0,172    | 0,290                            | 0,808                |
| 100%                 | Sieć neuronowa   | 0,688                        | 0,146     | 0,165    | 0,124                            | 0,882                |

We wszystkich przebiegach liczba ćwiczeń przeciwwskazanych wyniosła **0**.

![Jakość planu a kompletność danych](experiments/plan_quality.png)

**Obserwacje:**

1. **Bezpieczeństwo nie zależy od kompletności danych.** Ograniczenia zdrowotne są pytaniem
   obowiązkowym, a filtr przeciwwskazań działa niezależnie od klasyfikatora, więc żaden plan nie
   zawierał ćwiczenia przeciwwskazanego, nawet przy błędnie wyznaczonym poziomie.
2. **Błędny poziom zmienia plan w niewielkim stopniu.** Nawet przy samych danych podstawowych
   plany mają 81–88% wspólnych ćwiczeń z planem wzorcowym. Ćwiczenia dla poziomu niższego są
   dostępne także na wyższych poziomach, więc pomyłka o jeden poziom zmienia tylko część ćwiczeń
   (i liczbę serii u początkujących).
3. **Kierunek błędu zależy od metody.** System regułowy przy brakach danych częściej zaniża poziom
   (przy 100% braków 23% planów za łatwych i tylko 6% z ćwiczeniem za trudnym). Sieć przy 100%
   braków myli się w obie strony (15% za trudnych, 17% za łatwych), a drzewo decyzyjne aż u 29% osób
   daje ćwiczenie trudniejsze niż ich poziom. Z punktu widzenia bezpieczeństwa plan za łatwy jest
   lepszy niż za trudny.
4. Przy pełnych danych system regułowy częściej zawyża poziom (13% planów za trudnych) niż modele
   ML (6–9%). Progi reguł są więc dla tej populacji zbyt łagodne, co wskazuje kierunek ich korekty.
5. Do ok. 60% braków sieć neuronowa daje plany najbliższe wzorcowym i najrzadziej za trudne.

**Wniosek projektowy:** przy kompletnych danych najlepsze plany daje sieć neuronowa. Przy samych
danych podstawowych sieć i reguły mają podobną trafność, ale reguły mylą się „w bezpieczną stronę”
(6% planów z za trudnym ćwiczeniem wobec 12% u sieci). To argument, by przy bardzo niekompletnych
danych brać pod uwagę nie tylko trafność, ale i kierunek błędu, oraz by informować użytkownika
o niskiej kompletności danych.

## Eksperyment 5: wskaźnik siły u osób trenujących z ciężarami

**Pytanie:** czy pytania o ciężary w podstawowych ćwiczeniach poprawiają ocenę poziomu osób,
które trenują z ciężarami?

**Metodyka** (`strength_feature_study` w `experiments/evaluation.py`):
- Dane i braki jak w eksperymencie 2. Każdy klasyfikator jest uczony dwa razy na tych samych
  osobach: **z wskaźnikiem siły** i **bez niego** (cecha wyczyszczona).
- Ocena tylko na osobach testowych trenujących z ciężarami (ok. 390 na powtórzenie), bo tylko
  one odpowiadają na te pytania. Wynik dla pozostałych osób jest w obu wariantach taki sam.
- Pomijane są pozostałe odpowiedzi opcjonalne (0–100%), wskaźnik siły zostaje.

Wyniki: F1 makro, średnia z 5 ziaren (`docs/experiments/strength.csv`).

| Pominięte odpowiedzi | Reguły bez → z | Drzewo bez → z | Sieć bez → z |
|----------------------|----------------|----------------|--------------|
| 0%                   | 0,781 → 0,819  | 0,815 → 0,805  | 0,874 → 0,865 |
| 20%                  | 0,771 → 0,788  | 0,781 → 0,780  | 0,855 → 0,847 |
| 40%                  | 0,752 → 0,780  | 0,761 → 0,766  | 0,822 → 0,824 |
| 60%                  | 0,721 → 0,763  | 0,709 → 0,731  | 0,781 → 0,788 |
| 80%                  | 0,668 → 0,730  | 0,607 → 0,651  | 0,724 → 0,757 |
| 100%                 | 0,624 → 0,664  | 0,412 → 0,508  | 0,628 → 0,701 |

![Wskaźnik siły](experiments/strength.png)

**Obserwacje:**

1. **Wskaźnik siły pomaga najbardziej, gdy brakuje testów.** Przy samych danych podstawowych
   F1 sieci rośnie z 0,628 do 0,701, drzewa z 0,412 do 0,508, a reguł z 0,624 do 0,664. Osoba,
   która nie wykona testów, a poda serie z ciężarami, jest oceniana wyraźnie trafniej.
2. **Przy kompletnych testach modele ML nie zyskują.** Przy 0–20% braków różnice sieci i drzewa
   (−0,01) mieszczą się w odchyleniu (ok. 0,015–0,02): pompki, przysiady i deska niosą już tę samą
   informację o sprawności, a dodatkowa cecha nieco utrudnia uczenie przy ok. 1/3 osób z wartością.
3. **System regułowy zyskuje zawsze** (+0,02–0,06), bo dodatkowy wskaźnik z dobrze dobranymi
   progami uśrednia błędy pojedynczych testów.
4. Wynik zależy od założeń generatora: związek wskaźnika siły z prawdziwą sprawnością został
   przyjęty w modelu danych ([ML.md](ML.md#generator-danych-syntetycznych)). Eksperyment pokazuje,
   że metody potrafią wykorzystać taką cechę przy niekompletnych danych, ale wielkość zysku
   wymagałaby potwierdzenia na prawdziwych użytkownikach.

**Wniosek projektowy:** pytania o ciężary warto zadawać osobom trenującym, bo zabezpieczają ocenę
na wypadek pominięcia testów, a przy okazji pozwalają podać w planie ciężary startowe.

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
- Normy siły względnej (wskaźnik siły) są przybliżone na podstawie popularnych tabel norm, a wzór
  Epleya szacuje 1RM z serii z błędem rosnącym wraz z liczbą powtórzeń. Dla podciągania
  z obciążeniem norm jest mało, więc ta część wskaźnika jest najsłabiej uzasadniona.
- W eksperymencie 4 preferencje osób są losowane niezależnie od ich sprawności, a jakość planu
  oceniana jest względem planu wzorcowego z tego samego generatora, a nie przez trenera.
- Czasy lokalne zmierzono na jednym komputerze deweloperskim i służą do porównania metod.
  Pomiar wdrożenia zależy od łącza i obciążenia serwera w chwili pomiaru, a żądania były
  wysyłane kolejno (bez równoczesnych użytkowników), więc nie jest to test obciążeniowy.
