"""Tests de lectura y validacion de estructura del Excel."""

from io import BytesIO

import pandas as pd
import pytest

from app.utils.excel_reader import ExcelReader, ExcelReadError


# Helper para generar archivos Excel en memoria sin depender de archivos fisicos.
def build_excel(dataframe: pd.DataFrame, sheet_name: str = "Clientes") -> bytes:
    excel_file = BytesIO()

    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

    return excel_file.getvalue()


def test_read_clients_accepts_headers_with_extra_spaces():
    # Los encabezados con espacios deben normalizarse antes de validar columnas.
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "name ": "Ana Perez",
                " email": "ana@example.com",
                "country": "Uruguay",
                "age": 28,
            }
        ]
    )

    records = ExcelReader().read_clients(build_excel(dataframe))

    assert records == [
        {
            "customer_id": 1,
            "name": "Ana Perez",
            "email": "ana@example.com",
            "country": "Uruguay",
            "age": 28,
        }
    ]


def test_read_clients_rejects_duplicate_columns_after_stripping_spaces():
    # Al limpiar espacios, "name" y " name " pasan a ser la misma columna.
    dataframe = pd.DataFrame(
        [[1, "Ana Perez", "Otro Nombre", "ana@example.com", "Uruguay", 28]],
        columns=["customer_id", "name", " name ", "email", "country", "age"],
    )

    with pytest.raises(ExcelReadError, match="columnas duplicadas"):
        ExcelReader().read_clients(build_excel(dataframe))


def test_read_clients_rejects_missing_expected_columns():
    # age es opcional como valor, pero la columna debe existir en el archivo.
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "name": "Ana Perez",
                "email": "ana@example.com",
                "country": "Uruguay",
            }
        ]
    )

    with pytest.raises(ExcelReadError, match="exactamente estas columnas"):
        ExcelReader().read_clients(build_excel(dataframe))


def test_read_clients_rejects_wrong_sheet_name():
    # La consigna exige que la hoja se llame Clientes.
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 1,
                "name": "Ana Perez",
                "email": "ana@example.com",
                "country": "Uruguay",
                "age": 28,
            }
        ]
    )

    with pytest.raises(ExcelReadError, match="hoja llamada 'Clientes'"):
        ExcelReader().read_clients(build_excel(dataframe, sheet_name="Hoja1"))
