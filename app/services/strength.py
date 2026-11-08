"""Ćwiczenia z ciężarami w kwestionariuszu i szacowanie ciężaru maksymalnego (1RM).

Użytkownik nie musi znać swojego 1RM (ciężaru, który podniesie raz) ani go testować,
co byłoby ryzykowne. Podaje ostatnią serię roboczą: ciężar i liczbę powtórzeń,
a 1RM szacuje wzór Epleya. Wzór jest dokładny dla serii do ok. 10 powtórzeń,
dlatego kwestionariusz przyjmuje 1–10 powtórzeń.
"""

from dataclasses import dataclass

MAX_REPS = 10


@dataclass(frozen=True)
class Lift:
    """Ćwiczenie z kwestionariusza. Odpowiedzi trafiają do pól <name>_kg i <name>_reps."""

    name: str
    label: str
    min_kg: float
    max_kg: float
    # Przy podciąganiu podaje się obciążenie dodatkowe, a podnoszona jest też masa ciała.
    adds_body_weight: bool = False


LIFTS = [
    Lift("squat", "Przysiad ze sztangą", 1, 500),
    Lift("deadlift", "Martwy ciąg", 1, 500),
    Lift("bench_press", "Wyciskanie sztangi leżąc", 1, 400),
    Lift("overhead_press", "Wyciskanie sztangi nad głowę stojąc", 1, 250),
    Lift("pull_up", "Podciąganie na drążku", 0, 150, adds_body_weight=True),
]


def epley_one_rep_max(weight_kg: float, reps: int) -> float:
    """Wzór Epleya: 1RM = ciężar · (1 + powtórzenia / 30). Jedno powtórzenie to już 1RM."""
    if reps == 1:
        return weight_kg
    return weight_kg * (1 + reps / 30)


def estimate_one_rep_maxes(profile) -> dict[str, float]:
    """Szacowany 1RM każdego ćwiczenia, dla którego podano serię (klucz: nazwa ćwiczenia).

    Przy podciąganiu wynik obejmuje masę ciała, bo to ona jest głównym ciężarem.
    """
    result = {}
    for lift in LIFTS:
        weight = getattr(profile, f"{lift.name}_kg")
        reps = getattr(profile, f"{lift.name}_reps")
        if weight is None or reps is None:
            continue
        if lift.adds_body_weight:
            weight += profile.weight_kg
        result[lift.name] = round(epley_one_rep_max(weight, reps), 1)
    return result
