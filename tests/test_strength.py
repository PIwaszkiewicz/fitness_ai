"""Testy szacowania ciężaru maksymalnego (1RM) z serii roboczej."""

from types import SimpleNamespace

import pytest

from app.services.strength import LIFTS, epley_one_rep_max, estimate_one_rep_maxes


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
