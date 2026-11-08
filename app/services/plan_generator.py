"""Generator tygodniowego planu treningowego (system ekspertowy oparty na regułach).

Kroki:
1. Wybór ćwiczeń dopuszczonych dla użytkownika: dostępny sprzęt, poziom trudności
   zgodny z poziomem sprawności i brak przeciwwskazań (bezpieczeństwo).
2. Parametry treningu (serie, powtórzenia, przerwy) według celu treningowego.
3. Liczba ćwiczeń w treningu wyliczona z czasu, jaki użytkownik ma na trening.
4. Rozpisanie dni: przy 1–3 dniach trening całego ciała, przy 4–7 podział góra/dół.
   Ćwiczenia rotują między dniami, żeby plan był zróżnicowany.
5. Rekomendacje progresji i ostrzeżenia zdrowotne.

Ten sam profil zawsze daje ten sam plan (brak losowości), więc plan można odtworzyć.
"""

from app.ml.predictor import ClassifierName
from app.models.enums import (
    CARDIOVASCULAR_LIMITATIONS,
    Difficulty,
    Equipment,
    FitnessLevel,
    MuscleGroup,
    TrainingGoal,
)
from app.schemas import ExerciseRead, UserProfileRead
from app.schemas.plan import PlanDay, PlanExercise, TrainingPlan
from app.services.questionnaire_service import build_warnings

# Wartości przyjmowane, gdy użytkownik nie odpowiedział na pytania o preferencje.
DEFAULT_DAYS_PER_WEEK = 3
DEFAULT_SESSION_MINUTES = 45

# Szacowanie czasu treningu: rozgrzewka, czas jednej serii i przejście między ćwiczeniami.
WARMUP_MINUTES = 10
SECONDS_PER_SET = 45
TRANSITION_SECONDS = 60
MIN_EXERCISES = 3
MAX_EXERCISES = 8

# Parametry treningu zależne od celu (typowe zakresy stosowane w planowaniu treningu).
GOAL_PARAMETERS = {
    TrainingGoal.STRENGTH: {"sets": 4, "reps": "4–6", "rest_seconds": 150},
    TrainingGoal.MUSCLE_GAIN: {"sets": 3, "reps": "8–12", "rest_seconds": 90},
    TrainingGoal.WEIGHT_LOSS: {"sets": 3, "reps": "12–15", "rest_seconds": 45},
    TrainingGoal.ENDURANCE: {"sets": 3, "reps": "15–20", "rest_seconds": 30},
    TrainingGoal.GENERAL_FITNESS: {"sets": 3, "reps": "10–12", "rest_seconds": 60},
}

# Poziomy trudności ćwiczeń dozwolone dla danego poziomu sprawności.
ALLOWED_DIFFICULTIES = {
    FitnessLevel.BEGINNER: {Difficulty.BEGINNER},
    FitnessLevel.INTERMEDIATE: {Difficulty.BEGINNER, Difficulty.INTERMEDIATE},
    FitnessLevel.ADVANCED: {Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED},
}

# Wskazówki dla celu „redukcja masy ciała”. Źródła: docs/ZRODLA.md.
WEIGHT_LOSS_TIPS = [
    (
        "O spadku masy ciała decyduje przede wszystkim dieta. Zalecany deficyt to około "
        "500–750 kcal dziennie poniżej zapotrzebowania."
    ),
    (
        "Sam trening zwykle daje niewielki spadek masy, średnio 2–3 kg. "
        "Najlepsze efekty daje połączenie ruchu z dietą."
    ),
    (
        "Poza tym planem zaplanuj co najmniej 150–300 minut tygodniowo umiarkowanego wysiłku "
        "tlenowego, np. szybkiego marszu, roweru lub pływania. Im więcej ruchu, tym większy efekt."
    ),
    "Nie rezygnuj z ćwiczeń siłowych. Pomagają zachować mięśnie podczas redukcji.",
    (
        "Ćwiczenia interwałowe dają podobny spadek tkanki tłuszczowej jak dłuższy wysiłek ciągły, "
        "a zajmują mniej czasu."
    ),
    (
        "Już spadek o 3–5% masy ciała poprawia zdrowie. Regularny ruch pomaga też utrzymać wagę "
        "po redukcji."
    ),
]
INTERVAL_CONSULTATION_TIP = "Przed treningiem interwałowym skonsultuj się z lekarzem."

