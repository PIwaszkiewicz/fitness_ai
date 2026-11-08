"""Testy modułu ML: generator danych, cechy, system regułowy i modele."""

import numpy as np
import pandas as pd
import pytest

from app.ml.data_generator import generate_dataset, remove_n_answers
from app.ml.features import (
    CONDITIONAL_FEATURES,
    FEATURES,
    KNEE_PUSHUP_FACTOR,
    OPTIONAL_FEATURES,
    profile_to_features,
)
from app.ml.models import build_decision_tree, build_mlp
from app.ml.rule_based import RuleBasedClassifier
from app.ml.train import average_runs, select_best, train_and_evaluate
from app.schemas import UserProfileCreate

LEVELS = {"beginner", "intermediate", "advanced"}


def test_generator_jest_powtarzalny():
    X1, y1 = generate_dataset(200, seed=7)
    X2, y2 = generate_dataset(200, seed=7)
    pd.testing.assert_frame_equal(X1, X2)
    assert list(X1.columns) == FEATURES
    assert (y1 == y2).all()


def test_generator_daje_zrownowazone_poziomy():
    _, y = generate_dataset(3000)
    shares = y.value_counts(normalize=True)
    assert set(shares.index) == LEVELS
    assert shares.min() > 0.25


def test_generator_miesci_sie_w_zakresach_kwestionariusza():
    X, _ = generate_dataset(3000)
    assert X["age"].between(16, 100).all()
    assert X["pushups"].between(0, 150).all()
    assert X["squats"].between(0, 150).all()
    assert X["plank_seconds"].between(0, 600).all()
    assert X["resting_heart_rate"].between(30, 150).all()


def test_generator_usuwa_tylko_odpowiedzi_opcjonalne():
    X, _ = generate_dataset(4000, missing_rate=0.3)
    for column in OPTIONAL_FEATURES:
        assert 0.25 < X[column].isna().mean() < 0.35
    required = [c for c in FEATURES if c not in OPTIONAL_FEATURES + CONDITIONAL_FEATURES]
    assert not X[required].isna().any().any()


def test_cechy_z_profilu():
    profile = UserProfileCreate(
        age=30, gender="female", height_cm=170, weight_kg=65,
        training_goal="strength", activity_level="moderate", pushups=12,
    )
    row = profile_to_features(profile).iloc[0]
    assert row["is_male"] == 0
    assert row["bmi"] == pytest.approx(65 / 1.7**2)
    assert row["activity_level"] == 2  # sedentary=0, light=1, moderate=2
    assert row["pushups"] == 12
    assert np.isnan(row["training_experience"])
    assert np.isnan(row["plank_seconds"])


def make_row(**values) -> pd.DataFrame:
    """Tworzy jednowierszową tabelę cech; niepodane testy są brakujące."""
    base = dict.fromkeys(FEATURES, np.nan) | {"age": 30, "is_male": 1, "bmi": 23}
    return pd.DataFrame([base | values], columns=FEATURES).astype(float)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ({"activity_level": 4, "training_experience": 3, "pushups": 40, "squats": 50,
          "plank_seconds": 180, "resting_heart_rate": 55}, "advanced"),
        ({"activity_level": 2, "training_experience": 2, "pushups": 20, "squats": 30,
          "plank_seconds": 90, "resting_heart_rate": 72}, "intermediate"),
        ({"activity_level": 0, "training_experience": 0, "pushups": 5, "squats": 15,
          "plank_seconds": 20, "resting_heart_rate": 90}, "beginner"),
        # Bez testów decydują tylko aktywność i staż.
        ({"activity_level": 4}, "advanced"),
        ({"activity_level": 0}, "beginner"),
    ],
)
def test_system_regulowy(values, expected):
    assert RuleBasedClassifier().predict(make_row(**values))[0] == expected


def test_system_regulowy_uwzglednia_sile():
    rules = RuleBasedClassifier()
    # Aktywność 2 daje 1 punkt. Wskaźnik siły powyżej normy dodaje 2 (średnia 1,5: zaawansowany),
    # poniżej 0,7 dodaje 0 (średnia 0,5: początkujący).
    assert rules.predict(make_row(activity_level=2, strength_index=1.2))[0] == "advanced"
    assert rules.predict(make_row(activity_level=2, strength_index=0.5))[0] == "beginner"


