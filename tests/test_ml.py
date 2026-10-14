"""Testy modułu ML: generator danych, cechy, system regułowy i modele."""

import numpy as np
import pandas as pd
import pytest

from app.ml.data_generator import generate_dataset
from app.ml.features import FEATURES, OPTIONAL_FEATURES, profile_to_features
from app.ml.models import build_decision_tree, build_mlp
from app.ml.rule_based import RuleBasedClassifier
from app.ml.train import train_and_evaluate
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
    required = [column for column in FEATURES if column not in OPTIONAL_FEATURES]
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
