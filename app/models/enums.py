"""Słowniki wartości (enumy) wspólne dla modeli bazy danych i schematów API.

Zamknięta lista wartości zamiast dowolnego tekstu sprawia, że dane są spójne,
a kontuzje użytkownika można bezpośrednio porównać z przeciwwskazaniami ćwiczeń.
StrEnum dziedziczy po str, więc wartości zapisują się w bazie jako zwykły tekst.
"""

from enum import StrEnum


class Gender(StrEnum):
    """Płeć użytkownika (wpływa m.in. na normy sprawnościowe)."""

    MALE = "male"
    FEMALE = "female"


class TrainingGoal(StrEnum):
    """Główny cel treningowy użytkownika."""

    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    GENERAL_FITNESS = "general_fitness"


class ActivityLevel(StrEnum):
    """Poziom codziennej aktywności fizycznej użytkownika."""

    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Limitation(StrEnum):
    """Ograniczenia zdrowotne i ruchowe.

    Ten sam słownik opisuje kontuzje użytkownika i przeciwwskazania ćwiczeń,
    dzięki czemu wykrycie konfliktu to proste porównanie dwóch zbiorów.
    """

    KNEE = "knee"
    HIP = "hip"
    ANKLE = "ankle"
    LOWER_BACK = "lower_back"
    SHOULDER = "shoulder"
    ELBOW = "elbow"
    WRIST = "wrist"
    NECK = "neck"
    HYPERTENSION = "hypertension"
    HEART_CONDITION = "heart_condition"


# Ograniczenia układu krążenia, przy których wysiłek wymaga zgody lekarza.
CARDIOVASCULAR_LIMITATIONS = [Limitation.HYPERTENSION, Limitation.HEART_CONDITION]


class TrainingExperience(StrEnum):
    """Staż treningowy, czyli jak długo użytkownik regularnie trenuje."""

    NONE = "none"
    LESS_THAN_1_YEAR = "less_than_1_year"
    FROM_1_TO_3_YEARS = "1_to_3_years"
    MORE_THAN_3_YEARS = "more_than_3_years"


class MuscleGroup(StrEnum):
    """Główna grupa mięśniowa angażowana przez ćwiczenie."""

    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    LEGS = "legs"
    GLUTES = "glutes"
    CORE = "core"
    FULL_BODY = "full_body"


class Equipment(StrEnum):
    """Sprzęt potrzebny do wykonania ćwiczenia."""

    NONE = "none"
    DUMBBELLS = "dumbbells"
    BARBELL = "barbell"
    KETTLEBELL = "kettlebell"
    RESISTANCE_BAND = "resistance_band"
    PULL_UP_BAR = "pull_up_bar"
    MACHINE = "machine"


class Difficulty(StrEnum):
    """Poziom trudności ćwiczenia (odpowiada poziomom sprawności użytkownika)."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
