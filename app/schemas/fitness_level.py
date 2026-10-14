"""Schemat odpowiedzi z wynikiem klasyfikacji poziomu sprawności."""

from pydantic import BaseModel

from app.ml.predictor import ClassifierName
from app.models.enums import FitnessLevel


class FitnessLevelResult(BaseModel):
    """Poziom sprawności profilu wyznaczony wybranym klasyfikatorem."""

    profile_id: int
    method: ClassifierName
    level: FitnessLevel
    # Pewność modelu dla każdego poziomu (tylko modele ML; system regułowy ich nie podaje).
    probabilities: dict[FitnessLevel, float] | None
    # Kompletność danych profilu: im niższa, tym mniej wiarygodny wynik.
    data_completeness: int
