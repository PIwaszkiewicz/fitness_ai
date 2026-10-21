"""Eksperyment 4: jakość planu treningowego w zależności od kompletności danych.

Eksperyment 2 mierzy trafność samej klasyfikacji. Tutaj sprawdzamy, jak błędy klasyfikacji
przy brakach danych przekładają się na plan: dla każdej osoby testowej porównujemy plan
zbudowany dla przewidzianego poziomu z planem „wzorcowym”, zbudowanym dla prawdziwego poziomu
(tego, który dostałaby, gdyby klasyfikator się nie mylił).
"""

import numpy as np
import pandas as pd

from app.ml.data_generator import remove_answers
from app.ml.predictor import ClassifierName
from app.ml.train import TRAIN_MISSING_RATE
from app.models.enums import (
    ActivityLevel,
    Equipment,
    FitnessLevel,
    Gender,
    Limitation,
    TrainingGoal,
)
from app.schemas import ExerciseCreate, ExerciseRead, UserProfileRead
from app.services.plan_generator import generate_plan, is_safe
from experiments.evaluation import CLASSIFIERS, LEVELS, TEST_MISSING_RATES, split_data

# Kolejność poziomów: różnica indeksów mówi, o ile poziomów plan jest za trudny lub za łatwy.
LEVEL_INDEX = {level: index for index, level in enumerate(LEVELS)}
SESSION_MINUTES = [30, 45, 60, 90]
OPTIONAL_EQUIPMENT = [item for item in Equipment if item != Equipment.NONE]


def random_preferences(rng: np.random.Generator) -> dict:
    """Losuje preferencje i ograniczenia osoby, od których (obok poziomu) zależy plan.

    Każdy rodzaj sprzętu jest dostępny z prawdopodobieństwem 50%, a połowa osób
    zgłasza jedno lub dwa ograniczenia zdrowotne.
    """
    limitations = []
    if rng.random() < 0.5:
        limitations = list(rng.choice(list(Limitation), size=rng.integers(1, 3), replace=False))
    return {
        "training_goal": rng.choice(list(TrainingGoal)),
        "training_days_per_week": int(rng.integers(2, 6)),
        "session_minutes": int(rng.choice(SESSION_MINUTES)),
        "available_equipment": [Equipment.NONE]
        + [item for item in OPTIONAL_EQUIPMENT if rng.random() < 0.5],
        "limitations": limitations,
    }


def synthetic_profile(profile_id: int, preferences: dict) -> UserProfileRead:
    """Profil osoby testowej. Dane podstawowe nie wpływają na plan, więc są stałe."""
    return UserProfileRead(
        id=profile_id,
        age=30,
        gender=Gender.MALE,
        height_cm=175,
        weight_kg=75,
        activity_level=ActivityLevel.MODERATE,
        data_completeness=100,
        **preferences,
    )


def plan_exercises(profile: UserProfileRead, level: str, atlas: list[ExerciseRead]) -> set[int]:
    """Zbiór identyfikatorów ćwiczeń w tygodniowym planie dla danego poziomu."""
    plan = generate_plan(profile, FitnessLevel(level), ClassifierName.RULES, atlas)
    return {exercise.exercise_id for day in plan.days for exercise in day.exercises}


def jaccard(a: set, b: set) -> float:
    """Podobieństwo zbiorów: część wspólna podzielona przez sumę (1 – identyczne, 0 – rozłączne)."""
    return len(a & b) / len(a | b) if a | b else 1.0


def plan_quality_study(seeds: list[int], n_samples: int, atlas: list[ExerciseCreate]) -> pd.DataFrame:
    """Porównuje plany z przewidzianego i z prawdziwego poziomu przy rosnących brakach danych.

    Metryki dla każdego klasyfikatora, ziarna i odsetka braków:
    - level_match: część osób, które dostały plan dla swojego prawdziwego poziomu,
    - too_hard / too_easy: plan dla wyższego / niższego poziomu niż prawdziwy,
    - harder_exercises: część osób, których plan zawiera ćwiczenie trudniejsze niż ich prawdziwy poziom,
    - exercise_overlap: średnie podobieństwo (Jaccarda) ćwiczeń planu do planu wzorcowego,
    - unsafe_exercises: liczba ćwiczeń przeciwwskazanych dla osoby (powinno być zawsze 0).
    """
    exercises = [ExerciseRead(id=i, **item.model_dump()) for i, item in enumerate(atlas, start=1)]
    by_id = {exercise.id: exercise for exercise in exercises}
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        X_train, X_test, y_train, y_test = split_data(n_samples, seed)
        X_train = remove_answers(X_train, TRAIN_MISSING_RATE, rng)
        classifiers = {name: build(seed).fit(X_train, y_train) for name, build in CLASSIFIERS.items()}

        # Plan zależy tylko od poziomu i preferencji, więc dla każdej osoby budujemy
        # trzy plany (po jednym na poziom) i potem tylko wybieramy właściwy.
        profiles = [synthetic_profile(i, random_preferences(rng)) for i in range(len(X_test))]
        plans = [{level: plan_exercises(profile, level, exercises) for level in LEVELS} for profile in profiles]
        true_levels = list(y_test)

        for missing_rate in TEST_MISSING_RATES:
            X_incomplete = remove_answers(X_test, missing_rate, rng)
            for name, classifier in classifiers.items():
                predicted = classifier.predict(X_incomplete)
                shift = np.array([LEVEL_INDEX[p] - LEVEL_INDEX[t] for p, t in zip(predicted, true_levels)])
                overlap = [
                    jaccard(person_plans[p], person_plans[t])
                    for person_plans, p, t in zip(plans, predicted, true_levels)
                ]
                harder = [
                    any(LEVEL_INDEX[by_id[exercise_id].difficulty] > LEVEL_INDEX[t] for exercise_id in person_plans[p])
                    for person_plans, p, t in zip(plans, predicted, true_levels)
                ]
                unsafe = sum(
                    not is_safe(by_id[exercise_id], profile.limitations)
                    for profile, person_plans, p in zip(profiles, plans, predicted)
                    for exercise_id in person_plans[p]
                )
                rows.append({
                    "classifier": name,
                    "seed": seed,
                    "test_missing_rate": missing_rate,
                    "level_match": float(np.mean(shift == 0)),
                    "too_hard": float(np.mean(shift > 0)),
                    "too_easy": float(np.mean(shift < 0)),
                    "harder_exercises": float(np.mean(harder)),
                    "exercise_overlap": float(np.mean(overlap)),
                    "unsafe_exercises": unsafe,
                })
    return pd.DataFrame(rows)
