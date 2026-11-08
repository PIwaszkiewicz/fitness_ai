"""Schematy kwestionariusza: opis pytań wysyłany do frontendu i wynik wywiadu."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.user_profile import UserProfileRead


class Option(BaseModel):
    """Jedna odpowiedź do wyboru: wartość dla API i polska etykieta dla użytkownika."""

    value: str
    label: str


class ShowIf(BaseModel):
    """Warunek wyświetlenia pytania: odpowiedź na pole `field` to jedna z wartości `any_of`.

    Przy pytaniu wielokrotnego wyboru wystarczy, że lista zawiera jedną z nich.
    Odpowiedź tak/nie zapisuje się w any_of jako "true" / "false".
    """

    field: str
    any_of: list[str]


class Question(BaseModel):
    """Opis jednego pytania. Frontend buduje na jego podstawie pole formularza."""

    id: str  # nazwa pola w UserProfileCreate, pod którą wysyła się odpowiedź
    section: str
    text: str
    type: Literal["integer", "number", "choice", "multi_choice", "boolean"]
    required: bool
    unit: str | None = None
    min: float | None = None
    max: float | None = None
    hint: str | None = None
    options: list[Option] | None = None
    show_if: ShowIf | None = None


class QuestionnaireResult(BaseModel):
    """Odpowiedź po wysłaniu kwestionariusza: zapisany profil, braki i ostrzeżenia."""

    profile: UserProfileRead
    missing_answers: list[str]  # id pytań opcjonalnych, na które nie odpowiedziano
    warnings: list[str]  # ostrzeżenia zdrowotne do pokazania użytkownikowi