# Szablony dni: nazwa i kolejność grup mięśniowych, z których wybierane są ćwiczenia.
G = MuscleGroup
FULL_BODY_DAY = ("Całe ciało", [G.LEGS, G.CHEST, G.BACK, G.GLUTES, G.SHOULDERS, G.CORE, G.ARMS, G.FULL_BODY])
UPPER_DAY = ("Góra ciała", [G.CHEST, G.BACK, G.SHOULDERS, G.ARMS, G.CORE, G.BACK, G.CHEST, G.SHOULDERS])
LOWER_DAY = ("Dół ciała", [G.LEGS, G.GLUTES, G.CORE, G.LEGS, G.GLUTES, G.FULL_BODY, G.CORE, G.LEGS])


def is_safe(exercise: ExerciseRead, limitations: list[str]) -> bool:
    """Ćwiczenie jest bezpieczne, gdy żadne jego przeciwwskazanie nie dotyczy użytkownika."""
    return not set(exercise.contraindications) & set(limitations)


def select_exercises(
    exercises: list[ExerciseRead], profile: UserProfileRead, level: FitnessLevel
) -> tuple[list[ExerciseRead], int]:
    """Zwraca ćwiczenia dopuszczone dla użytkownika i liczbę odrzuconych z powodu przeciwwskazań."""
    # Ćwiczenia z masą ciała są dostępne zawsze.
    equipment = set(profile.available_equipment or []) | {Equipment.NONE}
    matching = [
        exercise for exercise in exercises
        if exercise.equipment in equipment and exercise.difficulty in ALLOWED_DIFFICULTIES[level]
    ]
    safe = [exercise for exercise in matching if is_safe(exercise, profile.limitations)]
    return safe, len(matching) - len(safe)


def exercises_per_session(minutes: int, sets: int, rest_seconds: int) -> int:
    """Liczba ćwiczeń, które zmieszczą się w treningu po odjęciu rozgrzewki."""
    seconds_per_exercise = sets * (SECONDS_PER_SET + rest_seconds) + TRANSITION_SECONDS
    count = (minutes - WARMUP_MINUTES) * 60 // seconds_per_exercise
    return max(MIN_EXERCISES, min(MAX_EXERCISES, count))


def day_templates(days_per_week: int) -> list[tuple[str, list[MuscleGroup]]]:
    """1–3 dni: całe ciało w każdym treningu; 4–7 dni: na zmianę góra i dół ciała."""
    if days_per_week <= 3:
        return [FULL_BODY_DAY] * days_per_week
    return [UPPER_DAY if day % 2 == 0 else LOWER_DAY for day in range(days_per_week)]


def build_days(pool: list[ExerciseRead], days_per_week: int, count: int) -> list[list[ExerciseRead]]:
    """Rozdziela ćwiczenia na dni według szablonów, rotując ćwiczenia w obrębie grup."""
    by_group: dict[str, list[ExerciseRead]] = {}
    for exercise in pool:
        by_group.setdefault(exercise.muscle_group, []).append(exercise)
    # Licznik użyć grupy: kolejne dni dostają kolejne ćwiczenia z tej samej grupy.
    times_used = dict.fromkeys(by_group, 0)

    days = []
    for _, groups in day_templates(days_per_week):
        chosen: list[ExerciseRead] = []
        for group in groups:
            candidates = [e for e in by_group.get(group, []) if e not in chosen]
            if len(chosen) == count or not candidates:
                continue
            chosen.append(candidates[times_used[group] % len(candidates)])
            times_used[group] += 1
        # Gdy dla części grup zabrakło ćwiczeń, uzupełniamy dowolnymi dopuszczonymi.
        for exercise in pool:
            if len(chosen) < count and exercise not in chosen:
                chosen.append(exercise)
        days.append(chosen)
    return days


