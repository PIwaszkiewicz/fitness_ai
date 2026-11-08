# Miejsca w kodzie wymagające źródeł

Lista wartości i reguł, które w pracy trzeba podeprzeć literaturą albo jawnie opisać jako
założenie projektowe. Proponowane źródła są punktem wyjścia: przed zacytowaniem trzeba sprawdzić
wydanie, stronę oraz to, czy dana pozycja rzeczywiście podaje przyjętą wartość. Jeśli źródło
podaje inną wartość, należy zmienić kod albo opisać różnicę.

Priorytety:
- **A:** zdrowie i bezpieczeństwo użytkownika. Komisja zapyta o to w pierwszej kolejności.
- **B:** normy sprawności i zasady treningu.
- **C:** metodyka badań (statystyka, uczenie maszynowe).
- **D:** założenia własne, których nie da się zacytować. Trzeba je nazwać założeniami
  i pokazać, jak je sprawdzono.

## A. Zdrowie i bezpieczeństwo

| # | Miejsce | Wartość | Co uzasadnić | Propozycja źródła |
|---|---------|---------|--------------|-------------------|
| A1 | `app/services/questionnaire_service.py:12` | ból ≥ 7 w skali NRS 1–10 = ból silny | próg bólu silnego | Serlin i in., *When is cancer pain mild, moderate or severe?*, Pain 1995; Hawker i in., *Measures of adult pain*, Arthritis Care & Research 2011 |
| A2 | `app/services/questionnaire_service.py:14` | tętno spoczynkowe > 100/min = tachykardia | definicja tachykardii | wytyczne ESC lub AHA/ACC dotyczące zaburzeń rytmu serca |
| A3 | `app/services/questionnaire_service.py:25`, `app/models/enums.py:58` | choroba serca lub nadciśnienie bez zgody lekarza → ostrzeżenie | zasada kwalifikacji do wysiłku | Riebe i in., *Updating ACSM's recommendations for exercise preparticipation health screening*, MSSE 2015; kwestionariusz PAR-Q+ (Warburton i in., 2011) |
| A4 | `app/ml/contraindication_detection.py:28` | wzorzec ruchu → obciążany staw (np. przysiad → kolano, zawias biodrowy → lędźwie) | reguła 1 detektora przeciwwskazań | Kisner, Colby, *Therapeutic Exercise: Foundations and Techniques*; Escamilla, *Knee biomechanics of the dynamic squat exercise*, MSSE 2001 |
| A5 | `app/ml/contraindication_detection.py:43` | ćwiczenie izolowane → staw pracującej grupy | reguła 2 | jak A4 |
| A6 | `app/ml/contraindication_detection.py:76` | podpór na dłoniach → nadgarstek | reguła 3 | jak A4; najlepiej opinia fizjoterapeuty |
| A7 | `app/ml/contraindication_detection.py:82` | ciężkie ćwiczenia ze sztangą → lędźwie, nadciśnienie | reguła 4 (wzrost ciśnienia przy dużym ciężarze) | MacDougall i in., *Arterial blood pressure response to heavy resistance exercise*, J Appl Physiol 1985; Pescatello i in., ACSM Position Stand *Exercise and hypertension*, MSSE 2004 |
| A8 | `app/ml/contraindication_detection.py:85` | intensywne cardio → nadciśnienie | reguła 5 | Pescatello i in. 2004 (jak A7) |
| A9 | `app/data/exercises.json` | 155 przeciwwskazań w 84 ćwiczeniach | etykiety atlasu są wzorcem w eksperymencie 3 (policzonym na 67 ćwiczeniach) | najlepiej przegląd przez fizjoterapeutę; ewentualnie Kisner, Colby (jak A4) |

## B. Normy sprawności i zasady treningu

