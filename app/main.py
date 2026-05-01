from fastapi import FastAPI

from app.database import Base, engine
from app.routers.clients import router as clients_router


# Crea las tablas en SQLite al iniciar la aplicacion si todavia no existen.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Clients API",
    description="API REST para importar y gestionar clientes.",
    version="1.0.0",
)

app.include_router(clients_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint para verificar que la API esta levantada."""

    return {"status": "ok"}
