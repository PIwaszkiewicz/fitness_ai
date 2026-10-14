"""Endpoint planu treningowego generowanego na żądanie z aktualnego profilu."""

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.v1.endpoints.profiles import ProfileFromPath
from app.ml import predictor
from app.ml.predictor import ClassifierName
from app.schemas import ExerciseRead, UserProfileRead
from app.schemas.plan import TrainingPlan
from app.services import exercise_service, plan_generator

router = APIRouter(prefix="/profiles", tags=["Plan treningowy"])


@router.get("/{profile_id}/plan", response_model=TrainingPlan)
def get_training_plan(
    profile: ProfileFromPath, db: DbSession, method: ClassifierName = ClassifierName.MLP
):
    """Klasyfikuje poziom sprawności i buduje plan z bezpiecznych ćwiczeń atlasu.

    Gdy wybrany model ML nie jest wytrenowany, poziom wyznacza system regułowy
    (pole classifier w odpowiedzi mówi, który klasyfikator został użyty).
    """
    try:
        level = predictor.classify(profile, method)["level"]
    except FileNotFoundError:
        method = ClassifierName.RULES
        level = predictor.classify(profile, method)["level"]

    exercises = [ExerciseRead.model_validate(e) for e in exercise_service.list_all_exercises(db)]
    return plan_generator.generate_plan(
        UserProfileRead.model_validate(profile), level, method, exercises
    )
