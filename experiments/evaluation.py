"""Eksperymenty porównujące klasyfikatory. Funkcje zwracają tabele wyników (pandas),
a zapis do MLflow i wykresy obsługuje experiments/run.py.
"""

from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

from app.ml.contraindication_detection import (
    LIMITATIONS,
    HybridDetector,
    RuleBasedDetector,
    TreeDetector,
    labels_to_matrix,
)
from app.ml.data_generator import generate_dataset, remove_answers
from app.ml.models import build_decision_tree, build_mlp
from app.ml.rule_based import RuleBasedClassifier
from app.ml.train import TEST_SIZE, TRAIN_MISSING_RATE

# Funkcje tworzące klasyfikatory (argument: seed). Reguły nie mają losowości.
CLASSIFIERS = {
    "rules": lambda seed: RuleBasedClassifier(),
    "decision_tree": build_decision_tree,
    "mlp": build_mlp,
}
LEVELS = ["beginner", "intermediate", "advanced"]
# Odsetki pominiętych odpowiedzi opcjonalnych badane w eksperymencie kompletności.
TEST_MISSING_RATES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def split_data(n_samples: int, seed: int):
    """Generuje pełne dane i dzieli je na część uczącą i testową (z zachowaniem proporcji poziomów)."""
    X, y = generate_dataset(n_samples, missing_rate=0.0, seed=seed)
    return train_test_split(X, y, test_size=TEST_SIZE, stratify=y, random_state=seed)


def measure_latency_ms(classifier, X: pd.DataFrame, repeats: int = 100) -> float:
    """Średni czas klasyfikacji jednej osoby w milisekundach (tak jak w pojedynczym żądaniu API)."""
    rows = [X.iloc[[i % len(X)]] for i in range(repeats)]
    start = perf_counter()
    for row in rows:
        classifier.predict(row)
    return (perf_counter() - start) / repeats * 1000


def compare_classifiers(seeds: list[int], n_samples: int) -> tuple[pd.DataFrame, dict]:
    """Eksperyment 1: porównanie klasyfikatorów przy typowej kompletności danych.

    Dla każdego ziarna losowania: nowe dane, uczenie i ocena każdego klasyfikatora.
    Zwraca tabelę wyników (wiersz = klasyfikator i ziarno) oraz macierze pomyłek
    zsumowane po wszystkich ziarnach.
    """
    rows = []
    matrices = {name: np.zeros((len(LEVELS), len(LEVELS)), dtype=int) for name in CLASSIFIERS}
    for seed in seeds:
        rng = np.random.default_rng(seed)
        X_train, X_test, y_train, y_test = split_data(n_samples, seed)
        X_train = remove_answers(X_train, TRAIN_MISSING_RATE, rng)
        X_test = remove_answers(X_test, TRAIN_MISSING_RATE, rng)

        for name, build in CLASSIFIERS.items():
            classifier = build(seed)
            start = perf_counter()
            classifier.fit(X_train, y_train)
            train_seconds = perf_counter() - start
            predicted = classifier.predict(X_test)

            rows.append({
                "classifier": name,
                "seed": seed,
                "accuracy": accuracy_score(y_test, predicted),
                "f1_macro": f1_score(y_test, predicted, average="macro"),
                "train_seconds": train_seconds,
                "latency_ms": measure_latency_ms(classifier, X_test),
            })
            matrices[name] += confusion_matrix(y_test, predicted, labels=LEVELS)
    return pd.DataFrame(rows), matrices


def completeness_study(seeds: list[int], n_samples: int) -> pd.DataFrame:
    """Eksperyment 2: jak trafność zależy od kompletności danych wejściowych.

    Klasyfikatory uczą się na danych z typowym odsetkiem braków, a potem są oceniane
    na tych samych osobach testowych z coraz większą częścią pominiętych odpowiedzi
    (od 0% do 100%, gdzie zostają tylko dane podstawowe: wiek, płeć, BMI, aktywność).
    """
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        X_train, X_test, y_train, y_test = split_data(n_samples, seed)
        X_train = remove_answers(X_train, TRAIN_MISSING_RATE, rng)
        classifiers = {name: build(seed).fit(X_train, y_train) for name, build in CLASSIFIERS.items()}

        for missing_rate in TEST_MISSING_RATES:
            X_incomplete = remove_answers(X_test, missing_rate, rng)
            for name, classifier in classifiers.items():
                predicted = classifier.predict(X_incomplete)
                rows.append({
                    "classifier": name,
                    "seed": seed,
                    "test_missing_rate": missing_rate,
                    "accuracy": accuracy_score(y_test, predicted),
                    "f1_macro": f1_score(y_test, predicted, average="macro"),
                })
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame, group_by: list[str], metrics: list[str]) -> pd.DataFrame:
    """Średnia i odchylenie standardowe metryk po wszystkich ziarnach losowania."""
    summary = results.groupby(group_by, sort=False)[metrics].agg(["mean", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    return summary.reset_index()


DETECTORS = {"rules": RuleBasedDetector, "decision_tree": TreeDetector, "hybrid": HybridDetector}


def leave_one_out_predictions(detector_class, exercises: list, labels: list) -> list[set]:
    """Walidacja krzyżowa „leave-one-out”: każde ćwiczenie po kolei jest traktowane jak nowe.

    Detektor uczy się na wszystkich pozostałych ćwiczeniach i przewiduje przeciwwskazania
    pominiętego. Przy małym atlasie pozwala to wykorzystać do oceny każde ćwiczenie.
    """
    predictions = []
    for i in range(len(exercises)):
        train = exercises[:i] + exercises[i + 1:]
        train_labels = labels[:i] + labels[i + 1:]
        detector = detector_class().fit(train, train_labels)
        predictions.append(detector.predict([exercises[i]])[0])
    return predictions


def contraindication_study(exercises: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Eksperyment 3: trafność wykrywania przeciwwskazań dla nowych ćwiczeń.

    Wzorcem są ręczne etykiety z atlasu. Każda para (ćwiczenie, ograniczenie) to jedna
    decyzja: przeciwwskazane albo nie. Zwraca podsumowanie dla detektorów
    oraz wyniki dla każdego ograniczenia osobno.
    """
    labels = [exercise.contraindications for exercise in exercises]
    true = labels_to_matrix(labels)
    summary, per_limitation = [], []
    for name, detector_class in DETECTORS.items():
        predicted = labels_to_matrix(leave_one_out_predictions(detector_class, exercises, labels))
        precision, recall, f1, _ = precision_recall_fscore_support(
            true, predicted, average="micro", zero_division=0
        )
        summary.append({
            "detector": name,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            # Przeoczone przeciwwskazania są groźne (ryzyko kontuzji),
            # fałszywe alarmy tylko niepotrzebnie zawężają wybór ćwiczeń.
            "missed": int(((true == 1) & (predicted == 0)).sum()),
            "false_alarms": int(((true == 0) & (predicted == 1)).sum()),
            "exact_match": float((true == predicted).all(axis=1).mean()),
        })
        values = precision_recall_fscore_support(true, predicted, average=None, zero_division=0)
        for limitation, (p, r, f, support) in zip(LIMITATIONS, zip(*values)):
            per_limitation.append({
                "detector": name,
                "limitation": limitation.value,
                "precision": p,
                "recall": r,
                "f1": f,
                "support": int(support),  # liczba ćwiczeń z tym przeciwwskazaniem w atlasie
            })
    return pd.DataFrame(summary), pd.DataFrame(per_limitation)
