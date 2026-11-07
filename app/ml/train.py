"""Uczenie i wstępna ocena klasyfikatorów sprawności na danych syntetycznych.

Uruchomienie: python -m app.ml.train
Wytrenowane modele trafiają do app/ml/artifacts/ i są wczytywane przez API.
Klasyfikatory są też oceniane osobno dla każdej liczby pustych odpowiedzi opcjonalnych
(0–5). Dla każdej z nich zapisywany jest najlepszy klasyfikator (best_classifier.json)
i to on wyznacza poziom sprawności użytkownika z taką liczbą braków.
"""

import json

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from app.ml.data_generator import generate_dataset, remove_n_answers
from app.ml.features import OPTIONAL_FEATURES
from app.ml.models import build_decision_tree, build_mlp
from app.ml.predictor import ARTIFACTS_DIR, best_classifier_path, model_path
from app.ml.rule_based import RuleBasedClassifier

SEED = 42
N_SAMPLES = 5000
# Część odpowiedzi opcjonalnych jest pomijana, bo tak będzie u prawdziwych użytkowników.
TRAIN_MISSING_RATE = 0.2
TEST_SIZE = 0.25


def train_and_evaluate(
    n_samples: int = N_SAMPLES, missing_rate: float = TRAIN_MISSING_RATE, seed: int = SEED
) -> tuple[dict, dict]:
    """Uczy wszystkie klasyfikatory i zwraca (modele, metryki na zbiorze testowym)."""
    X, y = generate_dataset(n_samples, missing_rate, seed)
    # stratify=y: proporcje poziomów są takie same w zbiorze uczącym i testowym.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=seed
    )
    classifiers = {
        "rules": RuleBasedClassifier(),
        "decision_tree": build_decision_tree(seed),
        "mlp": build_mlp(seed),
    }
    metrics = {}
    for name, classifier in classifiers.items():
        classifier.fit(X_train, y_train)
        predicted = classifier.predict(X_test)
        metrics[name] = {
            "accuracy": accuracy_score(y_test, predicted),
            # F1 makro: średnia F1 dla poziomów, każdy poziom liczy się tak samo.
            "f1_macro": f1_score(y_test, predicted, average="macro"),
        }
    return classifiers, metrics


def evaluate_by_missing_answers(
    classifiers: dict, n_samples: int = N_SAMPLES, seed: int = SEED
) -> dict[int, dict]:
    """Ocenia klasyfikatory na zbiorze testowym przy 0, 1, …, 5 pustych odpowiedziach na osobę.

    Zbiór testowy to te same osoby co w train_and_evaluate (ten sam seed i podział),
    ale z kompletnymi odpowiedziami, z których usuwana jest dokładnie zadana liczba.
    """
    X, y = generate_dataset(n_samples, missing_rate=0.0, seed=seed)
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=seed
    )
    rng = np.random.default_rng(seed)
    results = {}
    for n_missing in range(len(OPTIONAL_FEATURES) + 1):
        X_missing = remove_n_answers(X_test, n_missing, rng)
        results[n_missing] = {}
        for name, classifier in classifiers.items():
            predicted = classifier.predict(X_missing)
            results[n_missing][name] = {
                "accuracy": accuracy_score(y_test, predicted),
                "f1_macro": f1_score(y_test, predicted, average="macro"),
            }
    return results


def select_best(metrics: dict) -> str:
    """Zwraca nazwę klasyfikatora z najwyższym F1 makro (przy remisie decyduje accuracy).

    F1 makro jest kryterium głównym, bo każdy poziom sprawności liczy się w nim tak samo.
    """
    return max(metrics, key=lambda name: (metrics[name]["f1_macro"], metrics[name]["accuracy"]))


def main() -> None:
    classifiers, metrics = train_and_evaluate()
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    for name in ("decision_tree", "mlp"):
        joblib.dump(classifiers[name], model_path(name))
    by_missing = evaluate_by_missing_answers(classifiers)
    best = {n_missing: select_best(results) for n_missing, results in by_missing.items()}
    best_classifier_path().write_text(json.dumps({
        "best_by_missing_answers": best,
        "metrics": metrics,
        "metrics_by_missing_answers": by_missing,
    }, indent=2))

    print(f"{'Klasyfikator':<15}{'Accuracy':>10}{'F1 makro':>10}")
    for name, values in metrics.items():
        print(f"{name:<15}{values['accuracy']:>10.3f}{values['f1_macro']:>10.3f}")
    print(f"\nF1 makro przy danej liczbie pustych odpowiedzi (z {len(OPTIONAL_FEATURES)}):")
    print(f"{'Puste':<7}" + "".join(f"{name:>15}" for name in classifiers) + f"{'Najlepszy':>15}")
    for n_missing, results in by_missing.items():
        scores = "".join(f"{results[name]['f1_macro']:>15.3f}" for name in classifiers)
        print(f"{n_missing:<7}{scores}{best[n_missing]:>15}")
    print(f"Zapisano modele w {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
