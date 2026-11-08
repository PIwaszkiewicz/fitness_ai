"""Połączenie z bazą danych (SQLAlchemy + SQLite).

Tworzy silnik bazy, fabrykę sesji oraz klasę bazową modeli.
Funkcja get_db dostarcza sesję do endpointów przez mechanizm Depends w FastAPI.
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# check_same_thread=False: SQLite domyślnie pozwala używać połączenia tylko w wątku,
# który je utworzył, a FastAPI obsługuje żądania w wielu wątkach.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# Fabryka sesji: każde żądanie HTTP dostaje własną, krótko żyjącą sesję.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Klasa bazowa, po której dziedziczą wszystkie modele (tabele) bazy danych."""


def add_missing_columns(engine: Engine) -> list[str]:
    """Dodaje do istniejących tabel kolumny, które pojawiły się w modelach (prosta migracja).

    create_all tworzy tylko brakujące tabele, a nie zmienia istniejących, więc bez tego
    baza utworzona przed dodaniem nowego pola nie przyjmie profilu. Wszystkie nowe pola
    są opcjonalne, więc wystarczy dodać pustą kolumnę. Zmiany typów czy usuwanie kolumn
    wymagałyby pełnego narzędzia migracji (np. Alembic). Zwraca nazwy dodanych kolumn.
    """
    inspector = inspect(engine)
    added = []
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                column_type = column.type.compile(dialect=engine.dialect)
                connection.execute(
                    text(f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {column_type}')
                )
                added.append(f"{table.name}.{column.name}")
    return added


def get_db() -> Generator[Session, None, None]:
    """Otwiera sesję na czas jednego żądania i zawsze ją zamyka, także po błędzie."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