def test_system_regulowy_uwzglednia_wiek_przy_pompkach():
    # 12 pompek u 30-latka to poniżej progu (15), a u 60-latka już powyżej (15 * 0.7 = 10.5).
    young = make_row(activity_level=2, pushups=12)
    senior = make_row(activity_level=2, pushups=12, age=60)
    rules = RuleBasedClassifier()
    assert rules.predict(young)[0] == "beginner"
    assert rules.predict(senior)[0] == "intermediate"


@pytest.mark.parametrize("build", [build_decision_tree, build_mlp])
def test_modele_ml_radza_sobie_z_brakami(build):
    X, y = generate_dataset(1000, missing_rate=0.2)
    model = build().fit(X, y)
    predicted = model.predict(make_row(activity_level=2))  # prawie wszystko brakujące
    assert predicted[0] in LEVELS


def test_modele_ml_sa_lepsze_od_losowania():
    _, metrics = train_and_evaluate(n_samples=1500)
    for values in metrics.values():
        # Losowe zgadywanie przy trzech poziomach daje ok. 33%.
        assert values["accuracy"] > 0.6


def test_najlepszy_klasyfikator_ma_najwyzsze_f1_makro():
    metrics = {
        "rules": {"accuracy": 0.90, "f1_macro": 0.70},
        "decision_tree": {"accuracy": 0.80, "f1_macro": 0.80},
        "mlp": {"accuracy": 0.85, "f1_macro": 0.80},  # remis F1, wyższe accuracy
    }
    assert select_best(metrics) == "mlp"


def test_usuwanie_dokladnie_n_odpowiedzi():
    X, _ = generate_dataset(50)
    X_missing = remove_n_answers(X, 2, np.random.default_rng(0))
    assert (X_missing[OPTIONAL_FEATURES].isna().sum(axis=1) == 2).all()
    basic = X_missing.drop(columns=OPTIONAL_FEATURES + CONDITIONAL_FEATURES)
    assert basic.notna().all().all()  # dane podstawowe zostają


def test_usrednianie_powtorzen():
    runs = [{0: {"mlp": {"f1_macro": 0.8}}}, {0: {"mlp": {"f1_macro": 0.6}}}]
    averaged = average_runs(runs)[0]["mlp"]
    assert averaged["f1_macro"] == pytest.approx(0.7)
    assert averaged["f1_macro_std"] == pytest.approx(0.1)


def test_wskaznik_sily_maja_glownie_osoby_ze_stazem():
    X, _ = generate_dataset(4000)
    lifters = X["strength_index"].notna().groupby(X["training_experience"]).mean()
    assert lifters[0] < 0.1 < lifters[1] < lifters[2] < lifters[3]


def test_dodanie_wskaznika_sily_nie_zmienia_pozostalych_danych():
    # Wskaźnik siły ma osobny generator losowy, więc pozostałe cechy i braki są takie jak wcześniej.
    X, _ = generate_dataset(300, missing_rate=0.2, seed=3)
    assert X["pushups"].isna().sum() == 57  # wartość sprzed dodania wskaźnika siły


def test_pompki_z_kolan_przeliczane_na_klasyczne():
    answers = {"age": 30, "gender": "female", "height_cm": 170, "weight_kg": 65,
               "training_goal": "strength", "activity_level": "moderate", "pushups": 20}
    knees = profile_to_features(UserProfileCreate(**answers, pushup_variant="knees")).iloc[0]
    classic = profile_to_features(UserProfileCreate(**answers, pushup_variant="classic")).iloc[0]
    assert classic["pushups"] == 20
    assert knees["pushups"] == pytest.approx(20 * KNEE_PUSHUP_FACTOR)


def test_wskaznik_sily_z_profilu():
    # Mężczyzna 80 kg, przysiad 100 kg × 1 = 1,25 × masa ciała, czyli dokładnie norma.
    profile = UserProfileCreate(
        age=30, gender="male", height_cm=180, weight_kg=80, training_goal="strength",
        activity_level="active", lifts_weights=True, squat_kg=100, squat_reps=1,
    )
    assert profile_to_features(profile).iloc[0]["strength_index"] == pytest.approx(1.0)
