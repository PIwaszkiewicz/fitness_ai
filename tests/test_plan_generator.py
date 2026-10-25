"""Testy generatora planu treningowego (bez bazy danych, na atlasie z pliku JSON)."""

import pytest

from app.ml.predictor import ClassifierName
from app.models.enums import FitnessLevel
from app.schemas import ExerciseRead, UserProfileRead
from app.seed import load_atlas
from app.services.plan_generator import (
    INTERVAL_CONSULTATION_TIP,
    WEIGHT_LOSS_TIPS,
    exercises_per_session,
    generate_plan,
    is_safe,
    select_exercises,
)

# Atlas z pliku z nadanymi identyfikatorami, jak po zapisie do bazy.
ATLAS = [ExerciseRead(id=i, **e.model_dump()) for i, e in enumerate(load_atlas(), start=1)]

BASE = {
    "id": 1,
    "data_completeness": 0,
    "age": 30,
    "gender": "female",
    "height_cm": 168,
    "weight_kg": 62,
    "training_goal": "muscle_gain",
    "activity_level": "moderate",
}


def make_profile(**changes) -> UserProfileRead:
    return UserProfileRead(**(BASE | changes))


def plan_for(level=FitnessLevel.INTERMEDIATE, exercises=ATLAS, **changes):
    return generate_plan(make_profile(**changes), level, ClassifierName.RULES, exercises)


def plan_exercise_ids(plan) -> list[int]:
    return [exercise.exercise_id for day in plan.days for exercise in day.exercises]


def test_bezpieczenstwo_cwiczenia():
    squat = next(e for e in ATLAS if e.name == "Przysiad ze sztangą")
    assert not is_safe(squat, ["knee"])
    assert is_safe(squat, ["wrist"])
    assert is_safe(squat, [])


@pytest.mark.parametrize("limitation", ["knee", "lower_back", "shoulder", "heart_condition"])
def test_plan_nie_zawiera_przeciwwskazanych_cwiczen(limitation):
    plan = plan_for(FitnessLevel.ADVANCED, limitations=[limitation],
                    available_equipment=["dumbbells", "barbell", "machine"])
    by_id = {e.id: e for e in ATLAS}
    assert plan_exercise_ids(plan)
    assert all(limitation not in by_id[i].contraindications for i in plan_exercise_ids(plan))
    assert plan.excluded_for_safety > 0


def test_wybor_uwzglednia_sprzet_i_poziom():
    pool, _ = select_exercises(ATLAS, make_profile(), FitnessLevel.BEGINNER)
    assert pool
    assert {e.equipment for e in pool} == {"none"}  # brak odpowiedzi o sprzęt = masa ciała
    assert {e.difficulty for e in pool} == {"beginner"}

    pool, _ = select_exercises(ATLAS, make_profile(available_equipment=["barbell"]), FitnessLevel.ADVANCED)
    assert {e.equipment for e in pool} == {"none", "barbell"}
    assert "advanced" in {e.difficulty for e in pool}


def test_liczba_odrzuconych_z_powodu_przeciwwskazan():
    _, excluded_none = select_exercises(ATLAS, make_profile(), FitnessLevel.BEGINNER)
    _, excluded_knee = select_exercises(ATLAS, make_profile(limitations=["knee"]), FitnessLevel.BEGINNER)
    assert excluded_none == 0
    assert excluded_knee > 0


def test_domyslne_preferencje():
    plan = plan_for()
    assert plan.days_per_week == 3
    assert plan.session_minutes == 45
    assert [day.focus for day in plan.days] == ["Całe ciało"] * 3


def test_podzial_gora_dol_przy_4_dniach():
    plan = plan_for(training_days_per_week=4)
    assert [day.focus for day in plan.days] == ["Góra ciała", "Dół ciała"] * 2


def test_liczba_cwiczen_zalezy_od_czasu_treningu():
    assert exercises_per_session(20, 4, 150) == 3  # minimum
    assert exercises_per_session(180, 2, 30) == 8  # maksimum
    short = plan_for(session_minutes=30, available_equipment=["dumbbells", "machine"])
    long = plan_for(session_minutes=90, available_equipment=["dumbbells", "machine"])
    assert len(short.days[0].exercises) < len(long.days[0].exercises)


def test_brak_powtorzen_w_dniu_i_rotacja_miedzy_dniami():
    plan = plan_for(available_equipment=["dumbbells", "machine", "resistance_band"])
    for day in plan.days:
        ids = [e.exercise_id for e in day.exercises]
        assert len(ids) == len(set(ids))
    first, second = ([e.exercise_id for e in day.exercises] for day in plan.days[:2])
    assert first != second


def test_parametry_treningu_wedlug_celu_i_poziomu():
    strength = plan_for(training_goal="strength").days[0].exercises[0]
    assert (strength.sets, strength.reps, strength.rest_seconds) == (4, "4–6", 150)
    beginner = plan_for(FitnessLevel.BEGINNER, training_goal="strength").days[0].exercises[0]
    assert beginner.sets == 3  # początkujący: jedna seria mniej


def test_plan_jest_powtarzalny():
    assert plan_for(limitations=["knee"]) == plan_for(limitations=["knee"])


def test_ostrzezenia_i_rekomendacje():
    plan = plan_for(limitations=["heart_condition"])
    assert any("lekarzem" in warning for warning in plan.warnings)
    assert any("ból" in tip for tip in plan.progression)
    assert any("testy sprawności" in tip for tip in plan.progression)


def test_pusty_atlas_daje_ostrzezenie():
    plan = plan_for(exercises=[])
    assert all(day.exercises == [] for day in plan.days)
    assert any("Brak ćwiczeń" in warning for warning in plan.warnings)



def test_wskazowki_redukcyjne_tylko_dla_celu_redukcji():
    weight_loss = plan_for(training_goal="weight_loss")
    assert all(tip in weight_loss.progression for tip in WEIGHT_LOSS_TIPS)
    strength = plan_for(training_goal="strength")
    assert not any(tip in strength.progression for tip in WEIGHT_LOSS_TIPS)


@pytest.mark.parametrize(
    ("limitations", "expected"),
    [([], False), (["knee"], False), (["hypertension"], True), (["heart_condition"], True)],
)
def test_konsultacja_przed_interwalami_przy_chorobach_krazenia(limitations, expected):
    plan = plan_for(training_goal="weight_loss", limitations=limitations)
    assert (INTERVAL_CONSULTATION_TIP in plan.progression) == expected
