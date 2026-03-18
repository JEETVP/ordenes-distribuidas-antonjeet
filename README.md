Diseño de App Distribuida de Órdenes

Integrantes

- Anton Betak Licea
- Roberto Villegas Ojeda

Descripción

Este proyecto maneja ordenes usando varios servicios pequeños.

Lo que ya hacía el proyecto:

- `api-gateway` recibe la orden.
- guarda un estado rápido en Redis.
- manda la orden a `writer-service`.
- `writer-service` la guarda en PostgreSQL.

Lo nuevo que se agregó

Siguiendo el ejemplo visto en clase, despues de guardar la orden se publica un evento en RabbitMQ.

Ese evento es:

`order.created`

Después de eso:

- `inventory-service` escucha el evento y descuenta stock.
- `notification-service` escucha el mismo evento y manda una confirmacion simple por log.
- `analytics-service` escucha el mismo evento y registra una metrica sencilla.

Arquitectura

Cliente
↓
API Gateway
↓
Redis
↓
Writer Service
↓
PostgreSQL
↓
RabbitMQ
↓
Inventory Service
↓
Notification Service

Servicios

`api-gateway`

- expone `POST /orders`
- expone `GET /orders/{order_id}`

`writer-service`

- recibe la orden desde el gateway
- la guarda en PostgreSQL
- publica `order.created` en RabbitMQ

`inventory-service`

- tiene una tabla sencilla de inventario
- escucha eventos `order.created`
- resta stock por cada item de la orden
- expone endpoints para consultar y cargar stock

`notification-service`

- escucha eventos `order.created`
- imprime en consola una confirmacion

`analytics-service`

- escucha eventos `order.created`
- guarda metricas simples en Redis
- cuenta cuantas ordenes se han creado
- cuenta cuantos productos se pidieron en total

RabbitMQ

Se usa un exchange tipo `fanout` llamado:

`orders`

Asi un mismo evento le llega tanto a inventario como a notificaciones.
Tambien le llega a analytics.

Base de datos

Se usan dos tablas dentro de PostgreSQL:

- `orders`
- `inventory_items`

Levantar el proyecto

```bash
docker compose up --build
```

Puertos

- gateway: `8000`
- writer-service: `8001`
- inventory-service: `8002`
- postgres: `5432`
- redis: `6379`
- rabbitmq: `5672`

Probar inventario

Primero cargar stock:

```bash
curl -X POST http://localhost:8002/inventory/seed \
  -H "Content-Type: application/json" \
  -d '{"sku":"A1","stock":10}'
```

```bash
curl -X POST http://localhost:8002/inventory/seed \
  -H "Content-Type: application/json" \
  -d '{"sku":"B3","stock":5}'
```

Luego crear una orden:

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "Monica",
    "items": [
      {"sku": "A1", "qty": 2},
      {"sku": "B3", "qty": 1}
    ]
  }'
```

Despues revisar el inventario:

```bash
curl http://localhost:8002/inventory/A1
```

```bash
curl http://localhost:8002/inventory/B3
```

Ver notificacion

```bash
docker compose logs notification-service
```

Ver metrica

```bash
docker compose logs analytics-service
```

Ejemplo del evento

```json
{
  "event": "order.created",
  "order_id": "ORD-001",
  "customer": "Monica",
  "items": [
    { "sku": "A1", "qty": 2 },
    { "sku": "B3", "qty": 1 }
  ]
}
```

Comentario final

La idea principal de esta version es mostrar como una orden puede generar un evento y como otros servicios reaccionan sin que el gateway les tenga que hablar directo.
