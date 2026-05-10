# Sistema distribuido de ordenes

Arquitectura de microservicios para registro/autenticacion de usuarios, recepcion de ordenes, persistencia, reserva de inventario, notificaciones y metricas. El sistema esta orquestado con Docker Compose y combina comunicacion HTTP sincrona con mensajeria asincrona por RabbitMQ.

## Diagrama de arquitectura

```mermaid
flowchart LR
    user[Usuario / Cliente HTTP]
    frontend[frontend-service<br/>Express + EJS<br/>Puerto 3000]
    gateway[api-gateway<br/>FastAPI<br/>Puerto 8000]

    auth[auth-service<br/>FastAPI<br/>Puerto 8003]
    writer[writer-service<br/>FastAPI<br/>Puerto 8001]
    inventory[inventory-service<br/>FastAPI + consumidor RabbitMQ<br/>Puerto 8002]
    notifications[notification-service<br/>Consumidor RabbitMQ]
    analytics[analytics-service<br/>Consumidor RabbitMQ]

    postgres[(postgres<br/>orders_db<br/>orders, users, inventory)]
    postgres_notifications[(postgres-notifications<br/>notifications_db)]
    redis[(redis<br/>estado de ordenes,<br/>tokens revocados,<br/>metricas)]
    rabbit{{rabbitmq<br/>exchange fanout: orders}}

    user -->|Navegador| frontend
    user -->|REST / HTTP| gateway
    frontend -->|REST / HTTP| gateway

    gateway -->|/auth/*| auth
    gateway -->|/orders, /internal/orders| writer
    gateway -->|lee/escribe status order:*| redis

    auth -->|usuarios y roles| postgres
    auth -->|blacklist de JWT| redis

    writer -->|persistencia de ordenes| postgres
    writer -->|status PERSISTED| redis
    writer -->|publica order.created| rabbit

    rabbit -->|cola inventory.order.created| inventory
    rabbit -->|cola notification.order.created| notifications
    rabbit -->|cola analytics.order.created| analytics

    inventory -->|stock| postgres
    notifications -->|notificaciones| postgres_notifications
    analytics -->|contadores metrica:*| redis
```

> Nota: `frontend-service` existe en el repositorio como aplicacion Express, pero no esta incluido en el `docker-compose.yml` principal. Puede ejecutarse aparte o agregarse al Compose si se desea desplegar la interfaz junto con los microservicios.

## Componentes principales

| Componente | Tecnologia | Responsabilidad |
| --- | --- | --- |
| `api-gateway` | FastAPI | Punto de entrada HTTP. Expone autenticacion y ordenes, valida JWT, consulta Redis para estado y reenvia solicitudes al `auth-service` y `writer-service`. |
| `auth-service` | FastAPI + SQLAlchemy | Registra usuarios, valida credenciales, emite JWT, consulta usuario actual y revoca tokens usando Redis. |
| `writer-service` | FastAPI + SQLAlchemy | Persiste ordenes, asocia la orden al usuario autenticado, actualiza estado en Redis y publica eventos `order.created`. |
| `inventory-service` | FastAPI + consumidor RabbitMQ | Permite cargar/consultar inventario por HTTP y descuenta stock al consumir eventos de orden creada. |
| `notification-service` | Consumidor RabbitMQ + SQLAlchemy | Escucha eventos de orden creada y guarda notificaciones en una base PostgreSQL separada. |
| `analytics-service` | Consumidor RabbitMQ + Redis | Escucha eventos de orden creada y actualiza metricas simples en Redis. |
| `frontend-service` | Express + EJS | Interfaz web para login, registro, dashboard y creacion de ordenes. |

## Infraestructura

| Servicio | Puerto local | Uso |
| --- | --- | --- |
| `postgres` | `5432` | Base principal para ordenes, usuarios e inventario. |
| `postgres-notifications` | `5433` | Base aislada para notificaciones. |
| `redis` | `6379` | Estado rapido de ordenes, blacklist de JWT y metricas de analitica. |
| `rabbitmq` | `5672` | Broker AMQP para eventos de ordenes. |
| `rabbitmq-management` | `15672` | Consola de administracion de RabbitMQ en desarrollo. |

