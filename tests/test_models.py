"""Testy warstwy bazy danych: zapis, odczyt i ograniczenia tabel."""

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.database import Base, add_missing_columns, get_db
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
        movement_pattern="hinge",
        contraindications=["lower_back"],
    )
    db_session.add(Exercise(**data.model_dump()))
    db_session.commit()

    saved = db_session.query(Exercise).filter_by(name="Martwy ciąg").one()
    assert saved.contraindications == ["lower_back"]


def test_nazwa_cwiczenia_musi_byc_unikalna(db_session):
    fields = {
        "muscle_group": "chest",
        "equipment": "none",
        "difficulty": "beginner",
        "movement_pattern": "horizontal_push",
    }
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


def test_migracja_dodaje_brakujace_kolumny(tmp_path):
    # Baza z tabelą profili sprzed dodania pytań o ciężary (bez nowych kolumn).
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE user_profiles (id INTEGER PRIMARY KEY, age INTEGER)"))
    Base.metadata.create_all(bind=engine)  # istniejącej tabeli nie zmienia
    added = add_missing_columns(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("user_profiles")}
    assert "user_profiles.squat_kg" in added
    assert {"squat_kg", "lifts_weights", "pushup_variant"} <= columns
    assert add_missing_columns(engine) == []  # ponowne uruchomienie niczego nie zmienia
    engine.dispose()
