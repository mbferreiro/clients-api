import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session():
    """Crea una sesion SQLite en memoria para aislar cada test."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        # StaticPool mantiene la misma conexion durante el test para SQLite en memoria.
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    # Crea las tablas necesarias antes de ejecutar el test.
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()

    try:
        yield db
    finally:
        # Limpia la base temporal al finalizar.
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Crea un TestClient usando la base de datos temporal."""

    def override_get_db():
        yield db_session

    # Reemplaza la dependencia get_db para que la API use la sesion de test.
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
