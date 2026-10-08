"""Połączenie z bazą danych (SQLAlchemy + SQLite).

Tworzy silnik bazy, fabrykę sesji oraz klasę bazową modeli.
Funkcja get_db dostarcza sesję do endpointów przez mechanizm Depends w FastAPI.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# check_same_thread=False: SQLite domyślnie pozwala używać połączenia tylko w wątku,
# który je utworzył, a FastAPI obsługuje żądania w wielu wątkach.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# Fabryka sesji: każde żądanie HTTP dostaje własną, krótko żyjącą sesję.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Klasa bazowa, po której dziedziczą wszystkie modele (tabele) bazy danych."""


def get_db() -> Generator[Session, None, None]:
    """Otwiera sesję na czas jednego żądania i zawsze ją zamyka, także po błędzie."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
