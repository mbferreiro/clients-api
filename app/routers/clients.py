from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.client_repository import ClientRepository
from app.schemas import ClientCreate, ClientResponse, ClientUpdate, ImportResponse
from app.services.client_service import ClientService
from app.utils.excel_reader import ExcelReader, ExcelReadError


router = APIRouter(prefix="/clients", tags=["clients"])


def get_client_service(db: Session = Depends(get_db)) -> ClientService:
    # Construye el servicio con una sesion de base de datos inyectada por FastAPI.
    repository = ClientRepository(db)
    return ClientService(repository)


@router.get("", response_model=list[ClientResponse])
def list_clients(
    service: ClientService = Depends(get_client_service),
):
    return service.list_clients()


@router.get("/{customer_id}", response_model=ClientResponse)
def get_client(
    customer_id: int,
    service: ClientService = Depends(get_client_service),
):
    return service.get_client(customer_id)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreate,
    service: ClientService = Depends(get_client_service),
):
    return service.create_client(client_data)


@router.post("/import", response_model=ImportResponse)
async def import_clients(
    file: UploadFile = File(...),
    service: ClientService = Depends(get_client_service),
):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un Excel .xlsx",
        )

    file_content = await file.read()

    try:
        # ExcelReader valida la estructura del archivo y devuelve registros normalizados.
        records = ExcelReader().read_clients(file_content)
    except ExcelReadError as exc:
        # Los errores de lectura del Excel se informan como errores HTTP 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return service.import_clients(records)


@router.put("/{customer_id}", response_model=ClientResponse)
def update_client(
    customer_id: int,
    client_data: ClientUpdate,
    service: ClientService = Depends(get_client_service),
):
    return service.update_client(customer_id, client_data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    customer_id: int,
    service: ClientService = Depends(get_client_service),
):
    service.delete_client(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
