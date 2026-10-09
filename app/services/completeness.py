"""Ocena kompletności odpowiedzi z kwestionariusza.

Kompletność to procent pytań opcjonalnych, na które użytkownik odpowiedział.
Liczą się tylko pytania, które użytkownik faktycznie zobaczył (np. pytanie o ból
tylko przy zgłoszonych ograniczeniach). Wskaźnik posłuży w badaniu wpływu
kompletności danych na jakość klasyfikacji i rekomendacji.
"""

from app.data.questions import QUESTIONS
from app.schemas.questionnaire import Question

# Lista ograniczeń nie wchodzi do wskaźnika: pusta lista oznacza „brak ograniczeń”,
# a nie brak odpowiedzi, więc nie da się odróżnić pominięcia pytania.
SCORED_QUESTIONS = [q for q in QUESTIONS if not q.required and q.id != "limitations"]


def is_question_shown(question: Question, answers: dict) -> bool:
    """Sprawdza, czy pytanie było widoczne przy danych odpowiedziach (warunek show_if)."""
    if question.show_if is None:
        return True
    selected = answers.get(question.show_if.field) or []
    return any(value in question.show_if.any_of for value in selected)


def find_missing_answers(answers: dict) -> list[str]:
    """Zwraca id widocznych pytań opcjonalnych, na które nie udzielono odpowiedzi."""
    return [
        q.id for q in SCORED_QUESTIONS
        if is_question_shown(q, answers) and answers.get(q.id) is None
    ]


def calculate_completeness(answers: dict) -> int:
    """Zwraca procent (0–100) odpowiedzi na widoczne pytania opcjonalne."""
    shown = [q for q in SCORED_QUESTIONS if is_question_shown(q, answers)]
    answered = len(shown) - len(find_missing_answers(answers))
    return round(100 * answered / len(shown))
