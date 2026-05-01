"""Tests de reglas de negocio de importacion sin pasar por HTTP."""

from app.repositories.client_repository import ClientRepository
from app.schemas import ClientCreate
from app.services.client_service import ClientService


def test_import_clients_inserts_valid_records_and_reports_errors(db_session):
    repository = ClientRepository(db_session)
    service = ClientService(repository)
    # Guarda un cliente inicial para probar que la importacion rechace un customer_id ya existente.
    repository.create(
        ClientCreate(
            customer_id=10,
            name="Existing Client",
            email="existing@example.com",
            country="Uruguay",
            age=30,
        )
    )

    # Importa un registro valido, uno con errores de campos y uno duplicado en base.
    response = service.import_clients(
        [
            {
                "customer_id": 1,
                "name": "Ana Perez",
                "email": "ana@example.com",
                "country": "Uruguay",
                "age": 28,
            },
            {
                "customer_id": 2,
                "name": "",
                "email": "invalid-email",
                "country": "Argentina",
                "age": 17,
            },
            {
                "customer_id": 10,
                "name": "Duplicate",
                "email": "duplicate@example.com",
                "country": "Chile",
                "age": 35,
            },
        ]
    )

    assert response.summary.total_records == 3
    assert response.summary.inserted == 1
    assert response.summary.errors == 2
    assert repository.get_by_id(1) is not None
    assert repository.get_by_id(2) is None

    # Indexa los errores por customer_id para validar mensajes especificos.
    error_messages = {
        detail.customer_id: detail.errors for detail in response.error_details
    }
    assert "name es obligatorio" in error_messages[2]
    assert "Email invalido" in error_messages[2]
    assert "age debe ser mayor o igual a 18" in error_messages[2]
    assert "customer_id ya existe en la base de datos" in error_messages[10]


def test_import_clients_rejects_duplicate_customer_ids_in_file(db_session):
    service = ClientService(ClientRepository(db_session))

    # Ambos registros usan el mismo customer_id, por eso deben rechazarse los dos.
    response = service.import_clients(
        [
            {
                "customer_id": 1,
                "name": "Ana Perez",
                "email": "ana@example.com",
                "country": "Uruguay",
                "age": 28,
            },
            {
                "customer_id": 1,
                "name": "Ana Perez 2",
                "email": "ana2@example.com",
                "country": "Uruguay",
                "age": 29,
            },
        ]
    )

    assert response.summary.total_records == 2
    assert response.summary.inserted == 0
    assert response.summary.errors == 2
    assert all(
        "customer_id repetido en el archivo" in detail.errors
        for detail in response.error_details
    )
