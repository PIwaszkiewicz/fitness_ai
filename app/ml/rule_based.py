"""System ekspertowy (regułowy) klasyfikujący poziom sprawności: punkt odniesienia dla modeli ML.

Każdy dostępny wskaźnik dostaje 0, 1 albo 2 punkty według stałych progów,
wzorowanych na typowych normach sprawnościowych. Średnia punktów wyznacza poziom.
Brakujące wyniki testów są pomijane, więc system działa przy niepełnych danych.
"""

import numpy as np
import pandas as pd

from app.models.enums import FitnessLevel

# Progi (dolna granica 1 pkt, dolna granica 2 pkt) dla wyników testów.
PUSHUP_LIMITS = {"male": (15, 30), "female": (8, 20)}
SQUAT_LIMITS = (25, 40)  # przysiady w 1 minutę
PLANK_LIMITS = (60, 120)  # sekundy
RESTING_HR_LIMITS = (65, 81)  # tętno: im niższe, tym lepiej (punkty odwrócone)
# Od 50. roku życia normy dla pompek są niższe o 30%.
SENIOR_AGE = 50
SENIOR_FACTOR = 0.7

# Punkty za poziom aktywności (0–4) i staż (0–3).
ACTIVITY_POINTS = [0, 0, 1, 2, 2]
EXPERIENCE_POINTS = [0, 0, 1, 2]

# Średnia punktów poniżej 2/3 to poziom początkujący, poniżej 4/3 średni, wyżej zaawansowany.
LEVEL_LIMITS = (2 / 3, 4 / 3)


def points(value: float, limits: tuple[float, float]) -> int:
    """Zwraca 0, 1 lub 2 punkty zależnie od tego, które progi przekracza wartość."""
    low, high = limits
    if value < low:
        return 0
    if value < high:
        return 1
    return 2


class RuleBasedClassifier:
    """Klasyfikator regułowy z takim samym interfejsem jak modele scikit-learn (fit/predict).

    Wspólny interfejs pozwala porównywać wszystkie podejścia tym samym kodem.
    """

    def fit(self, X: pd.DataFrame, y=None):
        """Reguły są ustalone przez eksperta, więc nie ma czego uczyć."""
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Klasyfikuje każdy wiersz tabeli cech."""
        return np.array([self.classify_row(row) for _, row in X.iterrows()])

    def classify_row(self, row: pd.Series) -> str:
        """Zbiera punkty za dostępne wskaźniki i zamienia ich średnią na poziom."""
        scores = [ACTIVITY_POINTS[int(row["activity_level"])]]
        if not pd.isna(row["training_experience"]):
            scores.append(EXPERIENCE_POINTS[int(row["training_experience"])])
        if not pd.isna(row["pushups"]):
            low, high = PUSHUP_LIMITS["male" if row["is_male"] == 1 else "female"]
            if row["age"] >= SENIOR_AGE:
                low, high = low * SENIOR_FACTOR, high * SENIOR_FACTOR
            scores.append(points(row["pushups"], (low, high)))
        if not pd.isna(row["squats"]):
            scores.append(points(row["squats"], SQUAT_LIMITS))
        if not pd.isna(row["plank_seconds"]):
            scores.append(points(row["plank_seconds"], PLANK_LIMITS))
        if not pd.isna(row["resting_heart_rate"]):
            scores.append(2 - points(row["resting_heart_rate"], RESTING_HR_LIMITS))

        average = sum(scores) / len(scores)
        if average < LEVEL_LIMITS[0]:
            return FitnessLevel.BEGINNER.value
        if average < LEVEL_LIMITS[1]:
            return FitnessLevel.INTERMEDIATE.value
        return FitnessLevel.ADVANCED.value
