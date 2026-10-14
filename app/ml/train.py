"""Uczenie i wstępna ocena klasyfikatorów sprawności na danych syntetycznych.

Uruchomienie: python -m app.ml.train
Wytrenowane modele trafiają do app/ml/artifacts/ i są wczytywane przez API.
"""

import joblib
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from app.ml.data_generator import generate_dataset
from app.ml.models import build_decision_tree, build_mlp
from app.ml.predictor import ARTIFACTS_DIR, model_path
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


def main() -> None:
    classifiers, metrics = train_and_evaluate()
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    for name in ("decision_tree", "mlp"):
        joblib.dump(classifiers[name], model_path(name))

    print(f"{'Klasyfikator':<15}{'Accuracy':>10}{'F1 makro':>10}")
    for name, values in metrics.items():
        print(f"{name:<15}{values['accuracy']:>10.3f}{values['f1_macro']:>10.3f}")
    print(f"Zapisano modele w {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