| # | Miejsce | Wartość | Co uzasadnić | Propozycja źródła |
|---|---------|---------|--------------|-------------------|
| B1 | `app/ml/rule_based.py:14` | pompki: mężczyźni 15 / 30, kobiety 8 / 20 | progi punktów za pompki | ACSM's *Guidelines for Exercise Testing and Prescription* (11. wyd., 2021), tabele norm; normy CSEP-PATH (Canadian Society for Exercise Physiology) |
| B2 | `app/ml/rule_based.py:19` | od 50 lat progi pompek niższe o 30% | spadek norm z wiekiem | jak B1: normy podane w grupach wiekowych |
| B3 | `app/ml/rule_based.py:15` | przysiady w 1 min: 25 / 40 | progi testu przysiadów | brak jednej powszechnej normy; poszukać norm testu 1-minutowego (np. baterie testów sprawności dorosłych) |
| B4 | `app/ml/rule_based.py:16` | deska: 60 / 120 s | progi testu deski | Strand i in., *Norms for an isometric muscle endurance test*, J Hum Kinet 2014; McGill i in., *Endurance times for low back stabilization exercises*, Arch Phys Med Rehabil 1999 |
| B5 | `app/ml/rule_based.py:17` | tętno spoczynkowe: < 65 dobre, > 80 słabe | związek tętna spoczynkowego ze sprawnością | ACSM's *Guidelines* (jak B1); Nauman i in., *Temporal changes in resting heart rate and deaths from ischemic heart disease*, JAMA 2011 |
| B6 | `app/services/plan_generator.py:39` | serie, powtórzenia i przerwy zależne od celu (siła 4–6, masa 8–12, wytrzymałość 15–20) | parametry treningu | ACSM Position Stand *Progression models in resistance training for healthy adults*, MSSE 2009; Schoenfeld i in., *Loading recommendations for muscle strength, hypertrophy, and local endurance*, Sports 2021 |
| B7 | `app/services/plan_generator.py:157` | początkujący: o 1 serię mniej | mniejsza objętość na start | ACSM 2009 (jak B6): zalecenia dla osób początkujących |
| B8 | `app/services/plan_generator.py:87` | 1–3 dni: całe ciało, 4–7 dni: góra/dół | wybór podziału treningu | ACSM 2009 (jak B6): częstotliwość i podział treningu |
| B9 | `app/services/plan_generator.py:32` | rozgrzewka 10 min | czas rozgrzewki | Garber i in., ACSM Position Stand *Quantity and quality of exercise…*, MSSE 2011 (rozgrzewka 5–10 min) |
| B10 | `app/services/plan_generator.py:125` | 2–3 powtórzenia w zapasie | dobór ciężaru u początkujących | Helms i in., *Application of the repetitions in reserve-based RPE scale for resistance training*, Strength Cond J 2016 |
| B11 | `app/services/plan_generator.py:129` | zwiększenie obciążenia o 2,5–5% | zasada progresji | ACSM 2009 (jak B6): zaleca 2–10% |
| B12 | `app/services/plan_generator.py:138` | lżejszy tydzień co 4–6 tygodni | roztrenowanie (deload) | Bell i in., konsensus delficki dotyczący deloadu, Sports Medicine – Open 2023 |
| B13 | `app/ml/data_generator.py:82`, `app/ml/features.py` | BMI jako cecha | definicja i klasyfikacja BMI | WHO, klasyfikacja BMI |
| B14 | `app/schemas/user_profile.py:27` | wiek od 16 lat | dolna granica wieku | WHO 2020 (Bull i in., *WHO guidelines on physical activity and sedentary behaviour*, BJSM 2020). Zalecenia dla dorosłych dotyczą osób od 18 lat, a 16–17 lat to grupa młodzieży. Trzeba to uzasadnić albo podnieść granicę do 18 lat. |
| B15 | `app/services/plan_generator.py` (`WEIGHT_LOSS_TIPS`) | wskazówki dla celu „redukcja masy ciała”: deficyt 500–750 kcal dziennie, efekt samego treningu ok. 2–3 kg, 150–300 min wysiłku tlenowego tygodniowo, utrzymanie ćwiczeń siłowych, interwały, korzyści ze spadku masy o 3–5% | treść i liczby we wskazówkach redukcyjnych | Jensen i in., *2013 AHA/ACC/TOS Guideline for the Management of Overweight and Obesity in Adults*, Circulation 2014; Donnelly i in., ACSM Position Stand, MSSE 2009; Bull i in., WHO 2020 guidelines, BJSM 2020; Swift i in., Prog Cardiovasc Dis 2014; Oppert i in., EASO Physical Activity Working Group, Obesity Reviews 2021; Wewege i in., Obesity Reviews 2017 |

## C. Metodyka badań

