"""Wspólne fixture'y testów. Każdy test bazy dostaje osobną, pustą bazę SQLite."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (rejestruje tabele w Base.metadata)
from app.core.database import Base


@pytest.fixture
def db_session(tmp_path):
    """Tworzy bazę w pliku tymczasowym, więc testy nie dotykają prawdziwej bazy."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()
