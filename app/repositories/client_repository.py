from sqlalchemy.orm import Session

from app.models import Client
from app.schemas import ClientCreate, ClientUpdate


class ClientRepository:
    """Encapsula las operaciones de acceso a datos para clientes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Client]:
        return self.db.query(Client).order_by(Client.customer_id).all()

    def get_by_id(self, customer_id: int) -> Client | None:
        return (
            self.db.query(Client)
            .filter(Client.customer_id == customer_id)
            .first()
        )

    def get_existing_ids(self, customer_ids: list[int]) -> set[int]:
        """Devuelve los customer_id existentes para validar duplicados al importar."""

        if not customer_ids:
            return set()

        rows = (
            self.db.query(Client.customer_id)
            .filter(Client.customer_id.in_(customer_ids))
            .all()
        )
        return {row[0] for row in rows}

    def create(self, client_data: ClientCreate) -> Client:
        client = Client(**client_data.model_dump())
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def bulk_create(self, clients_data: list[ClientCreate]) -> list[Client]:
        clients = [Client(**client.model_dump()) for client in clients_data]
        self.db.add_all(clients)
        self.db.commit()

        for client in clients:
            self.db.refresh(client)

        return clients

    def update(self, client: Client, client_data: ClientUpdate) -> Client:
        # Solo actualiza los campos enviados en el request.
        update_data = client_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(client, field, value)

        self.db.commit()
        self.db.refresh(client)
        return client

    def delete(self, client: Client) -> None:
        self.db.delete(client)
        self.db.commit()
