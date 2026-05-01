from io import BytesIO

import pandas as pd


# Contrato esperado para la hoja Clientes.
EXPECTED_COLUMNS = ["customer_id", "name", "email", "country", "age"]


class ExcelReadError(ValueError):
    """Error controlado para problemas de lectura o estructura del Excel."""

    pass


class ExcelReader:
    """Lee el Excel de clientes y valida su estructura."""

    def read_clients(self, file_content: bytes) -> list[dict]:
        try:
            dataframe = pd.read_excel(BytesIO(file_content), sheet_name="Clientes")
        except ValueError as exc:
            raise ExcelReadError(
                "El archivo debe contener una hoja llamada 'Clientes'"
            ) from exc
        except Exception as exc:
            raise ExcelReadError("No se pudo leer el archivo Excel") from exc

        # Se toleran espacios accidentales en los encabezados del Excel.
        dataframe.columns = [str(column).strip() for column in dataframe.columns]

        self._validate_columns(dataframe)

        # Se reordenan las columnas para devolver siempre registros con el mismo contrato.
        dataframe = dataframe[EXPECTED_COLUMNS]
        # Pandas usa NaN para celdas vacias; el servicio trabaja mejor con None.
        dataframe = dataframe.astype(object).where(pd.notna(dataframe), None)
        return dataframe.to_dict(orient="records")

    def _validate_columns(self, dataframe: pd.DataFrame) -> None:
        columns = list(dataframe.columns)

        if len(columns) != len(set(columns)):
            raise ExcelReadError("El archivo contiene columnas duplicadas")

        if set(columns) != set(EXPECTED_COLUMNS):
            expected = ", ".join(EXPECTED_COLUMNS)
            found = ", ".join(str(column) for column in columns)
            raise ExcelReadError(
                "El archivo debe contener exactamente estas columnas: "
                f"{expected}. Columnas encontradas: {found}"
            )
