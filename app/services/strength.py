"""Ćwiczenia z ciężarami w kwestionariuszu i szacowanie ciężaru maksymalnego (1RM).

Użytkownik nie musi znać swojego 1RM (ciężaru, który podniesie raz) ani go testować,
co byłoby ryzykowne. Podaje ostatnią serię roboczą: ciężar i liczbę powtórzeń,
a 1RM szacuje wzór Epleya. Wzór jest dokładny dla serii do ok. 10 powtórzeń,
dlatego kwestionariusz przyjmuje 1–10 powtórzeń.

Dla klasyfikatorów wyniki łączone są w jeden wskaźnik siły względnej (strength_index):
1RM podzielony przez masę ciała i odniesiony do normy dla płci, uśredniony po ćwiczeniach.
Z 1RM generator planu wylicza też ciężary startowe (starting_load).
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


# Ćwiczenia z atlasu (app/data/exercises.json), które odpowiadają pytaniom o ciężary.
# Tylko przy nich plan podaje ciężar: przeliczanie 1RM na inne odmiany (np. hantle)
# byłoby zgadywaniem, którego nie da się uzasadnić.
ATLAS_LIFTS = {
    "Przysiad ze sztangą": "squat",
    "Martwy ciąg klasyczny": "deadlift",
    "Wyciskanie sztangi na ławce płaskiej": "bench_press",
    "Wyciskanie sztangi nad głowę": "overhead_press",
    "Podciąganie na drążku": "pull_up",
}
# Powtórzenia w zapasie przy doborze ciężaru (jak zalecenie 2–3 w planie, docs/ZRODLA.md B10).
REPS_IN_RESERVE = 2
# Ciężar zaokrąglany w dół do 2,5 kg, czyli do najmniejszej typowej zmiany obciążenia sztangi.
LOAD_STEP_KG = 2.5

# Norma siły względnej (1RM / masa ciała) dla osoby średniozaawansowanej w treningu siłowym.
# Wartości przybliżone na podstawie popularnych tabel norm siłowych; wymagają źródła
# (docs/ZRODLA.md). Przy podciąganiu 1RM obejmuje masę ciała, więc 1,0 to jedno podciągnięcie.
STRENGTH_NORMS = {
    "male": {"squat": 1.25, "deadlift": 1.5, "bench_press": 1.0, "overhead_press": 0.65,
             "pull_up": 1.3},
    "female": {"squat": 1.0, "deadlift": 1.25, "bench_press": 0.65, "overhead_press": 0.45,
               "pull_up": 1.0},
}


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


def strength_index(profile) -> float | None:
    """Średnia siła względna odniesiona do normy: 1,0 to poziom normy, 0,5 połowa normy.

    Każde ćwiczenie dzielone jest przez masę ciała i normę dla płci, więc wyniki różnych
    ćwiczeń są porównywalne i można je uśrednić. Działa przy dowolnej liczbie podanych
    ćwiczeń (od 1 do 5). Zwraca None, gdy użytkownik nie podał żadnej serii.
    """
    maxes = estimate_one_rep_maxes(profile)
    if not maxes:
        return None
    norms = STRENGTH_NORMS[profile.gender]
    ratios = [one_rep_max / profile.weight_kg / norms[name] for name, one_rep_max in maxes.items()]
    return sum(ratios) / len(ratios)


def starting_load(one_rep_max: float, reps: int, body_weight: float | None = None) -> str:
    """Ciężar startowy do serii o podanej liczbie powtórzeń, jako tekst do planu.

    Odwrotny wzór Epleya podaje ciężar, który da się podnieść reps + REPS_IN_RESERVE razy,
    więc w serii zostają powtórzenia w zapasie. Przy podciąganiu (body_weight podane)
    wynikiem jest obciążenie dodatkowe ponad masę ciała. Gdy wychodzi wyraźnie mniej niż
    masa ciała, użytkownik nie wykona tylu powtórzeń bez pomocy, więc zalecana jest asysta gumy.
    """
    load = one_rep_max / (1 + (reps + REPS_IN_RESERVE) / 30)
    if body_weight is not None:
        load -= body_weight
        if load <= -LOAD_STEP_KG:
            return "masa ciała, z asystą gumy"
        if load < LOAD_STEP_KG:
            return "masa ciała"
    load = load // LOAD_STEP_KG * LOAD_STEP_KG
    text = f"{load:g}".replace(".", ",") + " kg"
    return "+" + text if body_weight is not None else text
