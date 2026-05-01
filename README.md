# Clients API

API REST desarrollada con FastAPI para importar y gestionar clientes desde un archivo Excel.

El proyecto resuelve un microservicio simple de Clientes: valida registros, persiste los datos validos en SQLite y expone endpoints de ABM.

## Stack

- Python 3.10+
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- pandas
- openpyxl
- pytest

## Estructura

```text
app/
|-- main.py
|-- database.py
|-- models.py
|-- schemas.py
|-- routers/
|   `-- clients.py
|-- services/
|   `-- client_service.py
|-- repositories/
|   `-- client_repository.py
`-- utils/
    `-- excel_reader.py

tests/
|-- conftest.py
|-- test_client_service.py
`-- test_clients_api.py
```

## Instalacion

Crear y activar un entorno virtual:

```bash
python -m venv venv
.\venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecucion

Levantar la API:

```bash
uvicorn app.main:app --reload
```

La documentacion interactiva de Swagger queda disponible en:

```text
http://127.0.0.1:8000/docs
```

Desde Swagger se pueden probar todos los endpoints, incluido `POST /clients/import`, que permite seleccionar el archivo Excel desde la interfaz.

Health check:

```text
GET /health
```

## Endpoints

```text
POST   /clients/import
GET    /clients
GET    /clients/{customer_id}
POST   /clients
PUT    /clients/{customer_id}
DELETE /clients/{customer_id}
```

## Formato del Excel

El archivo debe ser `.xlsx` y contener una hoja llamada `Clientes`.

Columnas esperadas:

```text
customer_id
name
email
country
age
```

Reglas:

- `customer_id`: entero, obligatorio y unico.
- `name`: string obligatorio, no vacio.
- `email`: string obligatorio con formato valido.
- `country`: string obligatorio, no vacio.
- `age`: entero opcional, debe ser mayor o igual a 18 si se informa.

El archivo debe contener exactamente esas columnas. Las columnas pueden venir en distinto orden.

Los nombres de columnas se normalizan quitando espacios al inicio y al final. Por ejemplo, `name ` se interpreta como `name`. Si luego de esa normalizacion quedan columnas duplicadas, el archivo se rechaza.

## Importacion

El endpoint recibe un archivo Excel por `multipart/form-data`:

```text
POST /clients/import
```

Ejemplo con curl:

```bash
curl.exe -X POST "http://127.0.0.1:8000/clients/import" -F "file=@clientes_ejemplo.xlsx"
```

Respuesta esperada:

```json
{
  "summary": {
    "total_records": 10,
    "inserted": 9,
    "errors": 1
  },
  "error_details": [
    {
      "customer_id": 5,
      "errors": ["Email invalido"]
    }
  ]
}
```

Los registros invalidos no se guardan. Los registros validos se insertan en SQLite.

## Ejemplo de alta manual

```json
{
  "customer_id": 1,
  "name": "Ana Perez",
  "email": "ana@example.com",
  "country": "Uruguay",
  "age": 28
}
```

## Tests

Ejecutar desde la raiz del proyecto:

```bash
.\venv\Scripts\pytest.exe
```

Si el entorno virtual esta activado, tambien se puede usar:

```bash
pytest
```

Los tests cubren:

- Validacion e importacion de clientes.
- Duplicados por `customer_id`.
- Flujo ABM basico por API.
- Importacion desde un Excel generado en memoria.

## Decisiones tecnicas

La aplicacion esta separada en capas para mantener responsabilidades claras:

- `routers`: endpoints HTTP y dependencias de FastAPI.
- `services`: reglas de negocio y validaciones.
- `repositories`: acceso a datos con SQLAlchemy.
- `models`: modelo de persistencia.
- `schemas`: contratos de entrada y salida con Pydantic.
- `utils`: lectura del archivo Excel.

Se usa `customer_id` como clave primaria porque la consigna lo define como obligatorio y unico. La lectura del Excel esta separada de la validacion de negocio: `ExcelReader` verifica hoja y columnas, mientras que `ClientService` decide que registros son validos y cuales se insertan.

Para este challenge se usa `Base.metadata.create_all()` al iniciar la aplicacion para crear las tablas necesarias en SQLite si todavia no existen.
