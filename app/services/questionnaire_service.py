"""Obsługa wysłanego kwestionariusza: zapis profilu, braki w danych i ostrzeżenia zdrowotne."""

from sqlalchemy.orm import Session

from app.models.enums import CARDIOVASCULAR_LIMITATIONS
from app.schemas import UserProfileCreate, UserProfileRead
from app.schemas.questionnaire import QuestionnaireResult
from app.services import user_profile_service
from app.services.completeness import find_missing_answers

# Ból od 7 w skali 1–10 to ból silny według przyjętej w medycynie skali numerycznej (NRS).
SEVERE_PAIN_LEVEL = 7
# Tętno spoczynkowe powyżej 100 uderzeń/min to tachykardia.
MAX_NORMAL_RESTING_HEART_RATE = 100


def build_warnings(data: UserProfileCreate) -> list[str]:
    """Tworzy ostrzeżenia zdrowotne na podstawie odpowiedzi.

    Ostrzeżenia nie blokują zapisu profilu: informują użytkownika,
    że przed treningiem powinien skonsultować się ze specjalistą.
    """
    warnings = []
    has_cardio = any(item in CARDIOVASCULAR_LIMITATIONS for item in data.limitations)
    if has_cardio and data.medical_clearance is not True:
        warnings.append(
            "Zgłoszono chorobę układu krążenia bez potwierdzonej zgody lekarza. "
            "Przed rozpoczęciem treningu skonsultuj się z lekarzem."
        )
    if data.pain_level is not None and data.pain_level >= SEVERE_PAIN_LEVEL:
        warnings.append(
            "Zgłoszono silny ból. Przed treningiem zalecana jest konsultacja z fizjoterapeutą."
        )
    if data.resting_heart_rate is not None and data.resting_heart_rate > MAX_NORMAL_RESTING_HEART_RATE:
        warnings.append(
            "Tętno spoczynkowe powyżej 100 uderzeń/min. Zalecana konsultacja lekarska."
        )
    return warnings


def submit_questionnaire(db: Session, data: UserProfileCreate) -> QuestionnaireResult:
    """Zapisuje odpowiedzi jako nowy profil i zwraca go razem z brakami i ostrzeżeniami."""
    profile = user_profile_service.create_profile(db, data)
    return QuestionnaireResult(
        profile=UserProfileRead.model_validate(profile),
        missing_answers=find_missing_answers(data.model_dump()),
        warnings=build_warnings(data),
    )
