"""Test istotności statystycznej różnic między klasyfikatorami (test McNemara).

Dwa klasyfikatory oceniane są na tych samych osobach, więc porównujemy je parami:
liczymy osoby, które poprawnie sklasyfikował tylko pierwszy (b), i te, które poprawnie
sklasyfikował tylko drugi (c). Osoby, na których oba klasyfikatory zgadzają się
(oba dobrze lub oba źle), nic nie mówią o różnicy i są pomijane.

Hipoteza zerowa: oba klasyfikatory są tak samo dobre, więc każda „rozbieżna” osoba
z równym prawdopodobieństwem (50%) wpada do b lub c. Wersja dokładna testu sprawdza to
testem dwumianowym. Mała wartość p oznacza, że tak duża przewaga jednej metody
byłaby przy równych metodach bardzo mało prawdopodobna.
"""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from app.ml.data_generator import remove_answers
from app.ml.train import TRAIN_MISSING_RATE
from experiments.evaluation import CLASSIFIERS, TEST_MISSING_RATES, split_data

SIGNIFICANCE_LEVEL = 0.05


def mcnemar_test(y_true, predicted_a, predicted_b) -> dict:
    """Dokładny test McNemara dla dwóch klasyfikatorów ocenianych na tych samych osobach."""
    correct_a = np.asarray(predicted_a) == np.asarray(y_true)
    correct_b = np.asarray(predicted_b) == np.asarray(y_true)
    only_a = int((correct_a & ~correct_b).sum())
    only_b = int((~correct_a & correct_b).sum())
    disagreements = only_a + only_b
    p_value = binomtest(only_a, disagreements, 0.5).pvalue if disagreements else 1.0
    return {"only_a_correct": only_a, "only_b_correct": only_b, "p_value": p_value}


def significance_study(seeds: list[int], n_samples: int) -> pd.DataFrame:
    """Porównuje każdą parę klasyfikatorów przy każdym odsetku braków z eksperymentu 2.

    Dane i modele powstają dokładnie tak jak w eksperymencie 2. Osoby testowe ze wszystkich
    ziaren są łączone w jeden test. Liczba porównań jest duża, dlatego stosujemy poprawkę
    Bonferroniego: różnicę uznajemy za istotną, gdy p < 0,05 / liczba porównań.
    """
    pairs = list(combinations(CLASSIFIERS, 2))
    y_all = {rate: [] for rate in TEST_MISSING_RATES}
    predictions = {(rate, name): [] for rate in TEST_MISSING_RATES for name in CLASSIFIERS}
    for seed in seeds:
        rng = np.random.default_rng(seed)
        X_train, X_test, y_train, y_test = split_data(n_samples, seed)
        X_train = remove_answers(X_train, TRAIN_MISSING_RATE, rng)
        classifiers = {name: build(seed).fit(X_train, y_train) for name, build in CLASSIFIERS.items()}
        for rate in TEST_MISSING_RATES:
            X_incomplete = remove_answers(X_test, rate, rng)
            y_all[rate].extend(y_test)
            for name, classifier in classifiers.items():
                predictions[rate, name].extend(classifier.predict(X_incomplete))

    rows = []
    for rate in TEST_MISSING_RATES:
        for name_a, name_b in pairs:
            test = mcnemar_test(y_all[rate], predictions[rate, name_a], predictions[rate, name_b])
            rows.append({"test_missing_rate": rate, "classifier_a": name_a, "classifier_b": name_b, **test})
    results = pd.DataFrame(rows)
    results["significant"] = results["p_value"] < SIGNIFICANCE_LEVEL / len(results)
    return results
