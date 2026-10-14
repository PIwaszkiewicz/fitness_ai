"""Schemat podpowiedzi przeciwwskazań dla nowego ćwiczenia."""

from pydantic import BaseModel

from app.models.enums import Limitation


class ContraindicationSuggestion(BaseModel):
    """Przewidywane przeciwwskazania. To podpowiedź, którą przed zapisem musi zatwierdzić człowiek."""

    contraindications: list[Limitation]
    detector: str  # "hybrid" albo "rules", gdy atlas jest pusty i nie ma na czym uczyć drzewa