## Flujo de autenticacion

```mermaid
sequenceDiagram
    participant C as Cliente
    participant G as api-gateway
    participant A as auth-service
    participant P as postgres
    participant R as redis

    C->>G: POST /auth/register o /auth/login
    G->>A: Reenvia solicitud /auth/*
    A->>P: Consulta o crea usuario
    A-->>G: JWT + datos de usuario
    G-->>C: Respuesta HTTP

    C->>G: Request protegido con Authorization: Bearer
    G->>R: Verifica que el token no este revocado
    G-->>C: Permite o rechaza acceso
```

## Flujo de creacion de orden

```mermaid
sequenceDiagram
    participant C as Cliente
    participant G as api-gateway
    participant R as redis
    participant W as writer-service
    participant P as postgres
    participant MQ as RabbitMQ
    participant I as inventory-service
    participant N as notification-service
    participant A as analytics-service
    participant PN as postgres-notifications

    C->>G: POST /orders con JWT
    G->>R: Guarda order:{id} = RECEIVED
    G->>W: POST /internal/orders con JWT
    W->>P: Inserta orden
    W->>R: Actualiza order:{id} = PERSISTED
    W->>MQ: Publica order.created en exchange orders
    MQ-->>I: Entrega evento a inventory.order.created
    MQ-->>N: Entrega evento a notification.order.created
    MQ-->>A: Entrega evento a analytics.order.created
    I->>P: Descuenta stock
    N->>PN: Guarda notificacion
    A->>R: Incrementa metricas
    W-->>G: Orden persistida
    G-->>C: order_id y status
```

## Mensajeria

El `writer-service` publica eventos `order.created` en el exchange `orders`, declarado como `fanout`. Cada consumidor tiene su propia cola durable, por lo que todos reciben una copia del evento:

- `inventory.order.created`: descuenta stock de los productos de la orden.
- `notification.order.created`: guarda una notificacion de confirmacion.
- `analytics.order.created`: incrementa contadores como `metrica:ordenes_creadas` y `metrica:productos_pedidos`.

Este desacoplamiento permite que la escritura de la orden responda por HTTP mientras los procesos derivados ocurren de forma asincrona.

## Seguridad

- Las rutas publicas son `GET /health`, `POST /auth/register` y `POST /auth/login`.
- Las rutas de negocio requieren `Authorization: Bearer <token>`.
- El JWT incluye `sub`, `email`, `role` y `exp`.
- `api-gateway`, `writer-service` e `inventory-service` validan el token localmente.
- `auth-service` revoca tokens guardando una entrada temporal en Redis hasta su expiracion.
- `writer-service` filtra ordenes por usuario, salvo usuarios con rol `admin`.

## Despliegue local

```bash
docker compose up --build
```

Endpoints principales:

- API Gateway: `http://localhost:8000`
- Writer Service: `http://localhost:8001`
- Inventory Service: `http://localhost:8002`
- Auth Service: `http://localhost:8003`
- RabbitMQ Management: `http://localhost:15672`

Health checks utiles:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Variables de entorno relevantes

| Variable | Uso |
| --- | --- |
| `JWT_SECRET` | Llave para firmar y validar JWT. |
| `JWT_ALGORITHM` | Algoritmo JWT, por defecto `HS256`. |
| `JWT_EXPIRE_MINUTES` | Tiempo de vida del token. |
| `DATABASE_URL` | Conexion a PostgreSQL principal. |
| `NOTIFICATIONS_DATABASE_URL` | Conexion a PostgreSQL de notificaciones. |
| `REDIS_URL` | Conexion a Redis. |
| `RABBITMQ_URL` | Conexion AMQP a RabbitMQ. |
| `ORDERS_EXCHANGE` | Exchange de eventos de ordenes, por defecto `orders`. |
| `AUTH_SERVICE_URL` | URL interna del servicio de autenticacion. |
| `WRITER_SERVICE_URL` | URL interna del servicio de escritura de ordenes. |
