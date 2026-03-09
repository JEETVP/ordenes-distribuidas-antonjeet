Diseño de APP Distribuida de Órdenes

Nombres:
Anton Betak Licea
Roberto Villegas Ojeda

Número de Cuenta:
190013

Arquitectura del Sistema

El sistema está compuesto por cuatro elementos principales:

Cliente (Swagger o curl)

API Gateway

Redis

Writer Service con PostgreSQL

Esta arquitectura permite separar responsabilidades entre servicios y mantener una comunicación clara entre cada componente del sistema.

Flujo del Sistema

Primero, el cliente.

Cuando se utiliza POST /orders desde:

http://localhost:8000/docs

FastAPI del API Gateway recibe un JSON con los campos:

customer

items

Este endpoint está definido en:

api-gateway/app/main.py

FastAPI valida automáticamente el cuerpo usando los modelos definidos en schemas.py mediante Pydantic.
Pydantic convierte el JSON recibido en un objeto Python tipado llamado OrderCreate.

Generación del ID de Orden

Después de validar la petición, el gateway genera un identificador único para la orden utilizando:

uuid.uuid4()

Esto asegura que cada orden tenga un identificador único dentro del sistema.

En este punto el gateway todavía no escribe en PostgreSQL.

Primero registra el estado inicial de la orden en Redis.

Uso de Redis

Redis se utiliza como almacenamiento rápido de estado.

Se crea un hash con la clave:

order:{order_id}

y campos como:

status

last_update

Inicialmente el estado de la orden se guarda como:

RECEIVED

Esto indica que el gateway ya recibió la solicitud correctamente.

Comunicación con Writer Service

El gateway prepara un payload con los datos de la orden:

order_id

customer

items

Este payload se envía al Writer Service mediante una llamada HTTP interna.

Esta comunicación se realiza en el archivo:

writer_client.py

utilizando la librería httpx.

La URL del servicio es:

http://writer-service:8001/internal/orders

Este hostname funciona porque Docker Compose crea una red interna, permitiendo que los contenedores se comuniquen entre sí usando el nombre del servicio.

Persistencia en PostgreSQL

Cuando el Writer Service recibe la petición, entra al endpoint definido en:

writer-service/app/main.py

El JSON recibido se convierte en un objeto del modelo InternalOrder definido en schemas.py.

Después se abre una sesión de base de datos usando SQLAlchemy, configurada en:

db.py

mediante la variable:

DATABASE_URL
Control de Idempotencia

Antes de insertar la orden en la base de datos, el writer-service verifica si ya existe una orden con el mismo order_id.

Esto se realiza mediante el repositorio:

orders_repo.py

Este paso es importante porque hace que el endpoint sea idempotente.
Si el gateway envía la misma orden más de una vez, no se duplicará el registro en la base de datos.

Inserción de la Orden

Si la orden no existe, el repositorio construye un objeto Order usando el modelo ORM definido en:

models.py

Luego se inserta en PostgreSQL utilizando:

session.add()
session.commit()

En este momento la orden queda persistida en la tabla:

orders

dentro de la base de datos:

orders_db
Actualización de Estado en Redis

Después de insertar la orden, el writer-service vuelve a Redis y actualiza el estado del hash:

order:{order_id}

El campo status cambia a:

PERSISTED

Esto indica que la orden fue guardada correctamente en la base de datos.

Consulta del Estado de la Orden

Cuando el cliente utiliza:

GET /orders/{order_id}

en el gateway, este endpoint no consulta PostgreSQL.

En su lugar, consulta Redis usando:

HGETALL order:{order_id}

Redis responde con el estado actual de la orden, por ejemplo:

PERSISTED

Este diseño hace que la consulta sea muy rápida, ya que Redis es un sistema de almacenamiento en memoria.

Flujo Completo del Sistema

El flujo completo del sistema es el siguiente:

Cliente
   ↓
API Gateway
   ↓
Redis (estado inicial)
   ↓
Writer Service
   ↓
PostgreSQL (persistencia)
   ↓
Redis (estado actualizado)

Cuando el cliente consulta el estado de la orden, el gateway obtiene la información directamente desde Redis.                                                       |
