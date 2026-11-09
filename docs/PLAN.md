# Plan projektu

Każdy krok realizowany jest na osobnej gałęzi i scalany do `main` przez pull request po przejściu CI.

- [x] **Krok 0.** Inicjalizacja repozytorium (README, .gitignore)
- [x] **Krok 1.** Bazowa architektura warstwowa FastAPI, endpointy `/health` i `/api/v1/ping`, CI (ruff, pytest)
- [x] **Krok 2.** Baza danych: SQLAlchemy + SQLite, modele `UserProfile` i `Exercise`, schematy Pydantic z walidacją zakresów
- [x] **Krok 3.** CRUD profili i ćwiczeń, startowy atlas ok. 30 ćwiczeń (skrypt seed)
- [x] **Krok 4.** Kwestionariusz: endpoint przyjmujący odpowiedzi, walidacja, zapis profilu
- [x] **Krok 5.** Docker + docker-compose
- [x] **Krok 6.** Moduł ML: klasyfikacja poziomu sprawności
  - system regułowy (baseline)
  - drzewo decyzyjne
  - sieć neuronowa (`MLPClassifier`)
  - dane syntetyczne z opisanym generatorem
- [x] **Krok 7.** Eksperymenty
  - porównanie algorytmów (accuracy, F1, macierz pomyłek)
  - wpływ kompletności danych na wyniki
  - śledzenie eksperymentów w MLflow
- [x] **Krok 8.** Generator planu treningowego
  - filtrowanie ćwiczeń po przeciwwskazaniach
  - pomiar precyzji i recall wykrywania przeciwwskazań
- [x] **Krok 9.** Frontend kwestionariusza i widok planu
- [x] **Krok 10.** (opcjonalnie) CD: wdrożenie na Render

## Rozszerzenia części badawczej

- [x] Eksperyment 4: jakość planu treningowego w zależności od kompletności danych
- [x] Dobór hiperparametrów modeli ML walidacją krzyżową
- [x] Test istotności statystycznej różnic między klasyfikatorami
- [x] Pomiar czasu odpowiedzi API
- [x] Eksperyment 5: wskaźnik siły z pytań o ciężary u osób trenujących

## Rozszerzenia aplikacji

- [x] Dobór klasyfikatora do liczby pustych odpowiedzi (średnia z 5 powtórzeń oceny)
- [x] Pytania o ciężary w 5 ćwiczeniach ze sztangą (seria zamiast 1RM, wzór Epleya) i wariant pompek
- [x] Wskaźnik siły względnej jako cecha klasyfikatorów
- [x] Ciężary startowe w planie dla wszystkich ćwiczeń z obciążeniem (przeliczniki 1RM)
- [x] Informacja w aplikacji, który algorytm ocenił poziom i dlaczego
- [x] Prosta migracja bazy (nowe kolumny) i aktualizacja atlasu przy starcie serwera
