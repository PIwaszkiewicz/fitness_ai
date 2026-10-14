"""Uruchomienie wszystkich eksperymentów, zapis wyników do MLflow, tabel CSV i wykresów.

Uruchomienie:  python -m experiments.run
Podgląd w MLflow:  mlflow ui  (adres http://127.0.0.1:5000)
Wyniki dla pracy trafiają do docs/experiments/.
"""

from pathlib import Path

import mlflow
import pandas as pd
from matplotlib.figure import Figure
from sklearn.metrics import ConfusionMatrixDisplay

from experiments.evaluation import compare_classifiers, completeness_study, summarize

SEEDS = [1, 2, 3, 4, 5]
N_SAMPLES = 5000
OUTPUT_DIR = Path("docs/experiments")

# Polskie nazwy do wykresów.
CLASSIFIER_NAMES = {
    "rules": "System regułowy",
    "decision_tree": "Drzewo decyzyjne",
    "mlp": "Sieć neuronowa (MLP)",
}
LEVEL_NAMES = ["początkujący", "średni", "zaawansowany"]


def plot_confusion_matrices(matrices: dict, path: Path) -> None:
    """Rysuje znormalizowane macierze pomyłek: w wierszu prawdziwy poziom, w kolumnie przewidziany.

    Normalizacja po wierszach pokazuje, jaka część osób z danego poziomu trafiła do każdej klasy.
    """
    figure = Figure(figsize=(15, 4.5))
    axes = figure.subplots(1, len(matrices))
    for ax, (name, matrix) in zip(axes, matrices.items()):
        normalized = matrix / matrix.sum(axis=1, keepdims=True)
        display = ConfusionMatrixDisplay(normalized, display_labels=LEVEL_NAMES)
        display.plot(ax=ax, colorbar=False, values_format=".2f", cmap="Blues")
        ax.set_title(CLASSIFIER_NAMES[name])
        ax.set_xlabel("Przewidziany poziom")
        ax.set_ylabel("Prawdziwy poziom")
    figure.tight_layout()
    figure.savefig(path, dpi=120)


def plot_completeness(summary: pd.DataFrame, path: Path) -> None:
    """Rysuje accuracy w zależności od odsetka pominiętych odpowiedzi opcjonalnych."""
    figure = Figure(figsize=(7, 4.5))
    ax = figure.subplots()
    for name, group in summary.groupby("classifier", sort=False):
        ax.errorbar(
            group["test_missing_rate"] * 100,
            group["accuracy_mean"],
            yerr=group["accuracy_std"],
            marker="o",
            capsize=3,
            label=CLASSIFIER_NAMES[name],
        )
    ax.set_xlabel("Pominięte odpowiedzi opcjonalne [%]")
    ax.set_ylabel("Accuracy")
    ax.set_title("Wpływ kompletności danych na trafność klasyfikacji")
    ax.grid(alpha=0.3)
    ax.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=120)


def log_runs(experiment: str, results: pd.DataFrame, params: list[str], metrics: list[str]) -> None:
    """Zapisuje każdy wiersz wyników jako osobny przebieg (run) w MLflow."""
    mlflow.set_experiment(experiment)
    for _, row in results.iterrows():
        run_name = "-".join(str(row[column]) for column in params)
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params({column: row[column] for column in params})
            mlflow.log_metrics({column: float(row[column]) for column in metrics})


def run_experiments(output_dir: Path, seeds: list[int], n_samples: int) -> None:
    """Wykonuje oba eksperymenty, zapisuje tabele, wykresy i przebiegi w MLflow."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Eksperyment 1: porównanie klasyfikatorów
    metrics = ["accuracy", "f1_macro", "train_seconds", "latency_ms"]
    comparison, matrices = compare_classifiers(seeds, n_samples)
    comparison_summary = summarize(comparison, ["classifier"], metrics)
    comparison_summary.round(4).to_csv(output_dir / "comparison.csv", index=False)
    plot_confusion_matrices(matrices, output_dir / "confusion_matrices.png")
    log_runs("porownanie-klasyfikatorow", comparison, ["classifier", "seed"], metrics)
    with mlflow.start_run(run_name="macierze-pomylek"):
        mlflow.log_artifact(str(output_dir / "confusion_matrices.png"))

    # Eksperyment 2: wpływ kompletności danych
    metrics = ["accuracy", "f1_macro"]
    completeness = completeness_study(seeds, n_samples)
    completeness_summary = summarize(completeness, ["classifier", "test_missing_rate"], metrics)
    completeness_summary.round(4).to_csv(output_dir / "completeness.csv", index=False)
    plot_completeness(completeness_summary, output_dir / "completeness.png")
    log_runs("wplyw-kompletnosci", completeness, ["classifier", "seed", "test_missing_rate"], metrics)
    with mlflow.start_run(run_name="wykres-kompletnosci"):
        mlflow.log_artifact(str(output_dir / "completeness.png"))

    print(comparison_summary.round(3).to_string(index=False))
    print()
    print(completeness_summary.round(3).to_string(index=False))


if __name__ == "__main__":
    run_experiments(OUTPUT_DIR, SEEDS, N_SAMPLES)
