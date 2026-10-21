"""Dobór hiperparametrów modeli ML przeszukiwaniem siatki z walidacją krzyżową.

Dla każdej kombinacji parametrów z siatki model jest uczony 5 razy, za każdym razem
na 4/5 danych uczących, i oceniany na pozostałej 1/5 (5-krotna walidacja krzyżowa).
Dane testowe nie biorą udziału w doborze, więc nie zawyżają późniejszej oceny.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from app.ml.data_generator import remove_answers
from app.ml.models import build_decision_tree, build_mlp
from app.ml.train import SEED, TRAIN_MISSING_RATE
from experiments.evaluation import split_data

# Siatki parametrów. Przedrostek "model__" wskazuje krok potoku, którego dotyczy parametr.
SEARCH_SPACES = {
    "decision_tree": (
        build_decision_tree,
        {
            "model__max_depth": [3, 4, 6, 8, 10, None],  # None: drzewo bez ograniczenia głębokości
            "model__min_samples_leaf": [1, 5, 20, 50],
        },
    ),
    "mlp": (
        build_mlp,
        {
            "model__hidden_layer_sizes": [(16,), (32,), (32, 16), (64, 32)],
            "model__alpha": [0.0001, 0.001, 0.01],  # siła regularyzacji L2
        },
    ),
}
CV_FOLDS = 5


def tune_hyperparameters(n_samples: int, seed: int = SEED) -> pd.DataFrame:
    """Zwraca wyniki walidacji krzyżowej (F1 makro) dla wszystkich kombinacji parametrów.

    Kolumna is_current wskazuje kombinację używaną w aplikacji (app/ml/models.py).
    Kolumna within_one_se oznacza wyniki gorsze od najlepszego o mniej niż jego odchylenie
    standardowe (reguła jednego odchylenia: spośród nich wybiera się model najprostszy,
    bo różnica względem najlepszego mieści się w losowej zmienności wyniku).
    """
    rng = np.random.default_rng(seed)
    X_train, _, y_train, _ = split_data(n_samples, seed)
    X_train = remove_answers(X_train, TRAIN_MISSING_RATE, rng)
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)

    tables = []
    for name, (build, grid) in SEARCH_SPACES.items():
        current = build(seed).get_params()
        search = GridSearchCV(build(seed), grid, scoring="f1_macro", cv=folds, n_jobs=-1)
        search.fit(X_train, y_train)
        results = search.cv_results_
        for params, mean, std, rank in zip(
            results["params"],
            results["mean_test_score"],
            results["std_test_score"],
            results["rank_test_score"],
        ):
            tables.append({
                "classifier": name,
                "params": ", ".join(f"{key.removeprefix('model__')}={value}" for key, value in params.items()),
                "f1_macro_mean": mean,
                "f1_macro_std": std,
                "rank": int(rank),
                "is_current": all(current[key] == value for key, value in params.items()),
            })
    table = pd.DataFrame(tables).sort_values(["classifier", "rank"], ignore_index=True)
    best = table.groupby("classifier")[["f1_macro_mean", "f1_macro_std"]].transform("first")
    table["within_one_se"] = table["f1_macro_mean"] >= best["f1_macro_mean"] - best["f1_macro_std"]
    return table