def weight_loss_tips(profile: UserProfileRead) -> list[str]:
    """Wskazówki redukcyjne. Przy chorobach układu krążenia dochodzi zalecenie konsultacji."""
    tips = list(WEIGHT_LOSS_TIPS)
    if any(item in CARDIOVASCULAR_LIMITATIONS for item in profile.limitations):
        tips.append(INTERVAL_CONSULTATION_TIP)
    return tips


def progression_tips(profile: UserProfileRead, level: FitnessLevel) -> list[str]:
    """Rekomendacje, jak zwiększać trudność treningu w kolejnych tygodniach."""
    tips = []
    if level == FitnessLevel.BEGINNER:
        tips.append(
            "Przez pierwsze 2–3 tygodnie skup się na technice. Dobieraj ciężar tak, "
            "żeby w każdej serii zostały 2–3 powtórzenia w zapasie."
        )
    if profile.training_goal == TrainingGoal.STRENGTH:
        tips.append(
            "Gdy we wszystkich seriach wykonasz górny zakres powtórzeń, zwiększ obciążenie o 2,5–5%."
        )
    elif profile.training_goal in (TrainingGoal.WEIGHT_LOSS, TrainingGoal.ENDURANCE):
        tips.append("Co tydzień dodaj 1–2 powtórzenia w serii albo skróć przerwy o 5–10 sekund.")
        if profile.training_goal == TrainingGoal.WEIGHT_LOSS:
            tips.extend(weight_loss_tips(profile))
    else:
        tips.append(
            "Gdy we wszystkich seriach wykonasz górny zakres powtórzeń z dobrą techniką, "
            "zwiększ obciążenie lub trudność ćwiczenia."
        )
    tips.append("Co 4–6 tygodni zaplanuj lżejszy tydzień z około połową serii, żeby organizm się zregenerował.")
    if profile.limitations:
        tips.append("Przerwij ćwiczenie, jeśli ból w zgłoszonym miejscu się nasila.")
    tips.append(
        "Powtórz testy sprawności co 4 tygodnie i zaktualizuj profil. "
        "Plan dostosuje się do nowego poziomu automatycznie."
    )
    return tips


def generate_plan(
    profile: UserProfileRead,
    level: FitnessLevel,
    classifier: ClassifierName,
    exercises: list[ExerciseRead],
) -> TrainingPlan:
    """Buduje tygodniowy plan treningowy dla profilu o danym poziomie sprawności."""
    params = dict(GOAL_PARAMETERS[profile.training_goal])
    if level == FitnessLevel.BEGINNER:
        params["sets"] = max(2, params["sets"] - 1)  # mniejsza objętość na start

    days_per_week = profile.training_days_per_week or DEFAULT_DAYS_PER_WEEK
    minutes = profile.session_minutes or DEFAULT_SESSION_MINUTES
    pool, excluded = select_exercises(exercises, profile, level)
    count = exercises_per_session(minutes, params["sets"], params["rest_seconds"])

    days = []
    for number, (template, chosen) in enumerate(
        zip(day_templates(days_per_week), build_days(pool, days_per_week, count)), start=1
    ):
        days.append(PlanDay(
            day=number,
            focus=template[0],
            exercises=[
                PlanExercise(
                    exercise_id=exercise.id,
                    name=exercise.name,
                    muscle_group=exercise.muscle_group,
                    equipment=exercise.equipment,
                    **params,
                )
                for exercise in chosen
            ],
        ))

    warnings = build_warnings(profile)
    if not pool:
        warnings.append("Brak ćwiczeń spełniających kryteria. Sprawdź atlas ćwiczeń i dostępny sprzęt.")

    return TrainingPlan(
        profile_id=profile.id,
        fitness_level=level,
        classifier=classifier,
        training_goal=profile.training_goal,
        days_per_week=days_per_week,
        session_minutes=minutes,
        days=days,
        excluded_for_safety=excluded,
        progression=progression_tips(profile, level),
        warnings=warnings,
    )
