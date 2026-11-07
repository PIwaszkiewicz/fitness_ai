"""Klasyfikacja poziomu sprawności profilu wybranym klasyfikatorem.

Wytrenowane modele są wczytywane z dysku przy pierwszym użyciu i zapamiętywane
(lru_cache), więc kolejne żądania nie czytają pliku ponownie.
Aplikacja używa jednego klasyfikatora: tego, który wypadł najlepiej w ocenie
podczas uczenia (app/ml/train.py zapisuje jego nazwę w best_classifier.json).
"""

import json
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

import joblib

from app.ml.features import profile_to_features
from app.ml.rule_based import RuleBasedClassifier

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


class ClassifierName(StrEnum):
    """Dostępne klasyfikatory sprawności."""

    RULES = "rules"
    DECISION_TREE = "decision_tree"
    MLP = "mlp"


def model_path(name: str) -> Path:
    """Ścieżka pliku z wytrenowanym modelem."""
    return ARTIFACTS_DIR / f"{name}.joblib"


def best_classifier_path() -> Path:
    """Ścieżka pliku z nazwą i metrykami najlepszego klasyfikatora."""
    return ARTIFACTS_DIR / "best_classifier.json"


def best_classifier() -> ClassifierName:
    """Klasyfikator wybrany w ocenie jako najdokładniejszy.

    Gdy modele nie zostały jeszcze wytrenowane (brak pliku), używany jest
    system regułowy, bo działa bez uczenia.
    """
    path = best_classifier_path()
    if not path.exists():
        return ClassifierName.RULES
    return ClassifierName(json.loads(path.read_text())["name"])


@lru_cache
def load_classifier(name: ClassifierName):
    """Zwraca klasyfikator. Brak pliku modelu zgłasza FileNotFoundError."""
    if name == ClassifierName.RULES:
        return RuleBasedClassifier()
    path = model_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Brak wytrenowanego modelu: {path}")
    return joblib.load(path)


def classify(profile, name: ClassifierName) -> dict:
    """Zwraca poziom sprawności i, dla modeli ML, prawdopodobieństwa poziomów."""
    classifier = load_classifier(name)
    features = profile_to_features(profile)
    probabilities = None
    if hasattr(classifier, "predict_proba"):
        values = classifier.predict_proba(features)[0]
        probabilities = {
            level: round(float(value), 3) for level, value in zip(classifier.classes_, values)
        }
    return {"level": classifier.predict(features)[0], "probabilities": probabilities}
