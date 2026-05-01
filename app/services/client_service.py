from collections import Counter
import math
from typing import Any

from fastapi import HTTPException, status
from pydantic import EmailStr, TypeAdapter, ValidationError

from app.models import Client
from app.repositories.client_repository import ClientRepository
from app.schemas import ClientCreate, ClientUpdate, ImportErrorDetail, ImportResponse


email_adapter = TypeAdapter(EmailStr)


class ClientService:
    """Contiene las reglas de negocio para clientes e importacion."""

    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    def list_clients(self) -> list[Client]:
        return self.repository.get_all()

    def get_client(self, customer_id: int) -> Client:
        client = self.repository.get_by_id(customer_id)

        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado",
            )

        return client

    def create_client(self, client_data: ClientCreate) -> Client:
        existing_client = self.repository.get_by_id(client_data.customer_id)

        if existing_client is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un cliente con ese customer_id",
            )

        return self.repository.create(client_data)

    def update_client(self, customer_id: int, client_data: ClientUpdate) -> Client:
        client = self.get_client(customer_id)
        return self.repository.update(client, client_data)

    def delete_client(self, customer_id: int) -> None:
        client = self.get_client(customer_id)
        self.repository.delete(client)

    def import_clients(self, records: list[dict[str, Any]]) -> ImportResponse:
        # Primero se valida cada fila sin insertar nada, para reportar errores por registro.
        row_results = [self._validate_import_record(record) for record in records]
        customer_ids = [
            row["data"]["customer_id"]
            for row in row_results
            if row["data"].get("customer_id") is not None
        ]
        # Se detectan duplicados dentro del archivo antes de consultar la base.
        duplicate_ids = {
            customer_id
            for customer_id, count in Counter(customer_ids).items()
            if count > 1
        }
        # Se consulta la base una sola vez para saber que customer_id ya existen.
        existing_ids = self.repository.get_existing_ids(list(set(customer_ids)))

        valid_clients: list[ClientCreate] = []
        error_details: list[ImportErrorDetail] = []

        for row in row_results:
            data = row["data"]
            errors = row["errors"]
            customer_id = data.get("customer_id")

            if customer_id in duplicate_ids:
                errors.append("customer_id repetido en el archivo")

            if customer_id in existing_ids:
                errors.append("customer_id ya existe en la base de datos")

            if errors:
                error_details.append(
                    ImportErrorDetail(customer_id=customer_id, errors=errors)
                )
                continue

            valid_clients.append(ClientCreate(**data))

        # Solo se persisten los registros que no acumularon errores.
        if valid_clients:
            self.repository.bulk_create(valid_clients)

        return ImportResponse(
            summary={
                "total_records": len(records),
                "inserted": len(valid_clients),
                "errors": len(error_details),
            },
            error_details=error_details,
        )

    def _validate_import_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Normaliza un registro importado y acumula sus errores de validacion."""

        errors: list[str] = []
        data = {
            "customer_id": self._parse_required_int(
                record.get("customer_id"), "customer_id", errors
            ),
            "name": self._parse_required_string(record.get("name"), "name", errors),
            "email": self._parse_email(record.get("email"), errors),
            "country": self._parse_required_string(
                record.get("country"), "country", errors
            ),
            "age": self._parse_optional_age(record.get("age"), errors),
        }

        return {"data": data, "errors": errors}

    def _parse_required_int(
        self,
        value: Any,
        field_name: str,
        errors: list[str],
    ) -> int | None:
        if self._is_empty(value):
            errors.append(f"{field_name} es obligatorio")
            return None

        try:
            if isinstance(value, float) and not value.is_integer():
                raise ValueError
            return int(value)
        except (TypeError, ValueError):
            errors.append(f"{field_name} debe ser un entero")
            return None

    def _parse_required_string(
        self,
        value: Any,
        field_name: str,
        errors: list[str],
    ) -> str | None:
        if self._is_empty(value):
            errors.append(f"{field_name} es obligatorio")
            return None

        return str(value).strip()

    def _parse_email(self, value: Any, errors: list[str]) -> str | None:
        if self._is_empty(value):
            errors.append("email es obligatorio")
            return None

        email = str(value).strip()

        try:
            return str(email_adapter.validate_python(email))
        except ValidationError:
            errors.append("Email invalido")
            return email

    def _parse_optional_age(self, value: Any, errors: list[str]) -> int | None:
        if self._is_empty(value):
            return None

        try:
            if isinstance(value, float) and not value.is_integer():
                raise ValueError
            age = int(value)
        except (TypeError, ValueError):
            errors.append("age debe ser un entero")
            return None

        if age < 18:
            errors.append("age debe ser mayor o igual a 18")

        return age

    def _is_empty(self, value: Any) -> bool:
        """Considera vacios None, NaN y strings compuestos solo por espacios."""

        if value is None:
            return True

        if isinstance(value, float) and math.isnan(value):
            return True

        return str(value).strip() == ""
