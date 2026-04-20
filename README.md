Sistema distribuido de ordenes con autenticacion JWT

Integrantes

- Anton Betak Licea
- Roberto Villegas Ojeda

Descripcion

El repositorio implementa una arquitectura de microservicios con FastAPI, Docker Compose, RabbitMQ, PostgreSQL y Redis.

Servicios detectados

- `api-gateway`: punto de entrada HTTP del sistema. Expone registro, login, validacion de token y operaciones de ordenes.
- `auth-service`: nuevo microservicio de autenticacion. Registra usuarios, valida credenciales y emite JWT.
- `writer-service`: persiste ordenes en PostgreSQL y publica `order.created` en RabbitMQ.
- `inventory-service`: descuenta inventario al consumir eventos y expone endpoints HTTP para consulta/carga.
- `notification-service`: consume eventos y guarda notificaciones en su propia base PostgreSQL.
- `analytics-service`: consume eventos y guarda metricas simples en Redis.

Infraestructura reutilizada

- PostgreSQL principal: `postgres`, reutilizado para `orders` y `users`.
- PostgreSQL de notificaciones: `postgres-notifications`, sin cambios funcionales.
- Redis: reutilizado para estados rapidos del gateway y metricas de analytics.
- RabbitMQ: se mantiene el exchange `orders` y las colas actuales.

Autenticacion

- El `auth-service` usa la tabla `users` en el PostgreSQL principal.
- Las passwords se almacenan hasheadas con `passlib` y `pbkdf2_sha256`.
- El login emite un JWT firmado con `JWT_SECRET`.
- `POST /auth/logout` revoca el token actual en Redis hasta su expiracion.
- El token incluye `sub`, `email`, `role` y `exp`.
- Las rutas de negocio en `api-gateway`, `writer-service` e `inventory-service` ahora requieren `Authorization: Bearer <token>`.
- Las rutas publicas quedaron limitadas a:
  - `GET /health`
  - `POST /auth/register`
  - `POST /auth/login`

Rutas principales

- Gateway: `http://localhost:8000`
- Auth service directo: `http://localhost:8003`
- Writer service: `http://localhost:8001`
- Inventory service: `http://localhost:8002`

Variables de entorno nuevas

- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `AUTH_SERVICE_URL`

Las variables ya existentes (`DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `WRITER_SERVICE_URL`) se siguen reutilizando.

Levantar el proyecto

```bash
docker compose up --build
```

Health checks utiles

```bash
curl http://localhost:8000/health
curl http://localhost:8003/health
curl http://localhost:8002/health
```

Flujo de prueba

1. Registrar usuario

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'
```

2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'
```

3. Logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer TU_TOKEN"
```

4. Consultar datos del token

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer TU_TOKEN"
```

5. Crear una orden protegida

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN" \
  -d '{
    "customer": "Monica",
    "items": [
      {"sku": "A1", "qty": 2},
      {"sku": "B3", "qty": 1}
    ]
  }'
```

6. Consultar estado de la orden

```bash
curl http://localhost:8000/orders/ORDER_ID \
  -H "Authorization: Bearer TU_TOKEN"
```

7. Cargar inventario protegido

```bash
curl -X POST http://localhost:8002/inventory/seed \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN" \
  -d '{"sku":"A1","stock":10}'
```

8. Consultar inventario protegido

```bash
curl http://localhost:8002/inventory/A1 \
  -H "Authorization: Bearer TU_TOKEN"
```

Casos esperados de seguridad

- Sin token:

```bash
curl http://localhost:8000/orders/ORDER_ID
```

Respuesta esperada: `401 Unauthorized`

- Token invalido:

```bash
curl http://localhost:8000/orders/ORDER_ID \
  -H "Authorization: Bearer token-invalido"
```

Respuesta esperada: `401 Unauthorized`

Mensajeria

- `writer-service` sigue publicando `order.created`.
- `inventory-service`, `notification-service` y `analytics-service` siguen consumiendo el mismo flujo.
- La autenticacion HTTP no modifica exchanges, colas ni routing keys.

Notas tecnicas

- El gateway reenvia el header `Authorization` al `writer-service`.
- La validacion JWT tambien se hace localmente dentro de `writer-service` e `inventory-service` para evitar bypass si se les llama directamente dentro de la red Docker.
- No se agrego un nuevo contenedor de Postgres ni de Redis para auth; se reutiliza la infraestructura existente.
