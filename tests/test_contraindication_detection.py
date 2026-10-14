"""Testy detektorów przeciwwskazań."""

import pytest

from app.ml.contraindication_detection import (
    HybridDetector,
    RuleBasedDetector,
    TreeDetector,
    exercise_features,
    labels_to_matrix,
)
from app.schemas import ExerciseFeatures
from app.seed import load_atlas


def features(**values) -> ExerciseFeatures:
    base = {"muscle_group": "legs", "equipment": "none", "difficulty": "beginner", "movement_pattern": "squat"}
    return ExerciseFeatures(**(base | values))


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ({}, {"knee"}),
        ({"equipment": "barbell"}, {"knee", "lower_back", "hypertension"}),
        ({"muscle_group": "chest", "movement_pattern": "horizontal_push"}, {"shoulder", "wrist"}),
        ({"muscle_group": "chest", "movement_pattern": "horizontal_push", "equipment": "dumbbells"}, {"shoulder"}),
        ({"muscle_group": "arms", "movement_pattern": "isolation"}, {"elbow"}),
        ({"muscle_group": "full_body", "movement_pattern": "cardio"}, {"heart_condition", "wrist"}),
        ({"muscle_group": "full_body", "movement_pattern": "cardio", "difficulty": "intermediate"},
         {"heart_condition", "wrist", "hypertension"}),
        ({"muscle_group": "core", "movement_pattern": "core_stability"}, set()),
    ],
)
def test_reguly(values, expected):
    assert RuleBasedDetector().predict([features(**values)])[0] == expected


def test_kodowanie_cech():
    table = exercise_features([features(), features(difficulty="advanced")])
    assert table.loc[0, "MovementPattern_squat"] == 1
    assert table.loc[0, "MovementPattern_hinge"] == 0
    assert list(table["difficulty"]) == [0, 2]


def test_macierz_etykiet():
    matrix = labels_to_matrix([["knee"], []])
    assert matrix.shape == (2, 10)
    assert matrix[0].sum() == 1 and matrix[1].sum() == 0


def test_drzewo_uczy_sie_zaleznosci_z_atlasu():
    # Nowe ćwiczenie (przysiad na maszynie, poziom średni) nie występuje w atlasie,
    # ale wszystkie przysiady w atlasie są przeciwwskazane przy kontuzji kolana.
    atlas = load_atlas()
    detector = TreeDetector().fit(atlas, [exercise.contraindications for exercise in atlas])
    new = features(equipment="machine", difficulty="intermediate")
    assert "knee" in detector.predict([new])[0]


def test_hybryda_to_suma_regul_i_drzewa():
    atlas = load_atlas()
    labels = [exercise.contraindications for exercise in atlas]
    new = [features(muscle_group="glutes", movement_pattern="lunge")]
    from_rules = RuleBasedDetector().predict(new)[0]
    from_tree = TreeDetector().fit(atlas, labels).predict(new)[0]
    assert HybridDetector().fit(atlas, labels).predict(new)[0] == from_rules | from_tree
