"""Testy kodu eksperymentów (na małych danych, żeby działały szybko)."""

import numpy as np
import pandas as pd
import pytest

from app.ml.data_generator import generate_dataset, remove_answers
from app.ml.features import OPTIONAL_FEATURES
from app.seed import load_atlas
from experiments.evaluation import (
    TEST_MISSING_RATES,
    compare_classifiers,
    completeness_study,
    contraindication_study,
    summarize,
)
from experiments.plan_quality import jaccard, plan_quality_study, random_preferences
from experiments.run import run_experiments
from experiments.significance import mcnemar_test, significance_study
from experiments.tuning import SEARCH_SPACES, tune_hyperparameters


def test_usuwanie_odpowiedzi():
    X, _ = generate_dataset(300)
    rng = np.random.default_rng(0)
    pd.testing.assert_frame_equal(remove_answers(X, 0.0, rng), X)
    emptied = remove_answers(X, 1.0, rng)
    assert emptied[OPTIONAL_FEATURES].isna().all().all()
    assert not X[OPTIONAL_FEATURES].isna().any().any()  # oryginał bez zmian


def test_porownanie_klasyfikatorow():
    results, matrices = compare_classifiers(seeds=[1], n_samples=600)
    assert list(results["classifier"]) == ["rules", "decision_tree", "mlp"]
    assert results["accuracy"].between(0, 1).all()
    assert (results["latency_ms"] > 0).all()
    # Macierz pomyłek obejmuje wszystkie osoby testowe (25% z 600).
    assert all(matrix.sum() == 150 for matrix in matrices.values())


def test_braki_obnizaja_trafnosc():
    results = completeness_study(seeds=[1], n_samples=1500)
    assert len(results) == 3 * len(TEST_MISSING_RATES)
    mlp = results[results["classifier"] == "mlp"].set_index("test_missing_rate")
    assert mlp.loc[0.0, "accuracy"] > mlp.loc[1.0, "accuracy"]


def test_podsumowanie_liczy_srednia_i_odchylenie():
    results = pd.DataFrame({"classifier": ["a", "a"], "accuracy": [0.8, 0.9]})
    summary = summarize(results, ["classifier"], ["accuracy"])
    assert summary.loc[0, "accuracy_mean"] == pytest.approx(0.85)
    assert summary.loc[0, "accuracy_std"] > 0


def test_uruchomienie_eksperymentow(tmp_path, monkeypatch):
    # MLflow zapisuje do bazy w katalogu tymczasowym, a nie w katalogu projektu.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"sqlite:///{tmp_path / 'mlflow.db'}")
    output = tmp_path / "wyniki"
    run_experiments(output, seeds=[1], n_samples=400)
    expected = {
        "comparison.csv",
        "completeness.csv",
        "confusion_matrices.png",
        "completeness.png",
        "contraindications.csv",
        "contraindications_per_limitation.csv",
        "contraindications.png",
        "plan_quality.csv",
        "plan_quality.png",
        "tuning.csv",
        "significance.csv",
    }
    assert {path.name for path in output.iterdir()} == expected


def test_wykrywanie_przeciwwskazan():
    summary, per_limitation = contraindication_study(load_atlas())
    assert list(summary["detector"]) == ["rules", "decision_tree", "hybrid"]
    assert summary[["precision", "recall", "f1"]].stack().between(0, 1).all()
    assert len(per_limitation) == 3 * 10
    # Hybryda to suma wyników, więc nie może przeoczyć więcej niż reguły czy drzewo.
    missed = summary.set_index("detector")["missed"]
    assert missed["hybrid"] <= min(missed["rules"], missed["decision_tree"])


def test_podobienstwo_jaccarda():
    assert jaccard({1, 2}, {1, 2}) == 1.0
    assert jaccard({1, 2}, {3}) == 0.0
    assert jaccard({1, 2, 3}, {2, 3, 4}) == pytest.approx(0.5)


def test_losowe_preferencje_zawsze_maja_cwiczenia_bez_sprzetu():
    rng = np.random.default_rng(0)
    for _ in range(20):
        preferences = random_preferences(rng)
        assert "none" in preferences["available_equipment"]
        assert 2 <= preferences["training_days_per_week"] <= 5


def test_jakosc_planu():
    results = plan_quality_study(seeds=[1], n_samples=800, atlas=load_atlas())
    assert len(results) == 3 * len(TEST_MISSING_RATES)
    # Filtr bezpieczeństwa działa niezależnie od trafności klasyfikacji.
    assert (results["unsafe_exercises"] == 0).all()
    # Każda osoba dostaje plan dla swojego poziomu, za trudny albo za łatwy.
    total = results["level_match"] + results["too_hard"] + results["too_easy"]
    assert np.allclose(total, 1.0)
    assert results["exercise_overlap"].between(0, 1).all()


def test_dobor_hiperparametrow():
    results = tune_hyperparameters(n_samples=600)
    for name, (_, grid) in SEARCH_SPACES.items():
        rows = results[results["classifier"] == name]
        combinations = 1
        for values in grid.values():
            combinations *= len(values)
        assert len(rows) == combinations
        # Dokładnie jedna kombinacja odpowiada parametrom używanym w aplikacji.
        assert rows["is_current"].sum() == 1
        # Najlepszy wynik (rank 1) zawsze mieści się w granicy jednego odchylenia.
        assert rows.iloc[0]["rank"] == 1 and rows.iloc[0]["within_one_se"]


def test_mcnemar_liczy_rozbiezne_odpowiedzi():
    y = ["a", "a", "a", "a"]
    result = mcnemar_test(y, ["a", "a", "b", "b"], ["a", "b", "b", "a"])
    # Osoba 2: dobrze tylko A, osoba 4: dobrze tylko B, osoby 1 i 3 bez różnicy.
    assert result["only_a_correct"] == 1
    assert result["only_b_correct"] == 1
    assert result["p_value"] == pytest.approx(1.0)


def test_mcnemar_wykrywa_wyrazna_przewage():
    y = ["a"] * 30
    better = ["a"] * 30
    worse = ["b"] * 20 + ["a"] * 10
    assert mcnemar_test(y, better, worse)["p_value"] < 0.001
    assert mcnemar_test(y, better, better)["p_value"] == 1.0


def test_istotnosc_roznic():
    results = significance_study(seeds=[1], n_samples=600)
    # 3 pary klasyfikatorów dla każdego odsetka braków.
    assert len(results) == 3 * len(TEST_MISSING_RATES)
    assert results["p_value"].between(0, 1).all()
