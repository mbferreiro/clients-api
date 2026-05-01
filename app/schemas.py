from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints


# String que se limpia en bordes y no permite valores vacios.
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ClientBase(BaseModel):
    """Campos compartidos por creacion y respuesta de clientes."""

    name: NonEmptyStr
    email: EmailStr
    country: NonEmptyStr
    age: int | None = Field(default=None, ge=18)


class ClientCreate(ClientBase):
    """Payload requerido para crear un cliente."""

    customer_id: int


class ClientUpdate(BaseModel):
    """Payload de actualizacion parcial; todos los campos son opcionales."""

    name: NonEmptyStr | None = None
    email: EmailStr | None = None
    country: NonEmptyStr | None = None
    age: int | None = Field(default=None, ge=18)


class ClientResponse(ClientCreate):
    """Respuesta serializable desde modelos SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)


class ImportErrorDetail(BaseModel):
    customer_id: int | None
    errors: list[str]


class ImportSummary(BaseModel):
    total_records: int
    inserted: int
    errors: int


class ImportResponse(BaseModel):
    """Respuesta del endpoint de importacion."""

    summary: ImportSummary
    error_details: list[ImportErrorDetail]
