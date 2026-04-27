import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://orders_user:orders_pass@postgres:5432/orders_db"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")

ORDERS_EXCHANGE = os.getenv("ORDERS_EXCHANGE", "orders")

INVENTORY_QUEUE = os.getenv("INVENTORY_QUEUE", "inventory.order.created")

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
