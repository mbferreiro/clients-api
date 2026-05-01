from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# Base SQLite local usada por la API.
DATABASE_URL = "sqlite:///./clients.db"

engine = create_engine(
    DATABASE_URL,
    # Necesario para usar SQLite con sesiones manejadas por FastAPI.
    connect_args={"check_same_thread": False},
)

# Factory de sesiones de base de datos.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Clase base para los modelos SQLAlchemy."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Abre una sesion por request y la cierra al finalizar."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
