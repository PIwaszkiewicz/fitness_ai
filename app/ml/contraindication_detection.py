"""Wykrywanie przeciwwskazań ćwiczenia na podstawie jego cech.

Zastosowanie: podpowiedź przeciwwskazań przy dodawaniu do atlasu nowego ćwiczenia,
dla którego nikt ich jeszcze nie opisał. Porównywane są dwa podejścia:

- RuleBasedDetector: reguły eksperckie oparte na wzorcu ruchu, sprzęcie i trudności,
- TreeDetector: drzewo decyzyjne uczone na ćwiczeniach z atlasu (etykiety ręczne).

Oba mają interfejs fit/predict, a predict zwraca dla każdego ćwiczenia zbiór ograniczeń.
"""

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from app.models.enums import (
    Difficulty,
    Equipment,
    Limitation,
    MovementPattern,
    MuscleGroup,
)
from app.schemas import ExerciseFeatures

LIMITATIONS = list(Limitation)

# Reguła 1: ograniczenia wynikające z samego wzorca ruchu (które stawy pracują pod obciążeniem).
PATTERN_RULES = {
    MovementPattern.SQUAT: {Limitation.KNEE},
    MovementPattern.LUNGE: {Limitation.KNEE, Limitation.ANKLE},
    MovementPattern.HINGE: {Limitation.LOWER_BACK},
    MovementPattern.HORIZONTAL_PUSH: {Limitation.SHOULDER},
    MovementPattern.VERTICAL_PUSH: {Limitation.SHOULDER, Limitation.NECK},
    MovementPattern.HORIZONTAL_PULL: set(),
    MovementPattern.VERTICAL_PULL: {Limitation.SHOULDER, Limitation.ELBOW},
    MovementPattern.ISOLATION: set(),  # zależy od grupy mięśniowej (reguła 2)
    MovementPattern.CORE_STABILITY: set(),
    MovementPattern.CORE_DYNAMIC: {Limitation.LOWER_BACK},
    MovementPattern.CARDIO: {Limitation.HEART_CONDITION},
}

# Reguła 2: ćwiczenia izolowane obciążają staw pracującej grupy mięśniowej.
ISOLATION_RULES = {
    MuscleGroup.ARMS: {Limitation.ELBOW},
    MuscleGroup.SHOULDERS: {Limitation.SHOULDER},
    MuscleGroup.CHEST: {Limitation.SHOULDER},
    MuscleGroup.LEGS: {Limitation.KNEE},
    MuscleGroup.GLUTES: {Limitation.HIP},
    MuscleGroup.BACK: {Limitation.NECK},
}

# Wzorce, w których sztanga obciąża kręgosłup i podnosi ciśnienie przy dużym ciężarze.
HEAVY_BARBELL_PATTERNS = {
    MovementPattern.SQUAT,
    MovementPattern.HINGE,
    MovementPattern.HORIZONTAL_PUSH,
    MovementPattern.VERTICAL_PUSH,
}


class RuleBasedDetector:
    """System ekspertowy: przeciwwskazania z reguł opartych na budowie ćwiczenia."""

    def fit(self, exercises: list[ExerciseFeatures], labels=None):
        """Reguły są ustalone przez eksperta, więc nie ma czego uczyć."""
        return self

    def predict(self, exercises: list[ExerciseFeatures]) -> list[set[Limitation]]:
        return [self.detect(exercise) for exercise in exercises]

    def detect(self, exercise: ExerciseFeatures) -> set[Limitation]:
        """Zbiera ograniczenia ze wszystkich pasujących reguł."""
        found = set(PATTERN_RULES[exercise.movement_pattern])
        if exercise.movement_pattern == MovementPattern.ISOLATION:
            found |= ISOLATION_RULES.get(exercise.muscle_group, set())
        # Reguła 3: podpór na dłoniach przy ćwiczeniach z masą ciała obciąża nadgarstki.
        if exercise.equipment == Equipment.NONE and exercise.movement_pattern in (
            MovementPattern.HORIZONTAL_PUSH,
            MovementPattern.CARDIO,
        ):
            found.add(Limitation.WRIST)
        # Reguła 4: ciężkie ćwiczenia ze sztangą obciążają kręgosłup i podnoszą ciśnienie.
        if exercise.equipment == Equipment.BARBELL and exercise.movement_pattern in HEAVY_BARBELL_PATTERNS:
            found |= {Limitation.LOWER_BACK, Limitation.HYPERTENSION}
        # Reguła 5: intensywne ćwiczenia dynamiczne podnoszą ciśnienie.
        if exercise.movement_pattern == MovementPattern.CARDIO and exercise.difficulty != Difficulty.BEGINNER:
            found.add(Limitation.HYPERTENSION)
        return found


def exercise_features(exercises: list[ExerciseFeatures]) -> pd.DataFrame:
    """Zamienia ćwiczenia na liczby: kolumny 0/1 dla każdej wartości słownikowej (one-hot)
    oraz poziom trudności jako liczba 0–2.
    """
    rows = []
    for exercise in exercises:
        row = {}
        for enum_class, value in (
            (MovementPattern, exercise.movement_pattern),
            (MuscleGroup, exercise.muscle_group),
            (Equipment, exercise.equipment),
        ):
            for item in enum_class:
                row[f"{enum_class.__name__}_{item.value}"] = int(item == value)
        row["difficulty"] = list(Difficulty).index(Difficulty(exercise.difficulty))
        rows.append(row)
    return pd.DataFrame(rows)


def labels_to_matrix(labels: list[list[str]]) -> np.ndarray:
    """Zamienia listy przeciwwskazań na macierz 0/1: wiersz = ćwiczenie, kolumna = ograniczenie."""
    return np.array([[int(limitation in items) for limitation in LIMITATIONS] for items in labels])


class TreeDetector:
    """Drzewo decyzyjne przewidujące jednocześnie wszystkie 10 ograniczeń (klasyfikacja wieloetykietowa)."""

    def __init__(self, seed: int = 42):
        self.model = DecisionTreeClassifier(random_state=seed)

    def fit(self, exercises: list[ExerciseFeatures], labels: list[list[str]]):
        self.model.fit(exercise_features(exercises), labels_to_matrix(labels))
        return self

    def predict(self, exercises: list[ExerciseFeatures]) -> list[set[Limitation]]:
        matrix = self.model.predict(exercise_features(exercises))
        return [
            {limitation for limitation, flag in zip(LIMITATIONS, row) if flag}
            for row in matrix
        ]


class HybridDetector:
    """Suma wyników reguł i drzewa: ograniczenie jest wskazane, gdy wykryje je którakolwiek metoda.

    Przy bezpieczeństwie ważniejsze jest niepominięcie przeciwwskazania (recall)
    niż uniknięcie zbędnego wykluczenia ćwiczenia (precyzja).
    """

    def __init__(self, seed: int = 42):
        self.rules = RuleBasedDetector()
        self.tree = TreeDetector(seed)

    def fit(self, exercises: list[ExerciseFeatures], labels: list[list[str]]):
        self.tree.fit(exercises, labels)
        return self

    def predict(self, exercises: list[ExerciseFeatures]) -> list[set[Limitation]]:
        return [
            from_rules | from_tree
            for from_rules, from_tree in zip(self.rules.predict(exercises), self.tree.predict(exercises))
        ]
