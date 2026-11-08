"""Zamiana profilu użytkownika na cechy liczbowe dla klasyfikatorów.

Modele uczenia maszynowego operują tylko na liczbach, więc wartości słownikowe
zamieniamy na liczby porządkowe (np. poziom aktywności 0–4), a brak odpowiedzi na NaN.
"""

import numpy as np
import pandas as pd

from app.models.enums import ActivityLevel, Gender, PushupVariant, TrainingExperience
from app.services.strength import strength_index

# Kolejność kolumn, której oczekują wszystkie modele.
FEATURES = [
    "age",
    "is_male",
    "bmi",
    "activity_level",
    "training_experience",
    "pushups",
    "squats",
    "plank_seconds",
    "resting_heart_rate",
    "strength_index",
]

# Cechy pochodzące z pytań opcjonalnych, które każdy może pominąć.
OPTIONAL_FEATURES = ["training_experience", "pushups", "squats", "plank_seconds", "resting_heart_rate"]
# Cechy z pytań, które widzi tylko część osób (wskaźnik siły: tylko trenujący z ciężarami).
# Ich brak nie jest pominięciem odpowiedzi, dlatego nie liczy się do pustych odpowiedzi.
CONDITIONAL_FEATURES = ["strength_index"]

# Pompki z kolan obciążają ok. 49% masy ciała, a klasyczne ok. 64% (Ebben i in., 2011).
# Wynik z kolan przeliczamy na równoważną liczbę pompek klasycznych.
KNEE_PUSHUP_FACTOR = 0.49 / 0.64

# Kolejność wartości w enumach odpowiada rosnącemu poziomowi (indeks = liczba porządkowa).
ACTIVITY_ORDER = list(ActivityLevel)
EXPERIENCE_ORDER = list(TrainingExperience)


def profile_to_features(profile) -> pd.DataFrame:
    """Tworzy jednowierszową tabelę cech z profilu (obiektu bazy lub schematu Pydantic)."""
    experience = profile.training_experience
    row = {
        "age": profile.age,
        "is_male": 1 if profile.gender == Gender.MALE else 0,
        "bmi": profile.weight_kg / (profile.height_cm / 100) ** 2,
        "activity_level": ACTIVITY_ORDER.index(ActivityLevel(profile.activity_level)),
        "training_experience": (
            EXPERIENCE_ORDER.index(TrainingExperience(experience)) if experience else np.nan
        ),
        "pushups": (
            profile.pushups * KNEE_PUSHUP_FACTOR
            if profile.pushups is not None and profile.pushup_variant == PushupVariant.KNEES
            else profile.pushups
        ),
        "squats": profile.squats,
        "plank_seconds": profile.plank_seconds,
        "resting_heart_rate": profile.resting_heart_rate,
        "strength_index": strength_index(profile),
    }
    # astype(float) zamienia brakujące odpowiedzi (None) na NaN.
    return pd.DataFrame([row], columns=FEATURES).astype(float)


def count_missing_answers(profile) -> int:
    """Liczba pustych odpowiedzi opcjonalnych (0–5) w profilu."""
    return int(profile_to_features(profile)[OPTIONAL_FEATURES].isna().sum(axis=1).iloc[0])