| # | Miejsce | Metoda | Propozycja źródła |
|---|---------|--------|-------------------|
| C1 | `experiments/significance.py:34` | dokładny test McNemara | McNemar, Psychometrika 1947; Dietterich, *Approximate statistical tests for comparing supervised classification learning algorithms*, Neural Computation 1998 |
| C2 | `experiments/significance.py:24` | poprawka Bonferroniego | Dunn, *Multiple comparisons among means*, JASA 1961 |
| C3 | `docs/EXPERIMENTS.md` | dlaczego nie test Wilcoxona przy 5 powtórzeniach | Wilcoxon, Biometrics Bulletin 1945; Demšar, *Statistical comparisons of classifiers over multiple data sets*, JMLR 2006 |
| C4 | `experiments/tuning.py` | walidacja krzyżowa | Kohavi, *A study of cross-validation and bootstrap for accuracy estimation and model selection*, IJCAI 1995 |
| C5 | `experiments/tuning.py:72` | reguła jednego odchylenia standardowego | Breiman i in., *Classification and Regression Trees*, 1984; Hastie, Tibshirani, Friedman, *The Elements of Statistical Learning*, 2. wyd., 2009 |
| C6 | `app/ml/models.py` | drzewo decyzyjne, MLP, wczesne zatrzymanie | Breiman i in. 1984; Prechelt, *Early stopping – but when?*, 1998; Pedregosa i in., *Scikit-learn: machine learning in Python*, JMLR 2011 |
| C7 | `app/ml/data_generator.py:40` | braki danych losowe i niezależne (MCAR) | Rubin, *Inference and missing data*, Biometrika 1976 |
| C8 | `app/ml/models.py` | uzupełnianie medianą z kolumnami informującymi o braku | Little, Rubin, *Statistical Analysis with Missing Data*; dokumentacja scikit-learn (`SimpleImputer`) |
| C9 | `experiments/plan_quality.py:72` | indeks Jaccarda | Jaccard, *The distribution of the flora in the alpine zone*, New Phytologist 1912 |
| C10 | `docs/EXPERIMENTS.md` (czas odpowiedzi) | progi odczuwania czasu reakcji 0,1 s / 1 s | Nielsen, *Usability Engineering*, 1993; Miller, *Response time in man-computer conversational transactions*, 1968 |
| C11 | `experiments/api_latency.py` | percentyl p95 jako miara opóźnienia | Beyer i in., *Site Reliability Engineering*, O'Reilly 2016 |
| C12 | `experiments/evaluation.py` | accuracy, F1 makro, macierz pomyłek, precyzja i recall | dowolny podręcznik uczenia maszynowego, np. Hastie i in. 2009 |

## D. Założenia własne (opisać jako założenia)

| # | Miejsce | Założenie | Jak to obronić |
|---|---------|-----------|----------------|
| D1 | `app/ml/data_generator.py:72` | wzór ukrytej sprawności *S* (wagi aktywności, stażu i wieku) | jawny model danych syntetycznych. Kierunki zależności z literatury: spadek wydolności z wiekiem (Fleg i in., *Accelerated longitudinal decline of aerobic capacity in healthy older adults*, Circulation 2005), wpływ aktywności i treningu (ACSM). Wartości liczbowe to założenie. |
| D2 | `app/ml/data_generator.py:86` | współczynniki wyników testów (pompki, przysiady, deska, tętno) | dobrane tak, żeby rozkłady wyników mieściły się w normach z punktów B1–B5; warto to sprawdzić i opisać |
| D3 | `app/ml/data_generator.py:27` | rozkład aktywności 25/25/25/15/10% | można porównać z badaniem aktywności Polaków (np. Eurobarometr *Sport and physical activity*, 2022) |
| D4 | `app/ml/data_generator.py:24` | progi poziomów 42 i 60 | dobrane tak, by klasy były podobnej liczności (ok. 1/3 każda), co opisano w `docs/ML.md` |
| D5 | `app/ml/rule_based.py:23`, `:27` | punkty za aktywność i staż, progi średniej 2/3 i 4/3 | projekt systemu regułowego; jego trafność sprawdzono w eksperymentach 1, 2 i 4 |
| D6 | `app/ml/train.py:19` | typowo 20% pominiętych odpowiedzi | założenie; wpływ innych odsetków sprawdzono w eksperymencie 2 |
| D7 | `app/services/plan_generator.py:33` | 45 s na serię, 60 s na przejście między ćwiczeniami | przybliżenie do szacowania liczby ćwiczeń w treningu |
| D8 | `app/services/plan_generator.py:142` | powtórzenie testów co 4 tygodnie | założenie; można powiązać z typowym czasem mezocyklu |
| D9 | `app/services/plan_generator.py:48` | dozwolone trudności ćwiczeń dla poziomu | reguła projektowa: poziom ćwiczenia nie wyższy niż poziom użytkownika |
| D10 | `experiments/plan_quality.py` | losowe preferencje osób testowych | założenie eksperymentu 4, opisane w ograniczeniach |
| D11 | `app/data/exercises.json` (ćwiczenia cardio) | lista ćwiczeń cardio, ich poziom trudności i przeciwwskazania | literatura (Oppert 2021, Wewege 2017) uzasadnia obecność wysiłku tlenowego i interwałów w planie redukcyjnym, ale nie wskazuje konkretnych ćwiczeń; proponowana weryfikacja: wartości MET z Herrmann i in., *2024 Adult Compendium of Physical Activities*, JSHS 2024 |

## Rekomendacja

Najwięcej daje konsultacja z fizjoterapeutą lub trenerem, która obejmuje jednocześnie punkty
A4–A9 (reguły i etykiety atlasu) i B6–B12 (parametry planu). W pracy wystarczy opisać, kto
i w jakim zakresie zweryfikował te wartości.
