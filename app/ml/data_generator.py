"""Generator syntetycznych danych do uczenia i oceny klasyfikatorów sprawności.

Brak publicznego zbioru danych z wynikami testów i oceną sprawności sprawia,
że dane generujemy według jawnego, opisanego modelu:

1. Losujemy cechy osoby: płeć, wiek, wzrost, poziom aktywności, staż treningowy.
2. Wyznaczamy ukrytą „prawdziwą” sprawność (0–100): rośnie z aktywnością i stażem,
   spada z wiekiem po 30. roku życia, plus losowe różnice między ludźmi.
3. Z prawdziwej sprawności wyliczamy wyniki testów (pompki, przysiady, deska,
   tętno spoczynkowe) z losowym szumem, bo każdy test to niedokładny pomiar.
4. Etykieta (poziom sprawności) wynika z prawdziwej sprawności, której modele nie widzą.
   Klasyfikator musi więc odgadnąć poziom na podstawie zaszumionych pomiarów.

Pełny opis wzorów: docs/ML.md.
"""

import numpy as np
import pandas as pd

from app.ml.features import FEATURES, OPTIONAL_FEATURES
from app.models.enums import FitnessLevel

# Granice prawdziwej sprawności między poziomami: <42 początkujący, 42–60 średni, ≥60 zaawansowany.
LEVEL_THRESHOLDS = (42, 60)

# Rozkład poziomów aktywności w populacji (od siedzącego do bardzo wysokiego).
ACTIVITY_PROBABILITIES = [0.25, 0.25, 0.25, 0.15, 0.10]


def fitness_to_level(fitness: np.ndarray) -> np.ndarray:
    """Zamienia prawdziwą sprawność (0–100) na poziom sprawności."""
    low, high = LEVEL_THRESHOLDS
    return np.select(
        [fitness < low, fitness < high],
        [FitnessLevel.BEGINNER.value, FitnessLevel.INTERMEDIATE.value],
        default=FitnessLevel.ADVANCED.value,
    )


def generate_dataset(
    n_samples: int = 5000, missing_rate: float = 0.0, seed: int = 42
) -> tuple[pd.DataFrame, pd.Series]:
    """Zwraca tabelę cech X i etykiety y dla n_samples losowych osób.

    missing_rate to prawdopodobieństwo pominięcia każdej odpowiedzi opcjonalnej
    (symuluje użytkowników, którzy nie wykonali części testów).
    Ten sam seed zawsze daje te same dane, więc eksperymenty są powtarzalne.
    """
    rng = np.random.default_rng(seed)
    n = n_samples

    # 1. Cechy osoby
    is_male = rng.integers(0, 2, n)
    age = rng.integers(16, 76, n)
    height_cm = np.where(is_male == 1, rng.normal(178, 7, n), rng.normal(165, 6.5, n))
    activity = rng.choice(5, n, p=ACTIVITY_PROBABILITIES)
    # Staż jest powiązany z aktywnością: kto dużo się rusza, częściej trenuje dłużej.
    experience = np.clip(np.round(0.6 * activity + rng.normal(0, 0.9, n)), 0, 3)

    # 2. Ukryta prawdziwa sprawność
    fitness = (
        35
        + 9 * activity
        + 7 * experience
        - 0.35 * np.maximum(age - 30, 0)
        + rng.normal(0, 8, n)
    )
    fitness = np.clip(fitness, 0, 100)

    # Sprawniejsze osoby mają średnio niższe BMI.
    bmi = np.clip(26 - 0.08 * (fitness - 50) + rng.normal(0, 3.5, n), 16, 45)
    weight_kg = np.clip(bmi * (height_cm / 100) ** 2, 30, 300)

    # 3. Zaszumione wyniki testów
    pushup_factor = np.where(is_male == 1, 0.5, 0.32)  # kobiety wykonują średnio mniej pompek
    pushups = fitness * pushup_factor * rng.normal(1, 0.15, n) - 0.4 * np.maximum(bmi - 25, 0)
    squats = 0.55 * fitness + 5 - 0.1 * np.maximum(age - 40, 0) + rng.normal(0, 5, n)
    plank_seconds = 2.2 * fitness + rng.normal(0, 20, n)
    resting_heart_rate = 85 - 0.3 * fitness + rng.normal(0, 6, n)

    # Zakresy zgodne z walidacją kwestionariusza.
    X = pd.DataFrame({
        "age": age,
        "is_male": is_male,
        "bmi": weight_kg / (height_cm / 100) ** 2,
        "activity_level": activity,
        "training_experience": experience,
        "pushups": np.clip(np.round(pushups), 0, 150),
        "squats": np.clip(np.round(squats), 0, 150),
        "plank_seconds": np.clip(np.round(plank_seconds), 0, 600),
        "resting_heart_rate": np.clip(np.round(resting_heart_rate), 30, 150),
    }, columns=FEATURES).astype(float)

    # Symulacja pominiętych pytań opcjonalnych
    for column in OPTIONAL_FEATURES:
        X.loc[rng.random(n) < missing_rate, column] = np.nan

    # 4. Etykiety z prawdziwej sprawności
    y = pd.Series(fitness_to_level(fitness), name="fitness_level")
    return X, y
