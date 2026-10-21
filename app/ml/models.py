"""Definicje modeli uczenia maszynowego jako potoki (Pipeline) scikit-learn.

Potok łączy przygotowanie danych z modelem, więc przy predykcji dane
przechodzą dokładnie te same kroki co przy uczeniu.
"""

from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


def missing_values_imputer() -> SimpleImputer:
    """Uzupełnia braki medianą i dodaje kolumny 0/1 informujące, czego brakowało."""
    return SimpleImputer(strategy="median", add_indicator=True)


def build_decision_tree(seed: int = 42) -> Pipeline:
    """Drzewo decyzyjne: model interpretowalny, jego decyzje da się rozpisać jako reguły.

    max_depth i min_samples_leaf ograniczają rozrost drzewa, żeby nie uczyło się szumu.
    Wartości dobrano walidacją krzyżową (experiments/tuning.py, opis w docs/EXPERIMENTS.md).
    """
    return Pipeline([
        ("imputer", missing_values_imputer()),
        ("model", DecisionTreeClassifier(max_depth=6, min_samples_leaf=5, random_state=seed)),
    ])


def build_mlp(seed: int = 42) -> Pipeline:
    """Sieć neuronowa (perceptron wielowarstwowy) z dwiema warstwami ukrytymi: 32 i 16 neuronów.

    StandardScaler sprowadza cechy do podobnej skali, bez czego sieć uczy się źle.
    early_stopping przerywa uczenie, gdy wynik na części walidacyjnej przestaje rosnąć.
    Rozmiar warstw potwierdzono walidacją krzyżową (experiments/tuning.py).
    """
    return Pipeline([
        ("imputer", missing_values_imputer()),
        ("scaler", StandardScaler()),
        ("model", MLPClassifier(
            hidden_layer_sizes=(32, 16),
            max_iter=1000,
            early_stopping=True,
            random_state=seed,
        )),
    ])
