"""Wspólne zależności endpointów (mechanizm Depends w FastAPI).

Annotated łączy typ argumentu z informacją, skąd FastAPI ma wziąć jego wartość.
Dzięki temu w endpoincie wystarczy napisać `db: DbSession`.
"""

from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db

# Sesja bazy danych otwierana na czas jednego żądania.
DbSession = Annotated[Session, Depends(get_db)]

# Parametry stronicowania list: ile rekordów pominąć i ile maksymalnie zwrócić.
Skip = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]
