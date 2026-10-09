# Plan projektu

Każdy krok realizowany jest na osobnej gałęzi i scalany do `main` przez pull request po przejściu CI.

- [x] **Krok 0.** Inicjalizacja repozytorium (README, .gitignore)
- [x] **Krok 1.** Bazowa architektura warstwowa FastAPI, endpointy `/health` i `/api/v1/ping`, CI (ruff, pytest)
- [x] **Krok 2.** Baza danych: SQLAlchemy + SQLite, modele `UserProfile` i `Exercise`, schematy Pydantic z walidacją zakresów
- [x] **Krok 3.** CRUD profili i ćwiczeń, startowy atlas ok. 30 ćwiczeń (skrypt seed)
- [x] **Krok 4.** Kwestionariusz: endpoint przyjmujący odpowiedzi, walidacja, zapis profilu
- [ ] **Krok 5.** Docker + docker-compose
- [ ] **Krok 6.** Moduł ML: klasyfikacja poziomu sprawności
  - system regułowy (baseline)
  - drzewo decyzyjne
  - sieć neuronowa (`MLPClassifier`)
  - dane syntetyczne z opisanym generatorem
- [ ] **Krok 7.** Eksperymenty
  - porównanie algorytmów (accuracy, F1, macierz pomyłek)
  - wpływ kompletności danych na wyniki
  - śledzenie eksperymentów w MLflow
- [ ] **Krok 8.** Generator planu treningowego
  - filtrowanie ćwiczeń po przeciwwskazaniach
  - pomiar precyzji i recall wykrywania przeciwwskazań
- [ ] **Krok 9.** Frontend kwestionariusza i widok planu
- [ ] **Krok 10.** (opcjonalnie) CD: wdrożenie na Render
