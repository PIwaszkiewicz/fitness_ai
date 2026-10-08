"""Testy warstwy bazy danych: zapis, odczyt i ograniczenia tabel."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models import Exercise, UserProfile
from app.schemas import ExerciseCreate, UserProfileCreate, UserProfileRead


def test_zapis_i_odczyt_profilu(db_session):
    data = UserProfileCreate(
        age=25,
        gender="female",
        height_cm=165,
        weight_kg=60,
        training_goal="endurance",
        activity_level="light",
        limitations=["knee", "wrist"],
    )
    db_session.add(UserProfile(**data.model_dump()))
    db_session.commit()

    saved = db_session.query(UserProfile).one()
    assert saved.id is not None
    assert saved.gender == "female"
    assert saved.limitations == ["knee", "wrist"]


def test_schemat_odczytu_z_obiektu_bazy(db_session):
    profile = UserProfile(
        age=40,
        gender="male",
        height_cm=175,
        weight_kg=90,
        training_goal="weight_loss",
        activity_level="sedentary",
        limitations=[],
    )
    db_session.add(profile)
    db_session.commit()

    result = UserProfileRead.model_validate(profile)
    assert result.id == profile.id
    assert result.training_goal == "weight_loss"


def test_zapis_cwiczenia_z_przeciwwskazaniami(db_session):
    data = ExerciseCreate(
        name="Martwy ciąg",
        muscle_group="back",
        equipment="barbell",
        difficulty="advanced",
        contraindications=["lower_back"],
    )
    db_session.add(Exercise(**data.model_dump()))
    db_session.commit()

    saved = db_session.query(Exercise).filter_by(name="Martwy ciąg").one()
    assert saved.contraindications == ["lower_back"]


def test_nazwa_cwiczenia_musi_byc_unikalna(db_session):
    fields = {"muscle_group": "chest", "equipment": "none", "difficulty": "beginner"}
    db_session.add(Exercise(name="Pompki", **fields))
    db_session.commit()

    db_session.add(Exercise(name="Pompki", **fields))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_get_db_zwraca_i_zamyka_sesje():
    generator = get_db()
    session = next(generator)
    assert session.is_active
    generator.close()  # symuluje zakończenie żądania, wykonuje blok finally
