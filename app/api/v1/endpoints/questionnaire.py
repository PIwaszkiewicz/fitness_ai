"""Endpointy kwestionariusza: pobranie definicji pytań i wysłanie odpowiedzi."""

from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.data.questions import QUESTIONS
from app.schemas import UserProfileCreate
from app.schemas.questionnaire import Question, QuestionnaireResult
from app.services import questionnaire_service as service

router = APIRouter(prefix="/questionnaire", tags=["Kwestionariusz"])


@router.get("", response_model=list[Question])
def get_questions():
    """Zwraca listę pytań wraz z warunkami wyświetlania, z której frontend buduje formularz."""
    return QUESTIONS


@router.post("", response_model=QuestionnaireResult, status_code=status.HTTP_201_CREATED)
def submit_questionnaire(answers: UserProfileCreate, db: DbSession):
    """Przyjmuje odpowiedzi, zapisuje profil i zwraca braki w danych oraz ostrzeżenia."""
    return service.submit_questionnaire(db, answers)
