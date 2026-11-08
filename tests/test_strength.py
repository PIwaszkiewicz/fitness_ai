"""Testy szacowania ciężaru maksymalnego (1RM) z serii roboczej."""

from types import SimpleNamespace

import pytest

from app.services.strength import (
    LIFTS,
    epley_one_rep_max,
    estimate_one_rep_maxes,
    starting_load,
)


def profile(**lifts):
    """Profil z masą ciała 80 kg i podanymi seriami (pozostałe ćwiczenia puste)."""
    fields = {f"{lift.name}_{part}": None for lift in LIFTS for part in ("kg", "reps")}
    return SimpleNamespace(weight_kg=80, **(fields | lifts))


def test_wzor_epleya():
    assert epley_one_rep_max(100, 1) == 100  # jedno powtórzenie to już ciężar maksymalny
    assert epley_one_rep_max(100, 5) == pytest.approx(116.67, abs=0.01)
    assert epley_one_rep_max(60, 10) == pytest.approx(80)


def test_1rm_tylko_dla_podanych_cwiczen():
    result = estimate_one_rep_maxes(profile(squat_kg=100, squat_reps=5))
    assert result == {"squat": 116.7}


def test_podciaganie_uwzglednia_mase_ciala():
    # 80 kg masy ciała + 10 kg obciążenia, 3 powtórzenia: 90 · 1,1 = 99 kg.
    assert estimate_one_rep_maxes(profile(pull_up_kg=10, pull_up_reps=3)) == {"pull_up": 99.0}
    # Podciąganie bez obciążenia: liczy się sama masa ciała.
    assert estimate_one_rep_maxes(profile(pull_up_kg=0, pull_up_reps=1)) == {"pull_up": 80.0}


def test_ciezar_startowy_zostawia_powtorzenia_w_zapasie():
    # 1RM 116,7 kg, seria 12 powtórzeń + 2 w zapasie: 116,7 / (1 + 14/30) ≈ 79,6 → 77,5 kg.
    assert starting_load(116.7, 12) == "77,5 kg"
    assert starting_load(116.7, 6) == "90 kg"


def test_ciezar_startowy_przy_podciaganiu():
    # 1RM 120 kg przy masie ciała 80 kg, 5 powtórzeń + 2: 120 / 1,233 ≈ 97,3 → +15 kg obciążenia.
    assert starting_load(120, 5, body_weight=80) == "+15 kg"
    assert starting_load(99, 6, body_weight=80) == "masa ciała"
    # Za słaby na 12 podciągnięć z masą ciała: potrzebna asysta.
    assert starting_load(88, 12, body_weight=80) == "masa ciała, z asystą gumy"
