"""Endpoint klasyfikacji poziomu sprawności zapisanego profilu."""

from fastapi import APIRouter, HTTPException, status

from app.api.v1.endpoints.profiles import ProfileFromPath
from app.ml import predictor
from app.ml.predictor import ClassifierName
from app.schemas.fitness_level import FitnessLevelResult

router = APIRouter(prefix="/profiles", tags=["Klasyfikacja sprawności"])


@router.get("/{profile_id}/fitness-level", response_model=FitnessLevelResult)
def get_fitness_level(profile: ProfileFromPath, method: ClassifierName = ClassifierName.MLP):
    """Klasyfikuje poziom sprawności profilu. Parametr method wybiera klasyfikator."""
    try:
        result = predictor.classify(profile, method)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model nie został wytrenowany. Uruchom: python -m app.ml.train",
        ) from None
    return FitnessLevelResult(
        profile_id=profile.id,
        method=method,
        data_completeness=profile.data_completeness,
        **result,
    )
