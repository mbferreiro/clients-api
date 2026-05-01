"""Tests de endpoints HTTP usando el TestClient de FastAPI."""

from io import BytesIO

import pandas as pd


def test_clients_crud_flow(client):
    # Recorre el flujo basico de alta, consulta, modificacion y baja.
    create_response = client.post(
        "/clients",
        json={
            "customer_id": 1,
            "name": "Ana Perez",
            "email": "ana@example.com",
            "country": "Uruguay",
            "age": 28,
        },
    )

    assert create_response.status_code == 201
    assert create_response.json()["customer_id"] == 1

    list_response = client.get("/clients")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        "/clients/1",
        json={"country": "Argentina", "age": 31},
    )
    assert update_response.status_code == 200
    assert update_response.json()["country"] == "Argentina"
    assert update_response.json()["age"] == 31

    delete_response = client.delete("/clients/1")
    assert delete_response.status_code == 204

    get_response = client.get("/clients/1")
    assert get_response.status_code == 404


def test_import_clients_from_excel(client):
    # Genera un archivo Excel en memoria para probar el endpoint de importacion.
    excel_file = BytesIO()
    dataframe = pd.DataFrame(
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
        ]
    )

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="Clientes", index=False)

    # Vuelve al inicio del archivo antes de enviarlo en el request.
    excel_file.seek(0)

    # Envia el Excel como multipart/form-data, igual que lo haria Swagger o curl.
    response = client.post(
        "/clients/import",
        files={
            "file": (
                "clientes.xlsx",
                excel_file.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "total_records": 2,
        "inserted": 1,
        "errors": 1,
    }
    assert body["error_details"][0]["customer_id"] == 2

    list_response = client.get("/clients")
    assert len(list_response.json()) == 1
